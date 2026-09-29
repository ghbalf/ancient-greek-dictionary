# Pape Greek-German Dictionary

Digital edition of **Wilhelm Pape's Handwörterbuch der griechischen Sprache** (Greek-German Dictionary) with 98,893 entries. Available as a Flask web app and an Android app.

Source data: [StarDict format from Zeno.org](http://www.zeno.org).

## Project Structure

```
app.py                  # Flask web application
templates/index.html    # Web UI (HTML/CSS/JS)
scripts/convert_stardict.py  # StarDict → SQLite converter
scripts/make_icon.py    # Generates the Android launcher icon
data/
  front_matter/         # Preface, abbreviations (HTML)
  raw/stardict/         # StarDict source files + images
  pape_dictionary.db    # SQLite database (generated)
  pape_dictionary.jsonl # JSONL export (generated)
android/                # Android app (WebView + Kotlin)
```

## Features

- **Greek headword search** — type Greek directly (e.g. λόγος)
- **Transliteration search** — Latin keyboard input (e.g. logos → λόγος)
- **German fulltext search** — find entries by definition content (SQLite FTS4); shortest entries first, up to 50 results
- **Auto mode** — detects Greek vs. Latin input automatically
- **Front matter** — original prefaces and abbreviation list

## Data Preparation

The StarDict source files must be placed in `data/raw/stardict/` before generating the database:

```
data/raw/stardict/
  pape_gr-de.idx
  pape_gr-de.dict
  pape_gr-de.syn
  res/              # Images referenced in definitions
```

Generate the SQLite database:

```bash
python3 scripts/convert_stardict.py
```

This produces `data/pape_dictionary.db` (112 MB) and `data/pape_dictionary.jsonl`.

The fulltext index uses **FTS4**, not FTS5: Android's built-in SQLite ships without FTS5, so an FTS5 index fails on the device. The database is written in rollback-journal mode (no WAL) so the file is self-contained when bundled into the APK.

## Web App

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Open http://localhost:5000 in a browser.

## Android App

The Android app bundles the same database and UI in a WebView. A Kotlin `@JavascriptInterface` bridge replaces the Flask API. Runs on Android 7.0 (API 24) and later; targets Android 14 (API 34).

On first start the app copies the bundled database into its private storage. When the bundled database changes, bump `DB_VERSION` in `MainActivity.kt` — otherwise existing installations keep the old copy after an update.

### Prerequisites

- JDK 17+
- Android SDK with platform 34 and build-tools 34.0.0

Set up the SDK path:

```bash
echo "sdk.dir=$HOME/Android/Sdk" > android/local.properties
```

### Debug Build

```bash
cd android
./gradlew assembleDebug
```

APK: `android/app/build/outputs/apk/debug/app-debug.apk`

### Release Build

Generate a signing keystore (once):

```bash
keytool -genkeypair -v -keystore android/release-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias pape
```

Build with the keystore password:

```bash
cd android
./gradlew assembleRelease \
  -PRELEASE_STORE_PASSWORD='your-password' \
  -PRELEASE_KEY_PASSWORD='your-password'
```

Alternatively, put `RELEASE_STORE_PASSWORD` and `RELEASE_KEY_PASSWORD` into `~/.gradle/gradle.properties` (chmod 600) or the environment; then a plain `./gradlew assembleRelease` works.

APK: `android/app/build/outputs/apk/release/app-release.apk`

### Install

```bash
adb install app/build/outputs/apk/release/app-release.apk
```

Without a USB cable: serve the APK in the local network (e.g. `python3 -m http.server`), open the URL in the phone's browser and allow installing from unknown sources.

> **Upgrading from 1.0:** version 1.1 is signed with a new key. Android refuses to install it over 1.0 — uninstall the old app first.

### Launcher Icon

The icon (Greek capital Π in cream on olive green) is an adaptive vector icon with a monochrome layer for themed icons (Android 13+), plus PNG fallbacks for API 24/25. Regenerate it with:

```bash
pip install fonttools pillow
python3 scripts/make_icon.py android/app/src/main/res
```

The script uses the P052 Bold font (URW base35, package `fonts-urw-base35`).

## Changelog

### 1.1 (2026-09-29)

- **Fix:** German fulltext search failed on Android devices — the index was FTS5, which Android's SQLite does not support. Switched to FTS4; results are now ordered by entry length (shortest first) instead of FTS5 `rank`.
- The app replaces its database copy when the bundled database changes (`DB_VERSION`), atomically via a temp file.
- New launcher icon: adaptive vector icon, sharp at every screen density (the old 48 px bitmap was upscaled).
- New release signing key (see *Upgrading from 1.0*).

### 1.0 (2026-02-20)

- Initial release: Flask web app and Android app.

## Transliteration Table

| Greek | Latin | | Greek | Latin | | Greek | Latin | | Greek | Latin |
|-------|-------|-|-------|-------|-|-------|-------|-|-------|-------|
| α | a | | η | h | | ν | n | | τ | t |
| β | b | | θ | **q** | | ξ | **c** | | υ | u |
| γ | g | | ι | i | | ο | o | | φ | f |
| δ | d | | κ | k | | π | p | | χ | x |
| ε | e | | λ | l | | ρ | r | | ψ | **y** |
| ζ | z | | μ | m | | σ/ς | s | | ω | **w** |

Diacritics are ignored. Example: `yuxh` → ψυχή, `filosofia` → φιλοσοφία

## License

Dictionary content from Zeno.org. Software in this repository is provided as-is.
