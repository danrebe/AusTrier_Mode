# Kleid____oskop

Mode Kaleidoskop ist ein Prototyp, mit dem man historische Modebilder ohne Suchfeld erkunden kann. Ausgangspunkt ist eine von vier Perspektiven: **Farbe**, **Silhouette**, **Accessoires** oder **visuelle Ähnlichkeit (Embedding)**. Die Website zeigt dann eine Reihe von Bildern, die sich in diesem Merkmal schrittweise verändern.

Grundlage sind **2.021 Modebilder des Wien Museums** (vor allem kolorierte Kupferstiche, die meisten zwischen 1800 und 1845 entstanden), abgerufen über den [Kulturpool](https://kulturpool.at).

---

## Inhalt

- [So funktioniert die Auswahl](#so-funktioniert-die-auswahl)
- [Aufbau des Repositorys](#aufbau-des-repositorys)
- [Pipeline: von den Rohdaten zum Index](#pipeline-von-den-rohdaten-zum-index)
- [Website starten](#website-starten)
- [Datenformate](#datenformate)
- [Datenquellen und Lizenz](#datenquellen-und-lizenz)

---

## So funktioniert die Auswahl

1. **Merkmale extrahieren:** Für jedes Merkmal werden alle Bilder analysiert und sortiert. Die sortierten Listen stehen in der Index-Datei `index.json`, eine Liste pro Filter.
2. **Metadaten pro Bild:** Jedes Bild hat eine eigene JSON-Datei mit Titel, Inventarnummer, Datierung, Themen, Bild-URL und den Accessoire-Tags.
3. **Zentrales Bild:** Wählt man einen Filter, bestimmt die Website ein zentrales Bild und liest die Index-Liste dieses Filters.
4. **±10 Bilder:** Aus der Liste werden die 10 Bilder vor und die 10 Bilder nach dem zentralen Bild übernommen.
5. **Sonderthemen:** Einige seltene, auffällige Themen wurden von Hand ausgewählt: **Kind** (157 Bilder), **Sport** (19) und **Verkleidung, Maskierung** (15). Hat ein Bild eines dieser Themen, kommen die nächsten 4 Bilder aus der Liste dieses Themas.

---

## Aufbau des Repositorys

```
AusTrier_Mode/
├── data/                       Ausgangsdaten (Metadaten-Export, UUID-Liste) und Themen-Skript
├── Farbanalyse/                Farbpaletten der Bilder auslesen und in Filter umwandeln
├── silhouette/                 Kleider-Silhouetten freistellen und vergleichen
├── ähnlichkeitsanalyse/        Visuelle Ähnlichkeit, Accessoires, Themen-Häufigkeit
├── filter_jsons/               Fertige Filterdateien (Farbe, Ähnlichkeit, Sonderthemen)
├── metadata_jsons/json_output/ Eine Metadaten-JSON pro Bild (<uuid>.json)
├── results/                    Früher HTML-Prototyp
├── website/Mode Kaleidoskop/
│   ├── flask/                  Die Website (Flask-App, Templates, Daten, Skripte)
│   └── src/, Test/             Vue/Vite-Grundgerüst und Testdaten (noch nicht in Gebrauch)
└── exampe.json                 Vorlage für das Metadaten- und Filterformat
```

### Wichtige Dateien

| Datei | Inhalt |
|---|---|
| `data/dataset_modebilder.csv` | Metadaten aller 2.021 Bilder aus dem Kulturpool (SPARQL-Export): `uuid`, `titel`, `identifikator`, `datum`, `thema_.1` … `thema_.36` |
| `data/uuid.csv` | Liste aller UUIDs, Eingabe für mehrere Skripte |
| `Farbanalyse/farben.csv` | Farben pro Bild: `uuid, wm_objekt_id, inventarnummer, hex, r, g, b` |
| `filter_jsons/farben_filter.json` | Ein Eintrag pro Farbe mit CSS-Farbname und Hex-Wert |
| `filter_jsons/KindFilter.json`, `SportFilter.json`, `MaskierungFilter.json` | UUIDs der Sonderthemen, je Filter in Index-Reihenfolge |
| `silhouette/distanceList.json` | Die 10 ähnlichsten Silhouetten pro Bild |
| `website/Mode Kaleidoskop/flask/data/index.json` | Die sortierten Listen `Farbe`, `Aehnlichkeiten` und `Silhouette`, die die Website liest |

---

## Pipeline: von den Rohdaten zum Index

Die Skripte bauen aufeinander auf. Pfade sind relativ zum Ort des Skripts angelegt, sodass sie auf jedem Rechner laufen.

### 1. Ausgangsdaten

Die Metadaten stammen aus dem Kulturpool, abgefragt über den [SPARQL-Endpunkt](https://sparql.kulturpool.at) und die [Such-API](https://api.kulturpool.at/reference/api/suche/). Ausgewählt sind alle Objekte mit `edmType = IMAGE` und dem Schlagwort `Modebilder`. Ergebnis sind `data/dataset_modebilder.csv` und `data/uuid.csv`.

### 2. Farbe

| Skript | Was es macht | Ergebnis |
|---|---|---|
| `Farbanalyse/02_OCR_Farbpalette.py` | Ruft für jedes Bild die Objektseite der Wien-Museum-Sammlung auf und liest die dort angegebenen Palettenfarben aus | `farben.csv` |
| `Farbanalyse/farbejson.py` | Ordnet jedem Hex-Wert den ähnlichsten offiziellen CSS-Farbnamen zu (Abstand im Lab-Farbraum) | `filter_jsons/farben_filter.json` |
| `flask/scripts/sortImages.py` | Sortiert die Farben nach Farbton (HSV) und schreibt die Liste in den Index | `index.json` → `Farbe` |

Weil jedes Bild mehrere Farben hat, kommt jede UUID in der Liste `Farbe` mehrfach vor (11.211 Einträge für 2.021 Bilder).

### 3. Visuelle Ähnlichkeit (Embedding)

| Skript | Was es macht | Ergebnis |
|---|---|---|
| `ähnlichkeitsanalyse/ähnlichkeitsanalyse.py` | Fragt für jedes Bild die 10 visuell ähnlichsten Bilder über die Kulturpool-API `/v2/similar` ab | `aehnlichkeiten_values_top10.csv` (Grundlage für `filter_jsons/aehnlichkeiten_embeddings.json`) |
| `flask/scripts/sortImagesSimularity.py` | Bildet eine Kette: Ausgehend von einem Bild folgt immer das ähnlichste noch nicht verwendete Bild | `index.json` → `Aehnlichkeiten` |

### 4. Silhouette

| Skript | Was es macht | Ergebnis |
|---|---|---|
| `silhouette/download_extract_silhouette.py` | Findet das Kleid mit Grounding DINO und stellt es mit Segment Anything (SAM) frei | `sil_out/<uuid>.png` (weißes Kleid auf schwarz), `not_found.txt` |
| `silhouette/sil_similarity_width.py` | Vergleicht die Silhouetten über ihr Breitenprofil (normiert auf die Höhe) und speichert die 10 ähnlichsten | `distanceList.json` |

Für 2.006 Bilder liegt eine Silhouette vor. Bei den übrigen wurde kein Kleid erkannt.

### 5. Accessoires und Sonderthemen

| Skript | Was es macht | Ergebnis |
|---|---|---|
| `ähnlichkeitsanalyse/objektaanalyse2.py` | Sucht Bilder mit den Themen Fächer, Regenschirm, Muff, Schmuck, Schal und Spazierstock | `results/uuids_nach_thema.csv` |
| `data/extrathema.py` | Sucht Bilder mit den Sonderthemen; Kind, Mädchenkleid und Kleidung für Mädchen/Jungen werden zu **Kind** zusammengefasst | `results/themen_kind_sport_verkleidung.csv` |
| `ähnlichkeitsanalyse/themaHäufigkeit.py` | Zählt, wie oft jedes Schlagwort vorkommt (Hilfsmittel zur Auswahl der Themen) | `results/begriffe_haeufigkeit.csv` |

### 6. Metadaten-JSONs

`flask/scripts/indexen.py` trägt in jede Metadaten-JSON ein, an welchen Positionen das Bild im Index steht.

---

## Website starten

Die Website ist eine Flask-App.

**Voraussetzung:** Python 3

```bash
# im Projektordner
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install flask requests

cd "website/Mode Kaleidoskop/flask"
python app.py
```

Danach ist die Seite unter <http://127.0.0.1:5000> erreichbar.

- `/` – Startseite mit den vier Perspektiven
- `/sammlung?kategorie=farbe` – ebenso `silhouette`, `accessoires`, `embedding` oder `random`

Pro Aufruf lädt die App die ausgewählten Bilder vom Wien Museum herunter und legt sie in `flask/static/images/` ab. Dafür braucht sie eine Internetverbindung.

### Pakete für die Analyse-Skripte

```bash
python -m pip install requests tqdm pandas numpy pillow webcolors opencv-python torch transformers colorlog
```

Nicht jedes Skript braucht alle Pakete: `torch` und `transformers` sind nur für die Silhouetten nötig, `webcolors` nur für `farbejson.py`.

---

## Datenformate

**Metadaten pro Bild** (`metadata_jsons/json_output/<uuid>.json`):

```json
{
    "Type": "Metadaten",
    "Identifikator": "M 30999",
    "titel": "Modebild: Fünf Figuren, Damen-, Herren- und Kindermode, ein Kragen, Hüte, Frisuren",
    "Datum": "1837",
    "Thema": ["Frisur", "Mann", "Modebilder", "Kind", "Mädchenkleid", "…"],
    "URL": "https://sammlung.wienmuseum.at/openapi-images/objects/50260/513441_default.webp"
}
```

In der Kopie unter `flask/data/` kommen dazu `id` (die UUID), `Filter` (Positionen im Index) und bei Bildern mit Accessoires `accessoires`.

**Index** (`flask/data/index.json`):

```json
{
    "Filter": {
        "Farbe":          ["<uuid>", "<uuid>", "…"],
        "Aehnlichkeiten": ["<uuid>", "…"],
        "Silhouette":     ["<uuid>", "…"]
    }
}
```

**Sonderthemen** (`filter_jsons/KindFilter.json` usw.) haben denselben Aufbau, enthalten aber nur die Bilder des Themas, in derselben Reihenfolge wie im Index.

---

## Datenquellen und Lizenz

- **Bilder und Metadaten:** [Wien Museum Online Sammlung](https://sammlung.wienmuseum.at), bereitgestellt über den [Kulturpool](https://kulturpool.at). Die Texte und Metadaten des Wien Museums dürfen frei weiterverwendet werden. Für die Bilder gilt die Lizenz, die beim jeweiligen Objekt angegeben ist (meist CC0, teils CC BY 4.0). Das Wien Museum bittet darum, Urheber:in, Fotograf:in und das Wien Museum als Quelle zu nennen.
- **Visuelle Ähnlichkeit:** Kulturpool-API `/v2/similar`
- **Silhouetten:** [Grounding DINO](https://huggingface.co/IDEA-Research/grounding-dino-tiny) und [Segment Anything](https://huggingface.co/facebook/sam-vit-base)

Der Code steht unter der [Apache License 2.0](LICENSE).
