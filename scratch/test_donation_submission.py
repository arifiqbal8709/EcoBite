import requests
import sqlite3
import os
import json

BASE_URL = "http://localhost:3000"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "sharemeal.db")

def test_donation_flow():
    print("=== ECOBITE END-TO-END DONATION TEST ===")
    
    # 1. Check existing database state
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, role FROM users WHERE role = 'donor' LIMIT 1")
    donor = cursor.fetchone()
    if not donor:
        print("Creating test donor account...")
        cursor.execute("INSERT INTO users (name, email, password, role, phone) VALUES (?, ?, ?, ?, ?)",
                       ("Test Donor", "donor_test@ecobite.org", "pass123", "donor", "9876543210"))
        conn.commit()
        donor_id = cursor.lastrowid
    else:
        donor_id = donor[0]
    conn.close()
    
    print(f"Using donor ID: {donor_id}")

    # 2. Test JSON Submission to /api/donate
    payload = {
        "donor_id": donor_id,
        "food_name": "Paneer Butter Masala & Naan",
        "diet_type": "Veg",
        "food_category": "For Humans",
        "quantity": "25 Servings",
        "pickup_address": "Building 5, Tech Park, Indiranagar",
        "instructions": "Keep warm in thermal box.",
        "preparation_time": "2026-10-09T20:00",
        "storage_condition": "Insulated Container",
        "image_path": "uploads/sample_paneer.jpg"
    }

    headers = {"Content-Type": "application/json"}
    print(f"\nSubmitting POST /api/donate with payload...")
    res = requests.post(f"{BASE_URL}/api/donate", json=payload, headers=headers)
    print(f"HTTP Status: {res.status_code}")
    print(f"Response: {res.text}")
    
    assert res.status_code in (200, 201), f"Expected 200/201, got {res.status_code}"
    res_data = res.json()
    assert res_data.get("success") is True or "id" in res_data, "Expected success in response"
    created_id = res_data.get("id") or res_data.get("donation_id")
    print(f"Created donation ID: {created_id}")

    # 3. Verify Database Insertion
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM donations WHERE id = ?", (created_id,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None, "Donation record not found in SQLite database!"
    print(f"Database Record Verified: ID={row['id']}, donor_id={row['donor_id']}, food_name='{row['food_name']}', status='{row['status']}'")
    assert row['donor_id'] == int(donor_id), f"donor_id mismatch: expected {donor_id}, got {row['donor_id']}"
    assert row['food_name'] == "Paneer Butter Masala & Naan"
    assert row['status'] == "Available"

    # 4. Verify Donor Endpoint /api/donations/user/<donor_id>
    res_user_donations = requests.get(f"{BASE_URL}/api/donations/user/{donor_id}")
    assert res_user_donations.status_code == 200
    user_donations = res_user_donations.json()
    user_ids = [d['id'] for d in user_donations]
    assert created_id in user_ids, f"Created donation {created_id} not found in user donations list!"
    print(f"Donor list endpoint returned {len(user_donations)} donations for donor {donor_id}. Created donation present.")

    # 5. Verify NGO Available Feed /api/donations
    res_all = requests.get(f"{BASE_URL}/api/donations")
    assert res_all.status_code == 200
    all_donations = res_all.json()
    available_ids = [d['id'] for d in all_donations if d.get('status') == 'Available']
    assert created_id in available_ids, f"Created donation {created_id} not in NGO available feed!"
    print(f"NGO feed endpoint returned {len(available_ids)} Available donations. Created donation present.")

    # 6. Test Form-Validation Error Handling (Missing fields)
    bad_payload = {
        "donor_id": donor_id,
        "quantity": "" # Missing food_name & pickup_address
    }
    res_bad = requests.post(f"{BASE_URL}/api/donate", json=bad_payload, headers=headers)
    print(f"\nTesting Invalid Submission (Status: {res_bad.status_code}): {res_bad.text}")
    assert res_bad.status_code == 400

    print("\nALL END-TO-END TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_donation_flow()
