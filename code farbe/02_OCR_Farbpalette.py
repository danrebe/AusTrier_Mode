import os
import numpy as np
import cv2
from sklearn.cluster import KMeans

# Globale Variablen für die Farbpalette
clusters = 5  # Anzahl der Farben in der Palette
margin = 5    # Abstand zwischen den Farben im Farbbalken
offset = 0    # Offset für die Anzahl der Cluster

def create_colour_palette(image_path, output_folder):
    # Lesen des Bildes mit OpenCV
    image = cv2.imread(image_path)
    if image is None:
        print(f"\nFehler: Konnte Bild nicht laden oder Datei ist beschädigt: {image_path}")
        return

    # Bild ins RGB-Format konvertieren
    image_copy = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Umwandeln des Bildes in ein 2D-Array von Pixeln
    pixelImage = image_copy.reshape((image_copy.shape[0] * image_copy.shape[1], 3))

    # Anwenden des Kmeans-Algorithmus, um die Farben zu gruppieren
    clt = KMeans(n_clusters=clusters + offset, n_init=10)
    clt.fit(pixelImage)

    # Erstellen des Histogramms der Clusterzentren
    hist = centroid_histogram(clt)

    # Erstellen des Farbverlaufs für die Farbpalette
    bar = plot_colors(hist, clt.cluster_centers_)

    # Anpassen der Größe des Farbverlaufs
    bar = cv2.resize(bar, (100, 50))  # Festlegen der Breite auf 100 Pixel und Höhe auf 50 Pixel

    # Speichern der Farbpalette im results-Ordner
    palette_file_path = os.path.join(output_folder, f"{os.path.splitext(os.path.basename(image_path))[0]}_palette.png")
    cv2.imwrite(palette_file_path, bar)
    print(f"Farbpalette erfolgreich gespeichert unter: {palette_file_path}")

# Funktion zur Erstellung des Histogramms der Clusterzentren
def centroid_histogram(clt):
    numLabels = np.arange(0, len(np.unique(clt.labels_)) + 1)
    (hist, _) = np.histogram(clt.labels_, bins=numLabels)
    hist = hist.astype("float")
    hist /= hist.sum()
    return hist

# Funktion zur Erstellung des Farbverlaufs
def plot_colors(hist, centroids):
    bar = np.zeros((50, 300, 3), dtype="uint8")
    startX = 0

    centroids = sorted(centroids, key=lambda x: sum(x))

    excluded_ranges = [ 
        ((245, 230, 201), (255, 255, 255)) # Grober Ausschluss Hintergrundfarben
    ]

    # Farben vorab filtern, damit das Layout dynamisch an gültige Farben angepasst wird
    valid_colors = []
    for (percent, color) in zip(hist, centroids[offset:]):
        exclude_color = False
        for lower_bound, upper_bound in excluded_ranges:
            if all(lower_bound[i] <= color[i] <= upper_bound[i] for i in range(3)):
                exclude_color = True
                break
        if not exclude_color:
            valid_colors.append(color)

    num_valid = len(valid_colors)
    if num_valid == 0:
        return bar

    for color in valid_colors:
        new_length = 300 - margin * (num_valid - 1) if num_valid > 1 else 300
        endX = startX + new_length / num_valid
        cv2.rectangle(bar, (int(startX), 0), (int(endX), 50),
                      color.astype("uint8").tolist(), -1)
        cv2.rectangle(bar, (int(endX), 0), (int(endX + margin), 50),
                      (255, 255, 255), -1)
        startX = endX + margin

    return bar

# Hauptfunktion
def main():
    # --- HIER DEN PFAD ZU DEINEM BILD ANGEBEN ---
    image_path = r"ordner\Wien Museum Online Sammlung M 30237.jpg"  # Beispiel: "C:/Bilder/mein_foto.jpg" oder einfach "bild.jpg"

    # Prüfen, ob die Datei existiert
    if not os.path.exists(image_path):
        print(f"Fehler: Die Datei '{image_path}' wurde nicht gefunden.")
        return

    # Erstellen des Ergebnisordners, falls er nicht existiert
    output_folder = "results/"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    print(f"Starte Farbanalyse für: {image_path}...")
    create_colour_palette(image_path, output_folder)
    print("Vorgang abgeschlossen.")

if __name__ == "__main__":
    main()