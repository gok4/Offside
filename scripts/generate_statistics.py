#!/usr/bin/env python3
"""
generate_statistics.py

Aggregates season-wide player statistics (goals, assists, clean sheets,
total fantasy points) from every completed match file in data/matches/,
and writes ranked leaderboards to data/statistics.json.

Clean sheets are counted for Goalkeepers and Defenders only (the
conventional definition on most stats pages), even though the scoring
rulebook also awards a smaller clean-sheet bonus to Midfielders -- that's
a scoring detail, not a "clean sheet" stat in the traditional sense.

Player identification: exact "name" string, matched against the position
in teams.json (names are globally unique within the roster).

Usage:
    python3 generate_statistics.py \
        --matches-dir data/matches \
        --teams-file data/teams.json \
        --output data/statistics.json
"""

import argparse
import glob
import json
import os
import sys

POSITION_TO_BUCKET = {
    "GK": "GK",
    "RB": "DEF", "CB": "DEF", "LB": "DEF",
    "CDM": "MID", "CM": "MID", "CAM": "MID", "RM": "MID", "LM": "MID",
    "RW": "FWD", "LW": "FWD", "ST": "FWD",
}

TOP_N = 20


def load_player_lookup(teams_file):
    """Build {player_name: {"team": team_name, "position": position}}."""
    with open(teams_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    teams = data.get("teams", data) if isinstance(data, dict) else data

    lookup = {}
    for team in teams:
        team_name = team.get("name")
        for p in team.get("players", []):
            lookup[p["name"]] = {"team": team_name, "position": p.get("position")}
    return lookup


def init_player_record(name, team, position):
    return {
        "name": name,
        "team": team,
        "position": position,
        "appearances": 0,
        "goals": 0,
        "assists": 0,
        "cleanSheets": 0,
        "yellowCards": 0,
        "redCards": 0,
        "totalPoints": 0,
    }


def process_side(side, team_conceded, records, player_lookup):
    """Accumulate stats for every player on one side (home or away) of a match."""
    team_name = side.get("name")
    for player_name, stats in side.get("playerStats", {}).items():
        info = player_lookup.get(player_name)
        position = info["position"] if info else None
        bucket = POSITION_TO_BUCKET.get(position, "MID")

        if player_name not in records:
            records[player_name] = init_player_record(player_name, team_name, position)
        record = records[player_name]

        minutes = stats.get("minutesPlayed", 0) or 0
        if minutes > 0:
            record["appearances"] += 1

        record["goals"] += stats.get("goals", 0) or 0
        record["assists"] += stats.get("assists", 0) or 0
        record["totalPoints"] += stats.get("points", 0) or 0

        if stats.get("yellowCard"):
            record["yellowCards"] += 1
        if stats.get("redCard"):
            record["redCards"] += 1

        if bucket in ("GK", "DEF") and minutes >= 60 and (team_conceded or 0) == 0:
            record["cleanSheets"] += 1


def process_match_file(path, records, player_lookup):
    with open(path, "r", encoding="utf-8") as f:
        match = json.load(f)

    if match.get("status") != "completed":
        return False

    home = match.get("homeTeam", {})
    away = match.get("awayTeam", {})

    process_side(home, away.get("score", 0), records, player_lookup)
    process_side(away, home.get("score", 0), records, player_lookup)
    return True


def build_leaderboard(records, key, top_n=TOP_N):
    ranked = sorted(records.values(), key=lambda r: (-r[key], r["name"]))
    ranked = [r for r in ranked if r[key] > 0][:top_n]
    return [
        {"rank": i, "name": r["name"], "team": r["team"], "position": r["position"], "value": r[key]}
        for i, r in enumerate(ranked, start=1)
    ]


def main():
    parser = argparse.ArgumentParser(description="Aggregate season statistics from completed matches.")
    parser.add_argument("--matches-dir", default="data/matches")
    parser.add_argument("--teams-file", default="data/teams.json")
    parser.add_argument("--output", default="data/statistics.json")
    args = parser.parse_args()

    if not os.path.isfile(args.teams_file):
        print(f"ERROR: teams file not found at '{args.teams_file}'", file=sys.stderr)
        sys.exit(1)

    player_lookup = load_player_lookup(args.teams_file)

    match_files = sorted(glob.glob(os.path.join(args.matches_dir, "*.json")))
    records = {}
    completed_count = 0
    for path in match_files:
        if process_match_file(path, records, player_lookup):
            completed_count += 1

    output = {
        "generatedFrom": f"{completed_count} completed match file(s) in {args.matches_dir}",
        "topScorers": build_leaderboard(records, "goals"),
        "topAssists": build_leaderboard(records, "assists"),
        "cleanSheets": build_leaderboard(records, "cleanSheets"),
        "topPoints": build_leaderboard(records, "totalPoints"),
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Statistics generated from {completed_count} completed match(es).")
    print(f"  Top scorer:      {output['topScorers'][0] if output['topScorers'] else '(none yet)'}")
    print(f"  Top assist:      {output['topAssists'][0] if output['topAssists'] else '(none yet)'}")
    print(f"  Most clean sheets: {output['cleanSheets'][0] if output['cleanSheets'] else '(none yet)'}")
    print(f"Written: {args.output}")


if __name__ == "__main__":
    main()
