"""
registration.py — PET-to-MRI registration using SimpleITK.

Wraps the original register.py algorithm into an importable function.
Same parameters: Mattes Mutual Information, Gradient Descent optimizer,
multi-resolution with shrink factors [4, 2, 1].

Robust initialisation: sets image origin/spacing from affine, then uses
CenteredTransformInitializer with MOMENTS (centre-of-mass) mode so that
even images with very different sizes / resolutions overlap before
optimisation starts.
"""

import SimpleITK as sitk
import numpy as np


# ============================================================
# HELPERS
# ============================================================

def _affine_to_sitk_metadata(affine: np.ndarray):
    """
    Extract spacing, origin and direction cosines from a NiBabel-style
    4×4 affine matrix for a SimpleITK image.

    Returns (spacing, origin, direction) all as tuples/lists of floats.
    SimpleITK uses (x, y, z) ordering, same as NiBabel column-major.
    """
    # Column norms → voxel sizes
    spacing = tuple(float(np.linalg.norm(affine[:3, i])) for i in range(3))

    # Origin (translation column)
    origin = tuple(float(affine[i, 3]) for i in range(3))

    # Direction cosines (normalised columns, row-major for SimpleITK)
    direction = []
    for col in range(3):
        col_vec = affine[:3, col] / (spacing[col] if spacing[col] > 0 else 1.0)
        direction.extend(col_vec.tolist())

    return spacing, origin, direction


def _numpy_to_sitk(arr: np.ndarray, affine: np.ndarray = None) -> sitk.Image:
    """
    Convert a (x, y, z) numpy float32 array to a SimpleITK image,
    optionally applying spacing / origin / direction from an affine.
    """
    # SimpleITK stores arrays in (z, y, x) order
    sitk_img = sitk.GetImageFromArray(arr.astype(np.float32).transpose(2, 1, 0))

    if affine is not None:
        spacing, origin, direction = _affine_to_sitk_metadata(affine)
        sitk_img.SetSpacing(spacing)
        sitk_img.SetOrigin(origin)
        sitk_img.SetDirection(direction)
    else:
        # Default: 1 mm isotropic, origin at centre of volume so images
        # overlap even without affine information.
        sitk_img.SetSpacing((1.0, 1.0, 1.0))
        # Centre at origin
        cx = arr.shape[0] / 2.0
        cy = arr.shape[1] / 2.0
        cz = arr.shape[2] / 2.0
        sitk_img.SetOrigin((-cx, -cy, -cz))

    return sitk_img


# ============================================================
# REGISTRATION
# ============================================================

def register_pet_to_mri(
    mri_data: np.ndarray,
    pet_data: np.ndarray,
    mri_affine: np.ndarray = None,
    pet_affine: np.ndarray = None,
) -> dict:
    """
    Register PET image to MRI reference space using SimpleITK.

    Parameters:
        mri_data   : 3D numpy array (normalized MRI)
        pet_data   : 3D numpy array (normalized PET)
        mri_affine : 4×4 affine matrix for MRI (optional, uses identity if None)
        pet_affine : 4×4 affine matrix for PET (optional, uses identity if None)

    Returns:
        dict with:
            registered_pet : np.ndarray — registered PET volume
            metric_value   : float      — final metric value
            iterations     : int        — optimizer iterations used
            status         : str        — 'success' or 'failed'
            error          : str | None — error message if failed
    """
    result = {
        "registered_pet": None,
        "metric_value": None,
        "iterations": None,
        "status": "failed",
        "error": None,
    }

    try:
        # --------------------------------------------------
        # Build SimpleITK images with correct physical space
        # --------------------------------------------------
        fixed_image  = _numpy_to_sitk(mri_data, mri_affine)
        moving_image = _numpy_to_sitk(pet_data, pet_affine)

        # --------------------------------------------------
        # Initial alignment: try MOMENTS (centre-of-mass),
        # fall back to GEOMETRY if it throws.
        # MOMENTS is robust even when images have different
        # sizes — it aligns by intensity mass centres.
        # --------------------------------------------------
        try:
            initial_transform = sitk.CenteredTransformInitializer(
                fixed_image,
                moving_image,
                sitk.Euler3DTransform(),
                sitk.CenteredTransformInitializerFilter.MOMENTS,
            )
        except Exception:
            initial_transform = sitk.CenteredTransformInitializer(
                fixed_image,
                moving_image,
                sitk.Euler3DTransform(),
                sitk.CenteredTransformInitializerFilter.GEOMETRY,
            )

        # --------------------------------------------------
        # Registration method (same parameters as original)
        # --------------------------------------------------
        registration = sitk.ImageRegistrationMethod()

        # Similarity measurement — fewer bins for speed & stability
        registration.SetMetricAsMattesMutualInformation(numberOfHistogramBins=32)

        # Mask out near-zero background voxels from metric computation
        registration.SetMetricSamplingStrategy(registration.RANDOM)
        registration.SetMetricSamplingPercentage(0.10)

        # Interpolation
        registration.SetInterpolator(sitk.sitkLinear)

        # Optimizer
        registration.SetOptimizerAsGradientDescent(
            learningRate=1.0,
            numberOfIterations=200,
            convergenceMinimumValue=1e-6,
            convergenceWindowSize=10,
        )
        registration.SetOptimizerScalesFromPhysicalShift()

        # Multi-resolution pyramid
        registration.SetShrinkFactorsPerLevel(shrinkFactors=[4, 2, 1])
        registration.SetSmoothingSigmasPerLevel(smoothingSigmas=[2, 1, 0])
        registration.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

        registration.SetInitialTransform(initial_transform, inPlace=False)

        # --------------------------------------------------
        # Execute registration
        # --------------------------------------------------
        final_transform = registration.Execute(fixed_image, moving_image)

        result["metric_value"] = float(registration.GetMetricValue())
        result["iterations"]   = int(registration.GetOptimizerIteration())

        # --------------------------------------------------
        # Resample PET into MRI space
        # --------------------------------------------------
        registered_pet = sitk.Resample(
            moving_image,
            fixed_image,
            final_transform,
            sitk.sitkLinear,
            0.0,
            moving_image.GetPixelID(),
        )

        # Convert back to numpy (x, y, z)
        registered_array = sitk.GetArrayFromImage(registered_pet).transpose(2, 1, 0)

        result["registered_pet"] = registered_array.astype(np.float32)
        result["status"] = "success"

    except Exception as e:
        result["status"] = "failed"
        result["error"]  = str(e)

    return result
