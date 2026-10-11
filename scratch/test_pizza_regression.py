import os
import json
import urllib.request
from io import BytesIO
from PIL import Image, ImageDraw

def create_three_pizzas_image():
    """Generates a test image containing three pizzas on wooden serving boards."""
    img = Image.new('RGB', (600, 300), color=(170, 110, 60)) # Wooden board background
    draw = ImageDraw.Draw(img)

    # Draw 3 pizzas side-by-side
    centers = [(100, 150), (300, 150), (500, 150)]
    for (cx, cy) in centers:
        r = 75
        # Golden crust
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(200, 140, 50), outline=(150, 90, 20), width=3)
        # Tomato sauce
        draw.ellipse([cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10], fill=(190, 40, 30))
        # Melted cheese
        draw.ellipse([cx - r + 18, cy - r + 18, cx + r - 18, cy + r - 18], fill=(255, 230, 140))
        # Toppings: Olives, peppers, herbs
        for (ox, oy) in [(cx-30, cy-20), (cx+20, cy-30), (cx-10, cy+25), (cx+30, cy+10), (cx, cy)]:
            draw.ellipse([ox, oy, ox+10, oy+10], fill=(20, 20, 20), outline=(255, 255, 255), width=1)

    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='JPEG')
    return img_byte_arr.getvalue()

def test_pizza_regression():
    print("===============================================================")
    print("  RUNNING REAL TEST CASE: THREE PIZZAS REGRESSION TEST       ")
    print("===============================================================")

    server_url = "http://localhost:3000"
    image_bytes = create_three_pizzas_image()

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="three_pizzas_on_wooden_boards.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode('utf-8') + image_bytes + f"\r\n--{boundary}--\r\n".encode('utf-8')

    req = urllib.request.Request(
        f"{server_url}/api/ai-scan-food",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))

    print("\nAI SCANNER JSON OUTPUT:")
    print(json.dumps(res, indent=2))

    # Assertions for Pizza Regression Case
    assert res.get("success") == True, "API call failed"
    assert res.get("food_name") == "Pizza", f"Expected 'Pizza', got '{res.get('food_name')}'"
    assert "rice" not in res.get("food_name", "").lower(), "FAILED: Misclassified Pizza as Rice!"
    assert "biryani" not in res.get("food_name", "").lower(), "FAILED: Misclassified Pizza as Biryani!"
    assert res.get("visible_item_count") == 3, f"Expected 3 visible items, got {res.get('visible_item_count')}"
    
    ingredients = res.get("visible_ingredients") or res.get("possible_ingredients") or []
    print("Detected Visible Ingredients:", ingredients)
    assert any(i in ["Cheese", "Vegetables", "Olives", "Herbs", "Tomato Sauce"] for i in ingredients), "Missing pizza toppings"

    print("\n===============================================================")
    print("   THREE PIZZAS REGRESSION TEST PASSED 100%!            ")
    print("===============================================================")

if __name__ == "__main__":
    test_pizza_regression()
