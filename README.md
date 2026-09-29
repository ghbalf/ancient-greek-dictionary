# Pape Greek-German Dictionary

Digital edition of **Wilhelm Pape's Handwörterbuch der griechischen Sprache** (Greek-German Dictionary) with 98,893 entries. Available as a Flask web app and an Android app.

Source data: [StarDict format from Zeno.org](http://www.zeno.org).

## Project Structure

```
app.py                  # Flask web application
templates/index.html    # Web UI (HTML/CSS/JS)
scripts/convert_stardict.py  # StarDict → SQLite converter
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
- **German fulltext search** — find entries by definition content (FTS4)
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

The Android app bundles the same database and UI in a WebView. A Kotlin `@JavascriptInterface` bridge replaces the Flask API.

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

APK: `android/app/build/outputs/apk/release/app-release.apk`

### Install

```bash
adb install app/build/outputs/apk/release/app-release.apk
```

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
