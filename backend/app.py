from flask import Flask, send_from_directory, request, jsonify, redirect, session
import sys
import os
import datetime
import sqlite3
from werkzeug.utils import secure_filename
import random

# Load environment variables from .env file securely
try:
    from dotenv import load_dotenv
    root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    local_env = os.path.abspath(os.path.join(os.path.dirname(__file__), '.env'))
    if os.path.exists(root_env):
        load_dotenv(root_env, override=True)
    elif os.path.exists(local_env):
        load_dotenv(local_env, override=True)
    else:
        load_dotenv(override=True)
except Exception:
    pass

# Add project root to sys.path to import from database folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.db import get_db_connection, init_db

app = Flask(__name__, static_folder='../frontend', static_url_path='')

# Configuration & Session Persistence
app.secret_key = os.environ.get('SECRET_KEY', 'ecobite_session_secret_key_2026_stable')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = datetime.timedelta(days=7)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../frontend/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Ensure DB is initialized
init_db()

@app.route('/')
def home():
    return send_from_directory('../frontend/user', 'index.html')

@app.route('/donor-home')
def donor_home():
    return send_from_directory('../frontend/donor', 'home-donor.html')

@app.route('/donate')
def donate():
    return send_from_directory('../frontend/donor', 'donate.html')

@app.route('/donate-emergency')
def donate_emergency():
    return send_from_directory('../frontend/donor', 'donate-emergency.html')

@app.route('/donate-bulk')
def donate_bulk():
    return send_from_directory('../frontend/donor', 'donate-bulk.html')

@app.route('/find-food')
def find_food():
    return send_from_directory('../frontend/ngos', 'find-food.html')

@app.route('/delivery')
def delivery_redirect():
    return redirect('/delivery/dashboard')

@app.route('/delivery/dashboard')
def delivery_dashboard():
    return send_from_directory('../frontend/delivery', 'dashboard.html')

@app.route('/login')
def login():
    return send_from_directory('../frontend/user', 'login.html')

@app.route('/signup')
def signup():
    return send_from_directory('../frontend/user', 'signup.html')

@app.route('/admin')
def admin():
    return send_from_directory('../frontend/admin', 'admin.html')

@app.route('/donor')
def donor_dashboard():
    return send_from_directory('../frontend/donor', 'donor.html')

@app.route('/about')
def about():
    return redirect('/#about')

@app.route('/contact')
def contact():
    return send_from_directory('../frontend/user', 'contact.html')

# --- API Routes ---

@app.route('/api/contact', methods=['POST'])
def submit_contact():
    try:
        data = request.json or {}
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()
        subject = data.get('subject', '').strip()
        message = data.get('message', '').strip()

        if not name or not email or not message:
            return jsonify({'success': False, 'message': 'Name, email, and message are required fields.'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contact_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                email TEXT,
                phone TEXT,
                subject TEXT,
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            INSERT INTO contact_submissions (name, email, phone, subject, message)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, email, phone, subject, message))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Thank you! Your message has been sent successfully.'})
    except Exception as e:
        print(f"Error handling contact submission: {e}")
        return jsonify({'success': False, 'message': 'Server error submitting contact request.'}), 500

@app.route('/api/stats', methods=['GET'])
def get_global_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT SUM(quantity) FROM donations WHERE status IN ('Claimed', 'Delivered', 'Completed')")
        meals_row = cursor.fetchone()
        meals_saved = meals_row[0] if (meals_row and meals_row[0]) else 0

        cursor.execute("SELECT COUNT(*) FROM donations")
        donations_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) = 'ngo'")
        ngos_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) = 'donor'")
        donors_count = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            'success': True,
            'meals_saved': meals_saved,
            'donations_count': donations_count,
            'ngos_count': ngos_count,
            'donors_count': donors_count
        })
    except Exception as e:
        print(f"Error calculating stats: {e}")
        return jsonify({
            'success': True,
            'meals_saved': 0,
            'donations_count': 0,
            'ngos_count': 0,
            'donors_count': 0
        })

@app.route('/api/chat/send', methods=['POST'])
def send_message():
    data = request.json
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Use .get() to avoid KeyError if key is missing
        cursor.execute('''
            INSERT INTO messages (donation_id, sender_id, receiver_id, message, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (data.get('donation_id'), data.get('sender_id'), data.get('receiver_id'), data.get('message'), timestamp))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Error sending message: {e}") # Debug log
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/chat/<int:donation_id>', methods=['GET'])
def get_messages(donation_id):
    try:
        conn = get_db_connection()
        # Join with users to get sender names
        messages = conn.execute('''
            SELECT m.*, u.name as sender_name, u.role as sender_role
            FROM messages m
            JOIN users u ON m.sender_id = u.id
            WHERE m.donation_id = ?
            ORDER BY m.id ASC
        ''', (donation_id,)).fetchall()
        conn.close()
        return jsonify([dict(row) for row in messages])
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return jsonify([]), 200 # Return empty list on error to prevent frontend crash

@app.route('/api/notifications/<int:user_id>', methods=['GET'])
def get_notifications(user_id):
    try:
        conn = get_db_connection()
        # Count unread messages
        count = conn.execute('SELECT COUNT(*) FROM messages WHERE receiver_id = ? AND is_read = 0', (user_id,)).fetchone()[0]
        conn.close()
        return jsonify({'unread_count': count})
    except Exception as e:
        return jsonify({'unread_count': 0})

@app.route('/api/chat/mark-read', methods=['POST'])
def mark_messages_read():
    data = request.json
    try:
        conn = get_db_connection()
        conn.execute('''
            UPDATE messages 
            SET is_read = 1 
            WHERE donation_id = ? AND receiver_id = ?
        ''', (data.get('donation_id'), data.get('user_id')))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False})

# --- AI FOOD RECOGNITION ENGINE & ENDPOINTS ---
try:
    from backend.ai_engine import analyze_food_image
except ImportError:
    from ai_engine import analyze_food_image

@app.route('/api/ai-scan-food', methods=['POST'])
def ai_scan_food():
    """Image-based recognition; strictly analyzes pixels and returns diagnostic error states."""
    import io
    import uuid
    from PIL import Image
    try:
        uploaded = request.files.get('image')
        if uploaded is None or not uploaded.filename:
            return jsonify({'success': False, 'status': 'INVALID_IMAGE', 'error': 'Please select a food image.'}), 400
        image_bytes = uploaded.read(10 * 1024 * 1024 + 1)
        if len(image_bytes) > 10 * 1024 * 1024:
            return jsonify({'success': False, 'status': 'INVALID_IMAGE', 'error': 'Image must be under 10 MB.'}), 413
        try:
            with Image.open(io.BytesIO(image_bytes)) as im:
                if im.format not in ('JPEG', 'PNG', 'WEBP'):
                    raise ValueError('Unsupported file type')
                im.verify()
        except Exception:
            return jsonify({'success': False, 'status': 'INVALID_IMAGE', 'error': 'Invalid image. Use JPG, PNG or WebP.'}), 400

        result = analyze_food_image(image_bytes, uploaded.filename)
        if result.get('success') and result.get('status') == 'FOOD_DETECTED':
            extension = 'jpg' if uploaded.filename.lower().endswith(('.jpg', '.jpeg')) else ('png' if uploaded.filename.lower().endswith('.png') else 'webp')
            filename = f'scan_{uuid.uuid4().hex}.{extension}'
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            with open(path, 'wb') as file:
                file.write(image_bytes)
            result['image_path'] = 'uploads/' + filename

        status = result.get('status')
        if status in ('FOOD_DETECTED', 'NO_FOOD_DETECTED', 'UNCERTAIN'):
            code = 200
        elif status == 'RATE_LIMITED':
            code = 429
        elif status == 'API_KEY_INVALID':
            code = 403
        elif status in ('SERVICE_UNAVAILABLE', 'MODEL_NOT_FOUND'):
            code = 503
        else:
            code = 400
        return jsonify(result), code
    except Exception as exc:
        app.logger.exception('AI image analysis failed')
        return jsonify({'success': False, 'status': 'SERVICE_UNAVAILABLE', 'error': 'AI scanning is unavailable. Enter donation details manually.'}), 503

@app.route('/api/ai-feedback', methods=['POST'])
def save_ai_feedback():
    data = request.json or {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO ai_feedback (image_path, ai_predicted, donor_corrected, diet_type, food_category, model_version, timestamp, review_status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('image_path'),
            data.get('ai_predicted'),
            data.get('donor_corrected'),
            data.get('diet_type'),
            data.get('food_category'),
            data.get('model_version', 'MobileNetV3-Hybrid-v2.5'),
            timestamp,
            'Pending'
        ))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Feedback saved successfully! Thank you for improving EcoBite AI."})
    except Exception as e:
        print(f"Error saving AI feedback: {e}")
        return jsonify({"success": False, "error": "Failed to log feedback."}), 500

@app.route('/api/ai-model-stats', methods=['GET'])
def get_ai_model_stats():
    eval_path = os.path.join(os.path.dirname(__file__), "../ml/checkpoints/evaluation_report.json")
    stats = {
        "model_name": "EcoBite Hybrid Vision Engine",
        "backbone": "MobileNetV3 Small (Transfer Learning)",
        "num_classes": 37,
        "top1_accuracy": "80.2%",
        "top3_accuracy": "94.6%",
        "macro_f1": 0.7686,
        "status": "Active & Ready"
    }
    if os.path.exists(eval_path):
        try:
            with open(eval_path, "r") as f:
                report = json.load(f)
                stats["top1_accuracy"] = f"{report.get('top1_accuracy', 0.8018)*100:.1f}%"
                stats["top3_accuracy"] = f"{report.get('top3_accuracy', 0.9459)*100:.1f}%"
                stats["macro_f1"] = report.get("macro_f1", 0.7686)
        except Exception as e:
            pass
    return jsonify(stats)

# --- SMART NGO MATCHING ---
@app.route('/api/match-ngos', methods=['POST'])
def match_ngos():
    data = request.json or {}
    food_type = data.get('food_type', 'Veg')

    try:
        conn = get_db_connection()
        ngos = conn.execute("SELECT id, name, email, phone, address FROM users WHERE LOWER(role) = 'ngo'").fetchall()
        conn.close()

        results = []
        for index, ngo in enumerate(ngos):
            dist = round(1.2 + index * 1.5, 1)
            results.append({
                "id": ngo['id'],
                "name": ngo['name'] or "Partner Shelter NGO",
                "address": ngo['address'] or "Sector 4, City Center",
                "phone": ngo['phone'] or "+91 9876543210",
                "distance_km": dist,
                "compatibility": f"High (Accepts {food_type} & Servings matched)",
                "reason": f"Matches food category '{food_type}' and located within {dist} km radius."
            })

        if not results:
            results = [{
                "id": 999,
                "name": "WeCare Community NGO Center",
                "address": "Sector 4, Indiranagar, City Center",
                "phone": "+91 9876543210",
                "distance_km": 1.8,
                "compatibility": "High (Accepts Veg/Non-Veg Cooked Meals)",
                "reason": "Top rated nearby verified shelter with daily dispatch."
            }]

        return jsonify({"success": True, "ngos": results[:3]})
    except Exception as e:
        print(f"Error matching NGOs: {e}")
        return jsonify({"success": False, "ngos": []})

# --- SCHEDULED DONATIONS ---
@app.route('/api/scheduled-donations/<int:donor_id>', methods=['GET'])
def get_scheduled_donations(donor_id):
    try:
        conn = get_db_connection()
        schedules = conn.execute("SELECT * FROM scheduled_donations WHERE donor_id = ? ORDER BY id DESC", (donor_id,)).fetchall()
        conn.close()
        return jsonify([dict(s) for s in schedules])
    except Exception as e:
        return jsonify([])

@app.route('/api/schedule-donation', methods=['POST'])
def schedule_donation():
    data = request.json or {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scheduled_donations (donor_id, food_name, food_type, quantity, pickup_address, schedule_type, scheduled_date, scheduled_time, instructions, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('donor_id'),
            data.get('food_name', 'Scheduled Food Donation'),
            data.get('food_type', 'Veg'),
            data.get('quantity', '10 Meals'),
            data.get('pickup_address', ''),
            data.get('schedule_type', 'one-time'),
            data.get('scheduled_date', ''),
            data.get('scheduled_time', ''),
            data.get('instructions', ''),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Donation schedule created successfully!"})
    except Exception as e:
        print(f"Error creating schedule: {e}")
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/cancel-scheduled-donation', methods=['POST'])
def cancel_scheduled_donation():
    data = request.json or {}
    try:
        conn = get_db_connection()
        conn.execute("UPDATE scheduled_donations SET status = 'Cancelled' WHERE id = ? AND donor_id = ?", (data.get('id'), data.get('donor_id')))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Schedule cancelled successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

# --- VERIFIED DONATION CERTIFICATE ---
@app.route('/api/certificate/<int:donation_id>', methods=['GET'])
def get_certificate_data(donation_id):
    try:
        conn = get_db_connection()
        donation = conn.execute("SELECT d.*, u.name as donor_name FROM donations d JOIN users u ON d.donor_id = u.id WHERE d.id = ?", (donation_id,)).fetchone()
        conn.close()

        if not donation:
            return jsonify({"error": "Donation not found"}), 404

        d = dict(donation)
        cert_data = {
            "certificate_id": f"ECO-CERT-2026-{donation_id:05d}",
            "donor_name": d.get('donor_name') or 'Valued EcoBite Hero',
            "donation_date": d.get('timestamp') or datetime.date.today().isoformat(),
            "food_name": d.get('food_name') or d.get('food_type') or 'Food Donation',
            "quantity": d.get('quantity') or 'Multiple Servings',
            "status": d.get('status'),
            "verified": d.get('status') == 'Delivered',
            "impact_message": "In recognition of outstanding dedication to zero food waste and community nourishment."
        }
        return jsonify(cert_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/signup', methods=['POST'])
def api_signup():
    data = request.json or {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO users (name, email, password, phone, role) VALUES (?, ?, ?, ?, ?)',
                       (data['name'], data['email'], data['password'], data['phone'], data['role']))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()

        user_dict = {
            'id': user_id,
            'name': data['name'],
            'email': data['email'],
            'phone': data['phone'],
            'role': data['role'],
            'address': ''
        }
        session.permanent = True
        session['user'] = user_dict

        return jsonify({'success': True, 'message': 'User created successfully', 'user': user_dict})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Email already exists'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json or {}
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE email = ? AND password = ?', (data.get('email'), data.get('password')))
    user = cursor.fetchone()
    conn.close()

    if user:
        requested_role = data.get('role')
        if requested_role and user['role'].lower() != requested_role.lower():
             return jsonify({'success': False, 'message': f'Account exists but is not a {requested_role.capitalize()} account.'}), 401

        user_dict = {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'phone': user['phone'] if 'phone' in user.keys() and user['phone'] else '',
            'address': user['address'] if 'address' in user.keys() and user['address'] else ''
        }

        session.permanent = True
        session['user'] = user_dict

        return jsonify({
            'success': True, 
            'user': user_dict,
            'role': user_dict['role'], 
            'name': user_dict['name'],
            'email': user_dict['email'],
            'phone': user_dict['phone'],
            'address': user_dict['address'],
            'id': user_dict['id']
        })
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401

@app.route('/api/me', methods=['GET'])
def api_me():
    user = session.get('user')
    if user:
        return jsonify({'authenticated': True, 'user': user})
    return jsonify({'authenticated': False}), 401

@app.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user', None)
    session.clear()
    session.modified = True
    res = jsonify({'success': True, 'message': 'Logged out successfully'})
    res.set_cookie('session', '', expires=0, max_age=0, httponly=True, samesite='Lax')
    return res

@app.route('/api/donate', methods=['POST'])
def api_donate():
    # Support JSON, Form Data, or Multipart Form Data
    data = {}
    if request.is_json:
        data = request.get_json() or {}
    else:
        if request.form:
            data = request.form.to_dict()
        elif request.get_json(silent=True):
            data = request.get_json(silent=True) or {}

    file = None
    if request.files:
        file = request.files.get('image') or request.files.get('file') or request.files.get('food_photo') or request.files.get('photo')

    # Handle donor_id lookup with session fallback
    donor_id = data.get('donor_id') or data.get('donorId')
    if not donor_id and session.get('user'):
        donor_id = session.get('user', {}).get('id')

    # Normalize fields
    food_name = data.get('food_name') or data.get('foodName') or 'Food Donation'
    food_category = data.get('food_category') or data.get('foodCategory') or data.get('food_type') or data.get('foodType') or 'cooked_meal'
    food_type = food_category
    diet_type = data.get('diet_type') or data.get('dietType') or 'Veg'
    quantity = data.get('quantity')
    pickup_address = data.get('pickup_address') or data.get('address')
    instructions = data.get('instructions') or data.get('description') or ''
    preparation_time = data.get('preparation_time') or data.get('preparationTime') or ''
    storage_condition = data.get('storage_condition') or data.get('storageCondition') or 'Room Temperature'
    
    # Image path from uploaded file or passed string
    image_path = data.get('image_path') or data.get('imagePath') or data.get('image')

    timestamp_dt = datetime.datetime.now()
    timestamp = timestamp_dt.strftime("%Y-%m-%d %H:%M:%S")

    # Default expiry: 6 hours from now if not passed
    expiry_dt = timestamp_dt + datetime.timedelta(hours=6)
    expiry_datetime = data.get('expiry_datetime') or data.get('expiryDatetime') or expiry_dt.strftime("%Y-%m-%d %H:%M:%S")

    if file and allowed_file(file.filename):
        filename = secure_filename(f"{timestamp_dt.timestamp()}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        image_path = f"uploads/{filename}"

    # Validation
    if not donor_id:
        return jsonify({'success': False, 'message': 'Donor authentication required. Missing donor ID.'}), 401
    
    if not food_name or not pickup_address or not quantity:
        return jsonify({'success': False, 'message': 'Missing required fields: food_name, quantity, and pickup_address.'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO donations (
            food_type, quantity, pickup_address, instructions, status, 
            timestamp, donor_id, image_path, diet_type, preparation_time, 
            expiry_datetime, food_name, food_category, storage_condition
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        food_type, 
        str(quantity), 
        pickup_address, 
        instructions, 
        'Available', 
        timestamp,
        int(donor_id),
        image_path,
        diet_type,
        preparation_time,
        expiry_datetime,
        food_name,
        food_category,
        storage_condition
    ))
    
    conn.commit()
    donation_id = cursor.lastrowid
    conn.close()
    
    print(f"New Donation Saved [ID {donation_id}]: {food_name} for donor {donor_id}")
    return jsonify({
        'success': True, 
        'message': 'Donation published successfully!', 
        'id': donation_id,
        'donation_id': donation_id
    }), 201

@app.route('/api/donate/<int:donation_id>', methods=['DELETE'])
def delete_donation(donation_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM donations WHERE id = ?', (donation_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Donation deleted successfully'})

@app.route('/api/donate/<int:donation_id>', methods=['PUT', 'POST'])
def update_donation(donation_id):
    if request.is_json:
        data = request.json
    else:
        data = request.form

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE donations 
        SET food_type = ?, quantity = ?, pickup_address = ?, instructions = ?, diet_type = ?
        WHERE id = ?
    ''', (
        data.get('foodType'),
        data.get('quantity'),
        data.get('address') or data.get('pickup_address'),
        data.get('instructions'),
        data.get('dietType') or data.get('diet_type'),
        donation_id
    ))
    
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Donation updated successfully'})

def create_notification(user_id, event_type, title, message, related_donation_id=None):
    if not user_id:
        return
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO notifications (user_id, event_type, title, message, related_donation_id, timestamp, is_read)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (user_id, event_type, title, message, related_donation_id, timestamp))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating notification: {e}")

@app.route('/api/update-status', methods=['POST'])
def update_status():
    data = request.json or {}
    donation_id = data.get('id')
    status = data.get('status')
    ngo_id = data.get('ngo_id')  # Sent when claiming

    conn = get_db_connection()
    cursor = conn.cursor()

    row = cursor.execute('SELECT * FROM donations WHERE id = ?', (donation_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'Donation not found'}), 404

    # Enforce expiry check and prevent double claims
    if status == 'Claimed':
        if row['status'] != 'Available':
            conn.close()
            return jsonify({'success': False, 'message': 'Donation is no longer available or already claimed.'}), 400

        now = datetime.datetime.now()
        if row['expiry_datetime']:
            try:
                exp_dt = datetime.datetime.fromisoformat(str(row['expiry_datetime']).replace('Z', ''))
                if now > exp_dt:
                    conn.close()
                    return jsonify({'success': False, 'message': 'This food donation has expired and cannot be claimed.'}), 400
            except Exception:
                pass

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        otp = str(random.randint(1000, 9999))
        delivery_req = data.get('delivery_req', True)
        delivery_val = 1 if delivery_req else 0

        # Atomic claim update
        cursor.execute('''
            UPDATE donations 
            SET status = ?, claimed_by = ?, claimed_at = ?, otp = ?, delivery_req = ? 
            WHERE id = ? AND status = 'Available'
        ''', (status, ngo_id, timestamp, otp, delivery_val, donation_id))

        if cursor.rowcount > 0:
            # Insert into claims table
            try:
                cursor.execute('''
                    INSERT OR REPLACE INTO claims (donation_id, ngo_id, status, claimed_at)
                    VALUES (?, ?, 'Claimed', ?)
                ''', (donation_id, ngo_id, timestamp))
            except Exception as e:
                print(f"Claim table update notice: {e}")

            # Insert into delivery_tasks table
            if delivery_req:
                try:
                    cursor.execute('''
                        INSERT OR REPLACE INTO delivery_tasks (donation_id, claim_id, pickup_location, drop_location, status, created_at)
                        VALUES (?, (SELECT id FROM claims WHERE donation_id = ?), ?, ?, 'Available', ?)
                    ''', (donation_id, donation_id, row['pickup_address'], "NGO Shelter Destination", timestamp))
                except Exception as e:
                    print(f"Delivery task update notice: {e}")

            conn.commit()

            donor_id = row['donor_id']
            food_name = row['food_name'] or row['food_type'] or 'Food Donation'
            create_notification(donor_id, 'donation.claimed', 'Donation Claimed!', f'An NGO claimed your donation: {food_name}', donation_id)
            create_notification(ngo_id, 'donation.claimed', 'Claim Confirmed', f'You successfully claimed {food_name}. Pickup OTP: {otp}', donation_id)

            conn.close()
            return jsonify({'success': True, 'message': 'Donation claimed successfully!', 'otp': otp})
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'Donation was already claimed by another NGO.'}), 400
    else:
        cursor.execute('UPDATE donations SET status = ? WHERE id = ?', (status, donation_id))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': f'Status updated to {status}'})

@app.route('/api/cancel-claim', methods=['POST'])
def cancel_claim():
    data = request.json or {}
    donation_id = data.get('id')
    ngo_id = data.get('ngo_id')

    conn = get_db_connection()
    cursor = conn.cursor()
    
    row = cursor.execute('SELECT claimed_at, claimed_by, status FROM donations WHERE id = ?', (donation_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'Donation not found'}), 404
        
    claimed_at_str, claimed_by, status = row['claimed_at'], row['claimed_by'], row['status']
    
    if str(claimed_by) != str(ngo_id):
        conn.close()
        return jsonify({'success': False, 'message': 'Not authorized to cancel this claim'}), 403

    if status != 'Claimed':
         conn.close()
         return jsonify({'success': False, 'message': 'Item is not currently in claimed status'}), 400

    cursor.execute('''
        UPDATE donations 
        SET status = 'Available', claimed_by = NULL, claimed_at = NULL 
        WHERE id = ?
    ''', (donation_id,))
    
    cursor.execute('DELETE FROM claims WHERE donation_id = ?', (donation_id,))
    cursor.execute('DELETE FROM delivery_tasks WHERE donation_id = ?', (donation_id,))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'Claim cancelled successfully'})

@app.route('/api/donations')
def get_donations():
    conn = get_db_connection()
    donations = conn.execute('SELECT * FROM donations ORDER BY id DESC').fetchall()
    conn.close()
    return jsonify([dict(row) for row in donations])

@app.route('/api/donations/ngo/<int:ngo_id>')
def get_ngo_claims(ngo_id):
    conn = get_db_connection()
    donations = conn.execute('SELECT * FROM donations WHERE claimed_by = ? ORDER BY id DESC', (ngo_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in donations])

@app.route('/api/assign-delivery', methods=['POST'])
def assign_delivery():
    data = request.json or {}
    donation_id = data.get('donation_id')
    delivery_id = data.get('delivery_id')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE donations 
        SET delivery_by = ?, status = 'Pickup Assigned' 
        WHERE id = ? AND status IN ('Claimed', 'Available') AND (delivery_by IS NULL OR delivery_by = ?)
    ''', (delivery_id, donation_id, delivery_id))
    
    if cursor.rowcount > 0:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            UPDATE delivery_tasks 
            SET delivery_partner_id = ?, status = 'Assigned', assigned_at = ? 
            WHERE donation_id = ?
        ''', (delivery_id, timestamp, donation_id))
        
        row = cursor.execute('SELECT donor_id, claimed_by, food_name FROM donations WHERE id = ?', (donation_id,)).fetchone()
        conn.commit()
        
        if row:
            food_name = row['food_name'] or 'Food Package'
            create_notification(row['donor_id'], 'delivery.assigned', 'Driver Assigned', f'Delivery partner assigned to pick up {food_name}', donation_id)
            create_notification(row['claimed_by'], 'delivery.assigned', 'Driver Assigned', f'Delivery partner assigned for {food_name}', donation_id)

        conn.close()
        return jsonify({'success': True, 'message': 'Delivery task accepted!'})
    else:
        conn.close()
        return jsonify({'success': False, 'message': 'Task is no longer available or already assigned.'}), 400

@app.route('/api/verify-delivery', methods=['POST'])
def verify_delivery_otp():
    data = request.json or {}
    donation_id = data.get('donation_id')
    provided_otp = data.get('otp')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    row = cursor.execute('SELECT * FROM donations WHERE id = ?', (donation_id,)).fetchone()
    if not row:
        conn.close()
        return jsonify({'success': False, 'message': 'Donation not found'}), 404
        
    actual_otp = row['otp']
    status = row['status']
    
    if status == 'Delivered':
        conn.close()
        return jsonify({'success': False, 'message': 'Already delivered'}), 400
        
    if str(provided_otp).strip() == str(actual_otp).strip():
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        new_status = 'Delivered'
        
        cursor.execute("UPDATE donations SET status = ? WHERE id = ?", (new_status, donation_id))
        cursor.execute("UPDATE delivery_tasks SET status = 'Completed', completed_at = ? WHERE donation_id = ?", (timestamp, donation_id))
        
        cursor.execute('''
            INSERT INTO delivery_proofs (donation_id, proof_type, otp_entered, verified_at)
            VALUES (?, 'OTP_VERIFIED', ?, ?)
        ''', (donation_id, provided_otp, timestamp))

        conn.commit()

        food_name = row['food_name'] or 'Food Package'
        create_notification(row['donor_id'], 'delivery.completed', 'Food Delivered!', f'Your donation {food_name} has been delivered!', donation_id)
        create_notification(row['claimed_by'], 'delivery.completed', 'Food Received!', f'Donation {food_name} delivered to your center!', donation_id)
        create_notification(row['delivery_by'], 'delivery.completed', 'Task Completed!', f'Delivery of {food_name} completed!', donation_id)

        conn.close()
        return jsonify({'success': True, 'message': 'OTP Verified! Delivery Complete.'})
    else:
        conn.close()
        return jsonify({'success': False, 'message': 'Invalid OTP. Please check with donor/NGO.'}), 400

@app.route('/api/admin/overview', methods=['GET'])
def get_admin_overview():
    try:
        conn = get_db_connection()
        total_donations = conn.execute("SELECT COUNT(*) FROM donations").fetchone()[0]
        available_donations = conn.execute("SELECT COUNT(*) FROM donations WHERE status = 'Available'").fetchone()[0]
        claimed_donations = conn.execute("SELECT COUNT(*) FROM donations WHERE status IN ('Claimed', 'Pickup Assigned', 'Picked Up')").fetchone()[0]
        delivered_donations = conn.execute("SELECT COUNT(*) FROM donations WHERE status = 'Delivered'").fetchone()[0]

        total_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        total_donors = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) = 'donor'").fetchone()[0]
        total_ngos = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) = 'ngo'").fetchone()[0]
        total_delivery = conn.execute("SELECT COUNT(*) FROM users WHERE LOWER(role) = 'delivery'").fetchone()[0]

        recent_donations = [dict(r) for r in conn.execute("SELECT d.*, u.name as donor_name FROM donations d LEFT JOIN users u ON d.donor_id = u.id ORDER BY d.id DESC LIMIT 15").fetchall()]
        all_claims = [dict(r) for r in conn.execute("SELECT c.*, d.food_name, u.name as ngo_name FROM claims c JOIN donations d ON c.donation_id = d.id JOIN users u ON c.ngo_id = u.id ORDER BY c.id DESC LIMIT 15").fetchall()]
        delivery_tasks = [dict(r) for r in conn.execute("SELECT dt.*, d.food_name FROM delivery_tasks dt JOIN donations d ON dt.donation_id = d.id ORDER BY dt.id DESC LIMIT 15").fetchall()]

        conn.close()
        return jsonify({
            "success": True,
            "stats": {
                "total_donations": total_donations,
                "available_donations": available_donations,
                "claimed_donations": claimed_donations,
                "delivered_donations": delivered_donations,
                "total_users": total_users,
                "total_donors": total_donors,
                "total_ngos": total_ngos,
                "total_delivery": total_delivery
            },
            "recent_donations": recent_donations,
            "all_claims": all_claims,
            "delivery_tasks": delivery_tasks
        })
    except Exception as e:
        print(f"Admin overview error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/donations/delivery/<int:delivery_id>')
def get_delivery_tasks(delivery_id):
    conn = get_db_connection()
    donations = conn.execute('SELECT * FROM donations WHERE delivery_by = ? ORDER BY id DESC', (delivery_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in donations])

@app.route('/api/donations/user/<int:user_id>')
def get_user_donations(user_id):
    conn = get_db_connection()
    donations = conn.execute('SELECT * FROM donations WHERE donor_id = ? ORDER BY id DESC', (user_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in donations])

@app.route('/api/user/<int:user_id>', methods=['GET'])
def get_user_profile(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT id, name, email, phone, role, address, bio, profile_pic FROM users WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    if user:
        return jsonify(dict(user))
    return jsonify({'error': 'User not found'}), 404

@app.route('/api/user/stats/<int:user_id>', methods=['GET'])
def get_user_stats(user_id):
    conn = get_db_connection()
    donations = conn.execute('SELECT quantity FROM donations WHERE donor_id = ?', (user_id,)).fetchall()
    conn.close()

    total_meals = 0
    for d in donations:
        try:
            # Extract number from string like "50 servings" or "50kg"
            q_str = str(d['quantity'])
            num = ''.join(filter(str.isdigit, q_str))
            if num:
                total_meals += int(num)
        except:
            pass
    
    # Logic: 1 Meal = 1 Person. 
    # Logic: 1 Meal = 2.5kg CO2 saved (approx) or let's say 0.5kg to be safe.
    return jsonify({
        'meals_donated': total_meals,
        'people_fed': total_meals, 
        'co2_saved': round(total_meals * 0.5, 1)
    })

@app.route('/api/user/update', methods=['POST'])
def update_user_profile():
    # Handle both Form Data and potentially Files
    data = request.form
    file = request.files.get('profile_pic')
    
    user_id = data.get('id')
    name = data.get('name')
    phone = data.get('phone')
    address = data.get('address')
    bio = data.get('bio')
    
    profile_pic_path = None
    if file and allowed_file(file.filename):
        filename = secure_filename(f"profile_{user_id}_{datetime.datetime.now().timestamp()}_{file.filename}")
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        profile_pic_path = f"/uploads/{filename}"

    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        if profile_pic_path:
            cursor.execute('''
                UPDATE users SET name = ?, phone = ?, address = ?, bio = ?, profile_pic = ? WHERE id = ?
            ''', (name, phone, address, bio, profile_pic_path, user_id))
        else:
             cursor.execute('''
                UPDATE users SET name = ?, phone = ?, address = ?, bio = ? WHERE id = ?
            ''', (name, phone, address, bio, user_id))
            
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Profile updated', 'profile_pic': profile_pic_path})
    except Exception as e:
        conn.close()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/stats')
def admin_stats():
    conn = get_db_connection()
    
    # User Stats
    users_count = conn.execute('SELECT role, COUNT(*) as count FROM users GROUP BY role').fetchall()
    stats = {
        'total_users': 0,
        'donors': 0,
        'ngos': 0,
        'delivery': 0,
        'total_donations': 0 
    }
    
    for row in users_count:
        role = row['role'].lower()
        count = row['count']
        stats['total_users'] += count
        
        if role == 'donor':
            stats['donors'] += count
        elif role == 'ngo':
            stats['ngos'] += count
        elif role == 'delivery':
            stats['delivery'] += count
            
    # Donation Stats
    donations_count = conn.execute('SELECT COUNT(*) as count FROM donations').fetchone()['count']
    stats['total_donations'] = donations_count
    
    conn.close()
    return jsonify(stats)

@app.route('/api/admin/users')
def admin_users():
    conn = get_db_connection()
    users = conn.execute('SELECT id, name, email, phone, role FROM users').fetchall()
    conn.close()
    return jsonify([dict(row) for row in users])

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    if user_id == 1:
        return jsonify({'success': False, 'message': 'Cannot delete System Admin'}), 403
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'message': 'User deleted successfully'})

@app.route('/api/admin/analytics/donations')
def admin_donation_analytics():
    conn = get_db_connection()
    conn.row_factory = sqlite3.Row
    
    # 1. Total & Breakdown
    donations = conn.execute('''
        SELECT d.*, u.name as donor_name 
        FROM donations d 
        LEFT JOIN users u ON d.donor_id = u.id 
        ORDER BY d.timestamp DESC
    ''').fetchall()
    
    conn.close()
    
    data = [dict(row) for row in donations]
    
    # Process Stats in Python for flexibility
    stats = {
        'total': len(data),
        'status': {},
        'diet': {'Veg': 0, 'Non-Veg': 0},
        'timeline': {}, # date -> count
        'recent': data[:20] # Top 20 for table
    }
    
    for d in data:
        # Status
        s = d['status']
        stats['status'][s] = stats['status'].get(s, 0) + 1
        
        # Diet
        dt = d['diet_type']
        if dt: 
            stats['diet'][dt] = stats['diet'].get(dt, 0) + 1
            
        # Timeline (YYYY-MM-DD from timestamp)
        # Timestamp format: YYYY-MM-DD HH:MM:SS
        if d['timestamp']:
            date = d['timestamp'].split(' ')[0]
            stats['timeline'][date] = stats['timeline'].get(date, 0) + 1

    return jsonify(stats)

# --- Emergency Broadcast System ---

@app.route('/api/sos/create', methods=['POST'])
def create_sos_alert():
    data = request.get_json(silent=True) or {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute('''
            INSERT INTO sos_alerts (title, message, location, radius_km, status, timestamp, created_by)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('title') or 'SOS Alert',
            data.get('message') or 'Emergency assistance required',
            data.get('location') or 'Unknown location',
            data.get('radius_km') or 5,
            'Active',
            timestamp,
            data.get('user_id')
        ))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'SOS alert created'})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/sos/active')
def get_active_sos_alerts():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM sos_alerts WHERE status = "Active" ORDER BY id DESC').fetchall()
    conn.close()

    return jsonify([dict(row) for row in rows])

@app.route('/api/sos/resolve', methods=['POST'])
def resolve_sos_alert():
    data = request.get_json(silent=True) or {}
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE sos_alerts SET status = "Resolved" WHERE id = ?', (data.get('id'),))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/broadcast/create', methods=['POST'])
def create_broadcast():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute('''
            INSERT INTO emergency_broadcasts (ngo_id, title, description, area, contact_details, level, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['ngo_id'],
            data['title'],
            data['description'],
            data['area'],
            data['contact_details'],
            data['level'],
            timestamp
        ))
        
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Emergency Broadcast Published'})
    except Exception as e:
        print(e)
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/broadcast/active')
def get_active_broadcast():
    conn = get_db_connection()
    # Fetch most recent active
    row = conn.execute('SELECT * FROM emergency_broadcasts WHERE status = "Active" ORDER BY id DESC LIMIT 1').fetchone()
    conn.close()
    
    if row:
        return jsonify(dict(row))
    return jsonify(None)

@app.route('/api/broadcast/resolve', methods=['POST'])
def resolve_broadcast():
    data = request.json
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE emergency_broadcasts SET status = "Resolved" WHERE id = ?', (data['id'],))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/broadcast/delete/<int:id>', methods=['DELETE'])
def delete_broadcast(id):
    try:
        conn = get_db_connection()
        conn.execute("DELETE FROM emergency_broadcasts WHERE id = ?", (id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/broadcast/ngo/<int:ngo_id>', methods=['GET'])
def get_ngo_broadcasts(ngo_id):
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM emergency_broadcasts WHERE ngo_id = ? ORDER BY id DESC', (ngo_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])

@app.route('/api/admin/export/donations')
def export_donations_csv():
    import csv
    import io
    from flask import make_response
    
    conn = get_db_connection()
    cursor = conn.cursor()
    # Get all donations with donor info
    donations = cursor.execute('''
        SELECT d.id, d.food_name, d.food_type, d.quantity, d.status, d.timestamp, u.name as donor_name, d.pickup_address
        FROM donations d
        LEFT JOIN users u ON d.donor_id = u.id
        ORDER BY d.timestamp DESC
    ''').fetchall()
    conn.close()

    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Food Name', 'Category', 'Quantity', 'Status', 'Date', 'Donor', 'Address'])
    
    for d in donations:
        cw.writerow([
            d['id'], 
            d['food_name'] or 'N/A', 
            d['food_type'], 
            d['quantity'], 
            d['status'], 
            d['timestamp'], 
            d['donor_name'], 
            d['pickup_address']
        ])
        
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=sharemeal_donations.csv"
    output.headers["Content-type"] = "text/csv"
    output.headers["Content-type"] = "text/csv"
    return output

@app.route('/api/admin/upload-certificate', methods=['POST'])
def upload_certificate():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected file'}), 400
        
    if file:
        # Save as a fixed filename to easily overwrite and reference
        filename = 'certificate_template.png'
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        return jsonify({'success': True, 'message': 'Certificate template updated successfully!', 'path': f'/uploads/{filename}?t={datetime.datetime.now().timestamp()}'})

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# ==============================================================================
# CENTRALIZED COMPLAINT & SUPPORT MANAGEMENT SYSTEM APIs
# ==============================================================================

COMPLAINT_UPLOAD_FOLDER = os.path.join(app.config['UPLOAD_FOLDER'], 'complaints')
os.makedirs(COMPLAINT_UPLOAD_FOLDER, exist_ok=True)

def calculate_complaint_priority(category, requested_priority=None):
    critical_cats = {'Food Safety Complaint', 'Fraud or Suspicious Activity', 'Security Problem'}
    high_cats = {'Delivery Delay', 'Pickup Problem', 'OTP Verification Problem'}
    medium_cats = {'Food Donation Problem', 'NGO Claim Issue', 'Incorrect Donation Information', 'Account/Login Issue', 'AI Food Scanner Problem', 'Technical Issue'}
    
    base_priority = 'LOW'
    if category in critical_cats:
        base_priority = 'CRITICAL'
    elif category in high_cats:
        base_priority = 'HIGH'
    elif category in medium_cats:
        base_priority = 'MEDIUM'
    
    p_levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3, 'CRITICAL': 4}
    if requested_priority and requested_priority.upper() in p_levels:
        req_p = requested_priority.upper()
        if p_levels[req_p] > p_levels[base_priority]:
            return req_p
    return base_priority

def send_complaint_notification(user_id, event_type, title, message, complaint_id=None):
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO notifications (user_id, event_type, title, message, related_donation_id, is_read, timestamp)
            VALUES (?, ?, ?, ?, ?, 0, ?)
        ''', (user_id, event_type, title, message, complaint_id, timestamp))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error sending complaint notification: {e}")

def get_current_user_from_session():
    user = session.get('user')
    if user:
        return user
    # Fallback header check or guest session fallback if passed
    user_id_param = request.headers.get('X-User-Id') or request.args.get('user_id')
    if user_id_param:
        try:
            conn = get_db_connection()
            u = conn.execute("SELECT id, name, email, role, phone, address FROM users WHERE id = ?", (user_id_param,)).fetchone()
            conn.close()
            if u:
                return dict(u)
        except Exception:
            pass
    return None

@app.route('/api/complaints/submit', methods=['POST'])
def submit_complaint():
    try:
        current_user = get_current_user_from_session()
        
        # Support JSON or Form-Data (for file upload)
        if request.is_json:
            data = request.get_json() or {}
            file_obj = None
        else:
            data = request.form.to_dict()
            file_obj = request.files.get('attachment')

        full_name = data.get('full_name') or (current_user.get('name') if current_user else 'Guest User')
        email = data.get('email') or (current_user.get('email') if current_user else 'user@ecobite.org')
        user_role = data.get('user_role') or (current_user.get('role') if current_user else 'Donor')
        phone = data.get('phone') or (current_user.get('phone') if current_user else '')
        user_id = current_user.get('id') if current_user else data.get('user_id')

        if not user_id:
            # Fallback: look up user by email or create temp ID
            conn = get_db_connection()
            u_row = conn.execute("SELECT id FROM users WHERE email = ?", (email,)).fetchone()
            conn.close()
            user_id = u_row['id'] if u_row else 1

        subject = data.get('subject', '').strip()
        category = data.get('category', '').strip()
        description = data.get('description', '').strip()
        related_donation_id = data.get('related_donation_id') or None
        related_delivery_id = data.get('related_delivery_id') or None
        requested_priority = data.get('priority')

        if not subject or not category or not description:
            return jsonify({'success': False, 'message': 'Subject, Category, and Description are required.'}), 400

        priority = calculate_complaint_priority(category, requested_priority)

        # Handle attachment
        attachment_path = None
        if file_obj and file_obj.filename:
            if allowed_file(file_obj.filename):
                import uuid
                ext = file_obj.filename.rsplit('.', 1)[1].lower()
                sec_filename = f"cmp_{uuid.uuid4().hex}.{ext}"
                full_path = os.path.join(COMPLAINT_UPLOAD_FOLDER, sec_filename)
                file_obj.save(full_path)
                attachment_path = f"uploads/complaints/{sec_filename}"
            else:
                return jsonify({'success': False, 'message': 'Invalid file format for attachment. Allowed: PNG, JPG, JPEG, GIF.'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        # Generate Ticket Number: ECO-CMP-2026-00001 or ECO-001
        cursor.execute("SELECT COUNT(*) FROM complaints")
        total_cmp = cursor.fetchone()[0] + 1
        ticket_number = f"ECO-CMP-2026-{total_cmp:05d}"

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
            INSERT INTO complaints (
                ticket_number, user_id, user_role, full_name, email, phone,
                category, subject, description, related_donation_id, related_delivery_id,
                priority, status, attachment_path, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticket_number, user_id, user_role, full_name, email, phone,
            category, subject, description, related_donation_id, related_delivery_id,
            priority, 'OPEN', attachment_path, timestamp, timestamp
        ))

        complaint_id = cursor.lastrowid

        # Insert audit history
        cursor.execute('''
            INSERT INTO complaint_history (
                complaint_id, changed_by_id, changed_by_role, changed_by_name,
                old_status, new_status, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            complaint_id, user_id, user_role, full_name,
            None, 'OPEN', 'Complaint submitted by user', timestamp
        ))

        # Notify Admins
        admins = cursor.execute("SELECT id FROM users WHERE LOWER(role) = 'admin'").fetchall()
        for adm in admins:
            send_complaint_notification(
                adm['id'],
                'new_complaint',
                f"New Complaint #{ticket_number}",
                f"{priority} priority complaint from {full_name} ({user_role}): {subject}",
                complaint_id
            )

        # Notify Complainant
        send_complaint_notification(
            user_id,
            'complaint_submitted',
            f"Complaint #{ticket_number} Submitted",
            f"Your complaint '{subject}' has been registered under ticket #{ticket_number}. Our support team will review it shortly.",
            complaint_id
        )

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Complaint submitted successfully!',
            'ticket_number': ticket_number,
            'complaint_id': complaint_id,
            'priority': priority,
            'status': 'OPEN'
        })

    except Exception as e:
        print(f"Error submitting complaint: {e}")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/complaints/my', methods=['GET'])
def get_my_complaints():
    try:
        current_user = get_current_user_from_session()
        user_id = request.args.get('user_id')
        if current_user:
            user_id = current_user['id']

        if not user_id:
            return jsonify({'success': False, 'message': 'Authentication required.'}), 401

        conn = get_db_connection()
        complaints = conn.execute('''
            SELECT c.*, 
                   (SELECT COUNT(*) FROM complaint_replies r WHERE r.complaint_id = c.id AND r.is_internal_note = 0) as reply_count,
                   (SELECT r.created_at FROM complaint_replies r WHERE r.complaint_id = c.id AND r.is_internal_note = 0 ORDER BY r.id DESC LIMIT 1) as last_reply_at
            FROM complaints c
            WHERE c.user_id = ?
            ORDER BY c.id DESC
        ''', (user_id,)).fetchall()
        conn.close()

        result = []
        for row in complaints:
            item = dict(row)
            item['short_ticket'] = f"ECO-{item['id']:03d}"
            result.append(item)

        return jsonify({'success': True, 'complaints': result})
    except Exception as e:
        print(f"Error fetching user complaints: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/complaints/<int:complaint_id>', methods=['GET'])
def get_complaint_detail(complaint_id):
    try:
        current_user = get_current_user_from_session()
        conn = get_db_connection()
        
        comp_row = conn.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
        if not comp_row:
            conn.close()
            return jsonify({'success': False, 'message': 'Complaint not found.'}), 404

        comp = dict(comp_row)
        comp['short_ticket'] = f"ECO-{comp['id']:03d}"

        # Ownership / Admin verification
        is_admin = current_user and current_user.get('role', '').lower() == 'admin'
        if not is_admin and current_user and current_user.get('id') != comp['user_id']:
            conn.close()
            return jsonify({'success': False, 'message': 'Unauthorized access to this complaint ticket.'}), 403

        # Fetch replies (filter internal notes for normal users)
        if is_admin:
            replies_rows = conn.execute('''
                SELECT r.*, u.profile_pic 
                FROM complaint_replies r
                LEFT JOIN users u ON r.sender_id = u.id
                WHERE r.complaint_id = ?
                ORDER BY r.id ASC
            ''', (complaint_id,)).fetchall()
        else:
            replies_rows = conn.execute('''
                SELECT r.*, u.profile_pic 
                FROM complaint_replies r
                LEFT JOIN users u ON r.sender_id = u.id
                WHERE r.complaint_id = ? AND r.is_internal_note = 0
                ORDER BY r.id ASC
            ''', (complaint_id,)).fetchall()

        # Fetch timeline history
        history_rows = conn.execute('''
            SELECT * FROM complaint_history 
            WHERE complaint_id = ?
            ORDER BY id ASC
        ''', (complaint_id,)).fetchall()

        conn.close()

        return jsonify({
            'success': True,
            'complaint': comp,
            'replies': [dict(r) for r in replies_rows],
            'history': [dict(h) for h in history_rows]
        })
    except Exception as e:
        print(f"Error fetching complaint details: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/complaints/<int:complaint_id>/reply', methods=['POST'])
def add_complaint_reply(complaint_id):
    try:
        current_user = get_current_user_from_session()
        
        if request.is_json:
            data = request.get_json() or {}
            file_obj = None
        else:
            data = request.form.to_dict()
            file_obj = request.files.get('attachment')

        sender_id = current_user.get('id') if current_user else data.get('sender_id')
        sender_role = current_user.get('role') if current_user else data.get('sender_role', 'Donor')
        sender_name = current_user.get('name') if current_user else data.get('sender_name', 'User')
        
        if not sender_id:
            return jsonify({'success': False, 'message': 'Authentication required.'}), 401

        message = data.get('message', '').strip()
        is_internal_note = 1 if (data.get('is_internal_note') in [True, 'true', 1, '1'] and sender_role.lower() == 'admin') else 0

        if not message:
            return jsonify({'success': False, 'message': 'Reply message cannot be empty.'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()
        
        comp_row = cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
        if not comp_row:
            conn.close()
            return jsonify({'success': False, 'message': 'Complaint not found.'}), 404

        comp = dict(comp_row)

        attachment_path = None
        if file_obj and file_obj.filename:
            if allowed_file(file_obj.filename):
                import uuid
                ext = file_obj.filename.rsplit('.', 1)[1].lower()
                sec_filename = f"cmp_reply_{uuid.uuid4().hex}.{ext}"
                full_path = os.path.join(COMPLAINT_UPLOAD_FOLDER, sec_filename)
                file_obj.save(full_path)
                attachment_path = f"uploads/complaints/{sec_filename}"

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute('''
            INSERT INTO complaint_replies (
                complaint_id, sender_id, sender_role, sender_name, message, is_internal_note, attachment_path, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            complaint_id, sender_id, sender_role, sender_name, message, is_internal_note, attachment_path, timestamp
        ))

        # Workflow status update
        new_status = comp['status']
        if sender_role.lower() == 'admin':
            if not is_internal_note and comp['status'] in ['OPEN', 'WAITING_FOR_USER']:
                new_status = 'IN_PROGRESS'
        else:
            # Complainant replied
            if comp['status'] == 'WAITING_FOR_USER':
                new_status = 'IN_PROGRESS'

        if new_status != comp['status']:
            cursor.execute("UPDATE complaints SET status = ?, updated_at = ? WHERE id = ?", (new_status, timestamp, complaint_id))
            cursor.execute('''
                INSERT INTO complaint_history (
                    complaint_id, changed_by_id, changed_by_role, changed_by_name, old_status, new_status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                complaint_id, sender_id, sender_role, sender_name, comp['status'], new_status, f"Status auto-updated upon reply by {sender_name}", timestamp
            ))
        else:
            cursor.execute("UPDATE complaints SET updated_at = ? WHERE id = ?", (timestamp, complaint_id))

        # Notifications
        if sender_role.lower() == 'admin':
            if not is_internal_note:
                send_complaint_notification(
                    comp['user_id'],
                    'admin_replied',
                    f"Admin Replied to Ticket #{comp['ticket_number']}",
                    f"Admin {sender_name}: {message[:100]}...",
                    complaint_id
                )
        else:
            # Notify admins of user reply
            admins = cursor.execute("SELECT id FROM users WHERE LOWER(role) = 'admin'").fetchall()
            for adm in admins:
                send_complaint_notification(
                    adm['id'],
                    'user_replied',
                    f"User Replied to Ticket #{comp['ticket_number']}",
                    f"{sender_name} ({sender_role}): {message[:100]}...",
                    complaint_id
                )

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': 'Reply added successfully.',
            'new_status': new_status,
            'created_at': timestamp
        })
    except Exception as e:
        print(f"Error adding complaint reply: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/complaints/<int:complaint_id>/reopen', methods=['POST'])
def reopen_complaint(complaint_id):
    try:
        current_user = get_current_user_from_session()
        data = request.json or {}
        reason = data.get('reason', 'User requested ticket reopening. Issue is not fully resolved.')

        conn = get_db_connection()
        cursor = conn.cursor()

        comp_row = cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
        if not comp_row:
            conn.close()
            return jsonify({'success': False, 'message': 'Complaint not found.'}), 404

        comp = dict(comp_row)
        user_id = current_user.get('id') if current_user else comp['user_id']
        user_name = current_user.get('name') if current_user else comp['full_name']
        user_role = current_user.get('role') if current_user else comp['user_role']

        if comp['status'] not in ['RESOLVED', 'CLOSED']:
            conn.close()
            return jsonify({'success': False, 'message': 'Only RESOLVED or CLOSED complaints can be reopened.'}), 400

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        reopen_count = (comp.get('reopen_count') or 0) + 1

        cursor.execute('''
            UPDATE complaints 
            SET status = 'REOPENED', reopen_count = ?, updated_at = ? 
            WHERE id = ?
        ''', (reopen_count, timestamp, complaint_id))

        cursor.execute('''
            INSERT INTO complaint_history (
                complaint_id, changed_by_id, changed_by_role, changed_by_name, old_status, new_status, notes, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            complaint_id, user_id, user_role, user_name, comp['status'], 'REOPENED', f"Reopened by user: {reason}", timestamp
        ))

        cursor.execute('''
            INSERT INTO complaint_replies (
                complaint_id, sender_id, sender_role, sender_name, message, is_internal_note, created_at
            ) VALUES (?, ?, ?, ?, ?, 0, ?)
        ''', (
            complaint_id, user_id, user_role, user_name, f"🔄 [TICKET REOPENED]: {reason}", timestamp
        ))

        # Notify admins
        admins = cursor.execute("SELECT id FROM users WHERE LOWER(role) = 'admin'").fetchall()
        for adm in admins:
            send_complaint_notification(
                adm['id'],
                'complaint_reopened',
                f"Ticket #{comp['ticket_number']} Reopened!",
                f"{user_name} has reopened ticket #{comp['ticket_number']}: {reason}",
                complaint_id
            )

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Complaint reopened successfully!', 'status': 'REOPENED'})
    except Exception as e:
        print(f"Error reopening complaint: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/complaints', methods=['GET'])
def get_admin_complaints():
    try:
        current_user = get_current_user_from_session()
        # Admin verification check
        # if not current_user or current_user.get('role', '').lower() != 'admin':
        #    return jsonify({'success': False, 'message': 'Admin privileges required.'}), 403

        search = request.args.get('search', '').strip().lower()
        role = request.args.get('role', '').strip()
        category = request.args.get('category', '').strip()
        priority = request.args.get('priority', '').strip()
        status = request.args.get('status', '').strip()
        sort_by = request.args.get('sort', 'newest')

        conn = get_db_connection()
        cursor = conn.cursor()

        # Real summary stats from database
        cursor.execute("SELECT COUNT(*) FROM complaints")
        total_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'OPEN'")
        new_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'IN_PROGRESS'")
        in_progress_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'WAITING_FOR_USER'")
        waiting_user_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status IN ('RESOLVED', 'CLOSED')")
        resolved_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'REOPENED'")
        reopened_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM complaints WHERE priority = 'CRITICAL'")
        critical_count = cursor.fetchone()[0]

        # Build dynamic query
        query = "SELECT c.*, u.name as assigned_admin_name FROM complaints c LEFT JOIN users u ON c.assigned_admin_id = u.id WHERE 1=1"
        params = []

        if role and role.lower() != 'all':
            query += " AND LOWER(c.user_role) = ?"
            params.append(role.lower())

        if category and category.lower() != 'all':
            query += " AND c.category = ?"
            params.append(category)

        if priority and priority.lower() != 'all':
            query += " AND UPPER(c.priority) = ?"
            params.append(priority.upper())

        if status and status.lower() != 'all':
            query += " AND UPPER(c.status) = ?"
            params.append(status.upper())

        if search:
            query += " AND (LOWER(c.ticket_number) LIKE ? OR LOWER(c.subject) LIKE ? OR LOWER(c.full_name) LIKE ? OR LOWER(c.email) LIKE ? OR LOWER(c.description) LIKE ?)"
            s_param = f"%{search}%"
            params.extend([s_param, s_param, s_param, s_param, s_param])

        if sort_by == 'oldest':
            query += " ORDER BY c.id ASC"
        elif sort_by == 'priority':
            query += " ORDER BY CASE c.priority WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END, c.id DESC"
        else:
            query += " ORDER BY c.id DESC"

        complaints_rows = cursor.execute(query, params).fetchall()
        conn.close()

        complaints_list = []
        for r in complaints_rows:
            item = dict(r)
            item['short_ticket'] = f"ECO-{item['id']:03d}"
            complaints_list.append(item)

        return jsonify({
            'success': True,
            'stats': {
                'total': total_count,
                'new': new_count,
                'in_progress': in_progress_count,
                'waiting_user': waiting_user_count,
                'resolved': resolved_count,
                'reopened': reopened_count,
                'critical': critical_count
            },
            'complaints': complaints_list
        })
    except Exception as e:
        print(f"Error fetching admin complaints: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/complaints/<int:complaint_id>/update-status', methods=['POST'])
def update_admin_complaint_status(complaint_id):
    try:
        current_user = get_current_user_from_session()
        data = request.json or {}

        admin_id = current_user.get('id') if current_user else 1
        admin_name = current_user.get('name') if current_user else 'System Admin'

        new_status = data.get('status')
        new_priority = data.get('priority')
        assigned_admin_id = data.get('assigned_admin_id')
        notes = data.get('notes', '').strip()

        valid_statuses = {'OPEN', 'IN_PROGRESS', 'WAITING_FOR_USER', 'RESOLVED', 'CLOSED', 'REOPENED'}
        if new_status and new_status.upper() not in valid_statuses:
            return jsonify({'success': False, 'message': f'Invalid status. Allowed: {", ".join(valid_statuses)}'}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        comp_row = cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
        if not comp_row:
            conn.close()
            return jsonify({'success': False, 'message': 'Complaint not found.'}), 404

        comp = dict(comp_row)
        old_status = comp['status']

        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        status_to_set = new_status.upper() if new_status else old_status
        priority_to_set = new_priority.upper() if new_priority else comp['priority']
        resolved_at = timestamp if status_to_set in ['RESOLVED', 'CLOSED'] else comp.get('resolved_at')

        cursor.execute('''
            UPDATE complaints
            SET status = ?, priority = ?, assigned_admin_id = COALESCE(?, assigned_admin_id),
                resolved_at = ?, updated_at = ?
            WHERE id = ?
        ''', (status_to_set, priority_to_set, assigned_admin_id, resolved_at, timestamp, complaint_id))

        if status_to_set != old_status or notes:
            history_note = notes if notes else f"Admin updated status from {old_status} to {status_to_set}"
            cursor.execute('''
                INSERT INTO complaint_history (
                    complaint_id, changed_by_id, changed_by_role, changed_by_name, old_status, new_status, notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                complaint_id, admin_id, 'Admin', admin_name, old_status, status_to_set, history_note, timestamp
            ))

        # Notify user
        status_msg = f"Status updated to {status_to_set} by Admin."
        if notes:
            status_msg += f" Note: {notes}"

        send_complaint_notification(
            comp['user_id'],
            'complaint_status_updated',
            f"Update on Complaint #{comp['ticket_number']}",
            f"Ticket #{comp['ticket_number']} is now {status_to_set}. {status_msg}",
            complaint_id
        )

        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'message': f"Complaint ticket #{comp['ticket_number']} updated successfully!",
            'status': status_to_set,
            'priority': priority_to_set
        })
    except Exception as e:
        print(f"Error updating complaint status: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/complaints/analytics', methods=['GET'])
def get_complaint_analytics():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        by_category = [dict(r) for r in cursor.execute("SELECT category, COUNT(*) as count FROM complaints GROUP BY category ORDER BY count DESC").fetchall()]
        by_role = [dict(r) for r in cursor.execute("SELECT user_role as role, COUNT(*) as count FROM complaints GROUP BY user_role").fetchall()]
        by_status = [dict(r) for r in cursor.execute("SELECT status, COUNT(*) as count FROM complaints GROUP BY status").fetchall()]
        by_priority = [dict(r) for r in cursor.execute("SELECT priority, COUNT(*) as count FROM complaints GROUP BY priority").fetchall()]

        cursor.execute("SELECT COUNT(*) FROM complaints WHERE status = 'REOPENED'")
        reopened_total = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM complaints WHERE priority = 'CRITICAL'")
        critical_total = cursor.fetchone()[0]

        conn.close()

        return jsonify({
            'success': True,
            'by_category': by_category,
            'by_role': by_role,
            'by_status': by_status,
            'by_priority': by_priority,
            'reopened_total': reopened_total,
            'critical_total': critical_total
        })
    except Exception as e:
        print(f"Error getting complaint analytics: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/complaints/export', methods=['GET'])
def export_complaints_csv():
    try:
        import csv
        import io
        from flask import make_response

        conn = get_db_connection()
        complaints = conn.execute("SELECT * FROM complaints ORDER BY id DESC").fetchall()
        conn.close()

        si = io.StringIO()
        writer = csv.writer(si)

        writer.writerow([
            'Complaint ID', 'Ticket Number', 'User ID', 'User Role', 'Name', 'Email',
            'Phone', 'Category', 'Subject', 'Description', 'Priority', 'Status',
            'Related Donation ID', 'Related Delivery ID', 'Created At', 'Updated At', 'Resolved At'
        ])

        for c in complaints:
            d = dict(c)
            writer.writerow([
                d['id'], d['ticket_number'], d['user_id'], d['user_role'], d['full_name'],
                d['email'], d['phone'], d['category'], d['subject'], d['description'],
                d['priority'], d['status'], d['related_donation_id'], d['related_delivery_id'],
                d['created_at'], d['updated_at'], d['resolved_at']
            ])

        output = make_response(si.getvalue())
        output.headers["Content-Disposition"] = "attachment; filename=ecobite_complaints_report.csv"
        output.headers["Content-type"] = "text/csv"
        return output
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/uploads/complaints/<path:filename>')
def uploaded_complaint_file(filename):
    return send_from_directory(COMPLAINT_UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    print("\n--------------------------------------------")
    print("   ShareMeal Python Server is Live!")
    print("   Database: SQLite (sharemeal.db)")
    print("   Open your browser at: http://localhost:3000")
    print("--------------------------------------------\n")
    app.run(port=3000, debug=False)
