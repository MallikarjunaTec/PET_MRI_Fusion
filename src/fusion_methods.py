"""
fusion_methods.py — All four PET-MRI fusion algorithms.

Each function preserves the exact algorithm from the original scripts:
  - weighted_fusion   : from fusion.py
  - pca_fusion        : from pca_fusion.py
  - wavelet_fusion    : from wavelet_fusion.py
  - improved_wavelet_fusion : from wavelet_fusion_v2.py
"""

import numpy as np
import pywt


# ============================================================
# SHARED NORMALIZATION (same as all original scripts)
# ============================================================

def _normalize(image: np.ndarray) -> np.ndarray:
    """Normalize image to [0, 1]."""
    minimum = np.min(image)
    maximum = np.max(image)

    if maximum == minimum:
        return np.zeros_like(image)

    return (image - minimum) / (maximum - minimum)


# ============================================================
# 1. WEIGHTED FUSION  (from fusion.py)
# ============================================================

def weighted_fusion(
    mri: np.ndarray,
    pet: np.ndarray,
    mri_weight: float = 0.5,
    pet_weight: float = 0.5,
) -> np.ndarray:
    """
    Simple weighted average fusion.

    Parameters:
        mri        : 3D normalized MRI volume
        pet        : 3D normalized PET volume (registered)
        mri_weight : weight for MRI (default 0.5)
        pet_weight : weight for PET (default 0.5)

    Returns:
        3D fused volume, normalized to [0, 1]
    """
    mri_n = _normalize(mri.astype(np.float32))
    pet_n = _normalize(pet.astype(np.float32))

    fused = mri_weight * mri_n + pet_weight * pet_n

    return _normalize(fused)


# ============================================================
# 2. PCA FUSION  (from pca_fusion.py)
# ============================================================

def pca_fusion(mri: np.ndarray, pet: np.ndarray) -> np.ndarray:
    """
    PCA-based fusion using eigenvector weights.

    Preserves the exact algorithm from pca_fusion.py:
    1. Handle NaN/Inf
    2. Normalize both images
    3. Flatten and standardize
    4. Compute covariance matrix
    5. Extract principal eigenvector
    6. Use |eigenvector| as fusion weights
    7. Weighted sum → normalize

    Returns:
        3D fused volume, normalized to [0, 1]
    """
    mri_clean = np.nan_to_num(mri.astype(np.float32))
    pet_clean = np.nan_to_num(pet.astype(np.float32))

    mri_norm = _normalize(mri_clean)
    pet_norm = _normalize(pet_clean)

    # Flatten
    mri_flat = mri_norm.flatten()
    pet_flat = pet_norm.flatten()

    # Standardize for PCA
    mri_std = (mri_flat - np.mean(mri_flat)) / (np.std(mri_flat) + 1e-8)
    pet_std = (pet_flat - np.mean(pet_flat)) / (np.std(pet_flat) + 1e-8)

    # Data matrix
    data = np.vstack([mri_std, pet_std])

    # Covariance matrix
    covariance_matrix = np.cov(data)

    # Eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eigh(covariance_matrix)

    # Principal component
    largest_index = np.argmax(eigenvalues)
    principal_vector = eigenvectors[:, largest_index]

    # PCA weights (absolute values, normalized)
    weights = np.abs(principal_vector)
    weights = weights / np.sum(weights)

    mri_weight = weights[0]
    pet_weight = weights[1]

    # Fuse
    fused_flat = mri_weight * mri_norm.flatten() + pet_weight * pet_norm.flatten()
    fused = fused_flat.reshape(mri.shape)

    return _normalize(fused)


# ============================================================
# 3. WAVELET FUSION  (from wavelet_fusion.py)
# ============================================================

def _wavelet_fuse_slice_v1(mri_slice: np.ndarray, pet_slice: np.ndarray) -> np.ndarray:
    """
    Single-level Haar wavelet fusion for one 2D slice.
    Exact algorithm from wavelet_fusion.py.
    """
    # Haar wavelet decomposition
    mri_coeff = pywt.dwt2(mri_slice, "haar")
    pet_coeff = pywt.dwt2(pet_slice, "haar")

    mri_LL, (mri_LH, mri_HL, mri_HH) = mri_coeff
    pet_LL, (pet_LH, pet_HL, pet_HH) = pet_coeff

    # Low-frequency: average
    fused_LL = 0.5 * mri_LL + 0.5 * pet_LL

    # High-frequency: max absolute value selection
    fused_LH = np.where(np.abs(mri_LH) >= np.abs(pet_LH), mri_LH, pet_LH)
    fused_HL = np.where(np.abs(mri_HL) >= np.abs(pet_HL), mri_HL, pet_HL)
    fused_HH = np.where(np.abs(mri_HH) >= np.abs(pet_HH), mri_HH, pet_HH)

    # Reconstruct
    fused = pywt.idwt2((fused_LL, (fused_LH, fused_HL, fused_HH)), "haar")

    return fused


def wavelet_fusion(mri: np.ndarray, pet: np.ndarray) -> np.ndarray:
    """
    Haar wavelet fusion applied slice by slice.
    Exact algorithm from wavelet_fusion.py.
    """
    mri_n = _normalize(mri.astype(np.float32))
    pet_n = _normalize(pet.astype(np.float32))

    fused = np.zeros_like(mri_n, dtype=np.float32)

    for i in range(mri_n.shape[2]):
        fused[:, :, i] = _wavelet_fuse_slice_v1(mri_n[:, :, i], pet_n[:, :, i])

    return _normalize(fused)


# ============================================================
# 4. IMPROVED WAVELET FUSION  (from wavelet_fusion_v2.py)
# ============================================================

def _wavelet_fuse_slice_v2(mri_slice: np.ndarray, pet_slice: np.ndarray) -> np.ndarray:
    """
    2-level db2 wavelet fusion for one 2D slice.
    Exact algorithm from wavelet_fusion_v2.py.
    """
    # 2-level decomposition with db2
    mri_coeffs = pywt.wavedec2(mri_slice, wavelet="db2", level=2)
    pet_coeffs = pywt.wavedec2(pet_slice, wavelet="db2", level=2)

    fused_coeffs = []

    # Approximation coefficients: average
    fused_low = 0.5 * mri_coeffs[0] + 0.5 * pet_coeffs[0]
    fused_coeffs.append(fused_low)

    # Detail coefficients: max energy selection
    for level in range(1, len(mri_coeffs)):
        mri_details = mri_coeffs[level]
        pet_details = pet_coeffs[level]

        fused_details = []
        for mri_detail, pet_detail in zip(mri_details, pet_details):
            mri_energy = np.abs(mri_detail)
            pet_energy = np.abs(pet_detail)
            mask = mri_energy >= pet_energy
            fused_detail = np.where(mask, mri_detail, pet_detail)
            fused_details.append(fused_detail)

        fused_coeffs.append(tuple(fused_details))

    # Reconstruct
    fused = pywt.waverec2(fused_coeffs, wavelet="db2")

    # Trim to original size
    fused = fused[:mri_slice.shape[0], :mri_slice.shape[1]]

    return fused


def improved_wavelet_fusion(mri: np.ndarray, pet: np.ndarray) -> np.ndarray:
    """
    Improved (2-level db2) wavelet fusion applied slice by slice.
    Exact algorithm from wavelet_fusion_v2.py.
    """
    mri_n = _normalize(mri.astype(np.float32))
    pet_n = _normalize(pet.astype(np.float32))

    fused = np.zeros_like(mri_n, dtype=np.float32)

    for i in range(mri_n.shape[2]):
        fused[:, :, i] = _wavelet_fuse_slice_v2(mri_n[:, :, i], pet_n[:, :, i])

    return _normalize(fused)


# ============================================================
# REGISTRY — method name → function mapping
# ============================================================

FUSION_METHODS = {
    "Weighted Fusion": weighted_fusion,
    "PCA Fusion": pca_fusion,
    "Wavelet Fusion": wavelet_fusion,
    "Improved Wavelet Fusion": improved_wavelet_fusion,
}

FUSION_DESCRIPTIONS = {
    "Weighted Fusion": (
        "Combines MRI and PET using a simple weighted average. "
        "Equal weights preserve balanced structural and metabolic information."
    ),
    "PCA Fusion": (
        "Uses Principal Component Analysis to determine optimal fusion weights "
        "from the data covariance structure. Preserves the most important "
        "image information from both modalities."
    ),
    "Wavelet Fusion": (
        "Decomposes images using the Haar wavelet transform. Low-frequency "
        "components are averaged while high-frequency details are selected "
        "by maximum absolute value."
    ),
    "Improved Wavelet Fusion": (
        "Enhanced wavelet fusion using a 2-level Daubechies-2 (db2) decomposition. "
        "Provides better frequency separation and preserves finer structural details "
        "compared to single-level Haar."
    ),
}
