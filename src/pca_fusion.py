import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt


# ============================================================
# File paths
# ============================================================

MRI_PATH = r"E:\PET_MRI_Fusion\results\mri_normalized.nii.gz"

PET_PATH = r"E:\PET_MRI_Fusion\results\pet_registered.nii.gz"

OUTPUT_PATH = r"E:\PET_MRI_Fusion\results\pca_fused_image.nii.gz"


# ============================================================
# 1. Load MRI
# ============================================================

print("Loading MRI...")

mri_img = nib.load(MRI_PATH)
mri = mri_img.get_fdata(dtype=np.float32)

print("MRI shape:", mri.shape)


# ============================================================
# 2. Load registered PET
# ============================================================

print("\nLoading registered PET...")

pet_img = nib.load(PET_PATH)
pet = pet_img.get_fdata(dtype=np.float32)

print("PET shape:", pet.shape)


# ============================================================
# 3. Check dimensions
# ============================================================

if mri.shape != pet.shape:
    raise ValueError(
        f"MRI and PET dimensions do not match: "
        f"{mri.shape} vs {pet.shape}"
    )

print("\nMRI and PET dimensions match.")


# ============================================================
# 4. Handle invalid values
# ============================================================

mri = np.nan_to_num(mri)
pet = np.nan_to_num(pet)


# ============================================================
# 5. Normalize both images
# ============================================================

print("\nNormalizing images...")


def normalize(image):
    minimum = np.min(image)
    maximum = np.max(image)

    if maximum == minimum:
        return np.zeros_like(image)

    return (image - minimum) / (maximum - minimum)


mri_norm = normalize(mri)
pet_norm = normalize(pet)


print("Normalization complete.")


# ============================================================
# 6. Flatten images
# ============================================================

mri_flat = mri_norm.flatten()
pet_flat = pet_norm.flatten()


# ============================================================
# 7. Standardize for PCA
# ============================================================

print("\nPreparing data for PCA...")

mri_std = (
    mri_flat - np.mean(mri_flat)
) / (np.std(mri_flat) + 1e-8)

pet_std = (
    pet_flat - np.mean(pet_flat)
) / (np.std(pet_flat) + 1e-8)


# ============================================================
# 8. Create data matrix
# ============================================================

data = np.vstack([
    mri_std,
    pet_std
])


# ============================================================
# 9. Calculate covariance matrix
# ============================================================

print("\nCalculating covariance matrix...")

covariance_matrix = np.cov(data)

print("\nCovariance matrix:")
print(covariance_matrix)


# ============================================================
# 10. Calculate eigenvalues and eigenvectors
# ============================================================

print("\nCalculating PCA...")

eigenvalues, eigenvectors = np.linalg.eigh(
    covariance_matrix
)


# ============================================================
# 11. Select principal component
# ============================================================

largest_index = np.argmax(eigenvalues)

principal_vector = eigenvectors[:, largest_index]

print("\nEigenvalues:")
print(eigenvalues)

print("\nPrincipal eigenvector:")
print(principal_vector)


# ============================================================
# 12. Calculate PCA weights
# ============================================================

# PCA eigenvector can contain negative signs.
# We use absolute values for fusion weights.

weights = np.abs(principal_vector)

weights = weights / np.sum(weights)


mri_weight = weights[0]
pet_weight = weights[1]


print("\nPCA Fusion Weights:")
print("MRI weight:", mri_weight)
print("PET weight:", pet_weight)


# ============================================================
# 13. Perform PCA fusion
# ============================================================

print("\nPerforming PCA fusion...")


fused_flat = (
    mri_weight * mri_norm.flatten()
    + pet_weight * pet_norm.flatten()
)


# Convert back to 3D
fused = fused_flat.reshape(mri.shape)


# ============================================================
# 14. Normalize final fused image
# ============================================================

fused = normalize(fused)


print("PCA fusion completed.")


# ============================================================
# 15. Save fused NIfTI image
# ============================================================

fused_img = nib.Nifti1Image(
    fused.astype(np.float32),
    mri_img.affine,
    mri_img.header
)


nib.save(
    fused_img,
    OUTPUT_PATH
)


print("\nPCA fused image saved:")
print(OUTPUT_PATH)


# ============================================================
# 16. Display middle slice
# ============================================================

slice_index = fused.shape[2] // 2

mri_slice = mri_norm[:, :, slice_index]
pet_slice = pet_norm[:, :, slice_index]
fused_slice = fused[:, :, slice_index]


# Rotate for display
mri_slice = np.rot90(mri_slice)
pet_slice = np.rot90(pet_slice)
fused_slice = np.rot90(fused_slice)


# ============================================================
# 17. Display results
# ============================================================

plt.figure(figsize=(18, 6))


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


# Registered PET
plt.subplot(1, 3, 2)

plt.imshow(
    pet_slice,
    cmap="hot",
    vmin=0,
    vmax=1
)

plt.title("Registered PET")
plt.axis("off")


# PCA Fusion
plt.subplot(1, 3, 3)

plt.imshow(
    fused_slice,
    cmap="gray",
    vmin=0,
    vmax=1
)

plt.title(
    f"PCA Fusion\n"
    f"MRI={mri_weight:.3f}, PET={pet_weight:.3f}"
)

plt.axis("off")


plt.tight_layout()
plt.show()
