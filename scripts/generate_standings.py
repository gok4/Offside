#!/usr/bin/env python3
"""
generate_standings.py

Aggregates all completed match files in data/matches/ into a ranked league table,
per Rulebook §5: win = 3 pts, draw = 1 pt each, loss = 0 pts. Ranked by total points,
then goal difference (Total Goals Scored - Total Goals Conceded) as a tiebreaker.

All teams in teams.json are included in the table, even if they have 0 matches played
yet (so the table can be shown from matchweek 1 onward).

Usage:
    python scripts/generate_standings.py \
        --matches-dir data/matches \
        --teams-file data/teams.json \
        --output data/standings.json

Output:
    data/standings.json
"""

import argparse
import glob
import json
import os
import sys


def load_all_team_names(teams_file):
    with open(teams_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    teams = data.get("teams", data) if isinstance(data, dict) else data
    return [t.get("name") for t in teams]


def init_team_record(name):
    return {
        "team": name,
        "played": 0,
        "won": 0,
        "drawn": 0,
        "lost": 0,
        "goalsFor": 0,
        "goalsAgainst": 0,
        "goalDifference": 0,
        "points": 0,
    }


def apply_match_result(table, team_name, goals_for, goals_against, result):
    record = table[team_name]
    record["played"] += 1
    record["goalsFor"] += goals_for
    record["goalsAgainst"] += goals_against
    record["goalDifference"] = record["goalsFor"] - record["goalsAgainst"]

    if result == "win":
        record["won"] += 1
        record["points"] += 3
    elif result == "draw":
        record["drawn"] += 1
        record["points"] += 1
    elif result == "loss":
        record["lost"] += 1
        # 0 points, nothing to add


def process_match_file(path, table):
    with open(path, "r", encoding="utf-8") as f:
        match = json.load(f)

    if match.get("status") != "completed":
        return  # only completed matches count toward the table

    home = match.get("homeTeam", {})
    away = match.get("awayTeam", {})
    home_name = home.get("name")
    away_name = away.get("name")
    home_score = home.get("score", 0) or 0
    away_score = away.get("score", 0) or 0

    if home_name not in table or away_name not in table:
        missing = [n for n in (home_name, away_name) if n not in table]
        print(
            f"WARNING: {os.path.basename(path)} references unknown team(s) {missing} "
            f"not found in teams.json — skipping this match.",
            file=sys.stderr,
        )
        return

    if home_score > away_score:
        apply_match_result(table, home_name, home_score, away_score, "win")
        apply_match_result(table, away_name, away_score, home_score, "loss")
    elif home_score < away_score:
        apply_match_result(table, home_name, home_score, away_score, "loss")
        apply_match_result(table, away_name, away_score, home_score, "win")
    else:
        apply_match_result(table, home_name, home_score, away_score, "draw")
        apply_match_result(table, away_name, away_score, home_score, "draw")


def rank_table(table):
    """Sort by points desc, then goal difference desc (Rulebook §5.2). Assign rank."""
    records = list(table.values())
    records.sort(key=lambda r: (-r["points"], -r["goalDifference"], r["team"]))
    for i, record in enumerate(records, start=1):
        record["rank"] = i
    return records


def main():
    parser = argparse.ArgumentParser(description="Generate the Offside GFL league standings table.")
    parser.add_argument("--matches-dir", default="data/matches")
    parser.add_argument("--teams-file", default="data/teams.json")
    parser.add_argument("--output", default="data/standings.json")
    args = parser.parse_args()

    if not os.path.isfile(args.teams_file):
        print(f"ERROR: teams file not found at '{args.teams_file}'", file=sys.stderr)
        sys.exit(1)

    team_names = load_all_team_names(args.teams_file)
    table = {name: init_team_record(name) for name in team_names}

    match_files = sorted(glob.glob(os.path.join(args.matches_dir, "*.json")))
    if not match_files:
        print(f"No match files found in '{args.matches_dir}' — writing an empty table.", file=sys.stderr)

    for path in match_files:
        process_match_file(path, table)

    ranked = rank_table(table)

    output = {
        "generatedFrom": f"{len(match_files)} match file(s) in {args.matches_dir}",
        "standings": ranked,
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Standings written to {args.output}")
    print(f"{'Rank':<5}{'Team':<25}{'P':<4}{'W':<4}{'D':<4}{'L':<4}{'GF':<5}{'GA':<5}{'GD':<5}{'Pts':<4}")
    for r in ranked:
        print(
            f"{r['rank']:<5}{r['team']:<25}{r['played']:<4}{r['won']:<4}{r['drawn']:<4}"
            f"{r['lost']:<4}{r['goalsFor']:<5}{r['goalsAgainst']:<5}{r['goalDifference']:<5}{r['points']:<4}"
        )


if __name__ == "__main__":
    main()
