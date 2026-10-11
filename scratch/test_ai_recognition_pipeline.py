import requests
import sqlite3
import os
import json
from PIL import Image, ImageDraw

BASE_URL = "http://localhost:3000"
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "sharemeal.db")

def create_sample_food_photo():
    filepath = os.path.join(os.path.dirname(__file__), "sample_biryani_test.jpg")
    img = Image.new('RGB', (300, 300), color=(245, 235, 220))
    draw = ImageDraw.Draw(img)
    draw.ellipse([30, 30, 270, 270], fill=(210, 130, 40), outline=(180, 100, 20), width=3)
    draw.ellipse([60, 60, 240, 240], fill=(235, 205, 140))
    for (x, y) in [(80, 90), (150, 120), (200, 180), (120, 210)]:
        draw.ellipse([x, y, x+12, y+12], fill=(40, 140, 50))
    for (x, y) in [(100, 140), (180, 100), (140, 170)]:
        draw.ellipse([x, y, x+15, y+15], fill=(200, 60, 30))
    img.save(filepath, "JPEG")
    return filepath

def test_ai_pipeline():
    print("=========================================================")
    print("      ECOBITE AI FOOD RECOGNITION SYSTEM TEST           ")
    print("=========================================================")

    # 1. Test Model Stats Endpoint
    print("\n1. Testing GET /api/ai-model-stats...")
    res_stats = requests.get(f"{BASE_URL}/api/ai-model-stats")
    assert res_stats.status_code == 200, f"Expected 200, got {res_stats.status_code}"
    stats_data = res_stats.json()
    print("AI Model Statistics Response:")
    print(json.dumps(stats_data, indent=2))
    assert "top1_accuracy" in stats_data
    assert "macro_f1" in stats_data

    # 2. Test AI Scanner Endpoint
    print("\n2. Testing POST /api/ai-scan-food...")
    sample_img_path = create_sample_food_photo()
    with open(sample_img_path, "rb") as f:
        files = {"image": ("test_biryani.jpg", f, "image/jpeg")}
        res_scan = requests.post(f"{BASE_URL}/api/ai-scan-food", files=files)

    assert res_scan.status_code == 200, f"Expected 200, got {res_scan.status_code}"
    scan_data = res_scan.json()
    print("AI Food Scan Response:")
    print(json.dumps(scan_data, indent=2))
    assert scan_data.get("success") is True
    assert "food_name" in scan_data
    assert "diet_type" in scan_data
    assert "requires_confirmation" in scan_data
    print(f"Identified Dish: '{scan_data.get('food_name')}', Source: '{scan_data.get('source')}'")

    # 3. Test Donor Feedback Endpoint /api/ai-feedback
    print("\n3. Testing POST /api/ai-feedback...")
    feedback_payload = {
        "image_path": scan_data.get("image_path", "uploads/test_biryani.jpg"),
        "ai_predicted": scan_data.get("food_name"),
        "donor_corrected": "Vegetable Biryani",
        "diet_type": "Veg",
        "food_category": "For Humans",
        "model_version": scan_data.get("source", "MobileNetV3")
    }
    res_fb = requests.post(f"{BASE_URL}/api/ai-feedback", json=feedback_payload)
    assert res_fb.status_code == 200
    fb_data = res_fb.json()
    assert fb_data.get("success") is True
    print("Feedback Response:", fb_data.get("message"))

    # Verify Feedback DB Insertion
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ai_feedback ORDER BY id DESC LIMIT 1")
    fb_row = cursor.fetchone()
    conn.close()
    assert fb_row is not None, "AI feedback entry not found in database"
    print(f"Database Record Verified: ID={fb_row[0]}, AI='{fb_row[2]}', Corrected='{fb_row[3]}'")

    # 4. Test Auto-filled Donation Submission
    print("\n4. Submitting Auto-Filled Donation to /api/donate...")
    donate_payload = {
        "donor_id": 1,
        "food_name": "Vegetable Biryani",
        "diet_type": scan_data.get("diet_type", "Veg"),
        "food_category": "For Humans",
        "quantity": "20 Servings",
        "pickup_address": "Indiranagar Community Center, Sector 4",
        "instructions": "Contains dairy. Packed in thermal containers.",
        "preparation_time": "2026-10-09T21:00",
        "storage_condition": "Insulated Container",
        "image_path": scan_data.get("image_path")
    }
    res_donate = requests.post(f"{BASE_URL}/api/donate", json=donate_payload)
    assert res_donate.status_code in (200, 201)
    d_data = res_donate.json()
    created_id = d_data.get("id") or d_data.get("donation_id")
    print(f"Donation Published Successfully! Created ID = {created_id}")

    # 5. Verify NGO Availability
    res_ngo = requests.get(f"{BASE_URL}/api/donations")
    assert res_ngo.status_code == 200
    all_d = res_ngo.json()
    avail = [d for d in all_d if d['id'] == created_id]
    assert len(avail) == 1, "Published donation not found in available NGO feed"
    print(f"NGO Feed Verification Passed: Item {created_id} is 'Available'.")

    print("\nALL AI FOOD RECOGNITION SYSTEM TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_ai_pipeline()
