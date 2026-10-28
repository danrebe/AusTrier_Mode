
import json
from pathlib import Path

PROJEKT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJEKT_DIR / "data" / "metadata_jsons" / "json_output"

# Pfad zur Index-Datei
AEHNLICHKEITEN_DATEI = PROJEKT_DIR / "data" / "index.json"

# Index-JSON laden
with open(AEHNLICHKEITEN_DATEI, "r", encoding="utf-8") as f:
    aehnlichkeiten_dokument = json.load(f)

# UUID -> Liste aller Indizes
aehnlichkeiten = aehnlichkeiten_dokument["Filter"]["Silhouette"]
id_to_indices = {}

for index, uuid in enumerate(aehnlichkeiten):
    id_to_indices.setdefault(uuid, []).append(index)

# Alle Metadaten-JSONs verarbeiten
for datei in DATA_DIR.glob("*.json"):
    with open(datei, "r", encoding="utf-8") as f:
        data = json.load(f)

    # UUID aus den Metadaten
    identifikator = data["id"]

    if identifikator in id_to_indices:
        data.setdefault("Filter", {})["Silhouette"] = (
            id_to_indices[identifikator]
        )
    else:
        print(f"ID nicht gefunden: {identifikator} ({datei.name})")
        continue

    # Geänderte Metadaten speichern
    with open(datei, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(
        f"Aktualisiert: {datei.name} "
        f"(Indizes: {id_to_indices[identifikator]})"
    )
