"""akar: append-only record writer for rumpun project state.

Records live under ``<root>/ledger/`` (legacy ``<root>/akar/`` trees resolve
unchanged) as ``<YYYY-MM-DD>_<record_id>.md``. Each
file is a small header (id, date, title), the body, and a trailing
``sha256:`` line digesting the body bytes — the digest backs P11 evidence
refs of the form ``akar:<record-id>@<sha256>``. Records are immutable once
written; appending is the only mutation this module performs.
"""

import contextlib
import fcntl
import hashlib
import logging
import os
from collections.abc import Iterator
from datetime import date
from pathlib import Path
from typing import IO

from rumpun import paths

logger = logging.getLogger(__name__)

_ID_PREFIX = "id: "


class AkarError(Exception):
    """Invalid record input, record conflict, unreadable akar state, or lookup miss."""


def _validate(record_id: str, title: str) -> None:
    """Reject ids/titles that would break the record layout or escape akar/."""
    forbidden = ("/", "\\", "\0", "\n", "\r")
    if not record_id or any(ch in record_id for ch in forbidden):
        raise AkarError(f"invalid record_id {record_id!r}")
    if "\n" in title or "\r" in title:
        raise AkarError(f"title of {record_id!r} must be a single line")


def _declared(root: Path) -> dict[str, Path]:
    """Map every record id declared in the ledger to its file, sorted by filename."""
    ledger = paths.ledger_dir(root)
    if not ledger.is_dir():
        return {}
    found: dict[str, Path] = {}
    for path in sorted(ledger.iterdir()):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.exception("cannot read existing file %s", path)
            raise AkarError(f"cannot read {path}") from exc
        for line in text.splitlines():
            if line.startswith(_ID_PREFIX):
                rid = line.removeprefix(_ID_PREFIX).strip()
                if rid in found:
                    logger.warning(
                        "record id %s declared in both %s and %s", rid, found[rid], path
                    )
                else:
                    found[rid] = path
                break
        else:
            logger.debug("ignoring %s: no id line", path)
    return found


@contextlib.contextmanager
def _append_lock(root: Path) -> Iterator[IO[str]]:
    """Exclusive flock on ledger append.lock across one append.

    Held across the duplicate check, the existence check, and the atomic
    publish (external review H6): two concurrent appenders of one id can
    no longer both pass the checks and replace each other's record. The
    lock path resolves through ledger_new, the write resolver, not the
    read resolver: on a fresh tree ledger_dir falls back to legacy
    akar/ while the publish lands in ledger/, and the first publish
    mkdir flips ledger_dir mid-transaction -- an appender resolving
    after it flocks a different file and the lock excludes nothing
    (issue #17). ledger_new is constant across that flip, so
    concurrent appenders always flock one file. The lock file is
    opened append-only ("a"), so first use creates it without
    truncating.
    flock is per open file: a caller already inside this context must not
    re-enter -- a second fd would block on itself.
    """
    lock_path = paths.ledger_new(root) / "append.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with open(lock_path, "a", encoding="utf-8") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        try:
            yield lock_file
        finally:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)


def append_record(root: Path, record_id: str, title: str, body: str) -> Path:
    """Append one record and return its path.

    File layout, one element per line (the body may itself span lines):

        # akar record: <record_id>
        id: <record_id>
        date: <YYYY-MM-DD>
        title: <title>
        <body>
        sha256: <sha256 hex of the utf-8 body>

    The body is recoverable exactly as ``"\\n".join(lines[4:-1])``.

    Raises AkarError when record_id is invalid, already declared by any file
    in akar/, or the target filename already exists. Existing records are
    never modified. The duplicate check, existence check, and publish share
    one exclusive flock on the ledger append.lock (review H6): concurrent appends
    of one id serialize into one success and one AkarError.
    """
    _validate(record_id, title)
    iso_date = date.today().isoformat()
    final = paths.ledger_new(root) / f"{iso_date}_{record_id}.md"
    digest = hashlib.sha256(body.encode("utf-8")).hexdigest()
    text = (
        "\n".join(
            [
                f"# akar record: {record_id}",
                f"id: {record_id}",
                f"date: {iso_date}",
                f"title: {title}",
                body,
                f"sha256: {digest}",
            ]
        )
        + "\n"
    )

    # One lock spans the duplicate check, the existence check, and the
    # publish: outside it the two checks say nothing about the publish
    # instant, which is exactly the H6 replacement window.
    with _append_lock(root):
        if (dup := _declared(root).get(record_id)) is not None:
            raise AkarError(f"record_id {record_id!r} already declared in {dup}")
        if final.exists():
            raise AkarError(f"{final} already exists; akar is append-only")
        tmp = final.with_name(f".{final.name}.{os.getpid()}.tmp")
        try:
            final.parent.mkdir(parents=True, exist_ok=True)
            with open(tmp, "w", encoding="utf-8") as fh:
                fh.write(text)
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp, final)
        except OSError as exc:
            logger.exception("cannot append record %s to %s", record_id, final)
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                logger.exception("cannot remove tmp file %s", tmp)
            raise AkarError(f"cannot append record {record_id!r} to {final}") from exc
    logger.info("appended ledger record %s -> %s", record_id, final)
    return final


def find_record(root: Path, record_id: str) -> Path:
    """Return the path of the record declaring record_id, or raise AkarError."""
    path = _declared(root).get(record_id)
    if path is None:
        raise AkarError(f"no akar record declares id {record_id!r}")
    return path


def declared_ids(root: Path) -> dict[str, Path]:
    """All record ids declared in akar/ mapped to their declaring file.

    Read view over the same scan append_record and find_record guard with;
    lifecycle consumers (the evolve high-water mark, review M8) read
    declared ids instead of re-parsing record files or trusting filenames.
    """
    return dict(_declared(root))


def correct_record(root: Path, record_id: str, reason: str) -> Path:
    """Append a sealed correction record for record_id (#29).

    Akar is append-only: a flawed record is never edited in place. The
    correction carries corrects: <id>, the caller's reason, and the
    original seal -- or the honest 'absent' mark when appended content
    broke the sha256 trailer (the case that demands this verb).
    """
    original = find_record(root, record_id)
    text = original.read_text(encoding="utf-8")
    record_lines = text.rstrip("\n").splitlines()
    title = next(
        (ln[len("title: "):].strip() for ln in record_lines
         if ln.startswith("title: ")),
        record_id,
    )
    seal = record_lines[-1] if record_lines else ""
    if seal.startswith("sha256: "):
        digest_note = f"original digest: {seal[len('sha256: '):]}"
    else:
        digest_note = (
            "original digest: absent (record text ends before the sha256 line)"
        )
    body = (
        f"corrects: {record_id}\n"
        f"reason: {reason}\n"
        f"{digest_note}\n"
        f"the corrected citation target is correction-{record_id}\n"
    )
    return append_record(
        root, f"correction-{record_id}", f"correction: {title}", body,
    )
