import os
import json
import base64
import urllib.request
import urllib.error
import re
from io import BytesIO
from PIL import Image, ImageStat, ImageOps

# Ensure .env is loaded if present
try:
    from dotenv import load_dotenv
    root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    local_env = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
    if os.path.exists(root_env):
        load_dotenv(root_env)
    elif os.path.exists(local_env):
        load_dotenv(local_env)
    else:
        load_dotenv()
except Exception:
    pass

# Global Model Cache for Local PyTorch Checkpoint (MobileNetV3)
_MODEL_CACHE = None
_CLASS_MAPPING = None

MODEL_CHECKPOINT_PATH = os.path.join(os.path.dirname(__file__), "..", "ml", "checkpoints", "ecobite_food_model.pth")
CLASS_MAPPING_PATH = os.path.join(os.path.dirname(__file__), "..", "dataset", "food_dataset", "class_mapping.json")

def load_trained_model():
    """Loads the trained PyTorch MobileNetV3 model checkpoint into cache for offline benchmarking."""
    global _MODEL_CACHE, _CLASS_MAPPING
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE, _CLASS_MAPPING

    if not os.path.exists(MODEL_CHECKPOINT_PATH):
        return None, None

    try:
        import torch
        from torchvision import models
        device = torch.device("cpu")
        checkpoint = torch.load(MODEL_CHECKPOINT_PATH, map_location=device)
        class_names = checkpoint.get("class_names", [])

        model = models.mobilenet_v3_small()
        in_features = model.classifier[3].in_features
        model.classifier[3] = torch.nn.Linear(in_features, len(class_names))
        model.load_state_dict(checkpoint["model_state_dict"])
        model.eval()

        _MODEL_CACHE = model
        
        if os.path.exists(CLASS_MAPPING_PATH):
            with open(CLASS_MAPPING_PATH, "r", encoding="utf-8") as f:
                _CLASS_MAPPING = json.load(f)
        else:
            _CLASS_MAPPING = {str(i): {"slug": c, "info": {"name": c, "diet": "Requires Confirmation", "category": "cooked_meal", "ingredients": []}} for i, c in enumerate(class_names)}

        print("PyTorch EcoBite Food Model loaded successfully into memory.")
        return _MODEL_CACHE, _CLASS_MAPPING
    except Exception as e:
        print(f"Notice: Could not load local PyTorch checkpoint: {e}")
        return None, None

def assess_image_quality(pil_img):
    """
    Evaluates resolution, brightness, contrast, sharpness, and checks for solid/blank images.
    Returns visual metrics and detected anomalies.
    """
    width, height = pil_img.size
    gray = pil_img.convert("L")
    stat = ImageStat.Stat(gray)
    mean_val = stat.mean[0] if stat.mean else 128
    stddev_val = stat.stddev[0] if stat.stddev else 50
    
    notes = []
    is_blank = False

    # Check for solid color / blank image
    if stddev_val < 6.0:
        is_blank = True
        notes.append("Image appears solid or blank with no distinct visual features")
    elif width < 80 or height < 80:
        notes.append("Low image resolution")
    elif mean_val < 15:
        notes.append("Low lighting / dark environment")
    elif mean_val > 245:
        notes.append("Overexposed / white glare")

    quality_text = "Good visual clarity." if not notes else " • ".join(notes)
    return {
        "width": width,
        "height": height,
        "brightness": round(mean_val, 1),
        "stddev": round(stddev_val, 1),
        "is_blank": is_blank,
        "quality_notes": quality_text
    }

def predict_local_ml(pil_img):
    """
    Offline MobileNetV3 evaluation with strict unknown-food rejection mechanism.
    Used for benchmarking, evaluating training accuracy, and offline diagnostics.
    """
    try:
        import torch
        from torchvision import transforms
    except ImportError:
        return None

    model, class_mapping = load_trained_model()
    if model is None or class_mapping is None:
        return None

    try:
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        tensor = transform(pil_img).unsqueeze(0)
        with torch.no_grad():
            outputs = model(tensor)
            probs = torch.softmax(outputs, dim=1)[0]
            topk_probs, topk_indices = torch.topk(probs, k=min(3, len(probs)))

        top_prob_val = float(topk_probs[0].item())
        top_idx_str = str(topk_indices[0].item())
        margin = float((topk_probs[0] - topk_probs[1]).item()) if len(topk_probs) > 1 else 1.0

        meta = class_mapping.get(top_idx_str, {})
        info = meta.get("info", {})
        slug = meta.get("slug", "unknown_food")

        # Top-3 candidate dish names
        top3_candidates = []
        for idx_tensor in topk_indices:
            i_str = str(idx_tensor.item())
            c_meta = class_mapping.get(i_str, {})
            c_info = c_meta.get("info", {})
            c_name = c_info.get("name", c_meta.get("slug", "Food"))
            if c_name not in top3_candidates:
                top3_candidates.append(c_name)

        # Safe unknown-food rejection mechanism:
        # If top probability is low (< 60%), margin is narrow (< 15%), or class is explicitly 'unknown_food'
        is_unknown = (top_prob_val < 0.60) or (margin < 0.15) or (slug == "unknown_food")

        return {
            "confidence": round(top_prob_val, 3),
            "margin": round(margin, 3),
            "slug": slug,
            "food_name": "Unidentified Food" if is_unknown else info.get("name", slug.replace("_", " ").title()),
            "diet_type": info.get("diet", "Requires Confirmation"),
            "food_category": info.get("category", "cooked_meal"),
            "ingredients": info.get("ingredients", []),
            "top3_candidates": top3_candidates,
            "is_unknown": is_unknown
        }
    except Exception as e:
        print(f"Local PyTorch inference notice: {e}")
        return None

def analyze_food_image(image_bytes, filename="food.jpg"):
    """
    Real multimodal image recognition system.
    Strictly analyzes actual image pixels (NEVER filename or metadata).
    Connects to supported Gemini Vision API models with diagnostic error reporting.
    """
    def make_response(status, success=False, is_food=False, error=None, food_name=None,
                      food_items=None, food_category=None, diet_type="Requires Confirmation",
                      visible_ingredients=None, visible_portion_description=None,
                      allergens=None, confidence="Medium", uncertainty_notes="",
                      quality_notes="", source="EcoBite Vision System"):
        return {
            "success": success,
            "status": status,
            "is_food": is_food,
            "error": error,
            "source": source,
            "food_name": food_name,
            "food_items": food_items or ([] if not food_name else [food_name]),
            "food_category": food_category,
            "diet_type": diet_type,
            "quantity": None,
            "servings": None,
            "preparation_time": None,
            "expiry_datetime": None,
            "storage_condition": None,
            "requires_confirmation": True,
            "visible_ingredients": visible_ingredients or [],
            "visible_portion_description": visible_portion_description,
            "allergens": allergens or [],
            "confidence": confidence,
            "uncertainty_notes": uncertainty_notes or "Details are AI suggestions based on visible image evidence; donor must confirm freshness, allergens, and quantities.",
            "quality_notes": quality_notes
        }

    # 1. Image Data Validation
    if not image_bytes or len(image_bytes) == 0:
        return make_response("INVALID_IMAGE", error="No image data received. Please capture or upload a food photo.")
    
    if len(image_bytes) > 10 * 1024 * 1024:
        return make_response("INVALID_IMAGE", error="Image file size exceeds the 10 MB limit.")

    try:
        with Image.open(BytesIO(image_bytes)) as im:
            if im.format not in ("JPEG", "PNG", "WEBP"):
                return make_response("INVALID_IMAGE", error="Unsupported image format. Please use JPG, PNG, or WebP.")
            im.verify()

        with Image.open(BytesIO(image_bytes)) as im:
            # Transpose according to EXIF orientation
            image = ImageOps.exif_transpose(im).convert("RGB")
            quality = assess_image_quality(image)

            # Check if image is blank or solid color
            if quality["is_blank"]:
                return make_response("NO_FOOD_DETECTED", error="No Food Detected. The uploaded image is completely blank or a solid background.", quality_notes=quality["quality_notes"])

            # Resize to reasonable dimensions for API while preserving aspect ratio
            image.thumbnail((1600, 1600), Image.Resampling.LANCZOS)
            buf = BytesIO()
            image.save(buf, format="JPEG", quality=88, optimize=True)
            encoded_jpeg = base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception as exc:
        return make_response("INVALID_IMAGE", error=f"Could not read image file: {str(exc)}")

    # 2. Check Gemini API Configuration (always reload .env dynamically)
    try:
        from dotenv import load_dotenv
        root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        local_env = os.path.abspath(os.path.join(os.path.dirname(__file__), ".env"))
        if os.path.exists(root_env):
            load_dotenv(root_env, override=True)
        if os.path.exists(local_env):
            load_dotenv(local_env, override=True)
    except Exception:
        pass
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        return make_response(
            "AI_UNAVAILABLE",
            error="Gemini Vision AI is not configured. Set the GEMINI_API_KEY environment variable on the backend (in your .env file or hosting environment) to enable live multimodal scanning. Manual donation entry is available below.",
            quality_notes=quality["quality_notes"]
        )

    # Candidate supported vision models in order of preference (supports GEMINI_MODEL & ECOBITE_VISION_MODEL)
    configured_model = (os.environ.get("GEMINI_MODEL") or os.environ.get("ECOBITE_VISION_MODEL") or "").strip()
    models_to_try = []
    if configured_model and re.fullmatch(r"[a-zA-Z0-9._-]+", configured_model):
        models_to_try.append(configured_model)
    for default_m in ["gemini-flash-latest", "gemini-3.8-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]:
        if default_m not in models_to_try:
            models_to_try.append(default_m)

    system_prompt = """You are an expert food recognition and donation assistant for EcoBite, analyzing PHOTOGRAPHS to recognize food and reject non-food.

STRICT INSTRUCTIONS:
1. Base recognition SOLELY on visual pixels in the photograph. NEVER use filename, date, or outside assumptions.
2. RECOGNITION VARIETIES TO IDENTIFY:
   - Cooked Indian meals: Rice, Biryani, Dal, Roti, Chapati, Paneer curries, Indian Thali, Idli, Dosa, Samosa, Regional specialties.
   - International cuisines: Pizza, Burger, Pasta, Noodles, Sandwiches, Soups, Baked goods.
   - Fresh Produce: Raw vegetables, fresh fruits, leafy greens, herbs.
   - Grains & Ingredients: Raw rice, wheat flour, pulses, lentils, cooking spices, edible oils.
   - Packaged & dry food: Packaged snacks, biscuits, cereals, canned foods.
3. MULTIPLE FOOD DETECTION: If multiple distinct dishes/items are visible in a thali, buffet, plate, or tray, list all individual items in "food_items".
4. NON-FOOD REJECTION: If the image depicts no edible food (e.g. laptop, computer, smartphone, electronics, person without food, face, document, paper, furniture, clothing, astronaut poster, wall art, blank wall, empty background), return status "NO_FOOD_DETECTED". Never fabricate food names for non-food images.
5. UNCERTAIN REJECTION: If the image is blurry, ambiguous, or indistinct such that food cannot be reliably identified, return status "UNCERTAIN".
6. ACCURACY & SAFETY HONESTY: Never fabricate exact weights, quantities, number of servings, preparation times, or expiry dates—set them to null.
7. Return ONLY a valid JSON object with NO markdown formatting, NO backticks:
{
  "status": "FOOD_DETECTED" | "NO_FOOD_DETECTED" | "UNCERTAIN",
  "food_name": "Clear primary food/dish name" (or null if non-food/uncertain),
  "food_items": ["Item 1", "Item 2"],
  "food_category": "cooked_meal" | "raw_ingredients" | "packaged_snacks" | "fruits_vegetables" | "sweets_desserts" (or null),
  "diet_type": "Veg" | "Non-Veg" | "Vegan" | "Requires Confirmation",
  "visible_ingredients": ["Ingredient 1", "Ingredient 2"],
  "visible_portion_description": "Descriptive visual portion/container observation",
  "allergens": ["Potential allergen 1", "Potential allergen 2"],
  "confidence": "High" | "Medium" | "Low",
  "uncertainty_notes": "Specific notes on visibility, portion, or items requiring donor confirmation"
}"""

    last_error_message = None
    last_status = "AI_UNAVAILABLE"

    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        payload = {
            "contents": [{
                "parts": [
                    {"text": system_prompt},
                    {"inline_data": {"mime_type": "image/jpeg", "data": encoded_jpeg}}
                ]
            }],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }

        # Try with x-goog-api-key header first
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "x-goog-api-key": api_key}
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))

            candidates = resp_data.get("candidates", [])
            if not candidates:
                raise ValueError("No response candidate returned by vision model.")

            parts = candidates[0].get("content", {}).get("parts", [])
            raw_text = "".join(p.get("text", "") for p in parts).strip()

            # Clean JSON if any markdown formatting leaked through
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)

            parsed = json.loads(raw_text)
            status = parsed.get("status", "UNCERTAIN")

            if status == "NO_FOOD_DETECTED":
                return make_response(
                    "NO_FOOD_DETECTED",
                    error="No Food Detected. Please upload or capture a photo showing edible food.",
                    quality_notes=quality["quality_notes"],
                    source=f"Gemini Vision ({model_name})"
                )

            if status == "UNCERTAIN" or not parsed.get("food_name"):
                return make_response(
                    "UNCERTAIN",
                    error="Unable to identify food with certainty. Please upload a clearer photograph or enter details manually.",
                    uncertainty_notes=parsed.get("uncertainty_notes", "Visual recognition is uncertain."),
                    quality_notes=quality["quality_notes"],
                    source=f"Gemini Vision ({model_name})"
                )

            # Valid Food Detected
            food_name = str(parsed.get("food_name", "")).strip()[:150]
            food_items = [str(item).strip()[:100] for item in parsed.get("food_items", []) if item][:15]
            if not food_items and food_name:
                food_items = [food_name]

            food_cat = parsed.get("food_category")
            if food_cat not in ("cooked_meal", "raw_ingredients", "packaged_snacks", "fruits_vegetables", "sweets_desserts"):
                food_cat = "cooked_meal"

            diet_type = parsed.get("diet_type", "Requires Confirmation")
            if diet_type not in ("Veg", "Non-Veg", "Vegan"):
                diet_type = "Requires Confirmation"

            visible_ingredients = [str(x).strip()[:80] for x in parsed.get("visible_ingredients", []) if x][:20]
            allergens = [str(x).strip()[:80] for x in parsed.get("allergens", []) if x][:10]
            portion_desc = parsed.get("visible_portion_description")
            if portion_desc:
                portion_desc = str(portion_desc).strip()[:200]

            confidence = parsed.get("confidence", "Medium")
            if confidence not in ("High", "Medium", "Low"):
                confidence = "Medium"

            uncertainty_notes = parsed.get("uncertainty_notes", "Verified visually. Confirm preparation time, quantity and food safety.")

            return make_response(
                status="FOOD_DETECTED",
                success=True,
                is_food=True,
                source=f"Gemini Vision ({model_name})",
                food_name=food_name,
                food_items=food_items,
                food_category=food_cat,
                diet_type=diet_type,
                visible_ingredients=visible_ingredients,
                visible_portion_description=portion_desc,
                allergens=allergens,
                confidence=confidence,
                uncertainty_notes=str(uncertainty_notes)[:500],
                quality_notes=quality["quality_notes"]
            )

        except urllib.error.HTTPError as http_err:
            error_body = ""
            try:
                error_body = http_err.read().decode("utf-8")
                err_json = json.loads(error_body)
                err_message = err_json.get("error", {}).get("message", "")
                err_status = err_json.get("error", {}).get("status", "")
            except Exception:
                err_message = str(http_err)
                err_status = ""

            print(f"Gemini API model '{model_name}' HTTP Error {http_err.code} ({err_status}): {err_message}")

            if http_err.code in (400, 403) and ("API_KEY_INVALID" in err_message or "API key not valid" in err_message):
                return make_response(
                    "API_KEY_INVALID",
                    error="The provided GEMINI_API_KEY is invalid. Please check your Google AI Studio API key.",
                    quality_notes=quality["quality_notes"]
                )
            elif http_err.code == 429:
                return make_response(
                    "RATE_LIMITED",
                    error="Gemini Vision API rate limit reached. Please wait a moment before analyzing another photo.",
                    quality_notes=quality["quality_notes"]
                )
            elif http_err.code == 404:
                # Model not found for this account/endpoint; continue to next fallback model
                last_error_message = f"Model '{model_name}' was not found (404)."
                last_status = "MODEL_NOT_FOUND"
                continue
            else:
                last_error_message = f"Gemini API returned error ({http_err.code}): {err_message or str(http_err)}"
                last_status = "SERVICE_UNAVAILABLE"
                continue

        except (urllib.error.URLError, TimeoutError) as net_err:
            print(f"Network error connecting to Gemini API model '{model_name}': {net_err}")
            last_error_message = "Could not connect to Gemini Vision service. Check backend internet connection."
            last_status = "AI_UNAVAILABLE"
            break

        except Exception as gen_err:
            print(f"Vision response parsing exception with model '{model_name}': {gen_err}")
            last_error_message = f"Vision recognition response parsing error: {gen_err}"
            last_status = "AI_UNAVAILABLE"
            continue

    # If all models were exhausted without success
    return make_response(
        last_status,
        error=last_error_message or "AI Vision scanning is currently unavailable. Please verify API settings or enter details manually.",
        quality_notes=quality["quality_notes"]
    )
