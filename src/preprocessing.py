"""
preprocessing.py — NIfTI image preprocessing for PET-MRI fusion.

Provides normalization and validation utilities that wrap the original
preprocess.py algorithms into importable functions.
"""

import nibabel as nib
import numpy as np


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    Normalize image intensity to the range [0, 1].

    This is the same normalization used in the original preprocess.py.
    """
    image = image.astype(np.float32)

    image_min = np.min(image)
    image_max = np.max(image)

    if image_max == image_min:
        return np.zeros_like(image)

    normalized = (image - image_min) / (image_max - image_min)

    return normalized


# ============================================================
# VALIDATION
# ============================================================

def validate_nifti(nib_img: nib.Nifti1Image) -> dict:
    """
    Validate a loaded NIfTI image and return metadata + validation status.

    Returns a dict with:
        valid          : bool
        errors         : list[str]
        shape          : tuple
        voxel_spacing  : tuple
        orientation    : str
        dtype          : str
        intensity_min  : float
        intensity_max  : float
        ndim           : int
        has_nan        : bool
        has_inf        : bool
    """
    result = {
        "valid": True,
        "errors": [],
        "shape": None,
        "voxel_spacing": None,
        "orientation": None,
        "dtype": None,
        "intensity_min": None,
        "intensity_max": None,
        "ndim": None,
        "has_nan": False,
        "has_inf": False,
    }

    try:
        data = nib_img.get_fdata(dtype=np.float32)
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Cannot read image data: {e}")
        return result

    # Dimensions
    result["shape"] = data.shape
    result["ndim"] = data.ndim

    if data.ndim < 3:
        result["valid"] = False
        result["errors"].append(
            f"Expected a 3D volume, got {data.ndim}D data."
        )

    # Check for empty / corrupted data
    if data.size == 0:
        result["valid"] = False
        result["errors"].append("Image data is empty.")
        return result

    # NaN / Inf
    result["has_nan"] = bool(np.any(np.isnan(data)))
    result["has_inf"] = bool(np.any(np.isinf(data)))

    if result["has_nan"]:
        result["errors"].append("Image contains NaN values (will be replaced with 0).")
    if result["has_inf"]:
        result["errors"].append("Image contains Inf values (will be replaced with 0).")

    # Intensity range
    clean = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
    result["intensity_min"] = float(np.min(clean))
    result["intensity_max"] = float(np.max(clean))

    if result["intensity_max"] == result["intensity_min"]:
        result["errors"].append("Image has uniform intensity (constant value).")

    # Voxel spacing
    try:
        zooms = nib_img.header.get_zooms()
        result["voxel_spacing"] = tuple(float(z) for z in zooms[:3])
    except Exception:
        result["voxel_spacing"] = None
        result["errors"].append("Cannot read voxel spacing.")

    # Orientation
    try:
        orientation_codes = nib.aff2axcodes(nib_img.affine)
        result["orientation"] = "".join(orientation_codes)
    except Exception:
        result["orientation"] = "Unknown"

    # Data type
    result["dtype"] = str(nib_img.header.get_data_dtype())

    return result


from scipy.ndimage import zoom

def downsample_if_needed(data, affine, max_dim=64):
    """Downsample image if any dimension exceeds max_dim to save memory and CPU on Render."""
    shape = data.shape
    if any(s > max_dim for s in shape[:3]):
        factors = [min(1.0, max_dim / s) for s in shape[:3]]
        if len(shape) > 3:
            factors += [1.0] * (len(shape) - 3)
            
        data = zoom(data, factors, order=1)
        
        new_affine = affine.copy()
        for i in range(3):
            new_affine[:3, i] /= factors[i]
            
        return data, new_affine
    return data, affine

# ============================================================
# PREPROCESS PIPELINE
# ============================================================

def preprocess_volume(nib_img: nib.Nifti1Image) -> tuple:
    """
    Preprocess a NIfTI volume:
      1. Load data as float32
      2. Downsample large images to prevent OOM errors on Render
      3. Replace NaN/Inf with 0
      4. Normalize to [0, 1]

    Returns:
        (normalized_data, nib.Nifti1Image with normalized data)
    """
    data = nib_img.get_fdata(dtype=np.float32)

    # Downsample to save memory (Render free tier has 512MB RAM)
    data, new_affine = downsample_if_needed(data, nib_img.affine)

    # Clean invalid values
    data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)

    # Normalize
    normalized = normalize_image(data)

    # Create new NIfTI image with same affine/header
    normalized_img = nib.Nifti1Image(
        normalized,
        new_affine,
        nib_img.header
    )

    return normalized, normalized_img
