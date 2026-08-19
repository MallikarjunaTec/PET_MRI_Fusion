"""
server.py — Flask API server for PET–MRI Brain Image Fusion.

Serves the website/ static files and exposes REST endpoints that wrap
the existing src/ processing modules.
"""

import os
import sys
import json
import io
import base64
from pathlib import Path

import numpy as np
import nibabel as nib

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from flask import Flask, request, jsonify, send_from_directory, send_file


# ============================================================
# PROJECT SETUP
# ============================================================

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.preprocessing import validate_nifti, preprocess_volume
from src.registration import register_pet_to_mri
from src.fusion_methods import FUSION_METHODS
from src.evaluation import (
    evaluate_fusion,
    calculate_entropy,
    calculate_std,
    calculate_spatial_frequency,
)


# ============================================================
# APP SETUP
# ============================================================

app = Flask(
    __name__,
    static_folder=str(ROOT_DIR / "website"),
    static_url_path=""
)

app.config["MAX_CONTENT_LENGTH"] = 200 * 1024 * 1024


# ============================================================
# DIRECTORIES
# ============================================================

UPLOAD_DIR = ROOT_DIR / "uploads"
OUTPUT_DIR = ROOT_DIR / "outputs"

UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)


# ============================================================
# IN-MEMORY SESSION
# ============================================================
#
# Large NumPy arrays are NOT stored directly in the Flask
# session/state anymore. They are saved as .npy files.
#

session = {
    "mri_path": None,
    "pet_path": None,

    "mri_data_path": None,
    "pet_data_path": None,

    "mri_affine_path": None,
    "pet_affine_path": None,

    "registered_pet_path": None,
    "fused_data_path": None,

    "registration_info": None,

    "mri_meta": None,
    "pet_meta": None,
}


# ============================================================
# ARRAY / FILE HELPERS
# ============================================================

def save_array(array, path):
    """Save NumPy array to disk."""
    np.save(str(path), array)


def load_array(path):
    """Load NumPy array from disk."""
    if not path:
        return None

    path = Path(path)

    if not path.exists():
        return None

    return np.load(str(path))


def save_affine(affine, path):
    """Save affine matrix to disk."""
    np.save(str(path), affine)


def load_affine(path):
    """Load affine matrix from disk."""
    if not path:
        return None

    path = Path(path)

    if not path.exists():
        return None

    return np.load(str(path))


def get_mri_data():
    return load_array(session.get("mri_data_path"))


def get_pet_data():
    return load_array(session.get("pet_data_path"))


def get_registered_pet():
    return load_array(session.get("registered_pet_path"))


def get_fused_data():
    return load_array(session.get("fused_data_path"))


def get_mri_affine():
    return load_affine(session.get("mri_affine_path"))


def get_pet_affine():
    return load_affine(session.get("pet_affine_path"))


# ============================================================
# IMAGE HELPERS
# ============================================================

def array_to_base64_png(slice_2d, colormap="gray"):
    """Convert a 2D NumPy slice to a base64 PNG."""

    if slice_2d is None:
        return None

    fig, ax = plt.subplots(
        1,
        1,
        figsize=(3, 3),
        dpi=96
    )

    ax.imshow(
        slice_2d.T,
        cmap=colormap,
        origin="lower",
        aspect="equal"
    )

    ax.axis("off")

    fig.subplots_adjust(
        left=0,
        right=1,
        top=1,
        bottom=0
    )

    buf = io.BytesIO()

    fig.savefig(
        buf,
        format="png",
        bbox_inches="tight",
        pad_inches=0,
        facecolor="black",
        dpi=96
    )

    plt.close(fig)

    buf.seek(0)

    return base64.b64encode(
        buf.read()
    ).decode("utf-8")


def fused_composite_to_base64_png(
    mri_slice,
    pet_slice,
    fused_slice
):
    """
    Create a color composite using MRI, PET and fused data.
    """

    def norm(s):
        s = np.asarray(
            s,
            dtype=np.float32
        )

        mn = np.min(s)
        mx = np.max(s)

        return (s - mn) / (mx - mn + 1e-8)

    mri_n = norm(mri_slice)
    pet_n = norm(pet_slice)
    fused_n = norm(fused_slice)

    alpha = 0.55

    lum = fused_n

    r = np.clip(
        lum * (1 - alpha) +
        pet_n * alpha,
        0,
        1
    )

    g = np.clip(
        lum * (1 - alpha * 0.5) +
        pet_n * alpha * 0.35,
        0,
        1
    )

    b = np.clip(
        lum * (1 - alpha) +
        mri_n * alpha * 0.15,
        0,
        1
    )

    rgb = np.stack(
        [r, g, b],
        axis=-1
    )

    fig, ax = plt.subplots(
        1,
        1,
        figsize=(3, 3),
        dpi=96
    )

    ax.imshow(
        np.transpose(
            rgb,
            (1, 0, 2)
        ),
        origin="lower",
        aspect="equal"
    )

    ax.axis("off")

    fig.subplots_adjust(
        left=0,
        right=1,
        top=1,
        bottom=0
    )

    buf = io.BytesIO()

    fig.savefig(
        buf,
        format="png",
        bbox_inches="tight",
        pad_inches=0,
        facecolor="black",
        dpi=96
    )

    plt.close(fig)

    buf.seek(0)

    return base64.b64encode(
        buf.read()
    ).decode("utf-8")


def get_slice(volume, axis, index):
    """Extract a 2D slice from a 3D volume."""

    if volume is None:
        return None

    axis_map = {
        "axial": 2,
        "coronal": 1,
        "sagittal": 0
    }

    if axis not in axis_map:
        return None

    axis_num = axis_map[axis]

    max_index = volume.shape[axis_num] - 1

    index = max(
        0,
        min(index, max_index)
    )

    if axis == "axial":
        return volume[:, :, index]

    if axis == "coronal":
        return volume[:, index, :]

    return volume[index, :, :]


def build_meta_response(
    nib_img,
    validation
):
    """Build JSON-safe image metadata."""

    data = nib_img.get_fdata(
        dtype=np.float32
    )

    data = np.nan_to_num(
        data,
        nan=0.0,
        posinf=0.0,
        neginf=0.0
    )

    return {
        "shape": list(data.shape[:3]),

        "voxel_spacing": (
            list(validation["voxel_spacing"])
            if validation.get("voxel_spacing")
            else None
        ),

        "intensity_min": float(
            np.min(data)
        ),

        "intensity_max": float(
            np.max(data)
        ),

        "mean": float(
            np.mean(data)
        ),

        "std": float(
            np.std(data)
        ),

        "dtype": validation.get(
            "dtype",
            "Unknown"
        ),

        "orientation": validation.get(
            "orientation",
            "Unknown"
        ),

        "ndim": int(
            data.ndim
        ),
    }


# ============================================================
# STATIC ROUTE
# ============================================================

@app.route("/")
def index():
    return send_from_directory(
        app.static_folder,
        "index.html"
    )


# ============================================================
# UPLOAD ROUTE
# ============================================================

@app.route(
    "/api/upload/<modality>",
    methods=["POST"]
)
def upload_file(modality):

    if modality not in ("mri", "pet"):
        return jsonify({
            "error": "Invalid modality. Use mri or pet."
        }), 400

    if "file" not in request.files:
        return jsonify({
            "error": "No file provided."
        }), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({
            "error": "No file selected."
        }), 400

    # --------------------------------------------------------
    # Save uploaded file
    # --------------------------------------------------------

    if file.filename.endswith(".gz"):
        filename = f"{modality}_upload.nii.gz"
    else:
        filename = f"{modality}_upload.nii"

    filepath = UPLOAD_DIR / filename

    file.save(str(filepath))

    # --------------------------------------------------------
    # Load NIfTI
    # --------------------------------------------------------

    try:
        nib_img = nib.load(
            str(filepath)
        )

    except Exception as e:
        return jsonify({
            "error": f"Cannot load NIfTI file: {str(e)}"
        }), 400

    # --------------------------------------------------------
    # Validate
    # --------------------------------------------------------

    try:
        validation = validate_nifti(
            nib_img
        )
    except Exception as e:
        return jsonify({
            "error": f"Validation failed: {str(e)}"
        }), 400

    if (
        not validation["valid"]
        and any(
            "3D" in error
            for error in validation["errors"]
        )
    ):
        return jsonify({
            "error": "Invalid NIfTI file.",
            "reasons": validation["errors"]
        }), 400

    # --------------------------------------------------------
    # Preprocess
    # --------------------------------------------------------

    try:
        preprocessed_data, _ = preprocess_volume(
            nib_img
        )

        preprocessed_data = np.asarray(
            preprocessed_data,
            dtype=np.float32
        )

    except Exception as e:
        return jsonify({
            "error": f"Preprocessing failed: {str(e)}"
        }), 500

    # --------------------------------------------------------
    # Save data to disk
    # --------------------------------------------------------

    if modality == "mri":

        data_path = (
            UPLOAD_DIR /
            "mri_preprocessed.npy"
        )

        affine_path = (
            UPLOAD_DIR /
            "mri_affine.npy"
        )

        save_array(
            preprocessed_data,
            data_path
        )

        save_affine(
            nib_img.affine.copy(),
            affine_path
        )

        session["mri_path"] = str(filepath)
        session["mri_data_path"] = str(data_path)
        session["mri_affine_path"] = str(affine_path)

        session["mri_meta"] = build_meta_response(
            nib_img,
            validation
        )

    else:

        data_path = (
            UPLOAD_DIR /
            "pet_preprocessed.npy"
        )

        affine_path = (
            UPLOAD_DIR /
            "pet_affine.npy"
        )

        save_array(
            preprocessed_data,
            data_path
        )

        save_affine(
            nib_img.affine.copy(),
            affine_path
        )

        session["pet_path"] = str(filepath)
        session["pet_data_path"] = str(data_path)
        session["pet_affine_path"] = str(affine_path)

        session["pet_meta"] = build_meta_response(
            nib_img,
            validation
        )

    # --------------------------------------------------------
    # Preview
    # --------------------------------------------------------

    meta = build_meta_response(
        nib_img,
        validation
    )

    mid_slice_idx = (
        preprocessed_data.shape[2] // 2
    )

    slice_img = get_slice(
        preprocessed_data,
        "axial",
        mid_slice_idx
    )

    meta["preview"] = array_to_base64_png(
        slice_img
    )

    return jsonify(meta)


# ============================================================
# SLICE VIEWER
# ============================================================

@app.route(
    "/api/slice/<img_type>/<axis>/<int:index>"
)
def get_slice_image(
    img_type,
    axis,
    index
):

    if axis not in (
        "axial",
        "coronal",
        "sagittal"
    ):
        return jsonify({
            "error": "Invalid axis."
        }), 400

    # --------------------------------------------------------
    # FUSED
    # --------------------------------------------------------

    if img_type == "fused":

        fused_vol = get_fused_data()
        mri_vol = get_mri_data()
        pet_vol = get_registered_pet()

        if pet_vol is None:
            pet_vol = get_pet_data()

        if fused_vol is None:
            return jsonify({
                "error": "Fused image not available."
            }), 404

        fused_slice = get_slice(
            fused_vol,
            axis,
            index
        )

        if fused_slice is None:
            return jsonify({
                "error": "Could not extract fused slice."
            }), 500

        if (
            mri_vol is not None
            and pet_vol is not None
        ):

            mri_slice = get_slice(
                mri_vol,
                axis,
                index
            )

            pet_slice = get_slice(
                pet_vol,
                axis,
                index
            )

            if (
                mri_slice is not None
                and pet_slice is not None
            ):

                image_b64 = (
                    fused_composite_to_base64_png(
                        mri_slice,
                        pet_slice,
                        fused_slice
                    )
                )

                return jsonify({
                    "image": image_b64,
                    "index": index,
                    "axis": axis
                })

        image_b64 = array_to_base64_png(
            fused_slice,
            colormap="inferno"
        )

        return jsonify({
            "image": image_b64,
            "index": index,
            "axis": axis
        })

    # --------------------------------------------------------
    # NORMAL IMAGES
    # --------------------------------------------------------

    volume = None
    cmap = "gray"

    if img_type == "mri":

        volume = get_mri_data()
        cmap = "gray"

    elif img_type == "pet":

        volume = get_pet_data()
        cmap = "hot"

    elif img_type == "registered":

        volume = get_registered_pet()
        cmap = "hot"

    else:

        return jsonify({
            "error": "Invalid image type."
        }), 400

    if volume is None:
        return jsonify({
            "error": f"{img_type} not available."
        }), 404

    slice_data = get_slice(
        volume,
        axis,
        index
    )

    if slice_data is None:
        return jsonify({
            "error": "Could not extract slice."
        }), 500

    image_b64 = array_to_base64_png(
        slice_data,
        colormap=cmap
    )

    return jsonify({
        "image": image_b64,
        "index": index,
        "axis": axis
    })


# ============================================================
# SINGLE FUSION
# ============================================================

@app.route(
    "/api/fuse",
    methods=["POST"]
)
def run_fusion():

    mri = get_mri_data()
    pet = get_pet_data()

    if mri is None or pet is None:
        return jsonify({
            "error": "Please upload both MRI and PET scans first."
        }), 400

    data = request.get_json(
        silent=True
    ) or {}

    method_name = data.get(
        "method",
        "Weighted Fusion"
    )

    if method_name not in FUSION_METHODS:
        return jsonify({
            "error": f"Unknown method: {method_name}"
        }), 400

    # --------------------------------------------------------
    # Registration
    # --------------------------------------------------------

    try:

        reg_result = register_pet_to_mri(
            mri,
            pet,
            mri_affine=get_mri_affine(),
            pet_affine=get_pet_affine()
        )

    except Exception as e:

        return jsonify({
            "error": f"Registration failed: {str(e)}"
        }), 500

    if (
        reg_result.get("status") != "success"
        or reg_result.get("registered_pet") is None
    ):

        return jsonify({
            "error": "PET → MRI registration failed.",
            "details": reg_result.get(
                "error",
                "Unknown error"
            )
        }), 500

    registered_pet = np.asarray(
        reg_result["registered_pet"],
        dtype=np.float32
    )

    # Save registered PET
    registered_pet_path = (
        OUTPUT_DIR /
        "registered_pet.npy"
    )

    save_array(
        registered_pet,
        registered_pet_path
    )

    session["registered_pet_path"] = str(
        registered_pet_path
    )

    session["registration_info"] = {
        "status": reg_result.get(
            "status",
            "unknown"
        ),
        "metric_value": reg_result.get(
            "metric_value"
        ),
        "iterations": reg_result.get(
            "iterations"
        )
    }

    # --------------------------------------------------------
    # Fusion
    # --------------------------------------------------------

    try:

        fusion_func = FUSION_METHODS[
            method_name
        ]

        fused = fusion_func(
            mri,
            registered_pet
        )

        fused = np.asarray(
            fused,
            dtype=np.float32
        )

    except Exception as e:

        return jsonify({
            "error": f"Fusion failed: {str(e)}"
        }), 500

    fused_data_path = (
        OUTPUT_DIR /
        "fused_data.npy"
    )

    save_array(
        fused,
        fused_data_path
    )

    session["fused_data_path"] = str(
        fused_data_path
    )

    # --------------------------------------------------------
    # Save NIfTI outputs
    # --------------------------------------------------------

    try:

        mri_affine = get_mri_affine()

        fused_nib = nib.Nifti1Image(
            fused,
            mri_affine
        )

        nib.save(
            fused_nib,
            str(
                OUTPUT_DIR /
                "fused_image.nii.gz"
            )
        )

        reg_pet_nib = nib.Nifti1Image(
            registered_pet,
            mri_affine
        )

        nib.save(
            reg_pet_nib,
            str(
                OUTPUT_DIR /
                "registered_pet.nii.gz"
            )
        )

    except Exception as e:

        print(
            f"Warning: Could not save NIfTI outputs: {e}"
        )

    # --------------------------------------------------------
    # Evaluation
    # --------------------------------------------------------

    try:

        metrics = evaluate_fusion(
            mri,
            registered_pet,
            fused
        )

        metrics["mri_entropy"] = (
            calculate_entropy(mri)
        )

        metrics["pet_entropy"] = (
            calculate_entropy(registered_pet)
        )

        metrics["mri_std"] = (
            calculate_std(mri)
        )

        metrics["pet_std"] = (
            calculate_std(registered_pet)
        )

        metrics["mri_sf"] = (
            calculate_spatial_frequency(mri)
        )

        metrics["pet_sf"] = (
            calculate_spatial_frequency(
                registered_pet
            )
        )

    except Exception as e:

        metrics = {
            "error": str(e)
        }

    # --------------------------------------------------------
    # Save metrics
    # --------------------------------------------------------

    try:

        clean_metrics = {
            k: float(v)
            for k, v in metrics.items()
            if isinstance(
                v,
                (int, float, np.integer, np.floating)
            )
        }

        with open(
            OUTPUT_DIR /
            "metrics_report.json",
            "w"
        ) as f:

            json.dump(
                {
                    "method": method_name,
                    "metrics": clean_metrics
                },
                f,
                indent=2
            )

    except Exception as e:

        print(
            f"Warning: Could not save metrics: {e}"
        )

    # --------------------------------------------------------
    # Save PNG
    # --------------------------------------------------------

    try:

        mid = fused.shape[2] // 2

        fig, ax = plt.subplots(
            1,
            1,
            figsize=(4, 4),
            dpi=150
        )

        ax.imshow(
            fused[:, :, mid].T,
            cmap="gray",
            origin="lower"
        )

        ax.set_title(
            f"Fused ({method_name}) — Slice {mid}",
            fontsize=10
        )

        ax.axis("off")

        fig.savefig(
            str(
                OUTPUT_DIR /
                "fused_slice.png"
            ),
            bbox_inches="tight",
            facecolor="black",
            dpi=150
        )

        plt.close(fig)

    except Exception as e:

        print(
            f"Warning: Could not save PNG: {e}"
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({

        "status": "success",

        "method": method_name,

        "fused_shape": list(
            fused.shape
        ),

        "metrics": metrics,

        "registration": {
            "status": reg_result.get(
                "status"
            ),
            "metric_value": reg_result.get(
                "metric_value"
            ),
            "iterations": reg_result.get(
                "iterations"
            )
        },

        "downloads": {
            "fused_nifti":
                "fused_image.nii.gz",

            "registered_pet":
                "registered_pet.nii.gz",

            "metrics_report":
                "metrics_report.json",

            "png_fused":
                "fused_slice.png"
        }
    })


# ============================================================
# ALL FUSION METHODS
# ============================================================

@app.route(
    "/api/fuse/all",
    methods=["POST"]
)
def run_all_fusions():

    mri = get_mri_data()
    pet = get_pet_data()

    if mri is None or pet is None:
        return jsonify({
            "error": "Please upload both MRI and PET scans first."
        }), 400

    # --------------------------------------------------------
    # Registration once
    # --------------------------------------------------------

    existing_registered = get_registered_pet()

    if existing_registered is None:

        try:

            reg_result = register_pet_to_mri(
                mri,
                pet,
                mri_affine=get_mri_affine(),
                pet_affine=get_pet_affine()
            )

        except Exception as e:

            return jsonify({
                "error": f"Registration failed: {str(e)}"
            }), 500

        if (
            reg_result.get("status") != "success"
            or reg_result.get("registered_pet") is None
        ):

            return jsonify({
                "error": "Registration failed."
            }), 500

        registered_pet = np.asarray(
            reg_result["registered_pet"],
            dtype=np.float32
        )

        registered_pet_path = (
            OUTPUT_DIR /
            "registered_pet.npy"
        )

        save_array(
            registered_pet,
            registered_pet_path
        )

        session["registered_pet_path"] = str(
            registered_pet_path
        )

        session["registration_info"] = {
            "status": reg_result.get(
                "status"
            ),
            "metric_value": reg_result.get(
                "metric_value"
            ),
            "iterations": reg_result.get(
                "iterations"
            )
        }

    else:

        registered_pet = existing_registered

        info = session.get(
            "registration_info"
        )

        if info is None:

            info = {
                "status": "success",
                "metric_value": None,
                "iterations": None
            }

            session["registration_info"] = info

        reg_result = info

    # --------------------------------------------------------
    # Run all fusion methods
    # --------------------------------------------------------

    results = {}

    last_fused = None

    for method_name, fusion_func in FUSION_METHODS.items():

        try:

            fused = fusion_func(
                mri,
                registered_pet
            )

            fused = np.asarray(
                fused,
                dtype=np.float32
            )

            metrics = evaluate_fusion(
                mri,
                registered_pet,
                fused
            )

            metrics["mri_entropy"] = (
                calculate_entropy(mri)
            )

            metrics["pet_entropy"] = (
                calculate_entropy(
                    registered_pet
                )
            )

            metrics["mri_std"] = (
                calculate_std(mri)
            )

            metrics["pet_std"] = (
                calculate_std(
                    registered_pet
                )
            )

            metrics["mri_sf"] = (
                calculate_spatial_frequency(
                    mri
                )
            )

            metrics["pet_sf"] = (
                calculate_spatial_frequency(
                    registered_pet
                )
            )

            results[method_name] = {
                "metrics": metrics,
                "status": "success"
            }

            last_fused = fused

        except Exception as e:

            results[method_name] = {
                "metrics": None,
                "status": "failed",
                "error": str(e)
            }

    # --------------------------------------------------------
    # Save last fused result
    # --------------------------------------------------------

    if last_fused is not None:

        fused_data_path = (
            OUTPUT_DIR /
            "fused_data.npy"
        )

        save_array(
            last_fused,
            fused_data_path
        )

        session["fused_data_path"] = str(
            fused_data_path
        )

        try:

            mri_affine = get_mri_affine()

            fused_nib = nib.Nifti1Image(
                last_fused,
                mri_affine
            )

            nib.save(
                fused_nib,
                str(
                    OUTPUT_DIR /
                    "fused_image.nii.gz"
                )
            )

            reg_pet_nib = nib.Nifti1Image(
                registered_pet,
                mri_affine
            )

            nib.save(
                reg_pet_nib,
                str(
                    OUTPUT_DIR /
                    "registered_pet.nii.gz"
                )
            )

            mid = (
                last_fused.shape[2] // 2
            )

            fig, ax = plt.subplots(
                1,
                1,
                figsize=(4, 4),
                dpi=150
            )

            ax.imshow(
                last_fused[:, :, mid].T,
                cmap="gray",
                origin="lower"
            )

            ax.axis("off")

            fig.savefig(
                str(
                    OUTPUT_DIR /
                    "fused_slice.png"
                ),
                bbox_inches="tight",
                facecolor="black",
                dpi=150
            )

            plt.close(fig)

        except Exception as e:

            print(
                f"Warning: Could not save comparison outputs: {e}"
            )

    # --------------------------------------------------------
    # Save comparison report
    # --------------------------------------------------------

    try:

        report = {}

        for method_name, result in results.items():

            if result.get("metrics"):

                report[method_name] = {
                    k: float(v)
                    for k, v in result["metrics"].items()
                    if isinstance(
                        v,
                        (
                            int,
                            float,
                            np.integer,
                            np.floating
                        )
                    )
                }

        with open(
            OUTPUT_DIR /
            "comparison_report.json",
            "w"
        ) as f:

            json.dump(
                report,
                f,
                indent=2
            )

    except Exception as e:

        print(
            f"Warning: Could not save comparison report: {e}"
        )

    # --------------------------------------------------------
    # Response
    # --------------------------------------------------------

    return jsonify({

        "status": "success",

        "results": results,

        "fused_shape": (
            list(last_fused.shape)
            if last_fused is not None
            else None
        ),

        "registration": {
            "status": reg_result.get(
                "status",
                "unknown"
            ),

            "metric_value": reg_result.get(
                "metric_value"
            ),

            "iterations": reg_result.get(
                "iterations"
            )
        },

        "downloads": {
            "fused_nifti":
                "fused_image.nii.gz",

            "registered_pet":
                "registered_pet.nii.gz",

            "metrics_report":
                "comparison_report.json",

            "png_fused":
                "fused_slice.png"
        }
    })


# ============================================================
# DOWNLOAD
# ============================================================

@app.route(
    "/api/download/<file_key>"
)
def download_file(file_key):

    file_map = {

        "fused_nifti":
            "fused_image.nii.gz",

        "registered_pet":
            "registered_pet.nii.gz",

        "metrics_report":
            "metrics_report.json",

        "comparison_report":
            "comparison_report.json",

        "png_fused":
            "fused_slice.png"
    }

    filename = file_map.get(
        file_key
    )

    if not filename:

        return jsonify({
            "error": "Unknown file key."
        }), 404

    filepath = (
        OUTPUT_DIR /
        filename
    )

    if not filepath.exists():

        return jsonify({
            "error": f"File not found: {filename}"
        }), 404

    return send_file(
        str(filepath),
        as_attachment=True,
        download_name=filename
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(413)
def file_too_large(e):

    return jsonify({
        "error":
            "File too large. Maximum size is 200 MB."
    }), 413


@app.errorhandler(500)
def internal_error(e):

    return jsonify({
        "error":
            "Internal server error."
    }), 500


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("\n" + "=" * 60)

    print(
        "  PET–MRI Brain Image Fusion — Web Server"
    )

    print("=" * 60)

    print(
        "  Website:  http://localhost:5000"
    )

    print(
        "  API:      http://localhost:5000/api/"
    )

    print(
        f"  Uploads:  {UPLOAD_DIR}"
    )

    print(
        f"  Outputs:  {OUTPUT_DIR}"
    )

    print("=" * 60 + "\n")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True
    )