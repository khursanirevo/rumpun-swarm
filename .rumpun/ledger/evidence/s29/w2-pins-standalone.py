"""Spec-first pins for the discoveries link mapping (s29 w2).

Sources: akar codex-review-2026-09-14 (L1) plus s28-harvest (L1 confirmed
open). Contract under test: every discovery record renders a page its list
link resolves to (the href path exists after render and carries the record
body), ids sharing one sanitized slug render two distinct pages, and an all
lowercase-hyphen ledger (the current ledger) renders byte-identical list
plus pages to the pre-s29 render.

Standalone pins file: tests/test_rumpun.py stays byte-identical
(additions-only constraint). To integrate by appending into
tests/test_rumpun.py instead, drop this import block; the suite already
imports re, Path, and report. GOLDEN_DISCOVERIES is generated from the
pre-s29 code by scratch/capture_golden.py between the sentinels; capture
provenance (git rev, report.py sha256, determinism double-render) lives in
scratch/evidence/golden/capture.log.

Red/green map against pre-s29 code: pins 1-3 red (the list links the raw
id while pages land on the sanitized slug), pin 4 red (a-b and a.b both
write a-b.html and the second overwrites the first), pin 5 green on both
sides (it fails only if the fix drifts current-ledger bytes).
"""

import re
from pathlib import Path

from rumpun import report

# Clock-free fixed ledger fixture: akar files are written directly because
# akar.append_record stamps date.today(), and a clock read would poison
# pin 5's byte compare. Ids echo the real ledger's lowercase-hyphen shape.
AB_RECORDS: tuple[tuple[str, str, str], ...] = (
    ("audit-1", "reflection audit", "5 dead phases found"),
    ("glm-toolless-spawn", "tool-less spawns", "7 of 24 boot without tools"),
)


def _discovery_root(base: Path, records=AB_RECORDS) -> Path:
    """One .rumpun root whose akar holds fixed-date records; returns root."""
    root = base / "proj" / ".rumpun"
    (root / "akar").mkdir(parents=True)
    for rid, title, body in records:
        (root / "akar" / f"{rid}.md").write_text(
            f"id: {rid}\ntitle: {title}\ndate: 2026-09-15\n\n{body}\n",
            encoding="utf-8",
        )
    return root


def _list_links(out: Path) -> dict[str, str]:
    """The rendered list page's title -> href map."""
    found = re.findall(
        r'<a href="([^"]+)">([^<]+)</a>', out.read_text(encoding="utf-8")
    )
    return {title: href for href, title in found}


def _resolve(out: Path, title: str) -> Path:
    """Resolve the list's link for `title` to a path next to the list page.

    Asserts the entry exists; whether the target file exists stays with the
    caller so a pin failure names the missing page, not the parser.
    """
    links = _list_links(out)
    assert title in links, f"discoveries list lacks an entry for {title!r}: {links}"
    return out.parent / links[title]


def test_discovery_uppercase_id_link_resolves(tmp_path):
    """L1 pin 1: record "Audit-1" renders a page its list link resolves to.

    Red today: the list links the raw id (Audit-1.html) while the page is
    written to the sanitized slug audit-1.html; on a case-sensitive
    filesystem the link resolves to nothing.
    """
    root = _discovery_root(
        tmp_path, (("Audit-1", "uppercase id", "uppercase body line"),)
    )
    out = report.render_discoveries(root)
    page = _resolve(out, "uppercase id")
    assert page.is_file(), f"link href {page.name!r} resolves to no page file"
    assert "uppercase body line" in page.read_text(encoding="utf-8")


def test_discovery_underscore_id_link_resolves(tmp_path):
    """L1 pin 2: record "my_id" renders a page its list link resolves to.

    Red today: the list links my_id.html while the page is written to the
    sanitized slug my-id.html; the link resolves to nothing.
    """
    root = _discovery_root(tmp_path, (("my_id", "underscore id", "underscore body line"),))
    out = report.render_discoveries(root)
    page = _resolve(out, "underscore id")
    assert page.is_file(), f"link href {page.name!r} resolves to no page file"
    assert "underscore body line" in page.read_text(encoding="utf-8")


def test_discovery_dot_id_link_resolves(tmp_path):
    """L1 pin 3: record "a.b" renders a page its list link resolves to.

    Red today: the list links a.b.html while the page is written to the
    sanitized slug a-b.html; the link resolves to nothing.
    """
    root = _discovery_root(tmp_path, (("a.b", "dot id", "dot body line"),))
    out = report.render_discoveries(root)
    page = _resolve(out, "dot id")
    assert page.is_file(), f"link href {page.name!r} resolves to no page file"
    assert "dot body line" in page.read_text(encoding="utf-8")


def test_discovery_slug_collision_two_distinct_pages(tmp_path):
    """L1 pin 4: "a-b" and "a.b" render two distinct pages, no overwrite.

    Red today: both ids sanitize to the same slug, so one page file is
    written twice (the second render overwrites the first) and the list
    then links a.b.html, which was never written at all.
    """
    root = _discovery_root(
        tmp_path,
        (
            ("a-b", "collision hyphen", "hyphen body line"),
            ("a.b", "collision dot", "dot body line"),
        ),
    )
    out = report.render_discoveries(root)
    hyphen = _resolve(out, "collision hyphen")
    dot = _resolve(out, "collision dot")
    assert hyphen != dot, f"both links resolve to one page file: {hyphen.name}"
    assert hyphen.is_file(), f"link href {hyphen.name!r} resolves to no page file"
    assert dot.is_file(), f"link href {dot.name!r} resolves to no page file"
    hyphen_text = hyphen.read_text(encoding="utf-8")
    dot_text = dot.read_text(encoding="utf-8")
    assert "hyphen body line" in hyphen_text
    assert "dot body line" in dot_text
    assert "dot body line" not in hyphen_text, "dot page overwrote the hyphen page"
    assert "hyphen body line" not in dot_text, "hyphen page overwrote the dot page"


def test_discoveries_bytes_unchanged_from_pre_s29(tmp_path):
    """L1 pin 5 (A/B regression): the current ledger's id shape (all
    lowercase-hyphen) renders byte-identical list and pages to the
    pre-s29 render.

    Green before and after the fix; red the moment any byte drifts for
    the current ledger's shape. Golden bytes were captured from the
    pre-s29 code by scratch/capture_golden.py; capture provenance (git
    rev, report.py sha256, determinism double-render) lives in
    scratch/evidence/golden/capture.log.
    """
    root = _discovery_root(tmp_path)
    out = report.render_discoveries(root)
    written = sorted(p.name for p in out.parent.glob("*.html"))
    assert written == sorted(GOLDEN_DISCOVERIES), f"page set drifted: {written}"
    for name, golden in GOLDEN_DISCOVERIES.items():
        assert (out.parent / name).read_bytes() == golden, f"bytes drifted: {name}"


# --- BEGIN GOLDEN_DISCOVERIES (generated; do not hand-edit) ---
GOLDEN_DISCOVERIES: dict[str, bytes] = {
    "audit-1.html": (
        b'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8'
        b'">\n<meta name="viewport" content="width=device-width, initia'
        b'l-scale=1">\n<title>rumpun discovery audit-1</title>\n<style>b'
        b'ody{background:#020617;color:#F8FAFC;font-family:Inter,ui-sa'
        b'ns-serif,system-ui,sans-serif;margin:0;padding:1.5rem;max-wi'
        b'dth:64rem;margin-inline:auto}\na{color:#38BDF8;text-decoratio'
        b'n:none}a:focus-visible{outline:2px solid #F8FAFC}\nh1{font-si'
        b'ze:1.25rem;margin:0 0 .25rem}h2{font-size:.95rem;color:#94A3'
        b'B8;margin:1.5rem 0 .5rem;text-transform:uppercase;letter-spa'
        b'cing:.08em}}\n.card{background:#0E1223;border:1px solid #3341'
        b'55;border-radius:8px;padding:1rem;margin-top:.75rem}\ntable{b'
        b'order-collapse:collapse;width:100%;margin-top:.5rem}\nth,td{b'
        b'order:1px solid #334155;padding:.35rem .6rem;text-align:left'
        b';font-family:ui-monospace,monospace;font-size:.85rem}\nth{bac'
        b'kground:#020617;color:#94A3B8;font-weight:600}\n.prov{font-si'
        b'ze:.75em;color:#94A3B8;font-weight:normal}\n.policy,.legend-n'
        b'ote{color:#94A3B8;font-size:.85rem}\n.legend ul{margin:.3rem '
        b'0;padding-left:1.2rem}\n.footer{color:#94A3B8;font-size:.8rem'
        b';margin-top:2rem}\n.strip{display:flex;flex-wrap:wrap;gap:.5r'
        b'em}\n.strip a{display:block;min-width:6.2rem}\n.cell{border:1p'
        b'x solid #334155;border-radius:8px;padding:.5rem .6rem;backgr'
        b'ound:#0E1223}\n.cell .sid{font-family:ui-monospace,monospace;'
        b'font-weight:600}\n.cell .ver{font-size:.75rem}\n.change dt{mar'
        b'gin-top:.5rem}\n.change dd{margin:0 0 .25rem;font-family:ui-m'
        b'onospace,monospace;font-size:.85rem}\n.bar{fill:#38BDF8}.barl'
        b'oss{fill:#EF4444}.barwin{fill:#22C55E}\n.stat{display:flex;ga'
        b'p:1rem;flex-wrap:wrap;margin-top:.5rem}\n.stat .card{margin:0'
        b';flex:1;min-width:9rem}\n.stat .num{font-size:1.6rem;font-fam'
        b'ily:ui-monospace,monospace}\n.stat .lbl{color:#94A3B8;font-si'
        b'ze:.8rem}\n.one{font-size:.95rem;margin:.4rem 0 0}\n.plain{fon'
        b't-size:1rem;margin:.25rem 0}\n.idle{color:#94A3B8}</style>\n</'
        b'head>\n<body>\n<h1>reflection audit</h1>\n<p class="plain"><spa'
        b'n class="prov">audit-1 &middot; 2026-09-15 [A]</span> &middo'
        b't; <a href="index.html">all discoveries</a></p>\n<pre>id: aud'
        b'it-1\ntitle: reflection audit\ndate: 2026-09-15\n\n5 dead phases'
        b' found\n</pre>\n<p class="policy">State policy [D]: exit file '
        b'0 -&gt; exited; non-zero -&gt; failed; no exit file + live p'
        b'id -&gt; running (stalled after stall_minutes); no exit file'
        b' + dead pid -&gt; crashed; engine kill -&gt; terminated.</p>'
        b'\n</body>\n</html>\n'
    ),
    "glm-toolless-spawn.html": (
        b'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8'
        b'">\n<meta name="viewport" content="width=device-width, initia'
        b'l-scale=1">\n<title>rumpun discovery glm-toolless-spawn</titl'
        b'e>\n<style>body{background:#020617;color:#F8FAFC;font-family:'
        b'Inter,ui-sans-serif,system-ui,sans-serif;margin:0;padding:1.'
        b'5rem;max-width:64rem;margin-inline:auto}\na{color:#38BDF8;tex'
        b't-decoration:none}a:focus-visible{outline:2px solid #F8FAFC}'
        b'\nh1{font-size:1.25rem;margin:0 0 .25rem}h2{font-size:.95rem;'
        b'color:#94A3B8;margin:1.5rem 0 .5rem;text-transform:uppercase'
        b';letter-spacing:.08em}}\n.card{background:#0E1223;border:1px '
        b'solid #334155;border-radius:8px;padding:1rem;margin-top:.75r'
        b'em}\ntable{border-collapse:collapse;width:100%;margin-top:.5r'
        b'em}\nth,td{border:1px solid #334155;padding:.35rem .6rem;text'
        b'-align:left;font-family:ui-monospace,monospace;font-size:.85'
        b'rem}\nth{background:#020617;color:#94A3B8;font-weight:600}\n.p'
        b'rov{font-size:.75em;color:#94A3B8;font-weight:normal}\n.polic'
        b'y,.legend-note{color:#94A3B8;font-size:.85rem}\n.legend ul{ma'
        b'rgin:.3rem 0;padding-left:1.2rem}\n.footer{color:#94A3B8;font'
        b'-size:.8rem;margin-top:2rem}\n.strip{display:flex;flex-wrap:w'
        b'rap;gap:.5rem}\n.strip a{display:block;min-width:6.2rem}\n.cel'
        b'l{border:1px solid #334155;border-radius:8px;padding:.5rem .'
        b'6rem;background:#0E1223}\n.cell .sid{font-family:ui-monospace'
        b',monospace;font-weight:600}\n.cell .ver{font-size:.75rem}\n.ch'
        b'ange dt{margin-top:.5rem}\n.change dd{margin:0 0 .25rem;font-'
        b'family:ui-monospace,monospace;font-size:.85rem}\n.bar{fill:#3'
        b'8BDF8}.barloss{fill:#EF4444}.barwin{fill:#22C55E}\n.stat{disp'
        b'lay:flex;gap:1rem;flex-wrap:wrap;margin-top:.5rem}\n.stat .ca'
        b'rd{margin:0;flex:1;min-width:9rem}\n.stat .num{font-size:1.6r'
        b'em;font-family:ui-monospace,monospace}\n.stat .lbl{color:#94A'
        b'3B8;font-size:.8rem}\n.one{font-size:.95rem;margin:.4rem 0 0}'
        b'\n.plain{font-size:1rem;margin:.25rem 0}\n.idle{color:#94A3B8}'
        b'</style>\n</head>\n<body>\n<h1>tool-less spawns</h1>\n<p class="'
        b'plain"><span class="prov">glm-toolless-spawn &middot; 2026-0'
        b'9-15 [A]</span> &middot; <a href="index.html">all discoverie'
        b's</a></p>\n<pre>id: glm-toolless-spawn\ntitle: tool-less spawn'
        b's\ndate: 2026-09-15\n\n7 of 24 boot without tools\n</pre>\n<p cla'
        b'ss="policy">State policy [D]: exit file 0 -&gt; exited; non-'
        b'zero -&gt; failed; no exit file + live pid -&gt; running (st'
        b'alled after stall_minutes); no exit file + dead pid -&gt; cr'
        b'ashed; engine kill -&gt; terminated.</p>\n</body>\n</html>\n'
    ),
    "index.html": (
        b'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8'
        b'">\n<meta name="viewport" content="width=device-width, initia'
        b'l-scale=1">\n<title>rumpun discoveries</title>\n<style>body{ba'
        b'ckground:#020617;color:#F8FAFC;font-family:Inter,ui-sans-ser'
        b'if,system-ui,sans-serif;margin:0;padding:1.5rem;max-width:64'
        b'rem;margin-inline:auto}\na{color:#38BDF8;text-decoration:none'
        b'}a:focus-visible{outline:2px solid #F8FAFC}\nh1{font-size:1.2'
        b'5rem;margin:0 0 .25rem}h2{font-size:.95rem;color:#94A3B8;mar'
        b'gin:1.5rem 0 .5rem;text-transform:uppercase;letter-spacing:.'
        b'08em}}\n.card{background:#0E1223;border:1px solid #334155;bor'
        b'der-radius:8px;padding:1rem;margin-top:.75rem}\ntable{border-'
        b'collapse:collapse;width:100%;margin-top:.5rem}\nth,td{border:'
        b'1px solid #334155;padding:.35rem .6rem;text-align:left;font-'
        b'family:ui-monospace,monospace;font-size:.85rem}\nth{backgroun'
        b'd:#020617;color:#94A3B8;font-weight:600}\n.prov{font-size:.75'
        b'em;color:#94A3B8;font-weight:normal}\n.policy,.legend-note{co'
        b'lor:#94A3B8;font-size:.85rem}\n.legend ul{margin:.3rem 0;padd'
        b'ing-left:1.2rem}\n.footer{color:#94A3B8;font-size:.8rem;margi'
        b'n-top:2rem}\n.strip{display:flex;flex-wrap:wrap;gap:.5rem}\n.s'
        b'trip a{display:block;min-width:6.2rem}\n.cell{border:1px soli'
        b'd #334155;border-radius:8px;padding:.5rem .6rem;background:#'
        b'0E1223}\n.cell .sid{font-family:ui-monospace,monospace;font-w'
        b'eight:600}\n.cell .ver{font-size:.75rem}\n.change dt{margin-to'
        b'p:.5rem}\n.change dd{margin:0 0 .25rem;font-family:ui-monospa'
        b'ce,monospace;font-size:.85rem}\n.bar{fill:#38BDF8}.barloss{fi'
        b'll:#EF4444}.barwin{fill:#22C55E}\n.stat{display:flex;gap:1rem'
        b';flex-wrap:wrap;margin-top:.5rem}\n.stat .card{margin:0;flex:'
        b'1;min-width:9rem}\n.stat .num{font-size:1.6rem;font-family:ui'
        b'-monospace,monospace}\n.stat .lbl{color:#94A3B8;font-size:.8r'
        b'em}\n.one{font-size:.95rem;margin:.4rem 0 0}\n.plain{font-size'
        b':1rem;margin:.25rem 0}\n.idle{color:#94A3B8}</style>\n</head>\n'
        b'<body>\n<h1>Discoveries</h1>\n<p class="plain">What the campai'
        b'gn learned about itself and its tools <span class="prov">[A]'
        b'</span> &middot; <a href="../index.html">all progress</a></p'
        b'>\n<ul><li><a href="glm-toolless-spawn.html">tool-less spawns'
        b'</a> <span class="prov">glm-toolless-spawn &middot; 2026-09-'
        b'15</span></li><li><a href="audit-1.html">reflection audit</a'
        b'> <span class="prov">audit-1 &middot; 2026-09-15</span></li>'
        b'</ul>\n<p class="policy">State policy [D]: exit file 0 -&gt; '
        b'exited; non-zero -&gt; failed; no exit file + live pid -&gt;'
        b' running (stalled after stall_minutes); no exit file + dead '
        b'pid -&gt; crashed; engine kill -&gt; terminated.</p>\n</body>'
        b'\n</html>\n'
    ),
}
# --- END GOLDEN_DISCOVERIES ---
