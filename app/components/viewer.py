"""
viewer.py — Premium dark medical image visualization components.

Provides slice extraction, colormapping, synchronized multi-panel viewers
with brightness/contrast/opacity controls, and overlay rendering.
"""

import streamlit as st
import numpy as np
import matplotlib.cm as cm


# ════════════════════════════════════════════════════════════════
# SLICE EXTRACTION
# ════════════════════════════════════════════════════════════════

def get_slice(volume: np.ndarray, axis: int, index: int) -> np.ndarray:
    """
    Extract a 2D slice from a 3D volume.

    axis: 0=Sagittal, 1=Coronal, 2=Axial
    """
    index = max(0, min(index, volume.shape[axis] - 1))
    if axis == 0:
        return volume[index, :, :]
    elif axis == 1:
        return volume[:, index, :]
    else:
        return volume[:, :, index]


# ════════════════════════════════════════════════════════════════
# NORMALIZE SLICE
# ════════════════════════════════════════════════════════════════

def normalize_slice(slice_2d: np.ndarray) -> np.ndarray:
    """Normalize a 2D slice to [0, 1]."""
    s = slice_2d.astype(np.float32)
    s_min, s_max = np.min(s), np.max(s)
    if s_max - s_min > 0:
        return (s - s_min) / (s_max - s_min)
    return np.zeros_like(s)


# ════════════════════════════════════════════════════════════════
# COLORIZE SLICE
# ════════════════════════════════════════════════════════════════

def colorize_slice(
    slice_2d: np.ndarray,
    cmap_name: str = "gray",
    brightness: float = 1.0,
    contrast: float = 1.0,
) -> np.ndarray:
    """
    Apply a matplotlib colormap to a 2D slice.

    Returns an RGB uint8 array suitable for st.image().
    brightness: 0.5–2.0 (1.0 = neutral)
    contrast:   0.5–2.0 (1.0 = neutral)
    """
    norm = normalize_slice(slice_2d)

    # Apply contrast (centered at 0.5)
    if contrast != 1.0:
        norm = (norm - 0.5) * contrast + 0.5

    # Apply brightness
    if brightness != 1.0:
        norm = norm * brightness

    norm = np.clip(norm, 0, 1)

    colormap = cm.get_cmap(cmap_name)
    rgba = colormap(norm)
    return (rgba[:, :, :3] * 255).astype(np.uint8)


# ════════════════════════════════════════════════════════════════
# OVERLAY (MRI + PET alpha blend)
# ════════════════════════════════════════════════════════════════

def create_overlay(
    mri_slice: np.ndarray,
    pet_slice: np.ndarray,
    pet_alpha: float = 0.45,
    pet_threshold: float = 0.15,
) -> np.ndarray:
    """
    Create an MRI + PET overlay image.

    MRI is shown in grayscale, PET is overlaid in 'hot' colormap
    with alpha blending. Low PET values below threshold are transparent.
    """
    mri_norm = normalize_slice(mri_slice)
    pet_norm = normalize_slice(pet_slice)

    mri_rgb = colorize_slice(mri_norm, "gray").astype(np.float32) / 255.0
    pet_rgb = colorize_slice(pet_norm, "hot").astype(np.float32) / 255.0

    alpha_mask = np.zeros_like(pet_norm)
    above = pet_norm > pet_threshold
    alpha_mask[above] = pet_norm[above] * pet_alpha

    alpha_3d = np.expand_dims(alpha_mask, axis=2)
    blended  = mri_rgb * (1 - alpha_3d) + pet_rgb * alpha_3d
    return (np.clip(blended, 0, 1) * 255).astype(np.uint8)


# ════════════════════════════════════════════════════════════════
# AXIS MAP
# ════════════════════════════════════════════════════════════════

AXIS_MAP = {"Axial": 2, "Coronal": 1, "Sagittal": 0}


# ════════════════════════════════════════════════════════════════
# RENDER SINGLE SCAN PANEL
# ════════════════════════════════════════════════════════════════

def render_scan_panel(
    image: np.ndarray,
    label: str,
    badge_type: str = "mri",   # "mri" | "pet" | "fused" | "overlay"
    cmap: str = "gray",
    brightness: float = 1.0,
    contrast: float = 1.0,
):
    """Render a single premium dark scan panel."""
    badge_labels = {
        "mri":     "Structural",
        "pet":     "Metabolic",
        "fused":   "Fused",
        "overlay": "Overlay",
    }
    badge_text = badge_labels.get(badge_type, badge_type)

    st.markdown(
        f"""
        <div class="scan-panel">
          <div class="scan-panel-top">
            <span class="scan-label-text">{label}</span>
            <span class="scan-type-badge {badge_type}">{badge_text}</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    img_rgb = colorize_slice(image, cmap, brightness=brightness, contrast=contrast)
    st.image(img_rgb, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# THREE-PANEL VIEWER
# ════════════════════════════════════════════════════════════════

def render_three_panel_viewer(
    volumes: dict,
    key_prefix: str = "viewer",
    show_overlay: bool = False,
    mri_key: str = None,
    pet_key: str = None,
):
    """
    Render a synchronized three-panel medical image viewer.

    Parameters:
        volumes:      dict mapping label -> (volume_3d, colormap_name)
        key_prefix:   unique key prefix for Streamlit widgets
        show_overlay: if True, add an MRI+PET overlay panel
        mri_key:      key in volumes for MRI (for overlay)
        pet_key:      key in volumes for PET (for overlay)
    """
    # ── View plane + slice controls ──
    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4, ctrl_col5 = st.columns(
        [1.5, 3, 0.8, 1.2, 1.2], gap="small"
    )

    with ctrl_col1:
        st.markdown('<div class="viewer-ctrl-label">View Plane</div>', unsafe_allow_html=True)
        axis_name = st.radio(
            "plane",
            list(AXIS_MAP.keys()),
            horizontal=True,
            key=f"{key_prefix}_axis",
            label_visibility="collapsed",
        )

    axis         = AXIS_MAP[axis_name]
    first_vol    = list(volumes.values())[0][0]
    max_index    = first_vol.shape[axis] - 1
    default_idx  = max_index // 2

    with ctrl_col2:
        st.markdown('<div class="viewer-ctrl-label">Slice Position</div>', unsafe_allow_html=True)
        slice_index = st.slider(
            "slice",
            0,
            max_index,
            default_idx,
            key=f"{key_prefix}_slice",
            label_visibility="collapsed",
        )

    with ctrl_col3:
        st.markdown(
            f'<div style="padding-top:1.6rem; font-size:0.72rem; color:var(--text-3);">'
            f'{slice_index + 1} / {max_index + 1}</div>',
            unsafe_allow_html=True,
        )

    with ctrl_col4:
        brightness = st.slider(
            "Brightness",
            0.5,
            2.0,
            1.0,
            step=0.05,
            key=f"{key_prefix}_brightness",
        )

    with ctrl_col5:
        contrast = st.slider(
            "Contrast",
            0.5,
            2.0,
            1.0,
            step=0.05,
            key=f"{key_prefix}_contrast",
        )

    # ── Image panels ──
    labels = list(volumes.keys())
    n_panels = len(labels) + (1 if show_overlay and mri_key and pet_key else 0)
    cols = st.columns(min(n_panels, 4), gap="small")

    # Badge type mapping based on common label keywords
    def _badge(lbl: str) -> str:
        lbl_low = lbl.lower()
        if "pet" in lbl_low and "fused" not in lbl_low:
            return "pet"
        if "fused" in lbl_low or "fusion" in lbl_low or "pca" in lbl_low \
                or "wavelet" in lbl_low or "average" in lbl_low or "weighted" in lbl_low:
            return "fused"
        return "mri"

    for i, (label, (vol, cmap)) in enumerate(volumes.items()):
        idx    = min(slice_index, vol.shape[axis] - 1)
        sl     = get_slice(vol, axis, idx)
        badge  = _badge(label)

        with cols[i % len(cols)]:
            render_scan_panel(
                sl, label, badge_type=badge, cmap=cmap,
                brightness=brightness, contrast=contrast,
            )

    # Overlay panel
    if show_overlay and mri_key and pet_key and mri_key in volumes and pet_key in volumes:
        mri_vol = volumes[mri_key][0]
        pet_vol = volumes[pet_key][0]
        mri_s   = get_slice(mri_vol, axis, min(slice_index, mri_vol.shape[axis] - 1))
        pet_s   = get_slice(pet_vol, axis, min(slice_index, pet_vol.shape[axis] - 1))
        overlay = create_overlay(mri_s, pet_s)

        with cols[len(volumes) % len(cols)]:
            st.markdown(
                """
                <div class="scan-panel">
                  <div class="scan-panel-top">
                    <span class="scan-label-text">MRI + PET</span>
                    <span class="scan-type-badge overlay">Overlay</span>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.image(overlay, use_container_width=True)


# ════════════════════════════════════════════════════════════════
# COMPACT OVERLAY OPACITY CONTROL
# ════════════════════════════════════════════════════════════════

def get_overlay_opacity(key_prefix: str = "overlay") -> float:
    """Render a compact opacity slider and return the value."""
    return st.slider(
        "PET Overlay Opacity",
        0.1,
        0.9,
        0.45,
        step=0.05,
        key=f"{key_prefix}_opacity",
    )
