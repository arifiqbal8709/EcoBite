import os
import requests

BASE_URL = 'http://localhost:3000'

def run_test():
    print("=== Testing EcoBite Food Image Display Flow ===")
    
    # 1. Login as Donor
    session = requests.Session()
    login_resp = session.post(f"{BASE_URL}/api/login", json={
        "email": "donor@sharemeal.com",
        "password": "password123"
    })
    
    print("Donor Login Status:", login_resp.status_code)
    user_data = login_resp.json().get("user", {})
    user_id = user_data.get("id")
    print(f"Logged in User ID: {user_id}")

    # 2. Create dummy test image file
    img_path = "test_fresh_salad.jpg"
    with open(img_path, "wb") as f:
        f.write(b'\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xFF\xDB\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' \",#\x1c\x1c(7),01444\x1f\'9=82<.342\xFF\xC0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xFF\xC4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xFF\xDA\x00\x08\x01\x01\x00\x00?\x00\x7f\x00\xFF\xD9')

    # 3. Post donation with multipart image
    with open(img_path, "rb") as f:
        files = {"image": ("test_fresh_salad.jpg", f, "image/jpeg")}
        data = {
            "donor_id": user_id,
            "food_name": "Fresh Organic Garden Salad",
            "quantity": "8 servings",
            "category": "Cooked Food",
            "expiry_hours": "6",
            "address": "456 Green Way",
            "city": "Eco City",
            "latitude": "12.9716",
            "longitude": "77.5946"
        }
        don_resp = session.post(f"{BASE_URL}/api/donate", files=files, data=data)
        print("Donation Creation Response Status:", don_resp.status_code)
        don_data = don_resp.json()
        print("Donation Data:", don_data)

    if os.path.exists(img_path):
        os.remove(img_path)

    # 4. Fetch My Donations
    my_resp = session.get(f"{BASE_URL}/api/donations/user/{user_id}")
    print("Fetch My Donations Status:", my_resp.status_code)
    donations = my_resp.json()
    print(f"Retrieved {len(donations)} donations.")
    
    if len(donations) > 0:
        latest = donations[0]
        print("Latest Donation Food Name:", latest.get("food_name"))
        print("Latest Donation Saved Image Path:", latest.get("image_path"))
        
        # Verify static file accessibility over HTTP
        image_path = latest.get("image_path")
        if image_path:
            full_img_url = f"{BASE_URL}{image_path}" if image_path.startswith("/") else f"{BASE_URL}/{image_path}"
            print("Accessing Image URL over HTTP:", full_img_url)
            img_get = session.get(full_img_url)
            print("Image HTTP Status:", img_get.status_code, "Content-Type:", img_get.headers.get("Content-Type"), "Content Length:", len(img_get.content))
            assert img_get.status_code == 200, f"Expected 200 OK for image, got {img_get.status_code}"
            print("\nSUCCESS: Donation saved with image_path, and static image served with 200 OK HTTP status!")
        else:
            print("ERROR: image_path is null or empty!")

if __name__ == "__main__":
    run_test()
