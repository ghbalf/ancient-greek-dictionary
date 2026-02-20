import re
import sqlite3

from pathlib import Path

from flask import Flask, g, jsonify, request, send_from_directory

app = Flask(__name__)
DB_PATH = "data/pape_dictionary.db"
RES_DIR = "data/raw/stardict/res"
FRONT_MATTER_DIR = Path("data/front_matter")
FRONT_MATTER = {
    "vorwort": "Vorwort",
    "vorrede": "Vorrede",
    "vorrede3": "Vorrede zur dritten Auflage",
    "abkuerzungen": "Verzeichnis der Abkürzungen und der angeführten Schriftsteller",
}
MAX_RESULTS = 50

GREEK_RE = re.compile(r"[\u0370-\u03FF\u1F00-\u1FFF]")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def search_headword(db, q, limit):
    return db.execute(
        "SELECT id, headword, definition_html FROM entries WHERE headword LIKE ? ORDER BY headword LIMIT ?",
        (q + "%", limit),
    ).fetchall()


def search_transliteration(db, q, limit):
    return db.execute(
        """SELECT DISTINCT e.id, e.headword, e.definition_html
           FROM synonyms s JOIN entries e ON e.id = s.entry_id
           WHERE s.synonym LIKE ? ORDER BY e.headword LIMIT ?""",
        (q + "%", limit),
    ).fetchall()


def search_fulltext(db, q, limit):
    return db.execute(
        """SELECT e.id, e.headword, e.definition_html
           FROM entries_fts fts JOIN entries e ON e.id = fts.rowid
           WHERE entries_fts MATCH ? ORDER BY rank LIMIT ?""",
        (q, limit),
    ).fetchall()


def rows_to_dicts(rows):
    return [{"id": r["id"], "headword": r["headword"], "definition_html": r["definition_html"]} for r in rows]


def is_greek(text):
    return bool(GREEK_RE.search(text))


@app.route("/")
def index():
    return app.send_static_file("index.html") if False else __import__("flask").render_template("index.html")


@app.route("/res/<path:filename>")
def serve_resource(filename):
    return send_from_directory(RES_DIR, filename)


@app.route("/api/front_matter")
def api_front_matter():
    sections = []
    for key, title in FRONT_MATTER.items():
        path = FRONT_MATTER_DIR / f"{key}.html"
        html = path.read_text(encoding="utf-8") if path.exists() else ""
        sections.append({"key": key, "title": title, "html": html})
    return jsonify({"sections": sections})


@app.route("/api/search")
def api_search():
    q = request.args.get("q", "").strip()
    mode = request.args.get("mode", "auto")

    if not q or len(q) > 200:
        return jsonify({"results": [], "mode_used": mode})

    db = get_db()

    if mode == "headword":
        results = rows_to_dicts(search_headword(db, q, MAX_RESULTS))
        mode_used = "headword"
    elif mode == "transliteration":
        results = rows_to_dicts(search_transliteration(db, q, MAX_RESULTS))
        mode_used = "transliteration"
    elif mode == "fulltext":
        try:
            results = rows_to_dicts(search_fulltext(db, q, MAX_RESULTS))
        except Exception:
            results = []
        mode_used = "fulltext"
    else:  # auto
        if is_greek(q):
            results = rows_to_dicts(search_headword(db, q, MAX_RESULTS))
            mode_used = "headword"
        else:
            results = rows_to_dicts(search_transliteration(db, q, MAX_RESULTS))
            mode_used = "transliteration"
        # Also include fulltext results for auto mode
        if len(results) < MAX_RESULTS:
            try:
                ft = rows_to_dicts(search_fulltext(db, q, MAX_RESULTS - len(results)))
                seen = {r["id"] for r in results}
                for r in ft:
                    if r["id"] not in seen:
                        results.append(r)
            except Exception:
                pass

    return jsonify({"results": results, "mode_used": mode_used})


if __name__ == "__main__":
    app.run(debug=True)
