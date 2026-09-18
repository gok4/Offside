#!/usr/bin/env python3
"""
process_match.py

Runs the post-match pipeline in one command, once you've filled in a
match template:

    1. calculate_match_points.py  -> data/matches/<id>.json
    2. update_fixture_result.py   -> marks the fixture completed in fixtures.json
    3. generate_standings.py      -> refreshes the league table
    4. generate_statistics.py     -> refreshes goal/assist/points leaderboards

Player of the Week / Coach of the Month are deliberately NOT run here --
Player of the Week only makes sense once a full matchweek is complete
(run generate_awards.py yourself at that point; this script will tell you
when that happens), and Coach of the Month is a manual decision you make
once a full month of gameweeks has been played.

Usage (run from offside-tools, same as the individual scripts):
    python3 process_match.py --template ../offside/data/match_templates/gfl-2026-001.xlsx
"""

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent


def run(description, args):
    print(f"\n>>> {description}")
    result = subprocess.run([sys.executable, *args], cwd=SCRIPT_DIR)
    if result.returncode != 0:
        print(f"\nStopped: '{description}' failed (exit code {result.returncode}).")
        print("Fix the issue above and re-run process_match.py -- it's safe to re-run from scratch.")
        sys.exit(result.returncode)


def check_matchweek_now_complete(fixtures_file, match_id):
    """After updating the fixture, check whether the matchweek this match
    belongs to just became fully completed -- if so, let the user know
    it's a good time to run generate_awards.py."""
    try:
        with open(fixtures_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return

    fixtures = data.get("fixtures", [])
    this_match = next((fx for fx in fixtures if fx.get("matchId") == match_id), None)
    if not this_match:
        return
    matchweek = this_match.get("matchweek")

    same_week = [fx for fx in fixtures if fx.get("matchweek") == matchweek]
    total, completed = len(same_week), sum(1 for fx in same_week if fx.get("status") == "completed")

    if total > 0 and completed == total:
        print(f"\nMatchweek {matchweek} is now fully complete ({completed}/{total} fixtures played).")
        print("This is a good time to run: python generate_awards.py")
    else:
        print(f"\nMatchweek {matchweek}: {completed}/{total} fixtures completed so far.")


def main():
    parser = argparse.ArgumentParser(description="Run the post-match pipeline (points, fixture, standings, statistics) in one command.")
    parser.add_argument("--template", required=True, help="Path to the filled-in match .xlsx")
    parser.add_argument("--teams-file", default="../offside/data/teams.json")
    parser.add_argument("--matches-dir", default="../offside/data/matches")
    parser.add_argument("--fixtures-file", default="../offside/data/fixtures.json")
    parser.add_argument("--standings-output", default="../offside/data/standings.json")
    parser.add_argument("--statistics-output", default="../offside/data/statistics.json")
    args = parser.parse_args()

    template_path = Path(args.template)
    if not template_path.is_file():
        print(f"ERROR: template file not found at '{template_path}'")
        sys.exit(1)

    match_id = template_path.stem
    match_json_path = str(Path(args.matches_dir) / f"{match_id}.json")

    run("Calculating fantasy points", [
        str(SCRIPT_DIR / "calculate_match_points.py"),
        "--input", args.template, "--teams-file", args.teams_file, "--output-dir", args.matches_dir,
    ])

    run("Updating fixture result", [
        str(SCRIPT_DIR / "update_fixture_result.py"),
        "--match-file", match_json_path, "--fixtures-file", args.fixtures_file,
    ])

    run("Refreshing standings", [
        str(SCRIPT_DIR / "generate_standings.py"),
        "--matches-dir", args.matches_dir, "--teams-file", args.teams_file, "--output", args.standings_output,
    ])

    run("Refreshing statistics", [
        str(SCRIPT_DIR / "generate_statistics.py"),
        "--matches-dir", args.matches_dir, "--teams-file", args.teams_file, "--output", args.statistics_output,
    ])

    check_matchweek_now_complete(args.fixtures_file, match_id)

    print(f"\nAll done. Match {match_id} is fully processed:")
    print("  - Fantasy points calculated")
    print("  - Fixture marked completed")
    print("  - Standings and Statistics refreshed")
    print("\nNext: test locally, then git add / commit / push.")


if __name__ == "__main__":
    main()
