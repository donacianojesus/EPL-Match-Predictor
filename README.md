# EPL Match Predictor

A Premier League match outcome predictor. Uses historical match data and a Random Forest model to predict match results. Features a Flask API backend and React frontend.

## Key Features

- **Backend**: Flask REST API — serves predictions from trained Random Forest model
- **Frontend**: React SPA — team selector, predictions, and model performance metrics
- **Model**: Random Forest classifier trained on EPL seasons 2021–24, evaluated on 2024–25
- **Data**: Historical match CSVs (2021-22 through 2024-25)
- **Team Prediction**: Any team combo selectable; uses most recent 5-match form data across all seasons

## Quick Start

**Backend (Terminal 1):**
```bash
cd src/backend
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```
Flask API runs on `http://localhost:5001`

**Frontend (Terminal 2):**
```bash
cd src/frontend
npm install
npm start
```
React app runs on `http://localhost:3000`

## Setup (First Time)

```bash
# Backend
cd src/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 etl.py      # Download data and build database
python3 train.py    # Train model (creates model.pkl + metrics.json)

# Frontend
cd ../frontend
npm install
```

## File Structure

```
src/
├── backend/
│   ├── app.py           — Flask API
│   ├── etl.py           — Data pipeline
│   ├── train.py         — Model training
│   ├── features.py      — Feature engineering
│   ├── data/            — CSV files
│   ├── epl_data.db      — SQLite database
│   ├── model.pkl        — Trained model
│   └── metrics.json     — Model evaluation metrics
└── frontend/
    ├── src/App.js       — Main React component
    ├── src/App.css      — Styling
    └── public/          — Static assets
```

## API Endpoint

**POST** `http://localhost:5001/api/predict`
```json
{
  "home_team": "Arsenal",
  "away_team": "Chelsea"
}
```

Returns prediction, probabilities, confidence, and feature data.

## Model Info

- Accuracy: ~45% on 2024–25 test set
- Features: Last 5 matches form (points, goals scored/conceded for each team)
- Classes: Away Win, Draw, Home Win
