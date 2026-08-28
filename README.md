# Sahayak (सहायक / సహాయక్) — Informal Wage Agreement System

A mobile-friendly web application for informal laborers and contractors to create simple, verifiable wage agreements with downloadable PDF contracts and QR-code backed verification.

## Features
- ✍️ Simple high-contrast form for wage agreements
- 📄 Professional PDF contract generation with legal structure
- 📱 QR code linking to a public verification portal
- 🛡️ Read-only verification page for mediators and labor offices
- 🌐 Multilingual: English, हिन्दी (Hindi), తెలుగు (Telugu)
- 💾 SQLite database with UUID-based agreement IDs

## Run Locally

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:5000

## Deployment
Deployed on Render.com. Set the environment variable `PUBLIC_BASE_URL` to your Render service URL.
