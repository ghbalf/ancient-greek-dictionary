package com.pape.dictionary

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.webkit.JavascriptInterface
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

class DictionaryBridge(private val context: Context) {

    private val db: SQLiteDatabase by lazy {
        val dbFile = File(context.filesDir, "pape_dictionary.db")
        SQLiteDatabase.openDatabase(dbFile.path, null, SQLiteDatabase.OPEN_READONLY)
    }

    companion object {
        private const val MAX_RESULTS = 50
        private val GREEK_RE = Regex("[\\u0370-\\u03FF\\u1F00-\\u1FFF]")
    }

    @JavascriptInterface
    fun search(query: String, mode: String): String {
        val q = query.trim()
        if (q.isEmpty() || q.length > 200) {
            return JSONObject().put("results", JSONArray()).put("mode_used", mode).toString()
        }

        return when (mode) {
            "headword" -> {
                val results = searchHeadword(q, MAX_RESULTS)
                makeResponse(results, "headword")
            }
            "transliteration" -> {
                val results = searchTransliteration(q, MAX_RESULTS)
                makeResponse(results, "transliteration")
            }
            "fulltext" -> {
                val results = try { searchFulltext(q, MAX_RESULTS) } catch (_: Exception) { emptyList() }
                makeResponse(results, "fulltext")
            }
            else -> { // auto
                val isGreek = GREEK_RE.containsMatchIn(q)
                val (results, modeUsed) = if (isGreek) {
                    searchHeadword(q, MAX_RESULTS) to "headword"
                } else {
                    searchTransliteration(q, MAX_RESULTS) to "transliteration"
                }

                val combined = results.toMutableList()
                if (combined.size < MAX_RESULTS) {
                    try {
                        val ft = searchFulltext(q, MAX_RESULTS - combined.size)
                        val seen = combined.map { it.getInt("id") }.toSet()
                        for (r in ft) {
                            if (r.getInt("id") !in seen) combined.add(r)
                        }
                    } catch (_: Exception) { }
                }
                makeResponse(combined, modeUsed)
            }
        }
    }

    @JavascriptInterface
    fun getFrontMatter(): String {
        val sections = JSONArray()
        val items = listOf(
            "vorwort" to "Vorwort",
            "vorrede" to "Vorrede",
            "vorrede3" to "Vorrede zur dritten Auflage",
            "abkuerzungen" to "Verzeichnis der Abkürzungen und der angeführten Schriftsteller"
        )
        for ((key, title) in items) {
            val html = try {
                context.assets.open("front_matter/$key.html").bufferedReader().readText()
            } catch (_: Exception) { "" }
            sections.put(JSONObject().apply {
                put("key", key)
                put("title", title)
                put("html", html)
            })
        }
        return JSONObject().put("sections", sections).toString()
    }

    private fun searchHeadword(q: String, limit: Int): List<JSONObject> {
        val cursor = db.rawQuery(
            "SELECT id, headword, definition_html FROM entries WHERE headword LIKE ? ORDER BY headword LIMIT ?",
            arrayOf("$q%", limit.toString())
        )
        return cursorToList(cursor)
    }

    private fun searchTransliteration(q: String, limit: Int): List<JSONObject> {
        val cursor = db.rawQuery(
            """SELECT DISTINCT e.id, e.headword, e.definition_html
               FROM synonyms s JOIN entries e ON e.id = s.entry_id
               WHERE s.synonym LIKE ? ORDER BY e.headword LIMIT ?""",
            arrayOf("$q%", limit.toString())
        )
        return cursorToList(cursor)
    }

    private fun searchFulltext(q: String, limit: Int): List<JSONObject> {
        val cursor = db.rawQuery(
            """SELECT e.id, e.headword, e.definition_html
               FROM entries_fts fts JOIN entries e ON e.id = fts.rowid
               WHERE entries_fts MATCH ? ORDER BY rank LIMIT ?""",
            arrayOf(q, limit.toString())
        )
        return cursorToList(cursor)
    }

    private fun cursorToList(cursor: android.database.Cursor): List<JSONObject> {
        val results = mutableListOf<JSONObject>()
        cursor.use {
            while (it.moveToNext()) {
                results.add(JSONObject().apply {
                    put("id", it.getInt(0))
                    put("headword", it.getString(1))
                    put("definition_html", it.getString(2))
                })
            }
        }
        return results
    }

    private fun makeResponse(results: List<JSONObject>, modeUsed: String): String {
        val arr = JSONArray()
        for (r in results) arr.put(r)
        return JSONObject().put("results", arr).put("mode_used", modeUsed).toString()
    }
}
