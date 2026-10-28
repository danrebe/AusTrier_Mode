import requests
import pandas as pd
import os
import json
import sys
import numpy as np
import torch
import cv2
from PIL import Image
from transformers import (
    AutoProcessor,
    AutoModelForZeroShotObjectDetection,
    SamModel,
    SamProcessor,
)

# ---------- Einstellungen ----------
SCALE = 0.7
IMAGE_PATH = "/temp/out.jpg"
PROMPT = "dress."          # klein geschrieben, mit Punkt am Ende! z.B. "dress. skirt."
BOX_THRESHOLD = 0.35       # niedriger = mehr Treffer, höher = strenger
TEXT_THRESHOLD = 0.25
USE_ONLY_BEST_BOX = True   # True: nur das sicherste Kleid, False: alle Treffer
DEVICE = "cpu"             # für ein Bild völlig ausreichend und am stabilsten auf dem Mac
# -----------------------------------
data = pd.read_csv('../data/uuid.csv')
data = list(data["uuid"])
data = data[1364:]
#print(data)

base_url = "https://api.kulturpool.at/v2/object?id="

#Load Dino
dino_id = "IDEA-Research/grounding-dino-tiny"
dino_processor = AutoProcessor.from_pretrained(dino_id)
dino_model = AutoModelForZeroShotObjectDetection.from_pretrained(dino_id).to(DEVICE)

#Load SAM
sam_processor = SamProcessor.from_pretrained("facebook/sam-vit-base")
sam_model = SamModel.from_pretrained("facebook/sam-vit-base").to(DEVICE)

for uuid in data:
    path_url = f"{uuid}"
    url = base_url + path_url
    print(url)
    meta = requests.get(url).content
    meta_dict = json.loads(meta)
    img_url = meta_dict["metadata"]["isShownBy"]["id"]
    img = requests.get(img_url).content

    img = cv2.imdecode(
        np.frombuffer(img, np.uint8),
        cv2.IMREAD_COLOR
    )


    height, width = img.shape[:2]

    img_resized = cv2.resize(
        img,
        (int(width * SCALE), int(height * SCALE)),
        interpolation=cv2.INTER_AREA
    )

    #cv2.imwrite(IMAGE_PATH, img_resized)

    image = Image.fromarray(cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB))
    #image = Image.open(IMAGE_PATH).convert("RGB")
    print(f"Bild geladen: {image.size}")

    # 1) Grounding DINO: Text -> Bounding Box
    print("Lade Grounding DINO ...")


    inputs = dino_processor(images=image, text=PROMPT, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        outputs = dino_model(**inputs)

    # Der Parametername unterscheidet sich je nach transformers-Version
    try:
        results = dino_processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            threshold=BOX_THRESHOLD,
            text_threshold=TEXT_THRESHOLD,
            target_sizes=[image.size[::-1]],
        )[0]
    except TypeError:
        results = dino_processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            box_threshold=BOX_THRESHOLD,
            text_threshold=TEXT_THRESHOLD,
            target_sizes=[image.size[::-1]],
        )[0]

    boxes = results["boxes"]
    scores = results["scores"]

    if len(boxes) == 0:
        print("Kein Kleid gefunden. Versuche BOX_THRESHOLD zu senken (z.B. 0.25) "
              "oder einen anderen PROMPT.")
        with open("not_found.txt", "a") as f:
            f.write(f"{uuid}\n")
        continue

    print(f"{len(boxes)} Box(en) gefunden, Scores: {[round(s.item(), 2) for s in scores]}")

    if USE_ONLY_BEST_BOX:
        best = scores.argmax().item()
        boxes = boxes[best: best + 1]

    # 2) SAM: Box -> Maske
    print("Lade SAM ...")


    sam_inputs = sam_processor(
        image, input_boxes=[boxes.tolist()], return_tensors="pt"
    ).to(DEVICE)
    with torch.no_grad():
        sam_outputs = sam_model(**sam_inputs)

    masks = sam_processor.image_processor.post_process_masks(
        sam_outputs.pred_masks.cpu(),
        sam_inputs["original_sizes"].cpu(),
        sam_inputs["reshaped_input_sizes"].cpu(),
    )[0]  # Form: (Anzahl Boxen, 3, H, W)
    iou = sam_outputs.iou_scores.cpu()[0]  # Form: (Anzahl Boxen, 3)

    # Pro Box die beste der 3 vorgeschlagenen Masken wählen, dann alle vereinen
    final_mask = np.zeros(image.size[::-1], dtype=bool)
    for i in range(masks.shape[0]):
        best_idx = iou[i].argmax().item()
        final_mask |= masks[i, best_idx].numpy().astype(bool)

    # 3) Ergebnisse speichern
    silhouette = Image.fromarray((final_mask * 255).astype(np.uint8))
    silhouette.save(f"sil_out/{uuid}.png")