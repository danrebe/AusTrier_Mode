# distance calculations based on binarized silhouette images (Breitenprofil)
# Benötigt: opencv-python (oder contrib) und numpy (kein scipy nötig)

# imports
from glob import glob
import os
import cv2
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


def median_filter_1d(x, size):
    """ 1D-Median-Filter mit Randwerten als Fortsetzung (ersetzt scipy.ndimage.median_filter) """
    pad = size // 2
    padded = np.pad(x, (pad, size - 1 - pad), mode="edge")
    return np.median(sliding_window_view(padded, size), axis=1)


def pairwise_distances(profiles, metric):
    """ Distanzmatrix zwischen allen Profilen (ersetzt scipy.spatial.distance.cdist) """
    n = len(profiles)
    D = np.zeros((n, n), dtype=np.float64)
    if metric == "cosine":
        normed = profiles / (np.linalg.norm(profiles, axis=1, keepdims=True) + 1e-12)
    for i in range(n):
        if metric == "euclidean":
            D[i] = np.linalg.norm(profiles - profiles[i], axis=1)
        elif metric == "cityblock":
            D[i] = np.abs(profiles - profiles[i]).sum(axis=1)
        elif metric == "cosine":
            D[i] = 1.0 - normed @ normed[i]
        else:
            raise ValueError(f"Unknown METRIC: {metric}")
    return D

# Parameter und Pfade
path = sorted(glob("./data/Silhouetten/*.png"))
print(path)

NUM_ROWS = 100        # Anzahl Zeilen des Profils (normalisiert auf Kleidhöhe)
TOP_N = 10            # Anzahl nächster Nachbarn im Output
INVERT = False        # True, falls das Kleid schwarz auf weißem Hintergrund ist
SMOOTH_SIZE = 5       # Median-Filter-Breite (in Profilzeilen) gegen Arme/Rauschen, 1 = aus
NORMALIZE_BY = "height"  # "height": Breite/Höhe (Seitenverhältnis bleibt erhalten)
                         # "max_width": Breite/maximale Breite (nur Form, nicht Proportion)
METRIC = "euclidean"  # "euclidean", "cityblock" (L1), "cosine"


def clean_mask(im):
    """ Binarisieren, größte Komponente behalten, Löcher füllen """
    mode = cv2.THRESH_BINARY_INV if INVERT else cv2.THRESH_BINARY
    _, bw = cv2.threshold(im, 127, 255, mode)

    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        return None

    cnt = max(contours, key=cv2.contourArea)
    filled = np.zeros_like(bw)
    cv2.drawContours(filled, [cnt], -1, 255, thickness=cv2.FILLED)
    return filled


def width_profile(mask, num_rows=100):
    """ Breite der Silhouette pro Zeile, auf num_rows Zeilen der Kleidhöhe normalisiert """
    ys, xs = np.nonzero(mask)
    y0, y1 = ys.min(), ys.max()
    height = y1 - y0 + 1

    # Pro Zeile Ausdehnung (rechts - links + 1) innerhalb der Bounding Box
    widths = np.zeros(height, dtype=np.float32)
    for k, y in enumerate(range(y0, y1 + 1)):
        row_x = np.nonzero(mask[y])[0]
        if len(row_x) > 0:
            widths[k] = row_x.max() - row_x.min() + 1

    # Auf feste Zeilenzahl resamplen (Höhennormierung)
    src = np.linspace(0, 1, height)
    dst = np.linspace(0, 1, num_rows)
    profile = np.interp(dst, src, widths)

    # Glätten gegen Ausreißer (z.B. abstehende Arme)
    if SMOOTH_SIZE > 1:
        profile = median_filter_1d(profile, SMOOTH_SIZE)

    # Breitennormierung
    if NORMALIZE_BY == "height":
        profile = profile / height
    elif NORMALIZE_BY == "max_width":
        profile = profile / (profile.max() + 1e-9)
    else:
        raise ValueError(f"Unknown NORMALIZE_BY: {NORMALIZE_BY}")

    return profile.astype(np.float32)


# 1. Bilder einlesen und Profile berechnen
profileDict = {}

for img in path:
    print(f"Processing file: {img}")

    im = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
    if im is None:
        raise FileNotFoundError(f"Image not found or unreadable: {img}")
    print(f"Successfully read image: {img}")

    mask = clean_mask(im)
    if mask is None:
        print(f"WARNING: no contour found, skipping {img}")
        continue

    uuid = os.path.basename(img)[:-4]  # Remove the .png in filename
    profileDict[uuid] = width_profile(mask, NUM_ROWS)


# 2. Paarweise Distanzen (komplette Matrix auf einmal)
uuids = list(profileDict.keys())
profiles = np.stack([profileDict[u] for u in uuids])
distMatrix = pairwise_distances(profiles, METRIC)


# 3. Output im gleichen Format wie bei den bisherigen Skripten
distanceList = []

for i, uuid in enumerate(uuids):
    distanceDict = {
        uuid2: float(distMatrix[i, j])
        for j, uuid2 in enumerate(uuids) if j != i
    }
    distanceDict = dict(sorted(distanceDict.items(), key=lambda item: item[1]))
    print(f"\n \n \n Sorted distances for {uuid}: {distanceDict}", len(distanceDict))

    topidList = list(distanceDict.keys())[:TOP_N]
    topdistanceList = list(distanceDict.values())[:TOP_N]

    outputDict = {
        "Type": "Filter",
        "Identifikator": uuid,
        "Similarity": {
            "Tag": topidList,
            "Wert": topdistanceList
        }
    }

    distanceList.append(outputDict)

print("\n\n\n", distanceList)

    

    






