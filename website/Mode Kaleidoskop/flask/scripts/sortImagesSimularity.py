import json
from pathlib import Path

PROJEKT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = PROJEKT_DIR / "data"
datei = DATA_DIR / "distanceList.json"

with open(datei, "r", encoding="utf-8") as file:
    data = json.load(file)

# Schneller Zugriff auf Objekte über ihre ID
objekte = {
    obj["Identifikator"]: obj
    for obj in data
}

besuchte_ids = set()
sortierte_ids = []

aktuelle_id = data[0]["Identifikator"] if data else None

while aktuelle_id is not None:

    if aktuelle_id in besuchte_ids:
        break

    besuchte_ids.add(aktuelle_id)
    sortierte_ids.append(aktuelle_id)

    obj = objekte[aktuelle_id]
    tags = obj.get("Simularity", {}).get("Tag", [])
    werte = obj.get("Simularity", {}).get("Wert", [])

    kandidaten = [
        (tag_id, wert)
        for tag_id, wert in zip(tags, werte)
        if tag_id in objekte and tag_id not in besuchte_ids
    ]

    if kandidaten:
        aktuelle_id = min(kandidaten, key=lambda x: x[1])[0]
    else:
        aktuelle_id = next(
            (
                item["Identifikator"]
                for item in data
                if item["Identifikator"] not in besuchte_ids
            ),
            None
        )

print(sortierte_ids)

config_file = DATA_DIR / "index.json"

# Bestehende Config laden
if config_file.exists() and config_file.stat().st_size > 0:
    with config_file.open("r", encoding="utf-8") as file:
        config = json.load(file)
else:
    config = {}

# Sortierte IDs hinzufügen
config["Silhouette"] = sortierte_ids

# Config speichern
with config_file.open("w", encoding="utf-8") as file:
    json.dump(config, file, indent=4, ensure_ascii=False)