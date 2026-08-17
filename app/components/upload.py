"""
upload.py — Premium medical-grade upload panels with NIfTI validation.

Provides professional two-panel upload workspace for MRI and PET images,
with thumbnail previews, validation badges, and file information display.
"""

import streamlit as st
import nibabel as nib
import numpy as np
import tempfile
import os
from pathlib import Path


# ════════════════════════════════════════════════════════════════
# NIFTI LOADING
# ════════════════════════════════════════════════════════════════

def load_uploaded_nifti(uploaded_file) -> tuple:
    """
    Save uploaded file to a temp location and load with nibabel.

    Returns:
        (nib_img, error_message)
        nib_img is None if loading failed.
    """
    if uploaded_file is None:
        return None, "No file uploaded."

    filename = uploaded_file.name.lower()
    if not (filename.endswith(".nii") or filename.endswith(".nii.gz")):
        return None, (
            f"Unsupported format: '{uploaded_file.name}'. "
            "Please upload a NIfTI file (.nii or .nii.gz)."
        )

    try:
        suffix = ".nii.gz" if filename.endswith(".nii.gz") else ".nii"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.getvalue())
            tmp_path = tmp.name

        nib_img = nib.load(tmp_path)
        _ = nib_img.get_fdata(dtype=np.float32)   # force-read to verify
        return nib_img, None

    except Exception as e:
        return None, f"Failed to read NIfTI file: {e}"


# ════════════════════════════════════════════════════════════════
# VALIDATION
# ════════════════════════════════════════════════════════════════

def validate_nifti(nib_img) -> dict:
    """
    Validate a loaded NIfTI image.
    Returns a dict with validation results and metadata.
    """
    result = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "shape": None,
        "voxel_spacing": None,
        "orientation": None,
        "dtype": None,
        "intensity_min": None,
        "intensity_max": None,
        "ndim": None,
    }

    try:
        data = nib_img.get_fdata(dtype=np.float32)
    except Exception as e:
        result["valid"] = False
        result["errors"].append(f"Cannot read image data: {e}")
        return result

    result["shape"] = data.shape
    result["ndim"]  = data.ndim

    if data.ndim < 3:
        result["valid"] = False
        result["errors"].append(f"Expected 3D volume, got {data.ndim}D data.")

    if data.size == 0:
        result["valid"] = False
        result["errors"].append("Image data is empty.")
        return result

    has_nan = bool(np.any(np.isnan(data)))
    has_inf = bool(np.any(np.isinf(data)))
    if has_nan:
        result["warnings"].append("Contains NaN values — will be cleaned automatically.")
    if has_inf:
        result["warnings"].append("Contains Inf values — will be cleaned automatically.")

    clean = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
    result["intensity_min"] = float(np.min(clean))
    result["intensity_max"] = float(np.max(clean))

    if result["intensity_max"] == result["intensity_min"]:
        result["valid"] = False
        result["errors"].append("Image has uniform intensity (constant value).")

    try:
        zooms = nib_img.header.get_zooms()
        result["voxel_spacing"] = tuple(round(float(z), 4) for z in zooms[:3])
    except Exception:
        result["voxel_spacing"] = None
        result["warnings"].append("Cannot read voxel spacing.")

    try:
        codes = nib.aff2axcodes(nib_img.affine)
        result["orientation"] = "".join(codes)
    except Exception:
        result["orientation"] = "Unknown"

    result["dtype"] = str(nib_img.header.get_data_dtype())
    return result


# ════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════

def format_file_size(size_bytes: int) -> str:
    """Format bytes into human-readable size string."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _get_thumbnail(nib_img, cmap_name: str = "gray") -> np.ndarray:
    """Extract and colorize the middle axial slice for thumbnail display."""
    try:
        import matplotlib.cm as cm
        data  = nib_img.get_fdata(dtype=np.float32)
        data  = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)
        mid_z = data.shape[2] // 2
        sl    = data[:, :, mid_z].astype(np.float32)
        vmin, vmax = np.min(sl), np.max(sl)
        if vmax > vmin:
            sl = (sl - vmin) / (vmax - vmin)
        else:
            sl = np.zeros_like(sl)
        colormap = cm.get_cmap(cmap_name)
        rgba = colormap(sl)
        return (rgba[:, :, :3] * 255).astype(np.uint8)
    except Exception:
        return None


# ════════════════════════════════════════════════════════════════
# VALIDATION STATUS RENDER
# ════════════════════════════════════════════════════════════════

def render_validation_status(label: str, validation: dict):
    """Render inline validation status rows."""
    if validation["valid"]:
        shape = validation["shape"]
        voxel = validation["voxel_spacing"]
        shape_str = " × ".join(str(s) for s in shape[:3])
        voxel_str = (
            " × ".join(f"{v}" for v in voxel) + " mm"
            if voxel else "Unknown"
        )
        st.markdown(
            f'<div class="val-row ok">'
            f'<span>✓</span>'
            f'<span>{label} valid &nbsp;·&nbsp; {shape_str} &nbsp;·&nbsp; Voxel: {voxel_str}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
        for w in validation.get("warnings", []):
            st.markdown(
                f'<div class="val-row warn"><span>⚠</span><span>{w}</span></div>',
                unsafe_allow_html=True,
            )
    else:
        for err in validation["errors"]:
            st.markdown(
                f'<div class="val-row err"><span>✗</span><span>{err}</span></div>',
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════════════════════════
# SINGLE UPLOAD PANEL
# ════════════════════════════════════════════════════════════════

def _render_single_upload_panel(
    panel_type: str,     # "mri" or "pet"
    title: str,
    subtitle: str,
    icon: str,
    uploader_key: str,
    nib_key: str,
    validation_key: str,
    filename_key: str,
    thumbnail_cmap: str,
    downstream_keys: list,
):
    """Render a single premium upload panel with file info and thumbnail."""

    loaded = nib_key in st.session_state and st.session_state.get(
        validation_key, {}
    ).get("valid", False)
    panel_cls = f"upload-panel {panel_type} loaded" if loaded else f"upload-panel {panel_type}"

    # Panel wrapper with top-line effect
    st.markdown(
        f"""
        <div class="{panel_cls}">
          <div class="upload-panel-top-line"></div>
          <div class="upload-panel-header">
            <div class="upload-type-icon {panel_type}">{icon}</div>
            <div>
              <div class="upload-type-label">{title}</div>
              <div class="upload-type-sub">{subtitle}</div>
            </div>
          </div>
          <div class="upload-format-row">
            <span class="upload-fmt-tag">NIfTI</span>
            <span class="upload-fmt-tag">.nii</span>
            <span class="upload-fmt-tag">.nii.gz</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Native file uploader (styled via CSS)
    uploaded_file = st.file_uploader(
        f"Upload {title}",
        type=["nii", "gz"],
        key=uploader_key,
        label_visibility="collapsed",
        help=f"Drag & drop or click to browse — NIfTI format only · Max 500 MB",
    )

    if uploaded_file is not None:
        file_size = format_file_size(len(uploaded_file.getvalue()))

        # File info row
        badge_text = "Loaded" if loaded else "Loading…"
        st.markdown(
            f"""
            <div class="file-info-row">
              <span class="fi-icon">📄</span>
              <span class="fi-name">{uploaded_file.name}</span>
              <span class="fi-size">{file_size}</span>
              <span class="fi-badge">{badge_text}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Load & validate (only if new file)
        if (
            nib_key not in st.session_state
            or st.session_state.get(filename_key) != uploaded_file.name
        ):
            with st.spinner(f"Loading {title}…"):
                nib_img, error = load_uploaded_nifti(uploaded_file)

            if error:
                st.markdown(
                    f'<div class="val-row err"><span>✗</span><span>{error}</span></div>',
                    unsafe_allow_html=True,
                )
                for k in [nib_key, validation_key]:
                    st.session_state.pop(k, None)
            else:
                validation = validate_nifti(nib_img)
                st.session_state[nib_key]        = nib_img
                st.session_state[validation_key] = validation
                st.session_state[filename_key]   = uploaded_file.name
                for k in downstream_keys:
                    st.session_state.pop(k, None)

        # Show validation
        if validation_key in st.session_state:
            render_validation_status(title, st.session_state[validation_key])

        # Thumbnail
        if nib_key in st.session_state:
            thumb = _get_thumbnail(st.session_state[nib_key], thumbnail_cmap)
            if thumb is not None:
                st.image(thumb, use_container_width=True, caption="Middle axial slice")

    else:
        # File removed — clear state
        for k in [nib_key, validation_key, filename_key] + downstream_keys:
            st.session_state.pop(k, None)

        # Empty hint
        st.markdown(
            f"""
            <div class="upload-empty-state">
              <div class="upload-empty-icon">{icon}</div>
              <div class="upload-empty-text">
                Drag &amp; drop a <strong>{title}</strong> NIfTI file here,<br>
                or click <em>Browse files</em> above.
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════
# MAIN UPLOAD SECTION
# ════════════════════════════════════════════════════════════════

def render_upload_section():
    """
    Render the two-panel premium upload workspace.

    Stores results in st.session_state:
        mri_nib_img, mri_validation, mri_filename
        pet_nib_img, pet_validation, pet_filename
    """
    col_mri, col_pet = st.columns(2, gap="large")

    with col_mri:
        _render_single_upload_panel(
            panel_type="mri",
            title="Brain MRI",
            subtitle="Structural MRI Scan",
            icon="🧠",
            uploader_key="mri_uploader",
            nib_key="mri_nib_img",
            validation_key="mri_validation",
            filename_key="mri_filename",
            thumbnail_cmap="gray",
            downstream_keys=[
                "mri_preprocessed", "pet_registered",
                "fused_volume", "fusion_metrics", "comparison_results",
            ],
        )

    with col_pet:
        _render_single_upload_panel(
            panel_type="pet",
            title="Brain PET",
            subtitle="Metabolic PET Scan",
            icon="🔬",
            uploader_key="pet_uploader",
            nib_key="pet_nib_img",
            validation_key="pet_validation",
            filename_key="pet_filename",
            thumbnail_cmap="hot",
            downstream_keys=[
                "pet_preprocessed", "pet_registered",
                "fused_volume", "fusion_metrics", "comparison_results",
            ],
        )
