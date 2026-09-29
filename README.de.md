# Pape Griechisch-Deutsch Wörterbuch

Digitale Ausgabe von **Wilhelm Papes Handwörterbuch der griechischen Sprache** mit 98.893 Einträgen. Verfügbar als Flask-Webanwendung und als Android-App.

Quelldaten: [StarDict-Format von Zeno.org](http://www.zeno.org).

## Projektstruktur

```
app.py                  # Flask-Webanwendung
templates/index.html    # Web-Oberfläche (HTML/CSS/JS)
scripts/convert_stardict.py  # StarDict → SQLite Konverter
scripts/make_icon.py    # Erzeugt das Android-App-Icon
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
- **Deutsche Volltextsuche** — Einträge über Definitionstext finden (SQLite FTS4); kürzeste Einträge zuerst, bis zu 50 Treffer
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

Der Volltextindex verwendet **FTS4**, nicht FTS5: Das eingebaute SQLite von Android hat kein FTS5, ein FTS5-Index scheitert deshalb auf dem Gerät. Die Datenbank wird im Rollback-Journal-Modus (ohne WAL) geschrieben, damit die Datei in der APK in sich vollständig ist.

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

Die Android-App bündelt dieselbe Datenbank und Oberfläche in einem WebView. Eine Kotlin-`@JavascriptInterface`-Brücke ersetzt die Flask-API. Läuft ab Android 7.0 (API 24); Zielversion ist Android 14 (API 34).

Beim ersten Start kopiert die App die mitgelieferte Datenbank in ihren privaten Speicher. Wenn sich die mitgelieferte Datenbank ändert, `DB_VERSION` in `MainActivity.kt` hochzählen — sonst behalten bestehende Installationen nach einem Update die alte Kopie.

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

Alternativ `RELEASE_STORE_PASSWORD` und `RELEASE_KEY_PASSWORD` in `~/.gradle/gradle.properties` (chmod 600) oder in die Umgebung eintragen; dann genügt ein einfaches `./gradlew assembleRelease`.

APK: `android/app/build/outputs/apk/release/app-release.apk`

### Installation

```bash
adb install app/build/outputs/apk/release/app-release.apk
```

Ohne USB-Kabel: APK im Heimnetz bereitstellen (z.B. `python3 -m http.server`), die URL im Browser des Handys öffnen und die Installation aus unbekannten Quellen erlauben.

> **Update von 1.0:** Version 1.1 ist mit einem neuen Schlüssel signiert. Android verweigert die Installation über 1.0 — die alte App vorher deinstallieren.

### App-Icon

Das Icon (griechisches Π in Creme auf Olivgrün) ist ein adaptives Vektor-Icon mit Monochrom-Ebene für Designsymbole (Android 13+) sowie PNG-Varianten für API 24/25. Neu erzeugen mit:

```bash
pip install fonttools pillow
python3 scripts/make_icon.py android/app/src/main/res
```

Das Skript verwendet die Schrift P052 Bold (URW base35, Paket `fonts-urw-base35`).

## Änderungen

### 1.1 (29.09.2026)

- **Fehlerbehebung:** Die deutsche Volltextsuche funktionierte auf Android-Geräten nicht — der Index war FTS5, das Androids SQLite nicht unterstützt. Umstellung auf FTS4; Treffer werden jetzt nach Eintragslänge sortiert (kürzeste zuerst) statt nach FTS5-`rank`.
- Die App ersetzt ihre Datenbankkopie, wenn sich die mitgelieferte Datenbank ändert (`DB_VERSION`), atomar über eine Temp-Datei.
- Neues App-Icon: adaptives Vektor-Icon, scharf in jeder Bildschirmauflösung (das alte 48-px-Bitmap wurde hochskaliert).
- Neuer Release-Signaturschlüssel (siehe *Update von 1.0*).

### 1.0 (20.02.2026)

- Erste Version: Flask-Webanwendung und Android-App.

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
