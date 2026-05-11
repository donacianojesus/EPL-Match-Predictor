# Model Training Script
# Trains Random Forest on 2021-24 EPL data, evaluates on 2024-25, saves model.pkl + metrics.json

import json
import os
import sqlite3

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from features import DB_PATH, calculate_features

MODEL_PATH = os.path.join(os.path.dirname(__file__), "model.pkl")
METRICS_PATH = os.path.join(os.path.dirname(__file__), "metrics.json")

FEATURE_NAMES = [
    "home_form_points", "away_form_points",
    "home_form_goals_scored", "away_form_goals_scored",
    "home_form_goals_conceded", "away_form_goals_conceded",
]

TRAIN_SEASONS = ["2021-22", "2022-23", "2023-24"]
TEST_SEASON = "2024-25"


def build_dataset(conn):
    """Build feature matrix from all matches, skipping those with insufficient history."""
    cur = conn.cursor()
    cur.execute(
        "SELECT date, home_team, away_team, result, season FROM matches ORDER BY date"
    )

    records = []
    skipped = 0
    for date, home_team, away_team, result, season in cur.fetchall():
        feats = calculate_features(conn, home_team, away_team, date, season)
        if feats is None:
            skipped += 1
            continue
        feats["result"] = result
        feats["season"] = season
        records.append(feats)

    print(f"Dataset: {len(records)} usable, {skipped} skipped")
    return pd.DataFrame(records)


def main():
    """Train, evaluate, and save model + metrics."""
    conn = sqlite3.connect(DB_PATH)
    df = build_dataset(conn)
    conn.close()

    # Train/test split by season
    train_df = df[df["season"].isin(TRAIN_SEASONS)]
    test_df = df[df["season"] == TEST_SEASON]
    X_train, y_train = train_df[FEATURE_NAMES], train_df["result"]
    X_test, y_test = test_df[FEATURE_NAMES], test_df["result"]
    print(f"Train: {len(X_train)}  |  Test: {len(X_test)}")

    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred, labels=["A", "D", "H"])
    report = classification_report(y_test, y_pred, labels=["A", "D", "H"], output_dict=True)
    print(f"Accuracy: {accuracy:.4f}")
    print(classification_report(y_test, y_pred, labels=["A", "D", "H"]))

    # Save model and metrics
    joblib.dump(model, MODEL_PATH)
    metrics = {
        "model_type": "RandomForest",
        "accuracy": round(accuracy, 4),
        "confusion_matrix": cm.tolist(),
        "classification_report": {
            k: v for k, v in report.items()
            if k in ["A", "D", "H", "macro avg", "weighted avg"]
        },
        "feature_names": FEATURE_NAMES,
        "class_labels": ["Away Win", "Draw", "Home Win"],
    }
    with open(METRICS_PATH, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"Saved: {MODEL_PATH}, {METRICS_PATH}")


if __name__ == "__main__":
    main()
