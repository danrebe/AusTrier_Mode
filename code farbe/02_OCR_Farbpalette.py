"""
Speichert die Farben, die die Wien-Museum-Online-Sammlung zu jedem Bild angibt,
für alle Modebilder aus dem Kulturpool lokal ab.

Ablauf:
1. Kulturpool-API: alle Objekte mit edmType = IMAGE und Schlagwort "Modebilder" holen
   (dieselbe Auswahl wie die Suche auf kulturpool.at, ca. 2021 Bilder).
2. Für jedes Objekt die Originalseite beim Wien Museum (Feld isShownAt) aufrufen
   und die dort angegebenen Hex-Farben auslesen.
3. Farben in results/farben.csv speichern (uuid, wm_objekt_id, inventarnummer, hex, r, g, b).

Das Skript kann jederzeit abgebrochen und neu gestartet werden:
Objekte, die schon in results/farben.csv stehen, werden übersprungen.
"""

import os
import re
import csv
import time
import requests
from urllib.parse import urljoin
from tqdm import tqdm

# --- EINSTELLUNGEN ---
TEST_LIMIT = None  # Testlauf: nach so vielen Bildern stoppen. None = alle Bilder
API_URL = "https://api.kulturpool.at/v2/search"
FILTER = "edmType:=IMAGE && subject:=Modebilder"

OUTPUT_FOLDER = "results"
FARBEN_CSV = os.path.join(OUTPUT_FOLDER, "farben.csv")

PAUSE_SEKUNDEN = 1.0  # Pause zwischen den Seitenaufrufen beim Wien Museum

HEADERS = {"User-Agent": "Mozilla/5.0 (Farbanalyse Modebilder, Forschungsprojekt)"}



# ---------------------------------------------------------------------------
# 1. Objektliste aus der Kulturpool-API
# ---------------------------------------------------------------------------
def objekte_holen():
    objekte = []
    seite = 1
    while True:
        params = {
            "q": "*",
            "filter_by": FILTER,
            "per_page": 250,  # Maximum der API
            "page": seite,
            "include_fields": "uuid,title,identifier,dataProvider,isShownAt",
            "facet_by": "",   # Facetten abschalten, werden nicht gebraucht
        }
        response = requests.get(API_URL, params=params, timeout=60)
        response.raise_for_status()
        daten = response.json()

        if seite == 1:
            print(f"Kulturpool meldet {daten.get('found')} Objekte.")

        hits = daten.get("hits", [])
        if not hits:
            break
        objekte.extend(hit["document"] for hit in hits)

        if len(objekte) >= daten.get("found", 0):
            break
        seite += 1
        time.sleep(0.5)

    print(f"{len(objekte)} Objekte aus der API geladen.")
    return objekte


# ---------------------------------------------------------------------------
# 2. Farben von der Wien-Museum-Seite
# ---------------------------------------------------------------------------
def farben_aus_html(html):
    """Liest die Hex-Farben aus den Farbsuche-Links der Objektseite (?colors=%23ce709d)."""
    hexwerte = re.findall(r"colors=(?:%23|#)([0-9a-fA-F]{6})", html)
    return list(dict.fromkeys(h.lower() for h in hexwerte))  # Duplikate raus, Reihenfolge bleibt


def farben_holen(session, url):
    """
    Gibt (farben, tatsächlich_gelesene_url) zurück.
    Kulturpool liefert Kurzadressen wie .../objekt/46971/. Stehen dort keine Farben,
    wird die vollständige Objektseite (.../objekt/46971-titel-des-bildes/) gesucht und gelesen.
    """
    response = session.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    farben = farben_aus_html(response.text)
    if farben:
        return farben, response.url

    objekt_id = wm_objekt_id(url)
    if objekt_id:
        muster = rf"(?:https?://sammlung\.wienmuseum\.at)?/(?:objekt|en/object)/{objekt_id}-[A-Za-z0-9\-]+/?"
        treffer = re.search(muster, response.text)
        if treffer:
            volle_url = urljoin("https://sammlung.wienmuseum.at/", treffer.group(0))
            time.sleep(PAUSE_SEKUNDEN)
            response = session.get(volle_url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            farben = farben_aus_html(response.text)
            if farben:
                return farben, response.url

    # Für die Fehlersuche: HTML der ersten Seite ohne Farben aufheben
    debug_pfad = os.path.join(OUTPUT_FOLDER, "debug_seite_ohne_farben.html")
    if not os.path.exists(debug_pfad):
        with open(debug_pfad, "w", encoding="utf-8") as f:
            f.write(response.text)
    return [], response.url


def hex_zu_rgb(hexwert):
    return tuple(int(hexwert[i:i + 2], 16) for i in (0, 2, 4))


def wm_objekt_id(url):
    treffer = re.search(r"/(?:objekt|object)/(\d+)", url)
    return treffer.group(1) if treffer else ""


# ---------------------------------------------------------------------------
# Fortsetzen nach Abbruch
# ---------------------------------------------------------------------------
def erledigte_laden():
    """Alle Objekte, die schon Farben in farben.csv haben, gelten als erledigt."""
    erledigt = set()
    if os.path.exists(FARBEN_CSV):
        with open(FARBEN_CSV, newline="", encoding="utf-8") as f:
            for zeile in csv.DictReader(f):
                erledigt.add(zeile["uuid"])
    return erledigt


def csv_oeffnen(pfad, kopfzeile):
    neu = not os.path.exists(pfad)
    f = open(pfad, "a", newline="", encoding="utf-8")
    writer = csv.writer(f)
    if neu:
        writer.writerow(kopfzeile)
    return f, writer


def zaehler_kurz(zaehler):
    """Kurze Anzeige rechts neben dem Fortschrittsbalken."""
    return {"ok": zaehler["ok"], "ohne": zaehler["keine_farben"],
            "fremd": zaehler["kein_wienmuseum_link"], "err": zaehler["fehler"]}


# ---------------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------------
def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    objekte = objekte_holen()
    erledigt = erledigte_laden()
    offen = [d for d in objekte if d["uuid"] not in erledigt]
    print(f"{len(erledigt)} bereits erledigt, {len(offen)} noch offen.")
    if TEST_LIMIT:
        offen = offen[:TEST_LIMIT]
        print(f"TESTLAUF: Es werden nur {len(offen)} Bilder verarbeitet.")
    print()

    f_farben, farben_writer = csv_oeffnen(
        FARBEN_CSV,
        ["uuid", "wm_objekt_id", "inventarnummer", "hex", "r", "g", "b"],
    )

    zaehler = {"ok": 0, "keine_farben": 0, "kein_wienmuseum_link": 0, "fehler": 0}
    session = requests.Session()
    fortschritt = tqdm(offen, desc="Farben laden", unit="Bild")

    try:
        for i, doc in enumerate(fortschritt, start=1):
            uuid = doc["uuid"]
            url = doc.get("isShownAt", "") or ""
            inventarnummer = "; ".join(doc.get("identifier", []))

            if "wienmuseum.at" not in url:
                zaehler["kein_wienmuseum_link"] += 1
                fortschritt.set_postfix(zaehler_kurz(zaehler))
                continue

            try:
                farben_hex, gelesene_url = farben_holen(session, url)
            except requests.RequestException as e:
                zaehler["fehler"] += 1
                tqdm.write(f"Fehler: {url} ({e})")
                fortschritt.set_postfix(zaehler_kurz(zaehler))
                time.sleep(PAUSE_SEKUNDEN)
                continue

            if not farben_hex:
                tqdm.write(f"Keine Farben: {gelesene_url}")
                zaehler["keine_farben"] += 1
            else:
                objekt_id = wm_objekt_id(url)
                farben_rgb = [hex_zu_rgb(h) for h in farben_hex]
                for h, (r, g, b) in zip(farben_hex, farben_rgb):
                    farben_writer.writerow([uuid, objekt_id, inventarnummer, f"#{h}", r, g, b])
                zaehler["ok"] += 1

            # Sofort auf die Platte schreiben, damit bei Abbruch nichts verloren geht
            f_farben.flush()

            fortschritt.set_postfix(zaehler_kurz(zaehler))
            time.sleep(PAUSE_SEKUNDEN)

    except KeyboardInterrupt:
        tqdm.write("\nAbgebrochen. Beim nächsten Start geht es an dieser Stelle weiter.")
    finally:
        fortschritt.close()
        f_farben.close()

    print(f"\nErgebnis dieses Laufs: {zaehler}")
    print(f"Farben: {FARBEN_CSV}")
    if zaehler["fehler"] or zaehler["keine_farben"]:
        print("Objekte mit Fehler oder ohne Farben werden beim nächsten Start erneut versucht.")


if __name__ == "__main__":
    main()