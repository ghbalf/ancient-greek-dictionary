# Pape Griechisch-Deutsch Wörterbuch

Digitale Ausgabe von **Wilhelm Papes Handwörterbuch der griechischen Sprache** mit 98.893 Einträgen. Verfügbar als Flask-Webanwendung und als Android-App.

Quelldaten: [StarDict-Format von Zeno.org](http://www.zeno.org).

## Projektstruktur

```
app.py                  # Flask-Webanwendung
templates/index.html    # Web-Oberfläche (HTML/CSS/JS)
scripts/convert_stardict.py  # StarDict → SQLite Konverter
data/
  front_matter/         # Vorwort, Abkürzungen (HTML)
  raw/stardict/         # StarDict-Quelldateien + Bilder
  pape_dictionary.db    # SQLite-Datenbank (generiert)
  pape_dictionary.jsonl # JSONL-Export (generiert)
android/                # Android-App (WebView + Kotlin)
```

## Funktionen

- **Griechische Stichwortsuche** — griechisch eingeben (z.B. λόγος)
- **Transliterationssuche** — Eingabe über lateinische Tastatur (z.B. logos → λόγος)
- **Deutsche Volltextsuche** — Einträge über Definitionstext finden (FTS5)
- **Automodus** — erkennt automatisch griechische vs. lateinische Eingabe
- **Vorspann** — originale Vorreden und Abkürzungsverzeichnis

## Datenaufbereitung

Die StarDict-Quelldateien müssen in `data/raw/stardict/` liegen, bevor die Datenbank erzeugt werden kann:

```
data/raw/stardict/
  pape_gr-de.idx
  pape_gr-de.dict
  pape_gr-de.syn
  res/              # Bilder in den Definitionen
```

Datenbank erzeugen:

```bash
python3 scripts/convert_stardict.py
```

Erzeugt `data/pape_dictionary.db` (112 MB) und `data/pape_dictionary.jsonl`.

## Webanwendung

Erfordert Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

Öffne http://localhost:5000 im Browser.

## Android-App

Die Android-App bündelt dieselbe Datenbank und Oberfläche in einem WebView. Eine Kotlin-`@JavascriptInterface`-Brücke ersetzt die Flask-API.

### Voraussetzungen

- JDK 17+
- Android SDK mit Plattform 34 und Build-Tools 34.0.0

SDK-Pfad konfigurieren:

```bash
echo "sdk.dir=$HOME/Android/Sdk" > android/local.properties
```

### Debug-Build

```bash
cd android
./gradlew assembleDebug
```

APK: `android/app/build/outputs/apk/debug/app-debug.apk`

### Release-Build

Signatur-Keystore erzeugen (einmalig):

```bash
keytool -genkeypair -v -keystore android/release-keystore.jks \
  -keyalg RSA -keysize 2048 -validity 10000 -alias pape
```

Build mit Keystore-Passwort:

```bash
cd android
./gradlew assembleRelease \
  -PRELEASE_STORE_PASSWORD='dein-passwort' \
  -PRELEASE_KEY_PASSWORD='dein-passwort'
```

APK: `android/app/build/outputs/apk/release/app-release.apk`

### Installation

```bash
adb install app/build/outputs/apk/release/app-release.apk
```

## Transliterationstabelle

| Griechisch | Latein | | Griechisch | Latein | | Griechisch | Latein | | Griechisch | Latein |
|------------|--------|-|------------|--------|-|------------|--------|-|------------|--------|
| α | a | | η | h | | ν | n | | τ | t |
| β | b | | θ | **q** | | ξ | **c** | | υ | u |
| γ | g | | ι | i | | ο | o | | φ | f |
| δ | d | | κ | k | | π | p | | χ | x |
| ε | e | | λ | l | | ρ | r | | ψ | **y** |
| ζ | z | | μ | m | | σ/ς | s | | ω | **w** |

Diakritika werden ignoriert. Beispiel: `yuxh` → ψυχή, `filosofia` → φιλοσοφία

## Lizenz

Wörterbuchinhalt von Zeno.org. Software in diesem Repository wird ohne Gewährleistung bereitgestellt.
