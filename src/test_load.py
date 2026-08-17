import nibabel as nib
import matplotlib.pyplot as plt
import numpy as np

# -----------------------------------
# File paths
# -----------------------------------

MRI_PATH = r"E:\PET_MRI_Fusion\dataset\subject04\t1.nii.gz"
PET_PATH = r"E:\PET_MRI_Fusion\dataset\subject04\image_0.nii.gz"


# -----------------------------------
# Load MRI
# -----------------------------------

print("Loading MRI...")

mri_image = nib.load(MRI_PATH)
mri_data = mri_image.get_fdata()

print("MRI loaded successfully!")
print("MRI shape:", mri_data.shape)


# -----------------------------------
# Load PET
# -----------------------------------

print("\nLoading PET...")

pet_image = nib.load(PET_PATH)
pet_data = pet_image.get_fdata()

print("PET loaded successfully!")
print("PET shape:", pet_data.shape)


# -----------------------------------
# Select middle slice
# -----------------------------------

mri_slice_index = mri_data.shape[2] // 2
pet_slice_index = pet_data.shape[2] // 2

mri_slice = mri_data[:, :, mri_slice_index]
pet_slice = pet_data[:, :, pet_slice_index]


# -----------------------------------
# Display MRI and PET
# -----------------------------------

plt.figure(figsize=(12, 6))

# MRI
plt.subplot(1, 2, 1)

plt.imshow(
    np.rot90(mri_slice),
    cmap="gray"
)

plt.title("MRI - T1")
plt.axis("off")


# PET
plt.subplot(1, 2, 2)

plt.imshow(
    np.rot90(pet_slice),
    cmap="hot"
)

plt.title("PET - image_0")
plt.axis("off")


plt.tight_layout()
plt.show()