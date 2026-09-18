#!/usr/bin/env python3
"""
generate_awards.py

Computes Player of the Week from completed match files -- but ONLY for
matchweeks where every fixture has been played (checked against
fixtures.json), so an award is never handed out based on a partial,
still-in-progress matchweek.

Coach of the Month is NOT computed by this script at all -- it's a
manual decision made once a full calendar month of gameweeks has been
played. This script reads whatever is already in the output file's
"coachOfTheMonth" array and carries it forward unchanged; edit that
array by hand (or with a small helper) when you're ready to name one.

Usage:
    python3 generate_awards.py \
        --matches-dir data/matches \
        --fixtures-file data/fixtures.json \
        --output data/awards.json
"""

import argparse
import glob
import json
import os
from collections import defaultdict


def load_existing_coach_of_the_month(output_path):
    if not os.path.isfile(output_path):
        return []
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
        return existing.get("coachOfTheMonth", [])
    except (json.JSONDecodeError, OSError):
        return []


def fully_completed_matchweeks(fixtures_file):
    """Returns the set of matchweek numbers where every fixture is completed."""
    with open(fixtures_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    fixtures = data.get("fixtures", [])

    total_per_week, completed_per_week = defaultdict(int), defaultdict(int)
    for fx in fixtures:
        mw = fx.get("matchweek")
        total_per_week[mw] += 1
        if fx.get("status") == "completed":
            completed_per_week[mw] += 1

    return {mw for mw, total in total_per_week.items() if completed_per_week[mw] == total}


def compute_player_of_the_week(matches, eligible_matchweeks):
    by_week = defaultdict(list)
    for match in matches:
        matchweek = match.get("matchweek")
        if matchweek not in eligible_matchweeks:
            continue
        for side_key in ("homeTeam", "awayTeam"):
            side = match.get(side_key, {})
            team_name = side.get("name")
            for player_name, stats in side.get("playerStats", {}).items():
                points = stats.get("points", 0) or 0
                ict = (stats.get("ict") or {}).get("ictIndex", 0) or 0
                by_week[matchweek].append((player_name, team_name, points, ict))

    results = []
    for matchweek in sorted(by_week.keys()):
        candidates = by_week[matchweek]
        if not candidates:
            continue
        best = sorted(candidates, key=lambda c: (-c[2], -c[3], c[0]))[0]
        results.append({
            "matchweek": matchweek, "player": best[0], "team": best[1],
            "points": best[2], "ictIndex": round(best[3], 2),
        })
    return results


def main():
    parser = argparse.ArgumentParser(description="Compute Player of the Week for fully completed matchweeks.")
    parser.add_argument("--matches-dir", default="data/matches")
    parser.add_argument("--fixtures-file", default="data/fixtures.json")
    parser.add_argument("--output", default="data/awards.json")
    args = parser.parse_args()

    eligible_matchweeks = fully_completed_matchweeks(args.fixtures_file)

    match_files = sorted(glob.glob(os.path.join(args.matches_dir, "*.json")))
    matches = []
    for path in match_files:
        with open(path, "r", encoding="utf-8") as f:
            match = json.load(f)
        if match.get("status") == "completed":
            matches.append(match)

    potw = compute_player_of_the_week(matches, eligible_matchweeks)
    cotm = load_existing_coach_of_the_month(args.output)  # untouched, manual only

    output = {
        "generatedFrom": f"{len(matches)} completed match(es), {len(eligible_matchweeks)} fully completed matchweek(s)",
        "playerOfTheWeek": potw,
        "coachOfTheMonth": cotm,
    }

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Player of the Week computed for {len(potw)} fully-completed matchweek(s).")
    print(f"Coach of the Month left untouched ({len(cotm)} existing entr{'y' if len(cotm)==1 else 'ies'}) -- edit manually when ready.")
    if potw:
        print(f"  Latest POTW: {potw[-1]['player']} ({potw[-1]['team']}) — {potw[-1]['points']} pts, matchweek {potw[-1]['matchweek']}")
    print(f"Written: {args.output}")


if __name__ == "__main__":
    main()
