import os
import json
import random
import math
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

# 41 Food Categories including Indian & International Dishes
FOOD_CLASSES = [
    "pizza", "burger", "pasta", "noodles",
    "rice_plain", "rice_jeera", "pulao_veg", "biryani_veg", "biryani_chicken", "fried_rice", "khichdi",
    "roti_chapati", "naan", "paratha", "poori",
    "dal_tadka", "rajma", "chole", "paneer_butter_masala", "shahi_paneer", "curry_mixed_veg", "curry_chicken", "curry_egg",
    "samosa", "kachori", "pakora", "sandwich", "bread_pakora",
    "idli", "dosa", "uttapam", "vada", "sambar", "upma",
    "indian_thali", "fruits", "vegetables", "salads", "sweets_desserts", "packaged_meals", "unknown_food"
]

CLASS_LABELS = {
    "pizza": {"name": "Pizza", "diet": "Requires Confirmation", "category": "cooked_meal", "ingredients": ["Cheese", "Vegetables", "Olives", "Tomato Sauce", "Pizza Crust"]},
    "burger": {"name": "Veg / Meat Burger", "diet": "Requires Confirmation", "category": "cooked_meal", "ingredients": ["Bun", "Patty", "Lettuce", "Cheese", "Sauce"]},
    "pasta": {"name": "Italian Pasta", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Pasta", "Tomato / Cream Sauce", "Herbs", "Cheese"]},
    "noodles": {"name": "Stir-fried Noodles", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Noodles", "Cabbage", "Capsicum", "Soy Sauce"]},
    "rice_plain": {"name": "Plain Steamed Rice", "diet": "Vegan", "category": "cooked_meal", "ingredients": ["Rice"]},
    "rice_jeera": {"name": "Jeera Rice", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Rice", "Cumin Seeds", "Ghee"]},
    "pulao_veg": {"name": "Vegetable Pulao", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Basmati Rice", "Peas", "Carrots", "Spices"]},
    "biryani_veg": {"name": "Vegetable Biryani", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Basmati Rice", "Paneer", "Vegetables", "Spices"]},
    "biryani_chicken": {"name": "Chicken Biryani", "diet": "Non-Veg", "category": "cooked_meal", "ingredients": ["Basmati Rice", "Chicken", "Whole Spices", "Saffron"]},
    "fried_rice": {"name": "Veg Fried Rice", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Rice", "Spring Onion", "Soy Sauce", "Veggies"]},
    "khichdi": {"name": "Dal Khichdi", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Rice", "Moong Dal", "Turmeric", "Ghee"]},
    "roti_chapati": {"name": "Roti / Chapati", "diet": "Vegan", "category": "cooked_meal", "ingredients": ["Whole Wheat Flour"]},
    "naan": {"name": "Butter Naan", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Refined Flour", "Butter", "Yeast"]},
    "paratha": {"name": "Aloo Paratha", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Wheat Flour", "Mashed Potatoes", "Spices"]},
    "poori": {"name": "Golden Poori", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Wheat Flour", "Oil"]},
    "dal_tadka": {"name": "Dal Tadka", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Yellow Lentils", "Garlic", "Cumin", "Ghee"]},
    "rajma": {"name": "Rajma Masala", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Kidney Beans", "Tomato Onion Gravy", "Spices"]},
    "chole": {"name": "Amritsari Chole", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Chickpeas", "Spiced Gravy"]},
    "paneer_butter_masala": {"name": "Paneer Butter Masala", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Cottage Cheese", "Tomato Cream Gravy", "Butter"]},
    "shahi_paneer": {"name": "Shahi Paneer", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Paneer", "Cashew Gravy", "Cream"]},
    "curry_mixed_veg": {"name": "Mixed Vegetable Curry", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Carrots", "Beans", "Peas", "Spiced Gravy"]},
    "curry_chicken": {"name": "Chicken Curry", "diet": "Non-Veg", "category": "cooked_meal", "ingredients": ["Chicken Pieces", "Onion Tomato Gravy"]},
    "curry_egg": {"name": "Egg Curry", "diet": "Non-Veg", "category": "cooked_meal", "ingredients": ["Boiled Eggs", "Spiced Gravy"]},
    "samosa": {"name": "Crispy Potato Samosa", "diet": "Veg", "category": "packaged_snacks", "ingredients": ["Flour Crust", "Spiced Potato Filling"]},
    "kachori": {"name": "Khasta Kachori", "diet": "Veg", "category": "packaged_snacks", "ingredients": ["Flour Shell", "Spiced Lentil Filling"]},
    "pakora": {"name": "Vegetable Pakora", "diet": "Veg", "category": "packaged_snacks", "ingredients": ["Gram Flour (Besan)", "Onions", "Potatoes"]},
    "sandwich": {"name": "Veg / Cheese Sandwich", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Bread Slice", "Cucumber", "Tomato", "Cheese"]},
    "bread_pakora": {"name": "Bread Pakora", "diet": "Veg", "category": "packaged_snacks", "ingredients": ["Bread Slice", "Besan Batter", "Potato Filling"]},
    "idli": {"name": "Steamed Idli", "diet": "Vegan", "category": "cooked_meal", "ingredients": ["Fermented Rice & Urad Dal Batter"]},
    "dosa": {"name": "Masala Dosa", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Fermented Crepe", "Potato Masala Filling"]},
    "uttapam": {"name": "Onion Tomato Uttapam", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Thick Batter", "Onions", "Tomatoes"]},
    "vada": {"name": "Medu Vada", "diet": "Vegan", "category": "cooked_meal", "ingredients": ["Lentil Fritter", "Spices"]},
    "sambar": {"name": "South Indian Sambar", "diet": "Vegan", "category": "cooked_meal", "ingredients": ["Lentils", "Drumsticks", "Tamarind", "Sambar Powder"]},
    "upma": {"name": "Rava Upma", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Semolina", "Mustard Seeds", "Curry Leaves"]},
    "indian_thali": {"name": "Grand Indian Thali", "diet": "Veg", "category": "cooked_meal", "ingredients": ["Roti", "Rice", "Dal", "Paneer", "Sweet", "Curd"]},
    "fruits": {"name": "Fresh Mixed Fruits", "diet": "Vegan", "category": "raw_ingredients", "ingredients": ["Apples", "Bananas", "Oranges"]},
    "vegetables": {"name": "Fresh Farm Vegetables", "diet": "Vegan", "category": "raw_ingredients", "ingredients": ["Tomatoes", "Potatoes", "Spinach"]},
    "salads": {"name": "Green Salad", "diet": "Vegan", "category": "cooked_meal", "ingredients": ["Cucumber", "Carrot", "Onion", "Lemon"]},
    "sweets_desserts": {"name": "Gulab Jamun & Sweets", "diet": "Veg", "category": "packaged_snacks", "ingredients": ["Milk Solids", "Sugar Syrup", "Cardamom"]},
    "packaged_meals": {"name": "Sealed Packaged Food", "diet": "Veg", "category": "packaged_snacks", "ingredients": ["Packaged Meal / Biscuits / Grocery"]},
    "unknown_food": {"name": "Uncertain Food Item", "diet": "uncertain", "category": "cooked_meal", "ingredients": []}
}

COLOR_SCHEMES = {
    "pizza": [(210, 140, 50), (220, 50, 40), (255, 230, 140), (30, 30, 30), (50, 160, 50)],
    "burger": [(190, 130, 60), (120, 60, 30), (50, 160, 50), (240, 200, 40)],
    "pasta": [(240, 220, 150), (210, 60, 40), (255, 245, 200)],
    "noodles": [(230, 210, 140), (60, 140, 60), (180, 50, 40)],
    "rice_plain": [(245, 245, 240), (230, 230, 220)],
    "rice_jeera": [(240, 238, 225), (60, 45, 20)],
    "pulao_veg": [(240, 230, 190), (40, 140, 50), (220, 80, 30)],
    "biryani_veg": [(220, 140, 40), (240, 210, 150), (40, 120, 40)],
    "biryani_chicken": [(210, 120, 30), (140, 60, 20), (240, 210, 140)],
    "fried_rice": [(230, 220, 180), (50, 160, 70), (80, 80, 80)],
    "khichdi": [(230, 200, 70), (210, 170, 50)],
    "roti_chapati": [(210, 170, 110), (160, 110, 60)],
    "naan": [(245, 230, 190), (180, 140, 80), (40, 100, 40)],
    "paratha": [(220, 170, 100), (180, 130, 70)],
    "poori": [(230, 160, 50), (190, 120, 30)],
    "dal_tadka": [(240, 190, 40), (200, 50, 30)],
    "rajma": [(120, 40, 30), (160, 60, 40)],
    "chole": [(160, 100, 40), (110, 70, 30)],
    "paneer_butter_masala": [(230, 90, 30), (255, 230, 180)],
    "shahi_paneer": [(240, 180, 100), (255, 240, 200)],
    "curry_mixed_veg": [(210, 100, 40), (50, 150, 50), (240, 160, 30)],
    "curry_chicken": [(170, 60, 20), (120, 40, 15)],
    "curry_egg": [(200, 90, 30), (250, 240, 200), (240, 180, 30)],
    "samosa": [(210, 140, 60), (150, 90, 30)],
    "kachori": [(200, 130, 50), (140, 80, 30)],
    "pakora": [(220, 150, 40), (130, 80, 20)],
    "sandwich": [(240, 220, 180), (50, 150, 50), (220, 50, 40)],
    "bread_pakora": [(210, 140, 40), (180, 100, 30)],
    "idli": [(250, 250, 245), (235, 235, 230)],
    "dosa": [(210, 160, 80), (160, 110, 50)],
    "uttapam": [(230, 200, 150), (200, 50, 40), (40, 130, 50)],
    "vada": [(180, 110, 40), (130, 70, 20)],
    "sambar": [(190, 90, 30), (140, 60, 20)],
    "upma": [(235, 225, 200), (40, 120, 50)],
    "indian_thali": [(200, 200, 200), (230, 100, 30), (240, 200, 50), (210, 160, 100)],
    "fruits": [(220, 50, 40), (240, 180, 30), (50, 160, 50)],
    "vegetables": [(50, 150, 50), (220, 60, 40), (180, 120, 40)],
    "salads": [(60, 170, 60), (230, 60, 50), (240, 240, 230)],
    "sweets_desserts": [(120, 50, 20), (240, 200, 100)],
    "packaged_meals": [(40, 100, 200), (240, 240, 240), (220, 40, 40)],
    "unknown_food": [(140, 140, 140), (180, 180, 180)]
}

def generate_synthetic_food_image(category, index, img_size=(224, 224)):
    """Generates an authentic synthetic training image for a given food category with random visual variance."""
    colors = COLOR_SCHEMES.get(category, [(150, 150, 150), (200, 200, 200)])
    
    # Background (table, placemat, container, or wooden board)
    bg_color = (random.randint(220, 250), random.randint(215, 245), random.randint(200, 235))
    if category == "pizza":
        bg_color = (170, 110, 60) # Wooden serving board / table
    img = Image.new('RGB', img_size, bg_color)
    draw = ImageDraw.Draw(img)
    
    margin = random.randint(15, 30)
    
    if category == "pizza":
        # Render Pizza Crust & Cheese & Toppings
        crust_color = (200, 140, 50)
        sauce_color = (190, 40, 30)
        cheese_color = (255, 230, 140)
        
        # Outer golden crust
        draw.ellipse([margin, margin, img_size[0] - margin, img_size[1] - margin], fill=crust_color, outline=(150, 90, 20), width=3)
        # Inner sauce layer
        inner_m = margin + 12
        draw.ellipse([inner_m, inner_m, img_size[0] - inner_m, img_size[1] - inner_m], fill=sauce_color)
        # Cheese layer
        ch_m = inner_m + 8
        draw.ellipse([ch_m, ch_m, img_size[0] - ch_m, img_size[1] - ch_m], fill=cheese_color)
        
        # Toppings: Black olives, green bell peppers, red tomatoes, herbs
        for _ in range(random.randint(15, 30)):
            ox = random.randint(ch_m + 5, img_size[0] - ch_m - 15)
            oy = random.randint(ch_m + 5, img_size[1] - ch_m - 15)
            top_type = random.choice(["olive", "pepper", "herb", "onion"])
            if top_type == "olive":
                draw.ellipse([ox, oy, ox + 10, oy + 10], fill=(20, 20, 20), outline=(255, 255, 255), width=1)
            elif top_type == "pepper":
                draw.rectangle([ox, oy, ox + 12, oy + 6], fill=(40, 150, 40))
            elif top_type == "herb":
                draw.ellipse([ox, oy, ox + 6, oy + 6], fill=(30, 110, 30))
            else:
                draw.ellipse([ox, oy, ox + 8, oy + 8], fill=(180, 80, 120))
    else:
        plate_color = random.choice([(255, 255, 255), (240, 240, 240), (200, 200, 205), (180, 140, 100)])
        draw.ellipse([margin, margin, img_size[0] - margin, img_size[1] - margin], fill=plate_color, outline=(180, 180, 180), width=2)
        
        food_margin = margin + random.randint(15, 25)
        main_color = colors[0]
        draw.ellipse([food_margin, food_margin, img_size[0] - food_margin, img_size[1] - food_margin], fill=main_color)
        
        num_specks = random.randint(40, 120)
        for _ in range(num_specks):
            rx = random.randint(food_margin + 5, img_size[0] - food_margin - 5)
            ry = random.randint(food_margin + 5, img_size[1] - food_margin - 5)
            r_size = random.randint(2, 8)
            speck_color = random.choice(colors)
            draw.ellipse([rx, ry, rx + r_size, ry + r_size], fill=speck_color)

    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(random.uniform(0.85, 1.15))
    return img

def build_dataset(base_dir="dataset/food_dataset", images_per_class=20):
    print("=== BUILDING ECOBITE FOOD RECOGNITION DATASET ===")
    os.makedirs(base_dir, exist_ok=True)
    
    splits = ["train", "val", "test"]
    split_ratios = {"train": 0.70, "val": 0.15, "test": 0.15}
    
    class_mapping = {}
    
    for idx, category in enumerate(FOOD_CLASSES):
        class_mapping[idx] = {
            "slug": category,
            "info": CLASS_LABELS.get(category, {"name": category, "diet": "Veg", "category": "For Humans", "ingredients": []})
        }
        
        for split in splits:
            split_path = os.path.join(base_dir, split, category)
            os.makedirs(split_path, exist_ok=True)
            
        num_split_images = {
            "train": int(images_per_class * split_ratios["train"]),
            "val": int(images_per_class * split_ratios["val"]),
            "test": images_per_class - int(images_per_class * split_ratios["train"]) - int(images_per_class * split_ratios["val"])
        }
        
        count = 0
        for split, num_imgs in num_split_images.items():
            for i in range(num_imgs):
                count += 1
                img = generate_synthetic_food_image(category, count)
                filename = f"{category}_{split}_{count:03d}.jpg"
                filepath = os.path.join(base_dir, split, category, filename)
                img.save(filepath, "JPEG")
                
        print(f"Created {images_per_class} dataset images for class: {category}")
        
    mapping_file = os.path.join(base_dir, "class_mapping.json")
    with open(mapping_file, "w") as f:
        json.dump(class_mapping, f, indent=2)
        
    print(f"\nDataset construction complete! Created {len(FOOD_CLASSES)} classes at '{base_dir}'.")
    print(f"Class mapping saved to '{mapping_file}'.")

if __name__ == "__main__":
    build_dataset()
