
import json
import colorsys
from pathlib import Path


# Projektverzeichnis: eine Ebene über scripts/
PROJEKT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJEKT_DIR / "data"


def farbton(hex_farbe):
    """
    Konvertiert einen RGB-Hexwert wie '#d87f2d' in HSV
    und gibt den Farbton (Hue) zurück.
    """
    hex_farbe = hex_farbe.lstrip("#")

    if len(hex_farbe) != 6:
        raise ValueError(
            f"Ungültiger RGB-Hexwert: {hex_farbe}"
        )

    r = int(hex_farbe[0:2], 16) / 255
    g = int(hex_farbe[2:4], 16) / 255
    b = int(hex_farbe[4:6], 16) / 255

    h, s, v = colorsys.rgb_to_hsv(r, g, b)

    return h, s, v


def filter_sortieren(filter_name, input_file):
    config_file = DATA_DIR / "index.json"

    # Relativen Eingabepfad zum Projektverzeichnis auflösen
    input_file = Path(input_file)

    if not input_file.is_absolute():
        input_file = PROJEKT_DIR / input_file

    # 1. JSON-Array aus der Datei einlesen
    with input_file.open("r", encoding="utf-8") as file:
        filter_liste = json.load(file)

    if not isinstance(filter_liste, list):
        raise ValueError(
            "Die JSON-Datei muss ein Array enthalten."
        )

    # 2. Farben nach Farbton sortieren
    # Bei gleichem Farbton werden Sättigung und Helligkeit
    # als zusätzliche Sortierkriterien verwendet.
    filter_liste.sort(
        key=lambda eintrag: farbton(
            eintrag["Farbe"]["Wert"]
        )
    )

    # 3. Index setzen und Identifikatoren sammeln
    ids = []

    for index, daten in enumerate(filter_liste):
        daten["Index"] = index
        ids.append(daten["Identifikator"])


    # 5. Bestehende Konfiguration laden
    if config_file.exists() and config_file.stat().st_size > 0:
        with config_file.open("r", encoding="utf-8") as file:
            config = json.load(file)
    else:
        config = {}

    # 6. Nur den aktuellen Filter aktualisieren
    config.setdefault("Filter", {})
    config["Filter"][filter_name] = ids

    # 7. Konfiguration speichern
    with config_file.open("w", encoding="utf-8") as file:
        json.dump(
            config,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Filter '{filter_name}' erfolgreich aktualisiert.")
    print(f"{len(ids)} Einträge sortiert und indiziert.")


# Beispielaufruf
filter_sortieren("Farbe", "data/farben_filter.json")
