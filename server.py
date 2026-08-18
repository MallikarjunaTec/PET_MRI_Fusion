"""
server.py — Flask API server for PET–MRI Brain Image Fusion.

Serves the website/ static files and exposes REST endpoints that wrap
the existing src/ processing modules (preprocessing, registration,
fusion_methods, evaluation).
"""

import os
import sys
import json
import io
import base64
import traceback
from pathlib import Path

import numpy as np
import nibabel as nib
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt

from flask import Flask, request, jsonify, send_from_directory, send_file

# ── Ensure src/ is importable ────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.preprocessing import validate_nifti, preprocess_volume, normalize_image
from src.registration import register_pet_to_mri
from src.fusion_methods import FUSION_METHODS, FUSION_DESCRIPTIONS
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
    static_folder=str(ROOT_DIR / 'website'),
    static_url_path='',
)

app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB

# Directories
UPLOAD_DIR = ROOT_DIR / 'uploads'
OUTPUT_DIR = ROOT_DIR / 'outputs'
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ============================================================
# IN-MEMORY STATE
# ============================================================

session = {
    'mri_nib': None,       # nibabel image
    'pet_nib': None,
    'mri_data': None,      # preprocessed 3D numpy array
    'pet_data': None,
    'mri_affine': None,
    'pet_affine': None,
    'registered_pet': None, # 3D numpy array
    'fused_data': None,     # 3D numpy array
    'registration_info': None,
    'mri_meta': None,
    'pet_meta': None,
}


# ============================================================
# HELPERS
# ============================================================

def array_to_base64_png(slice_2d, colormap='gray'):
    """Convert a 2D numpy array to a base64-encoded PNG string."""
    fig, ax = plt.subplots(1, 1, figsize=(3, 3), dpi=96)
    ax.imshow(slice_2d.T, cmap=colormap, origin='lower', aspect='equal')
    ax.axis('off')
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0,
                facecolor='black', dpi=96)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def fused_composite_to_base64_png(mri_slice, pet_slice, fused_slice):
    """
    Create a color-composite image that blends MRI structure with PET
    metabolic activity, weighted by the fused data.

    - MRI provides grayscale structural base
    - PET provides warm color (metabolic activity)
    - Fused intensities control the blending

    Result: structural anatomy visible with colored metabolic overlay.
    """
    # Normalize all slices to [0, 1]
    def norm(s):
        s = s.astype(np.float32)
        mn, mx = s.min(), s.max()
        return (s - mn) / (mx - mn + 1e-8)

    mri_n = norm(mri_slice)
    pet_n = norm(pet_slice)
    fused_n = norm(fused_slice)

    # Build RGB composite:
    # R: PET metabolic (warm)
    # G: fused blended info
    # B: MRI structural (cool)
    # Then blend with a luminance base from fused for natural look
    alpha = 0.55  # PET color strength

    # Luminance base from fused image
    lum = fused_n

    r = np.clip(lum * (1 - alpha) + pet_n * alpha, 0, 1)
    g = np.clip(lum * (1 - alpha * 0.5) + pet_n * alpha * 0.35, 0, 1)
    b = np.clip(lum * (1 - alpha) + mri_n * alpha * 0.15, 0, 1)

    rgb = np.stack([r, g, b], axis=-1)

    fig, ax = plt.subplots(1, 1, figsize=(3, 3), dpi=96)
    ax.imshow(np.transpose(rgb, (1, 0, 2)), origin='lower', aspect='equal')
    ax.axis('off')
    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0,
                facecolor='black', dpi=96)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def get_slice(volume, axis, index):
    """Extract a 2D slice from a 3D volume."""
    if volume is None:
        return None
    index = max(0, min(index, volume.shape[{'axial': 2, 'coronal': 1, 'sagittal': 0}[axis]] - 1))
    if axis == 'axial':
        return volume[:, :, index]
    elif axis == 'coronal':
        return volume[:, index, :]
    else:  # sagittal
        return volume[index, :, :]


def build_meta_response(nib_img, validation):
    """Build a JSON-friendly metadata dict from a NiBabel image."""
    data = nib_img.get_fdata(dtype=np.float32)
    data = np.nan_to_num(data, nan=0.0, posinf=0.0, neginf=0.0)

    return {
        'shape': list(data.shape[:3]),
        'voxel_spacing': list(validation['voxel_spacing']) if validation['voxel_spacing'] else None,
        'intensity_min': float(np.min(data)),
        'intensity_max': float(np.max(data)),
        'mean': float(np.mean(data)),
        'std': float(np.std(data)),
        'dtype': validation['dtype'],
        'orientation': validation.get('orientation', 'Unknown'),
        'ndim': int(data.ndim),
    }


# ============================================================
# ROUTES — STATIC
# ============================================================

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


# ============================================================
# ROUTES — UPLOAD
# ============================================================

@app.route('/api/upload/<modality>', methods=['POST'])
def upload_file(modality):
    """Upload and validate a NIfTI file (modality = 'mri' or 'pet')."""
    if modality not in ('mri', 'pet'):
        return jsonify({'error': 'Invalid modality. Use mri or pet.'}), 400

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided.'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected.'}), 400

    # Save uploaded file
    filename = f'{modality}_upload.nii.gz' if file.filename.endswith('.gz') else f'{modality}_upload.nii'
    filepath = UPLOAD_DIR / filename
    file.save(str(filepath))

    # Load with nibabel
    try:
        nib_img = nib.load(str(filepath))
    except Exception as e:
        return jsonify({
            'error': f'Cannot load NIfTI file: {str(e)}',
            'reasons': [
                'Unsupported format',
                'Corrupted NIfTI file',
                'Missing image data',
            ]
        }), 400

    # Validate
    validation = validate_nifti(nib_img)
    if not validation['valid'] and any('3D' in e for e in validation['errors']):
        return jsonify({
            'error': 'Invalid NIfTI file.',
            'reasons': validation['errors'],
        }), 400

    # Preprocess
    preprocessed_data, preprocessed_img = preprocess_volume(nib_img)

    # Store in session
    if modality == 'mri':
        session['mri_nib'] = nib_img
        session['mri_data'] = preprocessed_data
        session['mri_affine'] = nib_img.affine.copy()
        session['mri_meta'] = build_meta_response(nib_img, validation)
    else:
        session['pet_nib'] = nib_img
        session['pet_data'] = preprocessed_data
        session['pet_affine'] = nib_img.affine.copy()
        session['pet_meta'] = build_meta_response(nib_img, validation)

    # Build response
    meta = build_meta_response(nib_img, validation)

    # Generate middle slice preview
    mid_slice_idx = preprocessed_data.shape[2] // 2
    slice_img = get_slice(preprocessed_data, 'axial', mid_slice_idx)
    meta['preview'] = array_to_base64_png(slice_img)

    return jsonify(meta)


# ============================================================
# ROUTES — SLICE VIEWER
# ============================================================

@app.route('/api/slice/<img_type>/<axis>/<int:index>')
def get_slice_image(img_type, axis, index):
    """Get a single 2D slice as base64 PNG."""
    if axis not in ('axial', 'coronal', 'sagittal'):
        return jsonify({'error': 'Invalid axis.'}), 400

    # For fused images, create a color composite blending MRI + PET
    if img_type == 'fused':
        fused_vol = session.get('fused_data')
        mri_vol = session.get('mri_data')
        pet_vol = session.get('registered_pet')
        if pet_vol is None:
            pet_vol = session.get('pet_data')

        if fused_vol is None:
            return jsonify({'error': 'Fused image not available.'}), 404

        fused_slice = get_slice(fused_vol, axis, index)
        if fused_slice is None:
            return jsonify({'error': 'Could not extract slice.'}), 500

        # If MRI and PET are available, create a color composite
        if mri_vol is not None and pet_vol is not None:
            mri_slice = get_slice(mri_vol, axis, index)
            pet_slice = get_slice(pet_vol, axis, index)
            if mri_slice is not None and pet_slice is not None:
                image_b64 = fused_composite_to_base64_png(mri_slice, pet_slice, fused_slice)
                return jsonify({'image': image_b64, 'index': index, 'axis': axis})

        # Fallback: render fused with inferno colormap
        image_b64 = array_to_base64_png(fused_slice, colormap='inferno')
        return jsonify({'image': image_b64, 'index': index, 'axis': axis})

    # Standard rendering for other image types
    volume = None
    cmap = 'gray'

    if img_type == 'mri':
        volume = session.get('mri_data')
    elif img_type == 'pet':
        volume = session.get('pet_data')
        cmap = 'hot'
    elif img_type == 'registered':
        volume = session.get('registered_pet')
        cmap = 'hot'
    else:
        return jsonify({'error': 'Invalid image type.'}), 400

    if volume is None:
        return jsonify({'error': f'{img_type} not available.'}), 404

    slice_data = get_slice(volume, axis, index)
    if slice_data is None:
        return jsonify({'error': 'Could not extract slice.'}), 500

    image_b64 = array_to_base64_png(slice_data, colormap=cmap)
    return jsonify({'image': image_b64, 'index': index, 'axis': axis})


# ============================================================
# ROUTES — FUSION
# ============================================================

@app.route('/api/fuse', methods=['POST'])
def run_fusion():
    """Run the full pipeline: register → fuse → evaluate."""
    if session['mri_data'] is None or session['pet_data'] is None:
        return jsonify({'error': 'Please upload both MRI and PET scans first.'}), 400

    data = request.get_json(silent=True) or {}
    method_name = data.get('method', 'Weighted Fusion')

    if method_name not in FUSION_METHODS:
        return jsonify({'error': f'Unknown method: {method_name}'}), 400

    mri = session['mri_data']
    pet = session['pet_data']

    # ── Registration ─────────────────────────────────────────
    try:
        reg_result = register_pet_to_mri(
            mri, pet,
            mri_affine=session.get('mri_affine'),
            pet_affine=session.get('pet_affine'),
        )
    except Exception as e:
        return jsonify({'error': f'Registration failed: {str(e)}'}), 500

    if reg_result['status'] != 'success' or reg_result['registered_pet'] is None:
        return jsonify({
            'error': 'PET → MRI registration failed.',
            'details': reg_result.get('error', 'Unknown error'),
        }), 500

    registered_pet = reg_result['registered_pet']
    session['registered_pet'] = registered_pet
    session['registration_info'] = reg_result

    # ── Fusion ───────────────────────────────────────────────
    try:
        fusion_func = FUSION_METHODS[method_name]
        fused = fusion_func(mri, registered_pet)
    except Exception as e:
        return jsonify({'error': f'Fusion failed: {str(e)}'}), 500

    session['fused_data'] = fused

    # Save fused NIfTI
    try:
        fused_nib = nib.Nifti1Image(fused, session['mri_affine'])
        nib.save(fused_nib, str(OUTPUT_DIR / 'fused_image.nii.gz'))

        reg_pet_nib = nib.Nifti1Image(registered_pet, session['mri_affine'])
        nib.save(reg_pet_nib, str(OUTPUT_DIR / 'registered_pet.nii.gz'))
    except Exception:
        pass  # Non-critical

    # ── Evaluation ───────────────────────────────────────────
    try:
        metrics = evaluate_fusion(mri, registered_pet, fused)
        # Add source metrics
        metrics['mri_entropy'] = calculate_entropy(mri)
        metrics['pet_entropy'] = calculate_entropy(registered_pet)
        metrics['mri_std'] = calculate_std(mri)
        metrics['pet_std'] = calculate_std(registered_pet)
        metrics['mri_sf'] = calculate_spatial_frequency(mri)
        metrics['pet_sf'] = calculate_spatial_frequency(registered_pet)
    except Exception as e:
        metrics = {'error': str(e)}

    # Save metrics report
    try:
        with open(str(OUTPUT_DIR / 'metrics_report.json'), 'w') as f:
            json.dump({
                'method': method_name,
                'metrics': {k: v for k, v in metrics.items() if isinstance(v, (int, float))},
            }, f, indent=2)
    except Exception:
        pass

    # Save middle slice PNG
    try:
        mid = fused.shape[2] // 2
        fig, ax = plt.subplots(1, 1, figsize=(4, 4), dpi=150)
        ax.imshow(fused[:, :, mid].T, cmap='gray', origin='lower')
        ax.set_title(f'Fused ({method_name}) — Slice {mid}', fontsize=10)
        ax.axis('off')
        fig.savefig(str(OUTPUT_DIR / 'fused_slice.png'), bbox_inches='tight',
                    facecolor='black', dpi=150)
        plt.close(fig)
    except Exception:
        pass

    return jsonify({
        'status': 'success',
        'method': method_name,
        'fused_shape': list(fused.shape),
        'metrics': metrics,
        'registration': {
            'status': reg_result['status'],
            'metric_value': reg_result['metric_value'],
            'iterations': reg_result['iterations'],
        },
        'downloads': {
            'fused_nifti': 'fused_image.nii.gz',
            'registered_pet': 'registered_pet.nii.gz',
            'metrics_report': 'metrics_report.json',
            'png_fused': 'fused_slice.png',
        },
    })


@app.route('/api/fuse/all', methods=['POST'])
def run_all_fusions():
    """Run all four fusion methods and return comparison metrics."""
    if session['mri_data'] is None or session['pet_data'] is None:
        return jsonify({'error': 'Please upload both MRI and PET scans first.'}), 400

    mri = session['mri_data']
    pet = session['pet_data']

    # ── Registration (once) ──────────────────────────────────
    if session.get('registered_pet') is None:
        try:
            reg_result = register_pet_to_mri(
                mri, pet,
                mri_affine=session.get('mri_affine'),
                pet_affine=session.get('pet_affine'),
            )
        except Exception as e:
            return jsonify({'error': f'Registration failed: {str(e)}'}), 500

        if reg_result['status'] != 'success' or reg_result['registered_pet'] is None:
            return jsonify({'error': 'Registration failed.'}), 500

        session['registered_pet'] = reg_result['registered_pet']
        session['registration_info'] = reg_result
    else:
        reg_result = session['registration_info']

    registered_pet = session['registered_pet']

    # ── Run all fusions ──────────────────────────────────────
    results = {}
    for method_name, fusion_func in FUSION_METHODS.items():
        try:
            fused = fusion_func(mri, registered_pet)
            metrics = evaluate_fusion(mri, registered_pet, fused)
            metrics['mri_entropy'] = calculate_entropy(mri)
            metrics['pet_entropy'] = calculate_entropy(registered_pet)
            metrics['mri_std'] = calculate_std(mri)
            metrics['pet_std'] = calculate_std(registered_pet)
            metrics['mri_sf'] = calculate_spatial_frequency(mri)
            metrics['pet_sf'] = calculate_spatial_frequency(registered_pet)

            results[method_name] = {
                'metrics': metrics,
                'status': 'success',
            }

            # Always store the latest fusion as the "active" one
            session['fused_data'] = fused

        except Exception as e:
            results[method_name] = {
                'metrics': None,
                'status': 'failed',
                'error': str(e),
            }

    # Save comparison report
    try:
        report = {}
        for m, r in results.items():
            if r['metrics']:
                report[m] = {k: v for k, v in r['metrics'].items() if isinstance(v, (int, float))}
        with open(str(OUTPUT_DIR / 'comparison_report.json'), 'w') as f:
            json.dump(report, f, indent=2)
    except Exception:
        pass

    # Save fused NIfTI of last method
    if session['fused_data'] is not None:
        try:
            fused_nib = nib.Nifti1Image(session['fused_data'], session['mri_affine'])
            nib.save(fused_nib, str(OUTPUT_DIR / 'fused_image.nii.gz'))

            reg_pet_nib = nib.Nifti1Image(registered_pet, session['mri_affine'])
            nib.save(reg_pet_nib, str(OUTPUT_DIR / 'registered_pet.nii.gz'))
        except Exception:
            pass

    return jsonify({
        'status': 'success',
        'results': results,
        'fused_shape': list(session['fused_data'].shape) if session['fused_data'] is not None else None,
        'registration': {
            'status': reg_result['status'] if isinstance(reg_result, dict) else 'unknown',
            'metric_value': reg_result.get('metric_value') if isinstance(reg_result, dict) else None,
            'iterations': reg_result.get('iterations') if isinstance(reg_result, dict) else None,
        },
        'downloads': {
            'fused_nifti': 'fused_image.nii.gz',
            'registered_pet': 'registered_pet.nii.gz',
            'metrics_report': 'comparison_report.json',
            'png_fused': 'fused_slice.png',
        },
    })


# ============================================================
# ROUTES — DOWNLOAD
# ============================================================

@app.route('/api/download/<file_key>')
def download_file(file_key):
    """Download a generated output file."""
    file_map = {
        'fused_nifti': 'fused_image.nii.gz',
        'registered_pet': 'registered_pet.nii.gz',
        'metrics_report': 'metrics_report.json',
        'comparison_report': 'comparison_report.json',
        'png_fused': 'fused_slice.png',
    }

    filename = file_map.get(file_key)
    if not filename:
        return jsonify({'error': 'Unknown file key.'}), 404

    filepath = OUTPUT_DIR / filename
    if not filepath.exists():
        return jsonify({'error': f'File not found: {filename}'}), 404

    return send_file(
        str(filepath),
        as_attachment=True,
        download_name=filename,
    )


# ============================================================
# ERROR HANDLERS
# ============================================================

@app.errorhandler(413)
def file_too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 200 MB.'}), 413


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error.'}), 500


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("  PET–MRI Brain Image Fusion — Web Server")
    print("=" * 60)
    print(f"  Website:  http://localhost:5000")
    print(f"  API:      http://localhost:5000/api/")
    print(f"  Uploads:  {UPLOAD_DIR}")
    print(f"  Outputs:  {OUTPUT_DIR}")
    print("=" * 60 + "\n")

    app.run(host='0.0.0.0', port=5000, debug=True)
