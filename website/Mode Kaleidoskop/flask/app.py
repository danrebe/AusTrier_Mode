from flask import Flask, render_template, jsonify, request, url_for
import scripts.manageImages as im
from random import randint
import requests
import shutil
from pathlib import Path
import json

app = Flask(__name__)

# --------------------------------------------------
# Pfade
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
IDS_DATEI = BASE_DIR / "ids.json"
BILD_ORDNER = BASE_DIR / "static" / "images"


# --------------------------------------------------
# IDs speichern und laden
# --------------------------------------------------

def speichere_ids(ids):
    """Speichert die IDs in ids.json."""
    try:
        IDS_DATEI.parent.mkdir(parents=True, exist_ok=True)

        with open(IDS_DATEI, "w", encoding="utf-8") as datei:
            json.dump(ids, datei, ensure_ascii=False, indent=4)

        print(f"IDs gespeichert: {IDS_DATEI}")
        print(f"Anzahl der IDs: {len(ids)}")

    except (OSError, TypeError) as e:
        print(f"Fehler beim Speichern der IDs: {e}")
        raise


def lade_ids():
    """Lädt die aktuell gespeicherten IDs."""
    if not IDS_DATEI.exists():
        return []

    with open(IDS_DATEI, "r", encoding="utf-8") as datei:
        return json.load(datei)


# --------------------------------------------------
# Bilder verwalten
# --------------------------------------------------

def ordnerAufraeumen():
    """Entfernt alle alten Dateien aus dem Bildordner."""
    BILD_ORDNER.mkdir(parents=True, exist_ok=True)

    for datei in BILD_ORDNER.iterdir():
        if datei.is_file() or datei.is_symlink():
            datei.unlink()
        elif datei.is_dir():
            shutil.rmtree(datei)


def bild_laden(bild_url, index):
    """
    Lädt ein Bild herunter und speichert es unter
    mode-00.webp, mode-01.webp usw.

    True wird nur zurückgegeben, wenn das Speichern
    erfolgreich war.
    """
    BILD_ORDNER.mkdir(parents=True, exist_ok=True)

    try:
        response = requests.get(bild_url, timeout=30)
        response.raise_for_status()

        bild_pfad = BILD_ORDNER / f"mode-{index:02d}.webp"
        bild_pfad.write_bytes(response.content)

        print(f"Bild gespeichert: {bild_pfad}")
        return True

    except (requests.RequestException, OSError, ValueError) as e:
        print(f"Fehler beim Laden des Bildes: {e}")
        return False


def speichere_bilder_mit_ids(ids):
    """
    Lädt Bilder anhand ihrer IDs.

    Nur erfolgreich gespeicherte Bilder werden in die
    Liste aufgenommen. Die Reihenfolge der IDs entspricht
    exakt der Reihenfolge der Bilddateien.
    """
    ordnerAufraeumen()

    erfolgreiche_ids = []
    bilder = []

    for uuid in ids:
        try:
            url = im.loadImage(uuid)

            if not url:
                print(f"Keine URL für ID {uuid}")
                continue

            # Erst nach erfolgreichem Download wird der
            # nächste fortlaufende Index verwendet.
            index = len(erfolgreiche_ids)

            if bild_laden(url, index):
                erfolgreiche_ids.append(uuid)

                bilder.append(
                    url_for(
                        "static",
                        filename=f"images/mode-{index:02d}.webp"
                    )
                )

        except Exception as e:
            print(f"Fehler bei Bild-ID {uuid}: {e}")

    # IDs und Bilder haben nun dieselbe Reihenfolge.
    speichere_ids(erfolgreiche_ids)

    return bilder


# --------------------------------------------------
# Startseite
# --------------------------------------------------

@app.route("/")
def home():
    return render_template("index.html", title="Home")


# --------------------------------------------------
# Sammlung anzeigen
# --------------------------------------------------

@app.route("/sammlung", methods=["GET", "POST"])
def sammlungClicked():
    kategorie = request.args.get("kategorie", "farbe")

    if kategorie == "random":
        kat = ["embedding", "farbe", "silhouette", "accessoires"]
        kategorie = kat[randint(0, len(kat) - 1)]

    filter_mapping = {
        "embedding": "Aehnlichkeiten",
        "farbe": "Farbe",
        "silhouette": "Silhouette",
    }

    if kategorie == "accessoires":
        # Diese Funktion liefert laut bisherigem Code URLs.
        # Die zugehörigen IDs sind hier nicht bekannt.
        urls = im.sucheAccessoires(9)

        ordnerAufraeumen()
        erfolgreiche_urls = []

        for url in urls:
            index = len(erfolgreiche_urls)

            if url and bild_laden(url, index):
                erfolgreiche_urls.append(url)

        # Keine alten IDs für neue Accessoire-Bilder verwenden.
        speichere_ids([])

    elif kategorie in filter_mapping:
        filter_list = filter_mapping[kategorie]

        if kategorie == "embedding":
            index = randint(0, 2000)
        elif kategorie == "farbe":
            index = randint(0, 11200)
        else:
            index = randint(0, 2000)

        ids = im.getImagebyIndex(index, filter_list, 9)
        speichere_bilder_mit_ids(ids)

    else:
        return "Unbekannte Kategorie", 400

    return render_template(
        "sammlung.html",
        title="Sammlung",
        kategorie=kategorie
    )


# --------------------------------------------------
# Daten für ein angeklicktes Bild laden
# --------------------------------------------------

@app.route("/lade_daten", methods=["GET"])
def lade_daten():
    try:
        nummer = int(request.args.get("image_id", "0"))
        kategorie = request.args.get("kategorie", "farbe")

        # Aktuelle IDs laden
        ids = lade_ids()

        if nummer < 0 or nummer >= len(ids):
            return jsonify({
                "fehler": (
                    f"Ungültige Bildnummer {nummer}. "
                    f"Es sind {len(ids)} IDs vorhanden."
                )
            }), 400

        # ID passend zum angeklickten Bild
        uuid = ids[nummer]

        # Metadaten laden
        daten = im.loadImagefull(uuid)

        filter_mapping = {
            "embedding": "Aehnlichkeiten",
            "farbe": "Farbe",
            "silhouette": "Silhouette",
        }

        if kategorie == "accessoires":
            return jsonify({
                "fehler": (
                    "Für Accessoires müssen die IDs den "
                    "Bild-URLs zugeordnet werden."
                )
            }), 400

        filter_list = filter_mapping.get(kategorie)

        if filter_list is None:
            return jsonify({
                "fehler": "Unbekannte Kategorie"
            }), 400

        # Index für die Suche nach ähnlichen Bildern bestimmen
        if kategorie == "embedding":
            index = daten["Filter"]["Aehnlichkeit"]
        else:
            index = daten["Filter"][filter_list][0]

        print(f"Ausgangs-ID: {uuid}")
        print(f"Suchindex: {index}")
        print(f"Kategorie: {kategorie}")

        # Neue IDs ermitteln
        new_ids = im.getImagebyIndex(
            index,
            filter_list,
            9,
            uuid
        )

        # Neue Bilder herunterladen und passende IDs speichern
        bilder = speichere_bilder_mit_ids(new_ids)

        return jsonify({
            "metadaten": daten,
            "bilder": bilder
        })

    except (ValueError, KeyError, IndexError, FileNotFoundError) as e:
        return jsonify({
            "fehler": str(e)
        }), 400

    except Exception as e:
        app.logger.exception("Fehler in /lade_daten")
        return jsonify({
            "fehler": str(e)
        }), 500


# --------------------------------------------------
# Anwendung starten
# --------------------------------------------------

if __name__ == "__main__":
    app.run(debug=True)
