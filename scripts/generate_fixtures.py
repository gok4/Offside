#!/usr/bin/env python3
"""
generate_fixtures.py

Generates a full double round-robin season schedule (each team plays every
other team twice — once home, once away) using the standard "circle method"
round-robin scheduling algorithm.

For 24 teams: 46 matchweeks, 12 matches per matchweek, 552 matches total.

Usage:
    python3 generate_fixtures.py teams.json fixtures.json --start-date 2026-08-30
"""

import sys
import json
import argparse
from datetime import date, timedelta
from pathlib import Path


def round_robin_single_leg(team_names):
    """Circle method: returns a list of rounds, each a list of (home, away) pairs.
    For N teams (must be even), produces N-1 rounds of N/2 matches each,
    with every team playing every other team exactly once."""
    n = len(team_names)
    if n % 2 != 0:
        raise ValueError("Circle method requires an even number of teams.")

    arr = list(range(n))
    rounds = []

    for r in range(n - 1):
        round_matches = []
        half = n // 2
        for i in range(half):
            t1, t2 = arr[i], arr[n - 1 - i]
            # Alternate home/away by round parity to balance venues over the season
            if r % 2 == 0:
                home, away = t1, t2
            else:
                home, away = t2, t1
            round_matches.append((team_names[home], team_names[away]))
        rounds.append(round_matches)
        # Rotate: keep index 0 fixed, move last element to position 1
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]

    return rounds


def build_double_round_robin(team_names, start_date, days_between_matchweeks=7):
    first_leg = round_robin_single_leg(team_names)
    # Second leg: same pairings, home/away swapped
    second_leg = [[(away, home) for (home, away) in rnd] for rnd in first_leg]
    all_rounds = first_leg + second_leg

    fixtures = []
    match_num = 1
    current_date = start_date

    for matchweek, round_matches in enumerate(all_rounds, start=1):
        for home, away in round_matches:
            fixtures.append({
                "matchId": f"gfl-2026-{match_num:03d}",
                "matchweek": matchweek,
                "homeTeam": home,
                "awayTeam": away,
                "date": current_date.isoformat(),
                "status": "scheduled",
                "homeScore": None,
                "awayScore": None,
            })
            match_num += 1
        current_date += timedelta(days=days_between_matchweeks)

    return fixtures


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("teams_file")
    parser.add_argument("output_file")
    parser.add_argument("--start-date", default=date.today().isoformat(),
                         help="ISO date (YYYY-MM-DD) for matchweek 1. Defaults to today.")
    args = parser.parse_args()

    teams_data = json.loads(Path(args.teams_file).read_text(encoding="utf-8"))
    teams = teams_data.get("teams", teams_data)
    team_names = [t["name"] for t in teams]

    if len(team_names) % 2 != 0:
        print(f"ERROR: {len(team_names)} teams found — must be an even number for round-robin scheduling.")
        sys.exit(1)

    start = date.fromisoformat(args.start_date)
    fixtures = build_double_round_robin(team_names, start)

    matchweeks = len(team_names) * 2 - 2
    output = {
        "season": "2026",
        "format": "double round-robin",
        "matchweeks": matchweeks,
        "fixtures": fixtures,
    }

    Path(args.output_file).write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Generated {len(fixtures)} fixtures across {matchweeks} matchweeks for {len(team_names)} teams.")
    print(f"Season runs {fixtures[0]['date']} to {fixtures[-1]['date']}.")
    print(f"Written: {args.output_file}")

    # Sanity check: confirm every team plays every other team exactly twice (once home, once away)
    from collections import Counter
    pair_counts = Counter()
    for f in fixtures:
        pair_counts[(f["homeTeam"], f["awayTeam"])] += 1
    issues = [k for k, v in pair_counts.items() if v != 1]
    if issues:
        print(f"WARNING: {len(issues)} fixture pairing(s) don't appear exactly once — check the schedule.")
    else:
        print("Validation OK: every home/away pairing appears exactly once.")


if __name__ == "__main__":
    main()
