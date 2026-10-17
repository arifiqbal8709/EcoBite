# EcoBite — AI-Powered Food Redistribution Platform

EcoBite is an intelligent food donation and surplus meal redistribution platform connecting donors (restaurants, caterers, individuals), NGOs, delivery personnel, and administrators to reduce food waste and combat hunger.

---

## 🌟 Key Features

- **🤖 AI Food Scanner**: Powered by Google Gemini Vision to recognize food items, estimate freshness, quantify servings, and suggest categories from photos.
- **🔐 Secure Delivery OTP Verification**: Dual OTP verification for pickups and deliveries ensuring verified chain-of-custody.
- **🏢 Multi-Role System**:
  - **Donor**: Donate surplus meals, emergency donations, and bulk food with automated expiry tracking.
  - **NGO**: Real-time food map and claims with instant status tracking.
  - **Delivery**: Delivery agent dashboard with OTP verification, route planning, and task completion.
  - **Admin**: Comprehensive platform analytics, user role management, and complaint ticket resolution.
- **📱 Responsive UI**: High-contrast, mobile-friendly interface designed for on-the-go donors and delivery agents.

---

## 📂 Project Structure

```text
ShareMeal-Website/
├── backend/
│   ├── app.py                # Primary Flask backend API & static asset server
│   └── server.js             # Legacy demonstration server
├── database/
│   ├── db.py                 # SQLite initialization & schema migrations
│   └── sharemeal.db          # SQLite persistent database
├── frontend/
│   ├── user/                 # Landing page, login, signup, contact
│   ├── donor/                # Donor dashboard, AI scanner, donation forms
│   ├── ngos/                 # NGO food finding and claim interface
│   ├── delivery/             # Delivery agent task dashboard & OTP verifier
│   ├── admin/                # Admin analytics and complaint management
│   ├── complaints.js         # Unified complaint handling client
│   └── style.css             # Main styling system
├── scripts/                  # Administrative and database maintenance utilities
├── render.yaml               # 1-Click Render blueprint deployment specification
├── Procfile                  # Production WSGI entry point (Gunicorn)
└── requirements.txt          # Python dependencies
```

---

## 🚀 How to Run Locally

### Prerequisites
- Python 3.10 or newer
- Git

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Create or edit your `.env` file in the project root:
```env
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3.5-flash
PORT=3000
SECRET_KEY=your_secure_session_secret
OTP_SALT=your_otp_salt
```

### 3. Start the Server
On Windows:
```powershell
python backend/app.py
```
Or on Linux/macOS:
```bash
./start.sh
# or
python3 backend/app.py
```

Open your browser and navigate to **http://localhost:3000**.

---

## ☁️ Deploying to Render

This repository includes first-class support for **[Render](https://render.com)** via `render.yaml` and `Procfile`:

1. In the **Render Dashboard**, click **New +** > **Blueprint**.
2. Connect your repository: `https://github.com/arifiqbal8709/EcoBite`.
3. Render automatically provisions the web service using:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn backend.app:app`
4. Set your `GEMINI_API_KEY` in the Render environment variables.
5. Click **Apply** to deploy your live platform.

---

## 👥 Authentication & Roles

| Role | Access URL | Features |
|---|---|---|
| **Public / User** | `/` | Platform overview, stats, impact metrics |
| **Donor** | `/donor` | AI food scanning, donation listings, history |
| **NGO** | `/find-food` | Food claims, urgent request matching |
| **Delivery** | `/delivery/dashboard` | Pickup/dropoff OTP verification |
| **Admin** | `/admin` | System health, analytics, dispute tickets |
