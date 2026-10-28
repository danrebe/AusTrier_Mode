"""
Silhouette similarity calculation:
- This script calculates similarities between dress silhouette shapes. Similarities are based on silhouette width (normalized by height).
- Input: Binarized images (masks) of silhouettes - white dress on black background
- Output: A JSON-style list of dictionaries for backend processing (contain uuids + top uuids similar by silhouette)
"""

# Imports
from glob import glob
import os
import cv2
import numpy as np
from colorlog import exception
from numpy.lib.stride_tricks import sliding_window_view
from tqdm import tqdm
from typing import Literal
import json

# Paths and parameters
path = sorted(glob("sil_out/*.png"))
print(path)

NUM_ROWS = 100  # Number of rows/height that will be used for normalization
TOP_N = 10  # Number of top similar silhouettes to output
SMOOTH_SIZE = 5  # Median-Filter-Breite (in Profilzeilen) gegen Arme/Rauschen, 1 = aus
METRIC = "euclidean"  # "euclidean", "manhattan" (L1), "cosine"


#Functions

def median_filter_1d(x, size):
    """ 1D-Median-Filter mit Randwerten als Fortsetzung (ersetzt scipy.ndimage.median_filter) """
    pad = size // 2
    padded = np.pad(x, (pad, size - 1 - pad), mode="edge")
    return np.median(sliding_window_view(padded, size), axis=1)


def pairwise_distances(profiles, metric: Literal["cosine", "euclidean", "manhattan"]):
    """ Calculate distance matrix between all profiles"""
    #Initalizing distance matrix D with zeros
    n = len(profiles)
    D = np.zeros((n, n), dtype=np.float64)

    # Choosing distance measure and calculate
    if metric == "cosine":
        normed = profiles / (np.linalg.norm(profiles, axis=1, keepdims=True) + 1e-12)
    for i in range(n):
        if metric == "euclidean":
            D[i] = np.linalg.norm(profiles - profiles[i], axis=1)
        elif metric == "manhattan":
            D[i] = np.abs(profiles - profiles[i]).sum(axis=1)
        elif metric == "cosine":
            D[i] = 1.0 - normed @ normed[i]
        else:
            raise ValueError(f"Unknown METRIC: {metric}")
    return D


def clean_mask(im):
    """Binarize, keep biggest components, fill holes"""
    mode = cv2.THRESH_BINARY
    _, bw = cv2.threshold(im, 127, 255, mode)

    contours, _ = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if len(contours) == 0:
        raise Exception("No contours found")

    cnt = max(contours, key=cv2.contourArea)
    filled = np.zeros_like(bw)
    cv2.drawContours(filled, [cnt], -1, 255, thickness=cv2.FILLED)
    return filled


def width_profile(mask, num_rows=100):
    """width of silhouette per row, normalizes on num_rows of dress height"""
    #Calculate height
    ys, xs = np.nonzero(mask)
    y0, y1 = ys.min(), ys.max()
    height = y1 - y0 + 1

    #Calculate width per row using white pixel furthest left and right
    widths = np.zeros(height, dtype=np.float32)
    for k, y in enumerate(range(y0, y1 + 1)):
        row_x = np.nonzero(mask[y])[0]
        if len(row_x) > 0:
            widths[k] = row_x.max() - row_x.min() + 1

    #Normalization using 100 rows per profile using linear interpolation
    src = np.linspace(0, 1, height)
    dst = np.linspace(0, 1, num_rows)
    profile = np.interp(dst, src, widths)

    # Glätten gegen Ausreißer (z.B. abstehende Arme)
    #if SMOOTH_SIZE > 1:
    #    profile = median_filter_1d(profile, SMOOTH_SIZE)

    # Normalizing width profile by height
    profile = profile / height

    return profile.astype(np.float32)


# 1. Read images and calculate profiles
profileDict = {}

for img in path:
    # print(f"Processing file: {img}")

    im = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
    if im is None:
        raise FileNotFoundError(f"Image not found or unreadable: {img}")
    # print(f"Successfully read image: {img}")

    mask = clean_mask(im)
    if mask is None:
        print(f"WARNING: no contour found, skipping {img}")
        continue

    uuid = os.path.basename(img)[:-4]  # Remove the .png in filename
    profileDict[uuid] = width_profile(mask, NUM_ROWS)

# 2. Calculate distance matrix
# Get profiles based on uuids(key)
uuids = list(profileDict.keys())
profiles = np.stack([profileDict[u] for u in uuids])
distMatrix = pairwise_distances(profiles, METRIC)

# 3. Output im gleichen Format wie bei den bisherigen Skripten
distanceList = []

for i, uuid in tqdm(enumerate(uuids)):
    distanceDict = {
        uuid2: float(distMatrix[i, j])
        for j, uuid2 in enumerate(uuids) if j != i
    }
    distanceDict = dict(sorted(distanceDict.items(), key=lambda item: item[1]))
    # print(f"\n \n \n Sorted distances for {uuid}: {distanceDict}", len(distanceDict))

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

json.dump(distanceList, open("distanceList.json", "w"))

#print("\n\n\n", distanceList)
