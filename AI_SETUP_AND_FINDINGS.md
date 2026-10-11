# EcoBite AI Food Camera Scanner — Audit, Root Causes & Implementation Findings

## 1. Verified Source-Code Findings & Root Causes of Scanner Failure

### Root Cause 1: Broken Camera Snap Transfer in Frontend
In `frontend/donor/donor.html`, the camera preview drew video frames to a `<canvas>` element and updated `<img id="aiScanPreview">`, but did not generate a `Blob` or `File` object or assign it to any input or global state. When `runAIScan()` executed, it attempted to read `document.getElementById('aiScanInput').files[0]`, which was always empty when capturing photos from the camera. This caused camera scans to fail immediately with an unhandled exception or missing file alert.
*Fix implemented:* Converted canvas snapshot to a `Blob`/`File` via `canvas.toBlob(...)`, stored in `window.selectedScanFile`, which is passed seamlessly to `/api/ai-scan-food` and attached to the donation listing.

### Root Cause 2: Dead Filename Heuristics and Fake Classification
`backend/app.py` contained a legacy helper `analyze_food_image_with_ai` (lines 235–349) with hardcoded substring matching (`if any(k in fn_lower for k in ["biryani", "pulao"])`). Previous versions also classified non-food images or API failures as "No Food" or defaulted to "Surplus Cooked Meal".
*Fix implemented:* Entirely removed the legacy filename-based code. AI scanning is routed strictly to `backend.ai_engine.analyze_food_image`, which operates exclusively on actual decoded image pixels, evaluates solid/blank image entropy, connects to Gemini multimodal vision models, and rejects non-food images accurately without filename cheats.

### Root Cause 3: Unsupported / Hardcoded Vision Model Names
Previous references targeted `gemini-2.5-flash` (which does not exist in Google Generative AI API v1beta and returns 404) or hardcoded legacy versions.
*Fix implemented:* Supported models default to `gemini-2.0-flash`, with configurable override via `ECOBITE_VISION_MODEL` and automated fallbacks to `gemini-1.5-flash` and `gemini-1.5-pro`.

### Root Cause 4: Poor Error Differentiation (API Failure != No Food)
Previous code conflated missing API keys, network failures, and rate limits with "No Food Detected".
*Fix implemented:* Clear HTTP status codes and diagnostic status payloads:
- `FOOD_DETECTED` (HTTP 200): Food items recognized with dish details, category, diet, ingredients, allergens.
- `NO_FOOD_DETECTED` (HTTP 200): Image visually confirmed to contain no edible food.
- `UNCERTAIN` (HTTP 200): Image is too blurry or ambiguous to identify reliably.
- `INVALID_IMAGE` (HTTP 400): Corrupt or non-image bytes.
- `API_KEY_INVALID` (HTTP 403): Gemini API key rejected.
- `RATE_LIMITED` (HTTP 429): Quota or rate limit exceeded.
- `SERVICE_UNAVAILABLE` (HTTP 503): API key unset or network unreachable.

### Root Cause 5: Image Distortion & Cropping
The CSS for `.camera-preview-wrapper img` had `object-fit: cover; height: 260px;`, which severely cropped food photos (especially portrait and square orientations).
*Fix implemented:* Changed preview styling to `object-fit: contain; max-height: 380px; width: auto;`, providing uncropped, aspect-ratio-accurate display for portrait, landscape, and square images.

---

## 2. Review of the 41-Class MobileNetV3 Checkpoint & Dataset

- **Model Architecture:** MobileNetV3-Small transfer learning checkpoint with 41 output classes (`ml/checkpoints/ecobite_food_model.pth`).
- **Dataset Audit:** Inspection of `ml/dataset_builder.py` and `dataset/food_dataset/` revealed that images are generated programmatically using PIL geometric primitives and colors (e.g., circles for rotis, colored arcs for curry). This is **synthetic artwork**, not natural photographs of real prepared meals.
- **Evaluation Findings:** Running `ml/evaluate_model.py` achieves 82.1% Top-1 and 96.7% Top-3 on the generated test set. **However, this performance is specific to synthetic drawings and cannot claim high real-world accuracy on real food photography.**
- **Honest Accuracy Disclosure:** We strictly document this limitation. Real-world food recognition relies on multimodal vision APIs (Gemini Vision) analyzing raw pixels, while the local model serves as an offline architectural baseline.

---

## 3. Environment & Running Instructions

### Backend (Python / Flask)
```bash
# 1. Install dependencies
pip install flask pillow torch torchvision

# 2. Set environment variables (or copy .env.example to .env)
# Windows PowerShell:
$env:GEMINI_API_KEY="your_actual_google_ai_studio_key"
$env:ECOBITE_VISION_MODEL="gemini-2.0-flash"

# 3. Start server
python backend/app.py
```
Server runs at `http://127.0.0.1:3000`.

### Node Server Note
`backend/server.js` was an early in-memory prototype. The full platform with database, authentication, NGO matching, and AI scanner runs on `backend/app.py`.
