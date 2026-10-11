# EcoBite — Working setup (Flask server)

## Start on Windows
1. Install Python 3.10 or newer.
2. Open PowerShell in this folder.
3. Run `python -m pip install -r requirements.txt`.
4. In the same PowerShell session, set `$env:GEMINI_API_KEY="YOUR_OWN_KEY"`. Never commit your API key or share it.
5. Run `python backend/app.py`.
6. Visit http://localhost:3000.

**Important:** DO NOT run `npm start` or `node backend/server.js` for this project. That is a separate legacy demonstration server and uses an in-memory donation list rather than the SQLite-backed Flask application. Only Flask should own port 3000.

## AI behavior
- Configured Gemini vision service analyzes actual image bytes. This is inference, not a newly-trained offline model.
- Non-food images produce no food suggestions; ambiguous images request review.
- Food category/name are suggestions; actual servings, cooking times and safety must be confirmed by the donor.
- If you have no valid API key or your key has no model access, the scanner reports `SERVICE_UNAVAILABLE` and manual donation entry remains available.
- Model defaults to `gemini-2.5-flash`. Override with `$env:ECOBITE_VISION_MODEL="supported-model-name"` if necessary.

## Verify
1. Upload white rice: should get a rice-related food suggestion, if vision API is configured and available.
2. Upload pizza: should get a pizza suggestion.
3. Upload non-food poster: should receive no food results.
4. Submit a manually reviewed donation and ensure it appears under My Donations.
5. To stop the server, press Ctrl+C.

Without a real API key and connected service we cannot certify the live recognition results or actual model accuracy.
