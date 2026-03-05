# Model Training Script
# Trains Random Forest on 2021-23 EPL data, evaluates on 2023-24, saves model.pkl + metrics.json

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

TRAIN_SEASONS = ["2021-22", "2022-23"]
TEST_SEASON = "2023-24"


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

    # TODO: Train RandomForestClassifier on X_train/y_train (n_estimators=100, random_state=42)

    # TODO: Evaluate on X_test/y_test — accuracy, confusion matrix, classification report

    # TODO: Save model to MODEL_PATH with joblib.dump, metrics to METRICS_PATH as JSON


if __name__ == "__main__":
    main()
