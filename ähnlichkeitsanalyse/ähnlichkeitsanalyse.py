import csv
import time
import requests

# Konfiguration
API_URL = "https://api.kulturpool.at/v2/similar"
input_filename = "uuid.csv"
results_data = []

source_ids = []

# 1. IDs aus der Datei einlesen
print(f"Lese IDs aus '{input_filename}' ein...")
try:
  with open(input_filename, mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
      uuid = row.get("uuid", "").strip()
      if uuid:
        source_ids.append(uuid)

  print(f"{len(source_ids)} IDs insgesamt geladen.")

  # Test-Modus: Nur die ersten 10 IDs verwenden
  source_ids = source_ids[:2300]
  print(f"-> Testlauf gestartet mit den ersten {len(source_ids)} IDs.\n")

except FileNotFoundError:
  print(
      f"Fehler: Die Datei '{input_filename}' wurde nicht gefunden. Bitte"
      " prüfen."
  )
  source_ids = []

# 2. Ähnlichkeitssuche für die Test-IDs durchführen
if source_ids:
  for source_id in source_ids:
    params = {
        "id": source_id,
        "on": "image",  # Visuelle Ähnlichkeit
        "per_page": 10,  # Top 5 Treffer
    }

    try:
      response = requests.get(API_URL, params=params)

      if response.status_code == 200:
        data = response.json()
        hits = data.get("hits", [])

        # Details für jeden Treffer extrahieren (ID, Distanz)
        matches = []
        for hit in hits:
          doc = hit.get("document", {})
          matches.append({
              "id": doc.get("id"),
              "distance": hit.get("vector_distance"),
          })

        results_data.append({"source_id": source_id, "matches": matches})
        print(f"[Erfolg] {source_id} -> {len(matches)} ähnliche gefunden")

      else:
        print(
            f"[Fehler {response.status_code}] Bei ID {source_id}:"
            f" {response.text}"
        )

    except Exception as e:
      print(f"[Exception] Fehler bei ID {source_id}: {e}")

    time.sleep(0.2)

  # 3. Erweiterte Ergebnisse in eine CSV-Datei exportieren
  output_filename = "aehnlichkeiten_values_top10.csv"
  with open(output_filename, mode="w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)

    # Header mit ID, Titel und Distanz für alle 5 Matches
    header = ["source_id"]
    for i in range(1, 6):
      header.extend(
          [f"sim_{i}_id", f"sim_{i}_vector_distance"]
      )
    writer.writerow(header)

    # Zeilen schreiben
    for row in results_data:
      line = [row["source_id"]]
      matches = row["matches"]

      # Für jeden der 5 möglichen Slots Daten schreiben (oder leer lassen, falls weniger da sind)
      for i in range(5):
        if i < len(matches):
          line.extend([
              matches[i]["id"],
              matches[i]["distance"],
          ])
        else:
          line.extend(["", "", ""])  # Leer auffüllen

      writer.writerow(line)

  print(
      f"\nTest beendet! Erweiterte Ergebnisse wurden in '{output_filename}'"
      " gespeichert."
  )