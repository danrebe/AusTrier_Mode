from PIL import Image
from rembg import remove
import numpy as np
import cv2


def remove_background_rembg(img):
    img_in = Image.open(img)
    img_out = remove(img_in)
    img_out.save("out.png")


def remove_background_cv(img):
    img_in = cv2.imread(img)
    height, width = img_in.shape[:2]

    # 0 = sicherer Hintergrund
    # 1 = sicherer Vordergrund
    # 2 = möglicher Hintergrund
    # 3 = möglicher Vordergrund

    mask = np.full(
        (height, width),
        cv2.GC_PR_FGD,
        dtype=np.uint8
    )

    background_model = np.zeros((1,65), np.float64)
    foreground_model = np.zeros((1,65), np.float64)

    cv2.grabCut(
        img_in,
        mask,
        None,
        background_model,
        foreground_model,
        5,
        cv2.GC_INIT_WITH_MASK
    )

    mask_final = np.where(
        (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD),
        255,
        0
    ).astype(np.uint8)

    result = cv2.cvtColor(img_in, cv2.COLOR_BGR2BGRA)
    result[:, :, 3] = mask_final

    return result


remove_background_cv("test_mode.webp")