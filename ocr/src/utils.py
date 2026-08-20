import cv2
import numpy as np
from typing import Tuple


def preprocess_image(
    img,
    scale_factor: float = 1.5,
    block_size: int = 65,
    constant: int = 13,
):
    """
    Prepare a medical document image for OCR.
    """

    image = np.array(img)

    if len(image.shape) == 3:
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_RGB2GRAY,
        )
    else:
        gray = image

    denoised = cv2.bilateralFilter(
        gray,
        9,
        75,
        75,
    )

    resized = cv2.resize(
        denoised,
        None,
        fx=scale_factor,
        fy=scale_factor,
        interpolation=cv2.INTER_CUBIC,
    )

    if block_size % 2 == 0:
        block_size += 1

    processed_image = cv2.adaptiveThreshold(
        resized,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block_size,
        constant,
    )

    kernel = cv2.getStructuringElement(
        cv2.MORPH_RECT,
        (2, 2),
    )

    processed_image = cv2.morphologyEx(
        processed_image,
        cv2.MORPH_CLOSE,
        kernel,
    )

    return processed_image


def get_optimal_preprocessing_params(
    img,
) -> Tuple[float, int, int]:

    image = np.array(img)

    if len(image.shape) == 3:
        gray = cv2.cvtColor(
            image,
            cv2.COLOR_RGB2GRAY,
        )
    else:
        gray = image

    height, width = gray.shape

    resolution = (
        width * height
    ) / 1_000_000

    if resolution < 2:
        scale_factor = 2.0

    elif resolution < 5:
        scale_factor = 1.5

    else:
        scale_factor = 1.0

    contrast = np.std(gray)

    if contrast < 30:
        block_size = 81

    elif contrast > 80:
        block_size = 49

    else:
        block_size = 65

    if block_size % 2 == 0:
        block_size += 1

    constant = 13

    return (
        scale_factor,
        block_size,
        constant,
    )


def enhance_text_contrast(img):

    if len(img.shape) == 3:
        gray = cv2.cvtColor(
            img,
            cv2.COLOR_RGB2GRAY,
        )
    else:
        gray = img

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8), 
    )

    return clahe.apply(gray)