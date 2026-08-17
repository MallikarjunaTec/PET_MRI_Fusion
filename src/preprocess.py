import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path


# -----------------------------------
# File paths
# -----------------------------------

MRI_PATH = r"E:\PET_MRI_Fusion\dataset\subject04\t1.nii.gz"
PET_PATH = r"E:\PET_MRI_Fusion\dataset\subject04\image_0.nii.gz"

RESULTS_DIR = Path(r"E:\PET_MRI_Fusion\results")
RESULTS_DIR.mkdir(exist_ok=True)


# -----------------------------------
# Normalization function
# -----------------------------------

def normalize_image(image):
    """
    Normalize image intensity to the range 0-1.
    """

    image_min = np.min(image)
    image_max = np.max(image)

    if image_max == image_min:
        return np.zeros_like(image)

    normalized = (image - image_min) / (image_max - image_min)

    return normalized


# -----------------------------------
# Load MRI
# -----------------------------------

print("Loading MRI...")

mri_img = nib.load(MRI_PATH)
mri_data = mri_img.get_fdata()

print("MRI shape:", mri_data.shape)


# -----------------------------------
# Load PET
# -----------------------------------

print("\nLoading PET...")

pet_img = nib.load(PET_PATH)
pet_data = pet_img.get_fdata()

print("PET shape:", pet_data.shape)


# -----------------------------------
# Normalize
# -----------------------------------

print("\nNormalizing MRI...")

mri_normalized = normalize_image(mri_data)

print("MRI normalization complete.")


print("\nNormalizing PET...")

pet_normalized = normalize_image(pet_data)

print("PET normalization complete.")


# -----------------------------------
# Save normalized MRI
# -----------------------------------

mri_output = RESULTS_DIR / "mri_normalized.nii.gz"

mri_normalized_img = nib.Nifti1Image(
    mri_normalized.astype(np.float32),
    mri_img.affine,
    mri_img.header
)

nib.save(mri_normalized_img, mri_output)

print("\nSaved:")
print(mri_output)


# -----------------------------------
# Save normalized PET
# -----------------------------------

pet_output = RESULTS_DIR / "pet_normalized.nii.gz"

pet_normalized_img = nib.Nifti1Image(
    pet_normalized.astype(np.float32),
    pet_img.affine,
    pet_img.header
)

nib.save(pet_normalized_img, pet_output)

print("Saved:")
print(pet_output)


# -----------------------------------
# Display normalized images
# -----------------------------------

slice_index = mri_normalized.shape[2] // 2

mri_slice = mri_normalized[:, :, slice_index]
pet_slice = pet_normalized[:, :, slice_index]


plt.figure(figsize=(12, 5))


# MRI

plt.subplot(1, 2, 1)

plt.imshow(
    np.rot90(mri_slice),
    cmap="gray",
    vmin=0,
    vmax=1
)

plt.title("Normalized MRI")
plt.axis("off")


# PET

plt.subplot(1, 2, 2)

plt.imshow(
    np.rot90(pet_slice),
    cmap="hot",
    vmin=0,
    vmax=1
)

plt.title("Normalized PET")
plt.axis("off")


plt.tight_layout()
plt.show()