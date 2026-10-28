"""
This script extracts the silhouette of a dress from an image.
- Input: Images of (in our case historic) fashion images
- Based on: Grounded Sam (Grounding DINO (for object detection) + Segment Anything Model (for segmentation / masking))
- Returns: Silhouette mask (white dress on black background)
"""

# imports
import requests
import pandas as pd
import json
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


### Paths and Parameters
SCALE = 0.7                # make resolution lower (for faster processing)
PROMPT = "dress."          # prompt for DINO object detection
BOX_THRESHOLD = 0.35       # lower -> more objects detected, higher -> stricter
TEXT_THRESHOLD = 0.25
USE_ONLY_BEST_BOX = True   # True: only the object most safely identified as dress, False: all detected objects
DEVICE = "cpu"

data = pd.read_csv('../data/uuid.csv')
data = list(data["uuid"])

base_url = "https://api.kulturpool.at/v2/object?id="


### Load models

# Load DINO
dino_id = "IDEA-Research/grounding-dino-tiny"
dino_processor = AutoProcessor.from_pretrained(dino_id)
dino_model = AutoModelForZeroShotObjectDetection.from_pretrained(dino_id).to(DEVICE)

# Load SAM
sam_processor = SamProcessor.from_pretrained("facebook/sam-vit-base")
sam_model = SamModel.from_pretrained("facebook/sam-vit-base").to(DEVICE)


### Download images and extract silhouettes

#  Download images using API
for uuid in data:
    path_url = f"{uuid}"
    url = base_url + path_url
    print(url)
    meta = requests.get(url).content
    meta_dict = json.loads(meta)
    img_url = meta_dict["metadata"]["isShownBy"]["id"]
    img = requests.get(img_url).content

    # Convert image to OpenCV format
    img = cv2.imdecode(
        np.frombuffer(img, np.uint8),
        cv2.IMREAD_COLOR
    )

    # Resizing
    height, width = img.shape[:2]
    img_resized = cv2.resize(
        img,
        (int(width * SCALE), int(height * SCALE)),
        interpolation=cv2.INTER_AREA
    )

    # Convert image to PIL format
    image = Image.fromarray(cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB))
    print(f"Image loaded: {image.size}")


    # 1) Grounding DINO: Object identification (via text -> bounding box)
    print("Louding Grounding DINO ...")

    inputs = dino_processor(images=image, text=PROMPT, return_tensors="pt").to(DEVICE)
    with torch.no_grad():
        outputs = dino_model(**inputs)

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

    # if no dress is found, write uuid to not_found.txt and continue with next image
    if len(boxes) == 0:
        print("No dress found. Try lowering BOX_TRESHOLD or using a different prompt.")
        with open("not_found.txt", "a") as f:
            f.write(f"{uuid}\n")
        continue

    print(f"{len(boxes)} boxes found, scores: {[round(s.item(), 2) for s in scores]}")

    # choose best box (if USE_ONLY_BEST_BOX = True)
    if USE_ONLY_BEST_BOX:
        best = scores.argmax().item()
        boxes = boxes[best: best + 1]


    # 2) SAM: Segment the dress objects (via box -> mask)
    print("Loading SAM ...")

    sam_inputs = sam_processor(
        image, input_boxes=[boxes.tolist()], return_tensors="pt"
    ).to(DEVICE)
    with torch.no_grad():
        sam_outputs = sam_model(**sam_inputs)

    masks = sam_processor.image_processor.post_process_masks(
        sam_outputs.pred_masks.cpu(),
        sam_inputs["original_sizes"].cpu(),
        sam_inputs["reshaped_input_sizes"].cpu(),
    )[0]  # form: (number of boxes, 3, H, W)
    iou = sam_outputs.iou_scores.cpu()[0]  # form: (number of boxes, 3)

    # Get final mask by choosing best of 3 masks proposed by SAM and combine with others (only relevant for USE_ONLY_BEST_BOX = False)
    final_mask = np.zeros(image.size[::-1], dtype=bool)
    for i in range(masks.shape[0]):
        best_idx = iou[i].argmax().item()
        final_mask |= masks[i, best_idx].numpy().astype(bool)

    # 3) Save final mask as a silhouette image
    silhouette = Image.fromarray((final_mask * 255).astype(np.uint8))
    silhouette.save(f"sil_out/{uuid}.png")