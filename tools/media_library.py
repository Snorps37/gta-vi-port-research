"""Build a searchable offline library from local video and audio inventories."""
import argparse
import csv
import math
from html import escape
from pathlib import Path


def entries(index, root, kind, delimiter):
    root = root.resolve()
    with index.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source, delimiter=delimiter)
        required = {"file", "duration_seconds"} | (
            {"archive", "width", "height"} if kind == "Video" else {"channels", "rate"}
        )
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"{index}: missing required columns")
        for row in reader:
            if not all(row[key] and row[key].strip() for key in required):
                raise ValueError(f"{index}, line {reader.line_num}: missing required value")
            media = (root / row["file"]).resolve()
            if not media.is_relative_to(root) or not media.is_file():
                raise ValueError(f"missing or out-of-root media: {row['file']}")
            if kind == "Video":
                title = media.stem
                detail = f"{row['archive']} · {row['width']} × {row['height']}"
            else:
                title = row.get("name") or media.stem
                detail = f"{row['channels']} channels · {row['rate']} Hz"
            try:
                seconds = float(row["duration_seconds"])
                if not math.isfinite(seconds) or seconds < 0:
                    raise ValueError
            except ValueError as exc:
                raise ValueError(f"{index}, line {reader.line_num}: invalid duration") from exc
            duration = round(seconds)
            yield kind, title, detail, f"{duration // 60}:{duration % 60:02}", media.as_uri()


def build(args):
    records = []
    for pair, kind, delimiter in ((args.videos, "Video", ","), (args.music, "Music", "\t"),
                                  (args.candidates, "Unidentified audio", "\t")):
        if pair:
            records.extend(entries(*pair, kind, delimiter))
    body = []
    for kind, title, detail, duration, uri in records:
        body.append(f'<tr data-kind="{kind}"><td>{kind}</td><td><a href="{escape(uri)}">'
                    f'{escape(title)}</a></td><td>{escape(detail)}</td><td>{duration}</td></tr>')
    html = TEMPLATE.replace("<!--ROWS-->", "\n".join(body)).replace("<!--TOTAL-->", str(len(records)))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    return len(records)


TEMPLATE = """<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Local media library</title><style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#10171c;color:#e8eeed;font:16px system-ui}
main{max-width:1060px;margin:auto;padding:32px 5vw}h1{font-size:clamp(32px,5vw,52px);margin:0 0 16px}
input,select{background:#1d292e;color:inherit;border:1px solid #51646a;border-radius:4px;padding:9px;margin:0 8px 8px 0}
label{display:inline-grid;gap:4px}a{color:#8de5ce}th,td{text-align:left;padding:8px;border-bottom:1px solid #344247}
table{width:100%;border-collapse:collapse}section{overflow:auto}video,audio{max-width:100%;width:640px;max-height:40vh}
#play{margin:12px 0 20px}#count{color:#adbec3}tbody tr:hover{background:#1b272d}</style>
<main><h1>Local media library</h1><label>Search<input type="search" id="q" placeholder="Title, archive or resolution"></label>
<label>Media type<select id="kind"><option>All</option><option>Video</option><option>Music</option>
<option>Unidentified audio</option></select></label><span id="count" aria-live="polite"><!--TOTAL--> items</span>
<div id="play"></div><section><table><thead><tr><th>Type</th><th>Title</th><th>Source or format</th><th>Length</th>
</tr></thead><tbody><!--ROWS--></tbody></table></section></main><script>
const q=document.querySelector('#q'), kind=document.querySelector('#kind'), rows=[...document.querySelectorAll('tbody tr')];
const text=rows.map(r=>r.textContent.toLowerCase());
function filter(){let n=0;const query=q.value.trim().toLowerCase();rows.forEach((r,i)=>{
  r.hidden=!(text[i].includes(query)&&(kind.value==='All'||kind.value===r.dataset.kind));if(!r.hidden)n++;
});document.querySelector('#count').textContent=n+' items';}
q.oninput=kind.onchange=filter;
const initialKind={videos:'Video',music:'Music',candidates:'Unidentified audio'}[location.hash.slice(1)];
if(initialKind){kind.value=initialKind;filter();}
document.querySelector('tbody').onclick=e=>{const link=e.target.closest('a');if(!link||e.ctrlKey||e.metaKey||e.shiftKey)return;
  e.preventDefault();const pane=document.querySelector('#play'),player=document.createElement(link.closest('tr').dataset.kind==='Video'?'video':'audio');
  const fallback=document.createElement('a');fallback.href=link.href;fallback.textContent='Open local file';
  const heading=document.createElement('h2');heading.textContent=link.textContent;
  player.controls=true;player.src=link.href;pane.replaceChildren(heading,player,document.createElement('br'),fallback);
  player.play().catch(()=>{});pane.scrollIntoView({block:'nearest'});};</script></html>"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    for flag in ("videos","music","candidates"):
        parser.add_argument("--"+flag, type=Path, nargs=2, metavar=("INVENTORY","FILE_ROOT"))
    args = parser.parse_args()
    if not any((args.videos,args.music,args.candidates)):
        parser.error("supply at least one inventory and its media root")
    try:
        print(f"Wrote {build(args)} media entries")
    except (OSError, ValueError, KeyError) as exc:
        parser.exit(1, f"Library build failed: {exc}\n")
