# s29 w2 notes — spec-first pins for the discovery-link mapping

## Verdict

Pins 1-4 red against pre-s29 code for the spec reasons. Pin 5 green.
133/133 suite green. Ruff clean. src/ and tests/ untouched by w2.

## Measured red set (pre-s29 code, report.py sha256 a7788656...)

| pin | spec | measured failure | verdict |
|---|---|---|---|
| 1 | id "Audit-1" | list href `Audit-1.html`; page file `audit-1.html`; `is_file()` false (pins line 81) | ✅ RED, in-spec |
| 2 | id "my_id" | href `my_id.html` missing; page at `my-id.html` (line 91) | ✅ RED, in-spec |
| 3 | id "a.b" | href `a.b.html` missing; page at `a-b.html` (line 107) | ✅ RED, in-spec |
| 4 | "a-b" vs "a.b" | hrefs differ, `a-b.html` exists but carries the dot record's body; `a.b.html` never written (line 130) | ✅ RED, in-spec |
| 5 | A/B vs pre-s29 bytes | passes (goldens byte-equal) | ✅ GREEN |

Full tracebacks: `scratch/evidence/red-run.txt` (measured 2026-09-15, pytest exit 1, "4 failed, 1 passed").

## Green gates

- Suite: 133 passed in 43.50s (`scratch/evidence/suite-run.txt`).
- Ruff (line-length 100, --no-respect-gitignore): exit 0 (`scratch/evidence/ruff-run.txt`).

## Deliverables (all under w2/ workspace)

- `scratch/test_s29_w2_pins.py` — the 5 pins. Standalone file; tests/test_rumpun.py
  stays byte-identical. Alternative integration: append into test_rumpun.py and
  drop the import block (suite already imports re, Path, report).
- `scratch/capture_golden.py` — golden capture + stamp, with compile and
  byte-equality readback gate.
- `scratch/evidence/golden/` — captured pre-s29 bytes + capture.log.
- `scratch/evidence/red-run.txt`, `suite-run.txt`, `ruff-run.txt`.

## Pin 5 provenance

- git HEAD 8bb175f at capture.
- report.py sha256 a778865686443f0ea8ac960de6a54aa741cbfc6c6edbe307ca89dafc7f39f7fc,
  identical before/after capture and pin runs (no w1 interference).
- Determinism double-render: identical.
- Goldens: audit-1.html 2357 bytes, glm-toolless-spawn.html 2397, index.html 2529.
- Fixture is clock-free: akar files written directly with fixed date; append_record
  stamps date.today() and would poison the byte compare.

## Fix guidance for w1

The list must link the sanitized slug (or pages must be written at the raw id);
either shape satisfies pins 1-4. Pin 5 holds the fix to byte-identical output for
lowercase-hyphen ids, where raw id equals slug, so slug-based links change no bytes.

## Incidents during this task (both fixed, both caught by gates)

1. Golden stamp corrupted the pins file (re.sub replacement processed \n escapes
   into raw newlines). Detected by SyntaxError on import; fixed by splicing on
   sentinel indexes; added compile + byte-equality readback gate to the stamp.
2. Pin helper `_list_links` built href->title; `_resolve` indexed by title, so
   pins 1-4 were red for the WRONG reason (KeyError-shaped assert, not the spec
   violation). Detected because pin 4's assert message showed the key present.
   Fixed to title->href; red set re-measured (this file's table is the re-run).

## Concurrent work observed (not w2's)

git status shows modifications to logs/s18__*, s19, s20, s22 outputs and
replay-matrix.md, plus untracked .rumpun/musim/s30.yaml. w2 wrote nothing
outside w2/; those changes belong to w1 or the engine.
