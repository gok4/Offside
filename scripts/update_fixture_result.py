#!/usr/bin/env python3
"""
update_fixture_result.py

After calculate_match_points.py produces a completed match JSON file,
this script updates the matching entry in fixtures.json with the final
score and marks it "completed" -- so the Fixtures page shows the real
result and links into the Match Center, instead of still showing "vs".

Usage:
    python3 update_fixture_result.py \
        --match-file data/matches/gfl-2026-001.json \
        --fixtures-file data/fixtures.json
"""

import argparse
import json
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--match-file", required=True)
    parser.add_argument("--fixtures-file", required=True)
    args = parser.parse_args()

    match_path = Path(args.match_file)
    fixtures_path = Path(args.fixtures_file)

    if not match_path.is_file():
        print(f"ERROR: match file not found at '{match_path}'", file=sys.stderr)
        sys.exit(1)
    if not fixtures_path.is_file():
        print(f"ERROR: fixtures file not found at '{fixtures_path}'", file=sys.stderr)
        sys.exit(1)

    match = json.loads(match_path.read_text(encoding="utf-8"))
    fixtures_data = json.loads(fixtures_path.read_text(encoding="utf-8"))

    match_id = match.get("matchId")
    home_score = match.get("homeTeam", {}).get("score")
    away_score = match.get("awayTeam", {}).get("score")

    found = False
    for fixture in fixtures_data.get("fixtures", []):
        if fixture.get("matchId") == match_id:
            fixture["status"] = "completed"
            fixture["homeScore"] = home_score
            fixture["awayScore"] = away_score
            found = True
            break

    if not found:
        print(f"ERROR: no fixture with matchId '{match_id}' found in {fixtures_path}", file=sys.stderr)
        sys.exit(1)

    fixtures_path.write_text(json.dumps(fixtures_data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Fixture {match_id} marked completed: {home_score}-{away_score}")
    print(f"Updated: {fixtures_path}")


if __name__ == "__main__":
    main()
