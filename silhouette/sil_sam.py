"""
Kleid-Silhouette aus einem Modebild extrahieren
Grounding DINO (Text -> Box) + SAM (Box -> Maske)
"""
import sys
import numpy as np
import torch
from PIL import Image
from transformers import (
    AutoProcessor,
    AutoModelForZeroShotObjectDetection,
    SamModel,
    SamProcessor,
)

# ---------- Einstellungen ----------
IMAGE_PATH = "test_mode.png"
PROMPT = "dress."          # klein geschrieben, mit Punkt am Ende! z.B. "dress. skirt."
BOX_THRESHOLD = 0.35       # niedriger = mehr Treffer, höher = strenger
TEXT_THRESHOLD = 0.25
USE_ONLY_BEST_BOX = True   # True: nur das sicherste Kleid, False: alle Treffer
DEVICE = "cpu"             # für ein Bild völlig ausreichend und am stabilsten auf dem Mac
# -----------------------------------

image = Image.open(IMAGE_PATH).convert("RGB")
print(f"Bild geladen: {image.size}")

# 1) Grounding DINO: Text -> Bounding Box
print("Lade Grounding DINO ...")
dino_id = "IDEA-Research/grounding-dino-tiny"
dino_processor = AutoProcessor.from_pretrained(dino_id)
dino_model = AutoModelForZeroShotObjectDetection.from_pretrained(dino_id).to(DEVICE)

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
    sys.exit()

print(f"{len(boxes)} Box(en) gefunden, Scores: {[round(s.item(), 2) for s in scores]}")

if USE_ONLY_BEST_BOX:
    best = scores.argmax().item()
    boxes = boxes[best : best + 1]

# 2) SAM: Box -> Maske
print("Lade SAM ...")
sam_processor = SamProcessor.from_pretrained("facebook/sam-vit-base")
sam_model = SamModel.from_pretrained("facebook/sam-vit-base").to(DEVICE)

sam_inputs = sam_processor(
    image, input_boxes=[boxes.tolist()], return_tensors="pt"
).to(DEVICE)
with torch.no_grad():
    sam_outputs = sam_model(**sam_inputs)

masks = sam_processor.image_processor.post_process_masks(
    sam_outputs.pred_masks.cpu(),
    sam_inputs["original_sizes"].cpu(),
    sam_inputs["reshaped_input_sizes"].cpu(),
)[0]                                   # Form: (Anzahl Boxen, 3, H, W)
iou = sam_outputs.iou_scores.cpu()[0]  # Form: (Anzahl Boxen, 3)

# Pro Box die beste der 3 vorgeschlagenen Masken wählen, dann alle vereinen
final_mask = np.zeros(image.size[::-1], dtype=bool)
for i in range(masks.shape[0]):
    best_idx = iou[i].argmax().item()
    final_mask |= masks[i, best_idx].numpy().astype(bool)

# 3) Ergebnisse speichern
silhouette = Image.fromarray((final_mask * 255).astype(np.uint8))
silhouette.save("silhouette.png")

rgba = np.dstack([np.array(image), (final_mask * 255).astype(np.uint8)])
Image.fromarray(rgba, "RGBA").save("cutout.png")

overlay = np.array(image).copy()
overlay[final_mask] = (0.5 * overlay[final_mask] + 0.5 * np.array([255, 0, 80])).astype(np.uint8)
Image.fromarray(overlay).save("overlay.png")

print("Fertig! Gespeichert: silhouette.png, cutout.png, overlay.png")