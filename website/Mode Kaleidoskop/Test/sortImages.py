
import json
from pathlib import Path

def filter_sortieren(filter_name, input_dir):
    config_file = Path("data/index.json")
    input_dir = Path(input_dir)

    # 1. Alle Filterdateien einlesen
    filter_liste = []

    for datei in input_dir.glob("*.json"):
        with datei.open("r", encoding="utf-8") as file:
            daten = json.load(file)

        # Dateipfad merken, um die Datei später zu aktualisieren
        filter_liste.append((daten, datei))

    # 2. Nach Farbe.Wert aufsteigend sortieren
    filter_liste.sort(
        key=lambda eintrag: float(eintrag[0]["Farbe"]["Wert"])
    )

    # 3. Index setzen und JSON-Dateien aktualisieren
    ids = []

    for index, (daten, datei) in enumerate(filter_liste):
        daten["Index"] = index
        ids.append(daten["Identifikator"])

        with datei.open("w", encoding="utf-8") as file:
            json.dump(
                daten,
                file,
                indent=4,
                ensure_ascii=False
            )

    # 4. Bestehende Konfiguration laden
    if config_file.exists() and config_file.stat().st_size > 0:
        with config_file.open("r", encoding="utf-8") as file:
            config = json.load(file)
    else:
        config = {}

    # 5. Nur den aktuellen Filter aktualisieren
    config.setdefault("Filter", {})
    config["Filter"][filter_name] = ids

    # 6. Konfiguration speichern
    with config_file.open("w", encoding="utf-8") as file:
        json.dump(
            config,
            file,
            indent=4,
            ensure_ascii=False
        )

    print(f"Filter '{filter_name}' erfolgreich aktualisiert.")
    print(f"{len(ids)} Dateien indiziert und sortiert.")


# Beispielaufruf
filter_sortieren("Farbe", "data/images")
