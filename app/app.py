"""
PET–MRI Image Fusion — Streamlit Application
==============================================

Premium enterprise-grade multimodal brain imaging research workstation.

Workflow: Upload → Validate → Preprocess → Register → Fuse → Visualize → Evaluate → Download
"""

import sys
import os
import io
import time
import tempfile
from pathlib import Path

import streamlit as st
import nibabel as nib
import numpy as np

# Add project root to path so we can import src modules
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.preprocessing import normalize_image, preprocess_volume, validate_nifti
from src.registration import register_pet_to_mri
from src.fusion_methods import FUSION_METHODS, FUSION_DESCRIPTIONS
from src.evaluation import evaluate_fusion, METRIC_DESCRIPTIONS

# Components
from components.ui import (
    inject_theme,
    render_top_nav,
    render_workspace_header,
    section_title,
    section_divider,
    render_pipeline,
    render_disclaimer,
    metric_card,
    info_card,
    render_empty_state,
    render_settings_panel,
)
from components.upload import render_upload_section
from components.viewer import (
    render_three_panel_viewer,
    render_scan_panel,
    get_slice,
    colorize_slice,
    create_overlay,
    normalize_slice,
    AXIS_MAP,
)
from components.metrics import (
    render_metric_cards,
    render_comparison_charts,
    render_comparison_table,
)


# ════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="PET–MRI Brain Image Fusion",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ════════════════════════════════════════════════════════════════
# INJECT PREMIUM THEME
# ════════════════════════════════════════════════════════════════

inject_theme()


# ════════════════════════════════════════════════════════════════
# TOP NAVIGATION
# ════════════════════════════════════════════════════════════════

render_top_nav()
render_settings_panel()



# ════════════════════════════════════════════════════════════════
# WORKSPACE HEADER
# ════════════════════════════════════════════════════════════════

render_workspace_header()


# ════════════════════════════════════════════════════════════════
# 1. IMAGE UPLOAD WORKSPACE
# ════════════════════════════════════════════════════════════════

section_title("01", "Image Upload Workspace", section_id="workspace")

render_upload_section()

section_divider()


# ════════════════════════════════════════════════════════════════
# CHECK IF BOTH IMAGES ARE LOADED
# ════════════════════════════════════════════════════════════════

mri_loaded = (
    "mri_nib_img" in st.session_state
    and st.session_state.get("mri_validation", {}).get("valid", False)
)
pet_loaded = (
    "pet_nib_img" in st.session_state
    and st.session_state.get("pet_validation", {}).get("valid", False)
)
both_loaded = mri_loaded and pet_loaded

if not both_loaded:
    if not mri_loaded and not pet_loaded:
        render_empty_state(
            icon="🧠",
            title="Upload Brain MRI & PET Images to Begin",
            description=(
                "Upload a Brain MRI (.nii / .nii.gz) and a Brain PET (.nii / .nii.gz) "
                "NIfTI file using the panels above. Both images are required to proceed "
                "with registration, fusion and analysis."
            ),
        )
    elif not mri_loaded:
        render_empty_state(
            icon="🧠",
            title="Brain MRI Required",
            description="A valid Brain MRI NIfTI file is needed to continue.",
        )
    else:
        render_empty_state(
            icon="🔬",
            title="Brain PET Required",
            description="A valid Brain PET NIfTI file is needed to continue.",
        )

    render_disclaimer()
    st.stop()


# ════════════════════════════════════════════════════════════════
# 2. IMAGE INFORMATION
# ════════════════════════════════════════════════════════════════

section_title("02", "Image Information", section_id="documentation")

mri_data = st.session_state["mri_nib_img"].get_fdata(dtype=np.float32)
pet_data = st.session_state["pet_nib_img"].get_fdata(dtype=np.float32)
mri_data = np.nan_to_num(mri_data, nan=0.0, posinf=0.0, neginf=0.0)
pet_data = np.nan_to_num(pet_data, nan=0.0, posinf=0.0, neginf=0.0)

with st.expander("View image metadata", expanded=False):
    col_mri, col_pet = st.columns(2, gap="large")

    mri_val = st.session_state["mri_validation"]
    pet_val = st.session_state["pet_validation"]

    with col_mri:
        st.markdown(
            '<div class="m-label" style="margin-bottom:0.6rem;">Brain MRI — Structural</div>',
            unsafe_allow_html=True,
        )
        info_card("Dimensions",     " × ".join(str(s) for s in mri_val["shape"][:3]))
        info_card("Voxel Spacing",
                  " × ".join(f"{v}" for v in mri_val["voxel_spacing"]) + " mm"
                  if mri_val["voxel_spacing"] else "Unknown")
        info_card("Orientation",    mri_val.get("orientation", "Unknown"))
        info_card("Data Type",      mri_val.get("dtype", "Unknown"))
        info_card("Intensity Range",
                  f"{mri_val['intensity_min']:.2f} — {mri_val['intensity_max']:.2f}")

    with col_pet:
        st.markdown(
            '<div class="m-label" style="margin-bottom:0.6rem;">Brain PET — Metabolic</div>',
            unsafe_allow_html=True,
        )
        info_card("Dimensions",     " × ".join(str(s) for s in pet_val["shape"][:3]))
        info_card("Voxel Spacing",
                  " × ".join(f"{v}" for v in pet_val["voxel_spacing"]) + " mm"
                  if pet_val["voxel_spacing"] else "Unknown")
        info_card("Orientation",    pet_val.get("orientation", "Unknown"))
        info_card("Data Type",      pet_val.get("dtype", "Unknown"))
        info_card("Intensity Range",
                  f"{pet_val['intensity_min']:.2f} — {pet_val['intensity_max']:.2f}")

section_divider()


# ════════════════════════════════════════════════════════════════
# 3. FUSION CONFIGURATION
# ════════════════════════════════════════════════════════════════

section_title("03", "Fusion Configuration")

st.markdown('<div class="fusion-ctrl-panel">', unsafe_allow_html=True)
st.markdown('<div class="fcp-title">Fusion Method &amp; Visualization Settings</div>', unsafe_allow_html=True)

cfg_col1, cfg_col2, cfg_col3, cfg_col4 = st.columns([2, 1.5, 1.5, 1.5], gap="medium")

with cfg_col1:
    fusion_method = st.selectbox(
        "Fusion Algorithm",
        list(FUSION_METHODS.keys()),
        index=1,          # Default: PCA Fusion
        key="fusion_method_select",
    )
    desc = FUSION_DESCRIPTIONS.get(fusion_method, "")
    if desc:
        st.caption(desc)

with cfg_col2:
    _mri_cmaps = ["gray", "bone", "viridis", "magma", "inferno"]
    _mri_default = st.session_state.get("settings_mri_cmap", "gray")
    cmap_choice = st.selectbox(
        "MRI Colormap",
        _mri_cmaps,
        index=_mri_cmaps.index(_mri_default) if _mri_default in _mri_cmaps else 0,
        key="cmap_select",
    )

with cfg_col3:
    _pet_cmaps = ["hot", "inferno", "magma", "plasma", "YlOrRd"]
    _pet_default = st.session_state.get("settings_pet_cmap", "hot")
    pet_cmap = st.selectbox(
        "PET Colormap",
        _pet_cmaps,
        index=_pet_cmaps.index(_pet_default) if _pet_default in _pet_cmaps else 0,
        key="pet_cmap_select",
    )

with cfg_col4:
    overlay_opacity = st.slider(
        "Overlay Opacity",
        0.1,
        0.9,
        0.45,
        step=0.05,
        key="overlay_opacity",
    )

st.markdown('</div>', unsafe_allow_html=True)

# ── Pipeline status ──
pipeline_step = st.session_state.get("pipeline_step", 1)
render_pipeline(pipeline_step)

# ── Run Fusion button ──
btn_l, btn_c, btn_r = st.columns([1, 2, 1])
with btn_c:
    generate_clicked = st.button(
        "▶  Run Fusion",
        use_container_width=True,
        type="primary",
        key="generate_fusion_btn",
    )


# ════════════════════════════════════════════════════════════════
# FUSION PROCESSING PIPELINE
# ════════════════════════════════════════════════════════════════

if generate_clicked:
    with st.container():
        status = st.status("Running processing pipeline…", expanded=True)

        with status:
            st.write("✓ MRI loaded")
            st.write("✓ PET loaded")
            st.write("✓ Images validated")
            st.session_state["pipeline_step"] = 2
            time.sleep(0.3)

            # Preprocess MRI
            st.write("⟳ Normalising MRI…")
            mri_nib = st.session_state["mri_nib_img"]
            mri_normalized, mri_norm_nib = preprocess_volume(mri_nib)
            st.session_state["mri_preprocessed"] = mri_normalized
            st.session_state["mri_norm_nib"]     = mri_norm_nib
            st.write("✓ MRI normalised")
            st.session_state["pipeline_step"] = 3
            time.sleep(0.2)

            # Preprocess PET
            st.write("⟳ Normalising PET…")
            pet_nib = st.session_state["pet_nib_img"]
            pet_normalized, pet_norm_nib = preprocess_volume(pet_nib)
            st.session_state["pet_preprocessed"] = pet_normalized
            st.write("✓ PET normalised")
            time.sleep(0.2)

            # Registration
            st.write("⟳ Registering PET → MRI space…")
            st.session_state["pipeline_step"] = 4

            reg_result = register_pet_to_mri(
                mri_normalized,
                pet_normalized,
                mri_affine=mri_nib.affine,
                pet_affine=pet_nib.affine,
            )

            if reg_result["status"] == "success":
                st.session_state["pet_registered"] = reg_result["registered_pet"]
                st.session_state["registration_info"] = {
                    "metric_value": reg_result["metric_value"],
                    "iterations":   reg_result["iterations"],
                    "status":       "success",
                }
                st.write(
                    f"✓ Registration completed "
                    f"(metric: {reg_result['metric_value']:.6f}, "
                    f"iterations: {reg_result['iterations']})"
                )
            else:
                st.error(
                    f"Registration failed: {reg_result['error']}. "
                    "Using unregistered PET for fusion."
                )
                st.session_state["pet_registered"] = pet_normalized
                st.session_state["registration_info"] = {
                    "metric_value": None,
                    "iterations":   None,
                    "status":       "failed",
                    "error":        reg_result["error"],
                }
                st.write("⚠ Using unregistered PET (registration failed)")

            time.sleep(0.2)

            # Fusion
            st.write(f"⟳ Applying {fusion_method}…")
            st.session_state["pipeline_step"] = 5

            mri_for_fusion = mri_normalized
            pet_for_fusion = st.session_state["pet_registered"]

            fusion_func  = FUSION_METHODS[fusion_method]
            fused_volume = fusion_func(mri_for_fusion, pet_for_fusion)

            st.session_state["fused_volume"]           = fused_volume
            st.session_state["selected_fusion_method"] = fusion_method
            st.write(f"✓ {fusion_method} completed")
            time.sleep(0.2)

            # Evaluation
            st.write("⟳ Calculating evaluation metrics…")
            st.session_state["pipeline_step"] = 6

            metrics = evaluate_fusion(mri_for_fusion, pet_for_fusion, fused_volume)
            st.session_state["fusion_metrics"] = metrics
            st.write("✓ Evaluation completed")

            # Save fused NIfTI for download
            fused_nib = nib.Nifti1Image(
                fused_volume.astype(np.float32),
                mri_nib.affine,
                mri_nib.header,
            )
            st.session_state["fused_nib"]     = fused_nib
            st.session_state["pipeline_step"] = 7  # done

        status.update(label="✓ Pipeline completed successfully!", state="complete")

    st.rerun()


section_divider()


# ════════════════════════════════════════════════════════════════
# 4. IMAGE VIEWER
# ════════════════════════════════════════════════════════════════

section_title("04", "Image Viewer", section_id="visualization")

preview_volumes = {
    "Brain MRI":       (mri_data, cmap_choice),
    "Brain PET":       (pet_data, pet_cmap),
}

if "fused_volume" in st.session_state:
    method_name = st.session_state.get("selected_fusion_method", "Fused")
    mri_v   = st.session_state.get("mri_preprocessed", mri_data)
    pet_v   = st.session_state.get("pet_registered",
                st.session_state.get("pet_preprocessed", pet_data))
    fused_v = st.session_state["fused_volume"]

    tab_fusion, tab_overlay = st.tabs(["Fusion View", "Overlay View"])

    with tab_fusion:
        fusion_volumes = {
            "Brain MRI":       (mri_v, cmap_choice),
            "Brain PET":       (pet_v, pet_cmap),
            f"{method_name}":  (fused_v, cmap_choice),
        }
        render_three_panel_viewer(fusion_volumes, key_prefix="fused_view")

    with tab_overlay:
        overlay_volumes = {
            "Brain MRI": (mri_v, cmap_choice),
            "Brain PET": (pet_v, pet_cmap),
        }
        render_three_panel_viewer(
            overlay_volumes,
            key_prefix="overlay_view",
            show_overlay=True,
            mri_key="Brain MRI",
            pet_key="Brain PET",
        )

else:
    # Before fusion: show preview
    render_three_panel_viewer(
        preview_volumes,
        key_prefix="preview",
        show_overlay=True,
        mri_key="Brain MRI",
        pet_key="Brain PET",
    )

section_divider()


# ════════════════════════════════════════════════════════════════
# 5. REGISTRATION INFO (if available)
# ════════════════════════════════════════════════════════════════

if "registration_info" in st.session_state:
    section_title("05", "PET → MRI Registration")

    reg_info = st.session_state["registration_info"]

    st.markdown(
        "<p style='color:var(--text-3);font-size:0.82rem;margin-bottom:0.8rem;'>"
        "Spatial alignment of PET metabolic information to the structural MRI reference space."
        "</p>",
        unsafe_allow_html=True,
    )

    r1, r2, r3 = st.columns(3, gap="medium")
    with r1:
        status_text = "✓ Success" if reg_info["status"] == "success" else "⚠ Failed"
        metric_card("Registration Status", status_text)
    with r2:
        mv = f"{reg_info['metric_value']:.6f}" if reg_info["metric_value"] is not None else "N/A"
        metric_card("Final Metric Value", mv)
    with r3:
        it = str(reg_info["iterations"]) if reg_info["iterations"] is not None else "N/A"
        metric_card("Optimizer Iterations", it)

    if reg_info["status"] == "failed" and reg_info.get("error"):
        st.error(f"Registration error: {reg_info['error']}")

    # Before/after comparison
    if "mri_preprocessed" in st.session_state and "pet_registered" in st.session_state:
        with st.expander("Before / After Registration", expanded=False):
            ba1, ba2 = st.columns(2, gap="medium")

            mri_pre = st.session_state["mri_preprocessed"]
            pet_pre = st.session_state["pet_preprocessed"]
            pet_reg = st.session_state["pet_registered"]
            mid     = mri_pre.shape[2] // 2

            with ba1:
                st.markdown(
                    '<div class="m-label" style="margin-bottom:0.5rem;">Before Registration</div>',
                    unsafe_allow_html=True,
                )
                st.image(
                    create_overlay(mri_pre[:, :, mid], pet_pre[:, :, mid]),
                    caption="MRI + PET (before)",
                    use_container_width=True,
                )
            with ba2:
                st.markdown(
                    '<div class="m-label" style="margin-bottom:0.5rem;">After Registration</div>',
                    unsafe_allow_html=True,
                )
                st.image(
                    create_overlay(mri_pre[:, :, mid], pet_reg[:, :, mid]),
                    caption="MRI + PET (after)",
                    use_container_width=True,
                )

else:
    render_empty_state(
        icon="⚖️",
        title="Comparison Pending",
        description="Run the fusion pipeline first to enable multi-algorithm comparison."
    )

section_divider()


# ════════════════════════════════════════════════════════════════
# 6. FUSION ANALYSIS — METRICS
# ════════════════════════════════════════════════════════════════

section_title("06", "Fusion Analysis", section_id="analysis")

if "fusion_metrics" in st.session_state:
    st.markdown(
        "<p style='color:var(--text-3);font-size:0.82rem;margin-bottom:0.8rem;'>"
        f"Quality metrics for <strong style='color:var(--text-2);'>"
        f"{st.session_state.get('selected_fusion_method','Fusion')}"
        f"</strong> result.</p>",
        unsafe_allow_html=True,
    )

    render_metric_cards(st.session_state["fusion_metrics"], METRIC_DESCRIPTIONS)

    with st.expander("Metric descriptions"):
        labels = {
            "entropy":           "Entropy",
            "mri_ssim":         "MRI SSIM",
            "pet_ssim":         "PET SSIM",
            "std":              "Standard Deviation",
            "spatial_frequency": "Spatial Frequency",
        }
        for key, desc in METRIC_DESCRIPTIONS.items():
            st.markdown(
                f"<div style='margin-bottom:0.4rem;'>"
                f"<span style='color:var(--cyan);font-weight:600;font-size:0.82rem;'>"
                f"{labels.get(key, key)}</span>"
                f"<span style='color:var(--text-3);font-size:0.78rem;'> — {desc}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )
else:
    render_empty_state(
        icon="📊",
        title="Analysis Pending",
        description="Run the fusion pipeline in section 03 to generate quality metrics and analysis."
    )

section_divider()


# ════════════════════════════════════════════════════════════════
# 7. ALGORITHM COMPARISON
# ════════════════════════════════════════════════════════════════

section_title("07", "Algorithm Comparison")

if "fused_volume" in st.session_state:

    if "comparison_results" not in st.session_state:
        c1, c2, c3 = st.columns([1, 2, 1])
        with c2:
            run_comparison = st.button(
                "Compare All Fusion Methods",
                use_container_width=True,
                key="compare_btn",
            )

        if run_comparison:
            mri_comp = st.session_state["mri_preprocessed"]
            pet_comp = st.session_state["pet_registered"]
            comparison_results = []

            comp_status = st.status("Comparing all fusion methods…", expanded=True)
            with comp_status:
                for m_name, m_func in FUSION_METHODS.items():
                    st.write(f"⟳ Running {m_name}…")
                    fused   = m_func(mri_comp, pet_comp)
                    metrics = evaluate_fusion(mri_comp, pet_comp, fused)
                    comparison_results.append({"Method": m_name, **metrics})
                    st.write(
                        f"✓ {m_name} — Entropy: {metrics['entropy']:.4f}, "
                        f"MRI SSIM: {metrics['mri_ssim']:.4f}, "
                        f"PET SSIM: {metrics['pet_ssim']:.4f}"
                    )

                st.session_state["comparison_results"] = comparison_results

            comp_status.update(label="✓ All methods compared!", state="complete")
            st.rerun()

    if "comparison_results" in st.session_state:
        render_comparison_charts(
            st.session_state["comparison_results"],
            selected_method=st.session_state.get("selected_fusion_method"),
        )
        with st.expander("View comparison table"):
            render_comparison_table(st.session_state["comparison_results"])
else:
    render_empty_state(
        icon="⚖️",
        title="Comparison Pending",
        description="Run the fusion pipeline first to enable multi-algorithm comparison."
    )

section_divider()


# ════════════════════════════════════════════════════════════════
# 8. EXPORT & DOWNLOAD
# ════════════════════════════════════════════════════════════════

section_title("08", "Export & Download")

if "fused_volume" in st.session_state:

    st.markdown('<div class="export-wrap">', unsafe_allow_html=True)
    st.markdown('<div class="export-title">Export Fused Image &amp; Analysis Report</div>', unsafe_allow_html=True)

    dl_col1, dl_col2, dl_col3, dl_col4 = st.columns(4, gap="small")

    # ── Fused NIfTI ──
    with dl_col1:
        if "fused_nib" in st.session_state:
            fused_nib = st.session_state["fused_nib"]
            buf = io.BytesIO()
            with tempfile.NamedTemporaryFile(suffix=".nii.gz", delete=False) as tmp:
                tmp_path = tmp.name
            nib.save(fused_nib, tmp_path)
            with open(tmp_path, "rb") as f:
                buf.write(f.read())
            os.unlink(tmp_path)
            buf.seek(0)
            st.download_button(
                "⬇ Fused NIfTI (.nii.gz)",
                data=buf.getvalue(),
                file_name="fused_brain_image.nii.gz",
                mime="application/gzip",
                use_container_width=True,
            )

    # ── Metrics TXT ──
    with dl_col2:
        if "fusion_metrics" in st.session_state:
            m     = st.session_state["fusion_metrics"]
            meth  = st.session_state.get("selected_fusion_method", "Unknown")
            txt   = f"PET-MRI Fusion Quality Metrics\n{'=' * 40}\nFusion Method: {meth}\n\n"
            for key, val in m.items():
                txt += f"{key.replace('_', ' ').title()}: {val:.6f}\n"
            st.download_button(
                "⬇ Metrics (.txt)",
                data=txt,
                file_name="fusion_metrics.txt",
                mime="text/plain",
                use_container_width=True,
            )

    # ── Comparison TXT ──
    with dl_col3:
        if "comparison_results" in st.session_state:
            comp = st.session_state["comparison_results"]
            ctxt = "PET-MRI Fusion Method Comparison\n" + "=" * 80 + "\n\n"
            for r in comp:
                ctxt += f"Method: {r['Method']}\n"
                ctxt += f"  Entropy:           {r['entropy']:.6f}\n"
                ctxt += f"  MRI SSIM:          {r['mri_ssim']:.6f}\n"
                ctxt += f"  PET SSIM:          {r['pet_ssim']:.6f}\n"
                ctxt += f"  Std Deviation:     {r['std']:.6f}\n"
                ctxt += f"  Spatial Frequency: {r['spatial_frequency']:.6f}\n"
                ctxt += "-" * 60 + "\n"
            st.download_button(
                "⬇ Comparison (.txt)",
                data=ctxt,
                file_name="fusion_comparison.txt",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            st.button(
                "⬇ Comparison (.txt)",
                disabled=True,
                help="Run comparison first",
                use_container_width=True,
            )

    # ── PNG Visualization ──
    with dl_col4:
        if (
            "fused_volume" in st.session_state
            and "mri_preprocessed" in st.session_state
        ):
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            mri_v   = st.session_state["mri_preprocessed"]
            pet_v   = st.session_state.get(
                "pet_registered",
                st.session_state.get("pet_preprocessed"),
            )
            fused_v = st.session_state["fused_volume"]
            mid_z   = mri_v.shape[2] // 2
            meth    = st.session_state.get("selected_fusion_method", "Fused")

            fig, axes = plt.subplots(1, 3, figsize=(15, 5), facecolor="#06101a")
            for ax in axes:
                ax.set_facecolor("#010c15")

            axes[0].imshow(normalize_slice(mri_v[:, :, mid_z]).T,
                           cmap="gray", origin="lower")
            axes[0].set_title("Brain MRI", fontsize=13, fontweight="bold",
                              color="#f0f9ff", pad=10)
            axes[0].axis("off")

            axes[1].imshow(normalize_slice(pet_v[:, :, mid_z]).T,
                           cmap="hot", origin="lower")
            axes[1].set_title("Brain PET", fontsize=13, fontweight="bold",
                              color="#f0f9ff", pad=10)
            axes[1].axis("off")

            axes[2].imshow(normalize_slice(fused_v[:, :, mid_z]).T,
                           cmap="gray", origin="lower")
            axes[2].set_title(meth, fontsize=13, fontweight="bold",
                              color="#f0f9ff", pad=10)
            axes[2].axis("off")

            plt.tight_layout(pad=1.5)
            png_buf = io.BytesIO()
            fig.savefig(png_buf, format="png", dpi=200, bbox_inches="tight",
                        facecolor=fig.get_facecolor())
            plt.close(fig)
            png_buf.seek(0)

            st.download_button(
                "⬇ Visualization (.png)",
                data=png_buf.getvalue(),
                file_name="fusion_visualization.png",
                mime="image/png",
                use_container_width=True,
            )

    st.markdown('</div>', unsafe_allow_html=True)
else:
    render_empty_state(
        icon="💾",
        title="Export Unavailable",
        description="Run the fusion pipeline to generate downloadable outputs."
    )

section_divider()


# ════════════════════════════════════════════════════════════════
# DISCLAIMER & FOOTER
# ════════════════════════════════════════════════════════════════

render_disclaimer()
