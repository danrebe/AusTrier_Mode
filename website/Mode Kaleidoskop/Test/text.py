
import json
from pathlib import Path

# Eingabedatei mit allen JSON-Objekten
input_file = Path("data/text.json")

# Ausgabeordner für die einzelnen JSON-Dateien
output_dir = Path("data")
output_dir.mkdir(parents=True, exist_ok=True)

# JSON-Datei einlesen
with input_file.open("r", encoding="utf-8") as file:
    data = json.load(file)

# Jedes Objekt in eine eigene Datei schreiben
for item in data:
    identifier = item.get("Identifikator")

    if not identifier:
        print("Übersprungen: Identifikator fehlt.")
        continue

    # Ungültige Zeichen im Dateinamen vermeiden
    safe_identifier = "".join(
        c for c in identifier
        if c.isalnum() or c in ("-", "_")
    )

    if not safe_identifier:
        print(f"Übersprungen: Ungültiger Identifikator: {identifier}")
        continue

    output_file = output_dir / f"{safe_identifier}.json"

    with output_file.open("w", encoding="utf-8") as file:
        json.dump(item, file, indent=4, ensure_ascii=False)

    print(f"Erstellt: {output_file}")

print("Aufteilung abgeschlossen!")
