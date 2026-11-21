"""Build a private offline console companion from the people and interior catalogs."""
import argparse
import csv
import json
from pathlib import Path


def build(people, interiors, output, activities=None):
    groups = json.loads(people.read_text(encoding="utf-8"))["groups"]
    missions = [
        [r["name"], r["summary"], r["fields"].get("Observed UI evaluator type", "")]
        for r in groups["missions"]
    ]
    schedules = [[r["name"], r["summary"]] for r in groups["schedules"] if r["kind"] == "Schedule"]
    with interiors.open(encoding="utf-8-sig", newline="") as source:
        places = [
            [r["stored_offset"] + "/" + r["decoded_offset"], r["label"] or r["archetype"],
             *[float(r[axis]) for axis in "xyz"]]
            for r in csv.DictReader(source)
        ]
    for rows in (missions, places):
        if len(rows) != len({row[0] for row in rows}):
            raise ValueError("Catalog identifiers must be unique")
    template = Path(__file__).with_suffix(".html")
    inputs = [template, people, interiors]
    activity_rows = []
    if activities is not None:
        inputs.append(activities)
        source = json.loads(activities.read_text(encoding="utf-8-sig"))
        if not isinstance(source, list):
            raise ValueError("Expected an array of activity records")
        for record in source:
            if not isinstance(record, dict) or not all(
                isinstance(record.get(k), str) and record[k].strip()
                for k in ("name", "classification", "evidence")
            ):
                raise ValueError("Each activity needs a name, classification and evidence")
            activity_rows.append({k: record[k] for k in ("name", "classification", "evidence")})
        if len({r["name"] for r in activity_rows}) != len(activity_rows):
            raise ValueError("Activity names must be unique")
    if output.resolve() in {p.resolve() for p in inputs}:
        raise ValueError("Choose a separate output file")
    data = json.dumps(dict(missions=missions, places=places, schedules=schedules,
                           activities=activity_rows), allow_nan=False)
    page = template.read_text(encoding="utf-8").replace('"CATALOG_PLACEHOLDER"', data.replace("<", r"\u003c"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    print(f"{len(missions)} replay entries, {len(places)} placements, {len(schedules)} schedules, "
          f"{len(activity_rows)} activities")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    for arg in ("people", "interiors", "output"):
        cli.add_argument(arg, type=Path)
    cli.add_argument("--activities", type=Path, help="Optional private activity evidence JSON")
    args = cli.parse_args()
    build(args.people, args.interiors, args.output, args.activities)
