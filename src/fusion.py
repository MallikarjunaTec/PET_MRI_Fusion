import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# ---------------------------------------
# File paths
# ---------------------------------------

MRI_PATH = r"E:\PET_MRI_Fusion\results\mri_normalized.nii.gz"
PET_PATH = r"E:\PET_MRI_Fusion\results\pet_normalized.nii.gz"

RESULTS_DIR = Path(r"E:\PET_MRI_Fusion\results")


# ---------------------------------------
# Load normalized MRI
# ---------------------------------------

print("Loading normalized MRI...")

mri_img = nib.load(MRI_PATH)
mri_data = mri_img.get_fdata()

print("MRI shape:", mri_data.shape)


# ---------------------------------------
# Load normalized PET
# ---------------------------------------

print("\nLoading normalized PET...")

pet_img = nib.load(PET_PATH)
pet_data = pet_img.get_fdata()

print("PET shape:", pet_data.shape)


# ---------------------------------------
# Check dimensions
# ---------------------------------------

if mri_data.shape != pet_data.shape:
    raise ValueError("MRI and PET dimensions do not match!")

print("\nMRI and PET dimensions match.")


# ---------------------------------------
# Weighted fusion
# ---------------------------------------

MRI_WEIGHT = 0.5
PET_WEIGHT = 0.5

print("\nPerforming fusion...")
print("MRI weight:", MRI_WEIGHT)
print("PET weight:", PET_WEIGHT)

fused_data = (
    MRI_WEIGHT * mri_data
    + PET_WEIGHT * pet_data
)


# ---------------------------------------
# Normalize fused image
# ---------------------------------------

fused_min = np.min(fused_data)
fused_max = np.max(fused_data)

fused_data = (
    fused_data - fused_min
) / (
    fused_max - fused_min
)

print("Fusion completed.")


# ---------------------------------------
# Save fused 3D NIfTI image
# ---------------------------------------

fused_path = RESULTS_DIR / "fused_image.nii.gz"

fused_img = nib.Nifti1Image(
    fused_data.astype(np.float32),
    mri_img.affine,
    mri_img.header
)

nib.save(fused_img, fused_path)

print("\nFused 3D image saved:")
print(fused_path)


# ---------------------------------------
# Select middle slice
# ---------------------------------------

slice_index = fused_data.shape[2] // 2

mri_slice = mri_data[:, :, slice_index]
pet_slice = pet_data[:, :, slice_index]
fused_slice = fused_data[:, :, slice_index]


# ---------------------------------------
# Display MRI, PET and Fused image
# ---------------------------------------

plt.figure(figsize=(15, 5))


# MRI
plt.subplot(1, 3, 1)

plt.imshow(
    np.rot90(mri_slice),
    cmap="gray",
    vmin=0,
    vmax=1
)

plt.title("MRI")
plt.axis("off")


# PET
plt.subplot(1, 3, 2)

plt.imshow(
    np.rot90(pet_slice),
    cmap="hot",
    vmin=0,
    vmax=1
)

plt.title("PET")
plt.axis("off")


# Fused
plt.subplot(1, 3, 3)

plt.imshow(
    np.rot90(fused_slice),
    cmap="gray",
    vmin=0,
    vmax=1
)

plt.title("PET + MRI Fused")
plt.axis("off")


plt.tight_layout()
plt.show()