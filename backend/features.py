#Feature engineering for EPL Match Predictor.

#Calculates 6 form-based features from match history:
# 1. home_form_points       — Points from home team's last 5 matches
# 2. away_form_points       — Points from away team's last 5 matches
# 3. home_form_goals_scored — Avg goals scored by home team in last 5
# 4. away_form_goals_scored — Avg goals scored by away team in last 5
# 5. home_form_goals_conceded — Avg goals conceded by home team in last 5
# 6. away_form_goals_conceded — Avg goals conceded by away team in last 5


import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "epl_data.db")


def get_team_last_n_matches(conn, team, before_date, season, n=5):
    """Query last n matches for a team (home or away) before a given date within the same season.

    Args:
        conn: SQLite connection.
        team: Team name (must match DB exactly).
        before_date: ISO date string (YYYY-MM-DD). Only matches before this date are included.
        season: Season label (e.g. '2023-24').
        n: Number of recent matches to retrieve.

    Returns:
        List of sqlite3.Row objects, most recent first.
    """
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT date, home_team, away_team, home_goals, away_goals, result
        FROM matches
        WHERE (home_team = ? OR away_team = ?)
          AND date < ?
          AND season = ?
        ORDER BY date DESC
        LIMIT ?
        """,
        (team, team, before_date, season, n),
    )
    return cur.fetchall()


def calculate_team_form(matches, team):
    """Calculate form stats from a list of match rows for a given team.

    Args:
        matches: List of sqlite3.Row objects (from get_team_last_n_matches).
        team: The team whose perspective to evaluate from.

    Returns:
        Dict with 'points', 'avg_goals_scored', 'avg_goals_conceded',
        or None if matches list is empty.
    """
    if not matches:
        return None

    total_points = 0
    total_scored = 0
    total_conceded = 0

    for match in matches:
        if match["home_team"] == team:
            scored = match["home_goals"]
            conceded = match["away_goals"]
            result = match["result"]
            if result == "H":
                total_points += 3
            elif result == "D":
                total_points += 1
        else:
            scored = match["away_goals"]
            conceded = match["home_goals"]
            result = match["result"]
            if result == "A":
                total_points += 3
            elif result == "D":
                total_points += 1

        total_scored += scored
        total_conceded += conceded

    n = len(matches)
    return {
        "points": total_points,
        "avg_goals_scored": round(total_scored / n, 2),
        "avg_goals_conceded": round(total_conceded / n, 2),
    }


def calculate_features(conn, home_team, away_team, date, season):
    """Calculate the 6-feature vector for a given matchup.

    Args:
        conn: SQLite connection.
        home_team: Home team name.
        away_team: Away team name.
        date: Match date (YYYY-MM-DD string).
        season: Season label (e.g. '2023-24').

    Returns:
        Dict with 6 feature values, or None if either team has fewer than 5
        prior matches in that season.
    """
    home_matches = get_team_last_n_matches(conn, home_team, date, season, n=5)
    away_matches = get_team_last_n_matches(conn, away_team, date, season, n=5)

    if len(home_matches) < 5 or len(away_matches) < 5:
        return None

    home_form = calculate_team_form(home_matches, home_team)
    away_form = calculate_team_form(away_matches, away_team)

    return {
        "home_form_points": home_form["points"],
        "away_form_points": away_form["points"],
        "home_form_goals_scored": home_form["avg_goals_scored"],
        "away_form_goals_scored": away_form["avg_goals_scored"],
        "home_form_goals_conceded": home_form["avg_goals_conceded"],
        "away_form_goals_conceded": away_form["avg_goals_conceded"],
    }


if __name__ == "__main__":
    conn = sqlite3.connect(DB_PATH)

    # Test: Arsenal vs Chelsea on 2023-12-29 (season 2023-24)
    test_home = "Arsenal"
    test_away = "Chelsea"
    test_date = "2023-12-29"
    test_season = "2023-24"

    print(f"Feature test: {test_home} vs {test_away} on {test_date} ({test_season})\n")

    # Show last 5 matches for each team
    for team in [test_home, test_away]:
        matches = get_team_last_n_matches(conn, team, test_date, test_season, n=5)
        print(f"{team}'s last 5 matches before {test_date}:")
        for m in matches:
            print(f"  {m['date']}  {m['home_team']} {m['home_goals']}-{m['away_goals']} {m['away_team']}")
        form = calculate_team_form(matches, team)
        print(f"  -> Points: {form['points']}, "
              f"Avg scored: {form['avg_goals_scored']}, "
              f"Avg conceded: {form['avg_goals_conceded']}\n")

    # Full feature vector
    features = calculate_features(conn, test_home, test_away, test_date, test_season)
    if features:
        print("Feature vector:")
        for k, v in features.items():
            print(f"  {k}: {v}")
    else:
        print("Insufficient match history for feature calculation.")

    conn.close()
