import requests
import sqlite3
import os
import json
from PIL import Image, ImageDraw

BASE_URL = "http://localhost:3000"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "sharemeal.db")

def create_sample_image():
    filepath = os.path.join(os.path.dirname(__file__), "sample_upload_food.jpg")
    img = Image.new('RGB', (320, 240), color=(220, 140, 50))
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 300, 220], fill=(240, 200, 100))
    draw.ellipse([80, 50, 240, 190], fill=(180, 50, 30))
    img.save(filepath, "JPEG")
    return filepath

def test_image_display_flow():
    print("=========================================================")
    print("      ECOBITE FOOD IMAGE DISPLAY & SERVING TEST          ")
    print("=========================================================")

    # 1. Test Direct Image File Upload via FormData
    sample_file = create_sample_image()
    print("\n1. Submitting Donation with direct image file upload...")
    with open(sample_file, "rb") as f:
        files = {"image": ("my_uploaded_curry.jpg", f, "image/jpeg")}
        data = {
            "donor_id": 1,
            "food_name": "Uploaded Butter Chicken Feast",
            "quantity": "15 Servings",
            "pickup_address": "Indiranagar Block A",
            "diet_type": "Non-Veg",
            "food_category": "For Humans"
        }
        res1 = requests.post(f"{BASE_URL}/api/donate", files=files, data=data)

    assert res1.status_code in (200, 201), f"Expected 200/201, got {res1.status_code}"
    res1_data = res1.json()
    id1 = res1_data.get("id") or res1_data.get("donation_id")
    print(f"Uploaded Donation ID = {id1}, Response: {res1_data}")

    # Verify DB saved image_path
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    row1 = cursor.execute("SELECT image_path FROM donations WHERE id = ?", (id1,)).fetchone()
    conn.close()
    assert row1['image_path'] is not None and row1['image_path'].startswith("uploads/"), f"Unexpected image path: {row1['image_path']}"
    print(f"Database Image Path Verified: '{row1['image_path']}'")

    # 2. Test Image HTTP Access from Static Serving Route
    img_url = f"{BASE_URL}/{row1['image_path'].lstrip('/')}"
    print(f"\n2. Testing HTTP GET image static serving route: {img_url}")
    res_img = requests.get(img_url)
    assert res_img.status_code == 200, f"Image static route returned HTTP {res_img.status_code}"
    assert len(res_img.content) > 100, "Image content empty"
    print(f"HTTP GET Image Static Route Passed: Received {len(res_img.content)} bytes.")

    # 3. Test AI Scanner Preserved Image Path
    print("\n3. Submitting Donation with AI Scanner image path...")
    ai_data = {
        "donor_id": 1,
        "food_name": "AI Scanned Vegetable Biryani",
        "quantity": "25 Servings",
        "pickup_address": "Sector 4 City Center",
        "diet_type": "Veg",
        "food_category": "For Humans",
        "image_path": row1['image_path'] # Reuse valid upload path
    }
    res2 = requests.post(f"{BASE_URL}/api/donate", json=ai_data)
    assert res2.status_code in (200, 201)
    id2 = res2.json().get("id")

    # 4. Test User Donations Query & Field Verification
    print("\n4. Verifying Donor My Donations Endpoint...")
    res_user = requests.get(f"{BASE_URL}/api/donations/user/1")
    assert res_user.status_code == 200
    user_donations = res_user.json()
    d1_entry = [d for d in user_donations if d['id'] == id1][0]
    assert d1_entry['image_path'] == row1['image_path'], f"Image path mismatch: expected {row1['image_path']}, got {d1_entry['image_path']}"
    print(f"My Donations verification passed: Card {id1} contains image_path '{d1_entry['image_path']}'")

    print("\n=========================================================")
    print("      ALL FOOD IMAGE DISPLAY TESTS PASSED SUCCESSFULLY!  ")
    print("=========================================================")

if __name__ == "__main__":
    test_image_display_flow()
