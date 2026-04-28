"""Flask API for EPL Match Predictor.

Endpoints:
    GET  /api/matches  — Hardcoded upcoming fixtures for demo
    POST /api/predict  — Predict match outcome given home/away teams
    GET  /api/metrics  — Return model evaluation metrics
"""

import json
import os
import sqlite3

import joblib
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS

from features import calculate_features

# Paths
BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, "epl_data.db")
MODEL_PATH = os.path.join(BASE_DIR, "model.pkl")
METRICS_PATH = os.path.join(BASE_DIR, "metrics.json")


model = joblib.load(MODEL_PATH)

with open(METRICS_PATH, "r") as f:
    metrics_data = json.load(f)

# Reference point for form lookups: end of 2023-24 season (most recent data)
PREDICT_SEASON = "2023-24"
PREDICT_DATE = "2024-05-20"

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000"])


def get_db():
    """Open a new SQLite connection with Row factory enabled.

    Returns:
        sqlite3.Connection with row_factory set to sqlite3.Row.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_valid_teams():
    """Fetch all distinct team names present in the database.

    Returns:
        Set of team name strings.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT DISTINCT home_team FROM matches "
        "UNION SELECT DISTINCT away_team FROM matches"
    )
    teams = {row[0] for row in cur.fetchall()}
    conn.close()
    return teams

# GET /api/matches
@app.route("/api/matches", methods=["GET"])
def get_matches():
    """Return a hardcoded list of upcoming EPL demo fixtures.

    Returns:
        JSON with a 'matches' array of fixture objects.
    """
    fixtures = [
        {"id": 1, "home_team": "Arsenal",    "away_team": "Chelsea",       "date": "2024-08-17"},
        {"id": 2, "home_team": "Man City",   "away_team": "Liverpool",     "date": "2024-08-17"},
        {"id": 3, "home_team": "Tottenham",  "away_team": "Newcastle",     "date": "2024-08-18"},
        {"id": 4, "home_team": "Aston Villa","away_team": "West Ham",      "date": "2024-08-18"},
        {"id": 5, "home_team": "Brentford",  "away_team": "Nott'm Forest", "date": "2024-08-18"},
    ]
    return jsonify({"matches": fixtures})

# POST /api/predict
@app.route("/api/predict", methods=["POST"])
def predict():
    """Predict the outcome of a match given home and away teams.

    Request JSON:
        { "home_team": "Arsenal", "away_team": "Chelsea" }

    Returns:
        JSON with prediction, probabilities, confidence, feature values,
        and model accuracy. Returns 400 on invalid input or insufficient data.
    """
    data = request.get_json(force=True)
    home_team = data.get("home_team", "").strip()
    away_team = data.get("away_team", "").strip()

    if not home_team or not away_team:
        return jsonify({"error": "Both home_team and away_team are required."}), 400

    if home_team == away_team:
        return jsonify({"error": "home_team and away_team must be different."}), 400

    valid_teams = get_valid_teams()
    if home_team not in valid_teams:
        return jsonify({"error": f"Team not found in database: '{home_team}'"}), 400
    if away_team not in valid_teams:
        return jsonify({"error": f"Team not found in database: '{away_team}'"}), 400

    conn = get_db()
    features = calculate_features(conn, home_team, away_team, PREDICT_DATE, PREDICT_SEASON)
    conn.close()

    if features is None:
        return jsonify({
            "error": (
                f"Insufficient match history for '{home_team}' or '{away_team}' "
                f"in the {PREDICT_SEASON} season."
            )
        }), 400

    # Build feature vector in the same column order used during training
    feature_names = metrics_data["feature_names"]
    feature_vector = np.array([[features[name] for name in feature_names]])

    # model.classes_ is ['A', 'D', 'H'] — map to readable labels
    class_map = {"A": "Away Win", "D": "Draw", "H": "Home Win"}
    probabilities_raw = model.predict_proba(feature_vector)[0]
    prediction_code = model.predict(feature_vector)[0]

    proba_dict = {
        class_map[cls]: round(float(prob), 4)
        for cls, prob in zip(model.classes_, probabilities_raw)
    }
    confidence = round(float(max(probabilities_raw)), 4)

    return jsonify({
        "home_team": home_team,
        "away_team": away_team,
        "prediction": class_map[prediction_code],
        "probabilities": proba_dict,
        "confidence": confidence,
        "features": features,
        "model_info": {
            "accuracy": metrics_data["accuracy"],
            "season_used": PREDICT_SEASON,
        },
    })


# GET /api/metrics
@app.route("/api/metrics", methods=["GET"])
def get_metrics():
    """Return the trained model's evaluation metrics.

    Returns:
        JSON with accuracy, confusion matrix, feature names, and class labels.
    """
    return jsonify(metrics_data)

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
