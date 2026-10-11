import os
import json
import urllib.request
import urllib.parse
import sqlite3
from io import BytesIO
from PIL import Image, ImageDraw

def create_sample_food_image():
    """Generates a sample Indian food image (Biryani) for integration testing."""
    img = Image.new('RGB', (300, 300), color=(245, 235, 220))
    draw = ImageDraw.Draw(img)
    # Draw plate
    draw.ellipse([20, 20, 280, 280], fill=(255, 255, 255), outline=(200, 200, 200), width=3)
    # Draw rice/biryani texture
    draw.ellipse([40, 40, 260, 260], fill=(220, 140, 40))
    # Green garnish specks
    for (x, y) in [(100, 100), (120, 150), (180, 110), (150, 180), (110, 200)]:
        draw.ellipse([x, y, x+10, y+10], fill=(40, 140, 40))
    
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

def test_full_vision_workflow():
    print("===============================================================")
    print("      TESTING ECOBITE AI VISION SCANNER & DONATION FLOW        ")
    print("===============================================================")

    server_url = "http://localhost:3000"
    image_bytes = create_sample_food_image()

    # 1. Test AI Vision Recognition API (/api/ai-scan-food)
    print("\n[Step 1] Sending sample food photo to /api/ai-scan-food...")
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="biryani_test.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode('utf-8') + image_bytes + f"\r\n--{boundary}--\r\n".encode('utf-8')

    req = urllib.request.Request(
        f"{server_url}/api/ai-scan-food",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )

    with urllib.request.urlopen(req) as resp:
        scan_res = json.loads(resp.read().decode('utf-8'))

    print("AI Scan Response Status:", scan_res.get("success"))
    print("Source Engine:", scan_res.get("source"))
    print("Detected Food Name:", scan_res.get("food_name"))
    print("Food Items:", scan_res.get("food_items"))
    print("Suggested Category:", scan_res.get("food_category"))
    print("Suggested Diet Type:", scan_res.get("diet_type"))
    print("Followup Questions:", scan_res.get("followup_questions"))
    print("Requires Confirmation:", scan_res.get("requires_confirmation"))

    assert scan_res.get("success") == True, "AI scan endpoint failed"
    assert scan_res.get("food_name") is not None, "Missing food_name in AI scan"
    assert scan_res.get("food_category") in ["cooked_meal", "raw_ingredients", "packaged_snacks", "animal_feed", "compost", "For Humans"], "Invalid category"
    print("-> STEP 1 PASSED: AI Vision scan returned valid structured output.")

    # 2. Test Donation Submission with AI-Autofilled + Donor-Confirmed Details (/api/api/donate)
    print("\n[Step 2] Submitting donation form with confirmed fields and attached photo...")
    donor_confirmed_name = "Special Hyderabadi Veg Biryani & Gravy"
    donor_confirmed_quantity = "25 Servings"
    donor_confirmed_address = "Sector 5, Community Hub, Ranchi"
    donor_prep_time = "2026-10-10T12:00"

    body2 = (
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"donorId\"\r\n\r\n1\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"donorName\"\r\n\r\nCity Hotel Donor\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"foodName\"\r\n\r\n{donor_confirmed_name}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"foodType\"\r\n\r\ncooked_meal\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"dietType\"\r\n\r\nVeg\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"quantity\"\r\n\r\n{donor_confirmed_quantity}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"address\"\r\n\r\n{donor_confirmed_address}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"preparationTime\"\r\n\r\n{donor_prep_time}\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"description\"\r\n\r\nVisual Portion: Container view. Ingredients: Basmati Rice, Vegetables, Spices.\r\n"
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"donation_biryani.jpg\"\r\nContent-Type: image/jpeg\r\n\r\n"
    ).encode('utf-8') + image_bytes + f"\r\n--{boundary}--\r\n".encode('utf-8')

    req2 = urllib.request.Request(
        f"{server_url}/api/donate",
        data=body2,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )

    with urllib.request.urlopen(req2) as resp2:
        donate_res = json.loads(resp2.read().decode('utf-8'))

    print("Donate Response:", donate_res)
    assert donate_res.get("success") == True, "Donation submission failed"
    new_donation_id = donate_res.get("id") or donate_res.get("donation_id")
    print(f"-> STEP 2 PASSED: Donation successfully saved with ID {new_donation_id}.")

    # 3. Test Database Integrity (Query SQLite sharemeal.db)
    print("\n[Step 3] Verifying database record in sharemeal.db...")
    db_path = os.path.join(os.path.dirname(__file__), "..", "database", "sharemeal.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    row = cursor.execute("SELECT * FROM donations WHERE id = ?", (new_donation_id,)).fetchone()
    conn.close()

    assert row is not None, "Donation record not found in database!"
    row_dict = dict(row)
    print("Database Row:", json.dumps(row_dict, indent=2))
    assert row_dict["food_name"] == donor_confirmed_name
    assert row_dict["quantity"] == donor_confirmed_quantity
    assert row_dict["image_path"] is not None and row_dict["image_path"].startswith("uploads/")
    print("-> STEP 3 PASSED: Database record contains uploaded image_path and donor confirmed fields.")

    # 4. Test Verified Donor AI Feedback Logging (/api/ai-feedback)
    print("\n[Step 4] Logging donor feedback / correction for model evaluation...")
    fb_payload = json.dumps({
        "image_path": row_dict["image_path"],
        "ai_predicted": scan_res.get("food_name"),
        "donor_corrected": donor_confirmed_name,
        "diet_type": "Veg",
        "food_category": "cooked_meal"
    }).encode('utf-8')

    req3 = urllib.request.Request(
        f"{server_url}/api/ai-feedback",
        data=fb_payload,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req3) as resp3:
        fb_res = json.loads(resp3.read().decode('utf-8'))

    print("AI Feedback Response:", fb_res)
    assert fb_res.get("success") == True
    print("-> STEP 4 PASSED: AI feedback logged successfully.")

    print("\n===============================================================")
    print("     ALL VISION SCANNER INTEGRATION TESTS PASSED 100%!         ")
    print("===============================================================")

if __name__ == "__main__":
    test_full_vision_workflow()
