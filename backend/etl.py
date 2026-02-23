"""
ETL Script — Download EPL match CSVs and load into SQLite.

Downloads 3 seasons (2021-22, 2022-23, 2023-24) from football-data.co.uk,
cleans the data, and stores it in a local SQLite database (epl_data.db).

Usage:
    python etl.py
"""

import os
import sqlite3
import urllib.request

import pandas as pd


# Season configurations: (season label, URL path segment)
SEASONS = [
    ("2021-22", "2122"),
    ("2022-23", "2223"),
    ("2023-24", "2324"),
]

BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/E0.csv"
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
DB_PATH = os.path.join(os.path.dirname(__file__), "epl_data.db")

# Columns to keep from the CSV and their renamed equivalents
CSV_COLUMNS = ["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"]
RENAMED_COLUMNS = {
    "Date": "date",
    "HomeTeam": "home_team",
    "AwayTeam": "away_team",
    "FTHG": "home_goals",
    "FTAG": "away_goals",
    "FTR": "result",
}


def download_csv(season_code, dest_path):
    """Download a season CSV from football-data.co.uk if not already cached.

    Args:
        season_code: URL path segment (e.g., '2324').
        dest_path: Local file path to save the CSV.
    """
    if os.path.exists(dest_path):
        print(f"  Already downloaded: {dest_path}")
        return

    url = BASE_URL.format(code=season_code)
    print(f"  Downloading {url} ...")
    urllib.request.urlretrieve(url, dest_path)
    print(f"  Saved to {dest_path}")


def load_season(csv_path, season_label):
    """Read a season CSV and return a cleaned DataFrame.

    Args:
        csv_path: Path to the CSV file.
        season_label: Season identifier (e.g., '2021-22').

    Returns:
        DataFrame with cleaned match records and a 'season' column.
    """
    df = pd.read_csv(csv_path, encoding="latin-1")

    # Select and rename columns
    df = df[CSV_COLUMNS].rename(columns=RENAMED_COLUMNS)

    # Parse dates — football-data.co.uk uses DD/MM/YYYY (UK format)
    df["date"] = pd.to_datetime(df["date"], dayfirst=True)

    # Store dates as YYYY-MM-DD strings for SQLite
    df["date"] = df["date"].dt.strftime("%Y-%m-%d")

    # Add season identifier
    df["season"] = season_label

    # Drop rows with missing values in any key column
    df = df.dropna()

    # Ensure goal columns are integers
    df["home_goals"] = df["home_goals"].astype(int)
    df["away_goals"] = df["away_goals"].astype(int)

    return df


def main():
    """Download CSVs, clean data, and load into SQLite."""
    os.makedirs(DATA_DIR, exist_ok=True)

    all_frames = []

    for season_label, season_code in SEASONS:
        print(f"\nProcessing {season_label} season:")
        csv_path = os.path.join(DATA_DIR, f"{season_label}.csv")

        download_csv(season_code, csv_path)
        df = load_season(csv_path, season_label)
        all_frames.append(df)
        print(f"  Loaded {len(df)} matches")

    # Combine all seasons
    combined = pd.concat(all_frames, ignore_index=True)

    # Write to SQLite
    conn = sqlite3.connect(DB_PATH)
    combined.to_sql("matches", conn, if_exists="replace", index=True, index_label="id")
    conn.close()

    # Print summary
    print(f"\n{'='*50}")
    print(f"ETL Complete — {len(combined)} total matches loaded into {DB_PATH}")
    print(f"{'='*50}")
    print("\nMatches per season:")
    for season_label, count in combined["season"].value_counts().sort_index().items():
        print(f"  {season_label}: {count}")

    # Print unique team names for verification
    teams = sorted(combined["home_team"].unique())
    print(f"\nUnique teams ({len(teams)}):")
    for team in teams:
        print(f"  {team}")


if __name__ == "__main__":
    main()
