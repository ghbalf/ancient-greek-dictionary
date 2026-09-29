#!/usr/bin/env python3
"""Convert Pape Greek-German dictionary from StarDict format to JSONL and SQLite."""

import json
import re
import sqlite3
import struct
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STARDICT_DIR = BASE_DIR / "data" / "raw" / "stardict"
OUTPUT_JSONL = BASE_DIR / "data" / "pape_dictionary.jsonl"
OUTPUT_DB = BASE_DIR / "data" / "pape_dictionary.db"

IDX_FILE = STARDICT_DIR / "pape_gr-de.idx"
DICT_FILE = STARDICT_DIR / "pape_gr-de.dict"
SYN_FILE = STARDICT_DIR / "pape_gr-de.syn"


def parse_idx(idx_data: bytes) -> list[tuple[str, int, int]]:
    """Parse .idx file: null-terminated word + 4-byte offset + 4-byte size."""
    entries = []
    pos = 0
    while pos < len(idx_data):
        nul = idx_data.index(b"\x00", pos)
        word = idx_data[pos:nul].decode("utf-8")
        offset, size = struct.unpack(">II", idx_data[nul + 1 : nul + 9])
        entries.append((word, offset, size))
        pos = nul + 9
    return entries


def parse_syn(syn_data: bytes) -> list[tuple[str, int]]:
    """Parse .syn file: null-terminated synonym + 4-byte entry index."""
    synonyms = []
    pos = 0
    while pos < len(syn_data):
        nul = syn_data.index(b"\x00", pos)
        synonym = syn_data[pos:nul].decode("utf-8")
        entry_idx = struct.unpack(">I", syn_data[nul + 1 : nul + 5])[0]
        synonyms.append((synonym, entry_idx))
        pos = nul + 5
    return synonyms


TAG_RE = re.compile(r"<[^>]+>")


def strip_html(html: str) -> str:
    """Strip HTML tags and collapse whitespace."""
    text = TAG_RE.sub("", html)
    text = text.replace("\n", " ").replace("\r", " ")
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def main():
    print("Reading StarDict files...")
    idx_data = IDX_FILE.read_bytes()
    dict_data = DICT_FILE.read_bytes()
    syn_data = SYN_FILE.read_bytes()

    print("Parsing index...")
    entries = parse_idx(idx_data)
    print(f"  {len(entries)} entries")

    print("Parsing synonyms...")
    syn_list = parse_syn(syn_data)
    print(f"  {len(syn_list)} synonyms")

    # Group synonyms by entry index
    syn_by_entry: dict[int, list[str]] = {}
    for synonym, entry_idx in syn_list:
        syn_by_entry.setdefault(entry_idx, []).append(synonym)

    # Read definitions and build records
    print("Reading definitions...")
    records = []
    for i, (headword, offset, size) in enumerate(entries):
        definition_html = dict_data[offset : offset + size].decode("utf-8")
        definition_text = strip_html(definition_html)
        synonyms = syn_by_entry.get(i, [])
        records.append(
            {
                "headword": headword,
                "definition_html": definition_html,
                "definition_text": definition_text,
                "synonyms": synonyms,
            }
        )

    # Write JSONL
    print(f"Writing {OUTPUT_JSONL}...")
    OUTPUT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSONL, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    # Write SQLite
    print(f"Writing {OUTPUT_DB}...")
    OUTPUT_DB.unlink(missing_ok=True)
    conn = sqlite3.connect(OUTPUT_DB)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(
        """CREATE TABLE entries (
            id INTEGER PRIMARY KEY,
            headword TEXT NOT NULL,
            definition_html TEXT NOT NULL,
            definition_text TEXT NOT NULL
        )"""
    )
    conn.execute("CREATE INDEX idx_headword ON entries(headword)")
    conn.execute(
        """CREATE TABLE synonyms (
            entry_id INTEGER NOT NULL REFERENCES entries(id),
            synonym TEXT NOT NULL
        )"""
    )
    conn.execute("CREATE INDEX idx_synonym ON synonyms(synonym)")
    conn.execute(
        # FTS4, not FTS5: Android's built-in SQLite ships without FTS5.
        # External content maps docid to entries.rowid (= entries.id).
        """CREATE VIRTUAL TABLE entries_fts USING fts4(
            content="entries", headword, definition_text, tokenize=unicode61
        )"""
    )

    print("  Inserting entries...")
    conn.executemany(
        "INSERT INTO entries (id, headword, definition_html, definition_text) VALUES (?, ?, ?, ?)",
        [(i, r["headword"], r["definition_html"], r["definition_text"]) for i, r in enumerate(records)],
    )

    print("  Inserting synonyms...")
    syn_rows = []
    for i, r in enumerate(records):
        for s in r["synonyms"]:
            syn_rows.append((i, s))
    conn.executemany("INSERT INTO synonyms (entry_id, synonym) VALUES (?, ?)", syn_rows)

    print("  Building FTS index...")
    conn.execute("INSERT INTO entries_fts(entries_fts) VALUES('rebuild')")

    conn.commit()
    # Ship without WAL so the file is self-contained when bundled in the APK
    conn.execute("PRAGMA journal_mode=DELETE")
    conn.execute("VACUUM")
    conn.close()

    print(f"\nDone! {len(records)} entries, {len(syn_rows)} synonyms.")
    print(f"  JSONL: {OUTPUT_JSONL}")
    print(f"  SQLite: {OUTPUT_DB}")


if __name__ == "__main__":
    main()
