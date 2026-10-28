from PIL import Image
from rembg import remove
import numpy as np
import cv2
from matplotlib import pyplot as plt


def remove_background_rembg(img):
    img_in = Image.open(img)
    img_out = remove(img_in)
    img_out.save("out.png")

def remove_white(img):
    image = Image.open(img)
    image_data = image.load()
    height, width = image.size
    for loop1 in range(height):
        for loop2 in range(width):
            r, g, b = image_data[loop1, loop2]
            image_data[loop1, loop2] = 0, g, b
    image.save('changed.png')


def remove_background_cv(img):
    img_in = cv2.imread(img)

    if img_in is None:
        raise ValueError(f"Bild konnte nicht geladen werden: {img}")

    height, width = img_in.shape[:2]

    # Rechteck über fast das gesamte Bild
    margin = 1
    rect = (margin, margin, width - 2 * margin, height - 2 * margin)

    mask = np.zeros((height, width), np.uint8)
    background_model = np.zeros((1, 65), np.float64)
    foreground_model = np.zeros((1, 65), np.float64)

    cv2.grabCut(
        img_in,
        mask,
        rect,
        background_model,
        foreground_model,
        5,
        cv2.GC_INIT_WITH_RECT
    )

    # Vordergrundpixel extrahieren
    mask_2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')

    image_segmented = img_in * mask_2[:, :, np.newaxis]

    plt.imshow(cv2.cvtColor(image_segmented, cv2.COLOR_BGR2RGB))

    plt.show()

def binarize(path):
    img = cv2.imread(path, cv.IMREAD_GRAYSCALE)
    assert img is not None, "file could not be read, check with os.path.exists()"
    ret, thresh1 = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY)
    plt.imshow(thresh1, 'gray', vmin=0, vmax=255)
    plt.show()

binarize()
#remove_white("test_mode.webp")
#remove_background_cv("changed.png")