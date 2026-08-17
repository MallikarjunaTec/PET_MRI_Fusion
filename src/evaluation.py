"""
evaluation.py — Fusion quality evaluation metrics.

Consolidates metric functions from compare_all_fusions.py and
evaluate_fusion.py into importable functions.
"""

import numpy as np
from skimage.metrics import structural_similarity as ssim


# ============================================================
# NORMALIZATION
# ============================================================

def _normalize(image: np.ndarray) -> np.ndarray:
    """Normalize to [0, 1]."""
    image = image.astype(np.float32)
    image = image - np.min(image)
    max_val = np.max(image)
    if max_val > 0:
        image = image / max_val
    return image


# ============================================================
# ENTROPY
# ============================================================

def calculate_entropy(image: np.ndarray) -> float:
    """
    Calculate Shannon entropy of an image.

    Measures the amount of information contained in the image.
    Higher entropy indicates more information content.
    """
    image = _normalize(image)
    histogram, _ = np.histogram(image, bins=256, range=(0, 1))
    probability = histogram / np.sum(histogram)
    probability = probability[probability > 0]
    return float(-np.sum(probability * np.log2(probability)))


# ============================================================
# SSIM
# ============================================================

def calculate_ssim(reference: np.ndarray, fused: np.ndarray) -> float:
    """
    Calculate mean Structural Similarity Index (SSIM) over all axial slices.

    Measures structural similarity between source and fused image.
    Values closer to 1 indicate higher similarity.
    """
    reference = _normalize(reference)
    fused = _normalize(fused)

    scores = []
    for z in range(reference.shape[2]):
        score = ssim(
            reference[:, :, z],
            fused[:, :, z],
            data_range=1.0
        )
        scores.append(score)

    return float(np.mean(scores))


# ============================================================
# STANDARD DEVIATION
# ============================================================

def calculate_std(image: np.ndarray) -> float:
    """
    Calculate standard deviation of image intensity.

    Higher standard deviation indicates greater contrast and
    dynamic range in the fused image.
    """
    image = _normalize(image)
    return float(np.std(image))


# ============================================================
# SPATIAL FREQUENCY
# ============================================================

def calculate_spatial_frequency(image: np.ndarray) -> float:
    """
    Calculate spatial frequency of the image.

    Measures the overall activity level (edge content) in the image.
    Higher spatial frequency indicates more detail preservation.
    """
    image = _normalize(image)

    rf = np.diff(image, axis=0)
    cf = np.diff(image, axis=1)

    rf = np.mean(rf ** 2)
    cf = np.mean(cf ** 2)

    return float(np.sqrt(rf + cf))


# ============================================================
# FULL EVALUATION
# ============================================================

def evaluate_fusion(
    mri: np.ndarray,
    pet: np.ndarray,
    fused: np.ndarray,
) -> dict:
    """
    Compute all quality metrics for a fused image.

    Returns:
        dict with entropy, mri_ssim, pet_ssim, std, spatial_frequency
    """
    return {
        "entropy": calculate_entropy(fused),
        "mri_ssim": calculate_ssim(mri, fused),
        "pet_ssim": calculate_ssim(pet, fused),
        "std": calculate_std(fused),
        "spatial_frequency": calculate_spatial_frequency(fused),
    }


# ============================================================
# METRIC DESCRIPTIONS (for UI tooltips)
# ============================================================

METRIC_DESCRIPTIONS = {
    "entropy": (
        "Measures the amount of information contained in the fused image. "
        "Higher entropy indicates the fused image retains more information "
        "from both source modalities."
    ),
    "mri_ssim": (
        "Structural Similarity Index between MRI and fused image. "
        "Values closer to 1.0 indicate that the fused image preserves "
        "more structural information from the MRI."
    ),
    "pet_ssim": (
        "Structural Similarity Index between PET and fused image. "
        "Values closer to 1.0 indicate that the fused image preserves "
        "more metabolic information from the PET."
    ),
    "std": (
        "Standard deviation of intensity values in the fused image. "
        "Higher values indicate greater contrast and dynamic range."
    ),
    "spatial_frequency": (
        "Measures the overall level of spatial detail (edge activity) in "
        "the fused image. Higher values indicate better preservation "
        "of fine details from both modalities."
    ),
}
