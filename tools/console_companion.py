"""Build a private offline console companion from the people and interior catalogs."""
import argparse
import csv
import json
from pathlib import Path


def build(people, interiors, output):
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
    if output.resolve() in {p.resolve() for p in (template, people, interiors)}:
        raise ValueError("Choose a separate output file")
    data = json.dumps(dict(missions=missions, places=places, schedules=schedules), allow_nan=False)
    page = template.read_text(encoding="utf-8").replace('"CATALOG_PLACEHOLDER"', data.replace("<", r"\u003c"))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(page, encoding="utf-8")
    print(f"{len(missions)} replay entries, {len(places)} placements, {len(schedules)} schedules")


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    for arg in ("people", "interiors", "output"):
        cli.add_argument(arg, type=Path)
    args = cli.parse_args()
    build(args.people, args.interiors, args.output)
