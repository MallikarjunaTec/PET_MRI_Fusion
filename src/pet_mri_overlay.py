import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt


# ---------------------------------------
# File paths
# ---------------------------------------

MRI_PATH = r"E:\PET_MRI_Fusion\results\mri_normalized.nii.gz"
PET_PATH = r"E:\PET_MRI_Fusion\results\pet_normalized.nii.gz"


# ---------------------------------------
# Load MRI
# ---------------------------------------

print("Loading MRI...")

mri_img = nib.load(MRI_PATH)
mri_data = mri_img.get_fdata()

print("MRI shape:", mri_data.shape)


# ---------------------------------------
# Load PET
# ---------------------------------------

print("\nLoading PET...")

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
# Select middle slice
# ---------------------------------------

slice_index = mri_data.shape[2] // 2

mri_slice = mri_data[:, :, slice_index]
pet_slice = pet_data[:, :, slice_index]


# Rotate for correct display orientation
mri_slice = np.rot90(mri_slice)
pet_slice = np.rot90(pet_slice)


# ---------------------------------------
# PET threshold
# ---------------------------------------
# Remove very low PET activity from
# the color overlay.

threshold = 0.20

pet_mask = pet_slice > threshold


# ---------------------------------------
# Create PET alpha/transparency
# ---------------------------------------

alpha = np.zeros_like(pet_slice)

alpha[pet_mask] = pet_slice[pet_mask]

# Make PET slightly transparent
alpha = alpha * 0.75


# ---------------------------------------
# Display
# ---------------------------------------

plt.figure(figsize=(15, 5))


# MRI
plt.subplot(1, 3, 1)

plt.imshow(
    mri_slice,
    cmap="gray",
    vmin=0,
    vmax=1
)

plt.title("MRI")
plt.axis("off")


# PET
plt.subplot(1, 3, 2)

plt.imshow(
    pet_slice,
    cmap="hot",
    vmin=0,
    vmax=1
)

plt.title("PET")
plt.axis("off")


# PET + MRI overlay
plt.subplot(1, 3, 3)

plt.imshow(
    mri_slice,
    cmap="gray",
    vmin=0,
    vmax=1
)

plt.imshow(
    pet_slice,
    cmap="hot",
    vmin=threshold,
    vmax=1,
    alpha=alpha
)

plt.title("PET + MRI Overlay")
plt.axis("off")


plt.tight_layout()
plt.show()