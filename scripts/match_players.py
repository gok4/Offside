#!/usr/bin/env python3
"""
match_players.py

Matches player_cards image filenames (e.g. "Kobel.png") back to the full
player names listed in the team sheet (e.g. "Gregor Kobel"), per team.

Why this exists: image filenames only use a short form of the name
(usually the surname), so we can't just do a plain string match. This
script uses "trailing token" matching -- e.g. "Wan-Bissaka" matches
"Aaron Wan-Bissaka" because the filename's tokens are the trailing
tokens of the full name.

Usage:
    python3 match_players.py teams.json player_cards/

Exits non-zero if any team has an unmatched, ambiguous, or missing image,
so this is safe to run as a CI validation step.
"""

import sys
import json
import unicodedata
from pathlib import Path

# Characters that don't cleanly decompose via NFKD (Turkish letters, etc.)
MANUAL_MAP = {
    "ı": "i", "İ": "i", "ğ": "g", "Ğ": "g", "ş": "s", "Ş": "s",
    "ß": "ss", "ø": "o", "Ø": "o", "æ": "ae", "Æ": "ae",
}


def normalize_token(token: str) -> str:
    """Lowercase + strip accents, keep hyphens, drop other punctuation."""
    for src, dst in MANUAL_MAP.items():
        token = token.replace(src, dst)
    token = unicodedata.normalize("NFKD", token)
    token = "".join(c for c in token if not unicodedata.combining(c))
    token = token.lower().strip()
    # keep letters, digits, hyphens only
    token = "".join(c for c in token if c.isalnum() or c == "-")
    return token


def tokenize(name: str) -> list[str]:
    return [normalize_token(t) for t in name.split()]


def find_match(filename_tokens, candidates):
    """Return list of candidate full names whose trailing tokens equal filename_tokens."""
    matches = []
    for full_name in candidates:
        full_tokens = tokenize(full_name)
        n = len(filename_tokens)
        if len(full_tokens) >= n and full_tokens[-n:] == filename_tokens:
            matches.append(full_name)
    return matches


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 match_players.py teams.json player_cards/")
        sys.exit(2)

    teams_path = Path(sys.argv[1])
    cards_dir = Path(sys.argv[2])

    teams_data = json.loads(teams_path.read_text(encoding="utf-8"))

    # Support both formats:
    #   {"teams": [{"name": "...", "players": [...]}, ...]}   <- actual teams.json
    #   {"Team Name": {"players": [...]}, ...}                 <- older flat format
    if isinstance(teams_data, dict) and "teams" in teams_data:
        teams = {t["name"]: t for t in teams_data["teams"]}
    else:
        teams = teams_data

    total_issues = 0
    report = {}

    for team_name, team_data in teams.items():
        team_dir = cards_dir / team_name
        sheet_names = [p["name"] for p in team_data["players"]]

        team_report = {
            "matched": {},
            "unmatched_images": [],
            "ambiguous_images": {},
            "missing_images": [],
        }

        if not team_dir.is_dir():
            team_report["missing_images"] = sheet_names
            total_issues += len(sheet_names)
            report[team_name] = team_report
            continue

        image_files = sorted(
            [p for p in team_dir.iterdir() if p.suffix.lower() in (".png", ".webp")]
        )
        matched_sheet_names = set()

        for img in image_files:
            stem = img.stem
            filename_tokens = tokenize(stem)
            matches = find_match(filename_tokens, sheet_names)

            if len(matches) == 1:
                team_report["matched"][img.name] = matches[0]
                matched_sheet_names.add(matches[0])
            elif len(matches) == 0:
                team_report["unmatched_images"].append(img.name)
                total_issues += 1
            else:
                team_report["ambiguous_images"][img.name] = matches
                total_issues += 1

        # Any sheet player with no matched image at all
        for name in sheet_names:
            if name not in matched_sheet_names:
                team_report["missing_images"].append(name)
                total_issues += 1

        report[team_name] = team_report

    # --- Print human-readable summary ---
    for team_name, r in report.items():
        problems = r["unmatched_images"] or r["ambiguous_images"] or r["missing_images"]
        status = "OK" if not problems else "ISSUES"
        print(f"[{status}] {team_name}: {len(r['matched'])}/25 matched")
        if r["unmatched_images"]:
            print(f"   Unmatched image files (no sheet name found): {r['unmatched_images']}")
        if r["ambiguous_images"]:
            print(f"   Ambiguous image files (matched >1 player): {r['ambiguous_images']}")
        if r["missing_images"]:
            print(f"   Sheet players with no image: {r['missing_images']}")

    print(f"\nTotal issues: {total_issues}")

    # Save full machine-readable report
    Path("match_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Full report written to match_report.json")

    # Build a site-ready teams.full.json with real image/logo filenames baked in
    # (only meaningful once every team is fully matched, but we build it regardless
    # so partial progress can still be previewed)
    enriched_teams = []
    for team_name, team_data in teams.items():
        r = report[team_name]
        name_to_image = {v: k for k, v in r["matched"].items()}
        players = []
        for p in team_data["players"]:
            players.append({
                "name": p["name"],
                "position": p["position"],
                "image": name_to_image.get(p["name"]),  # None if unmatched/missing
            })
        enriched_teams.append({
            "name": team_name,
            "manager": team_data.get("manager"),
            "logo": f"{team_name}.png",
            "players": players,
        })

    Path("teams.full.json").write_text(
        json.dumps({"teams": enriched_teams}, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print("Site-ready data written to teams.full.json")

    sys.exit(1 if total_issues > 0 else 0)


if __name__ == "__main__":
    main()
