import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
from skimage.metrics import structural_similarity as ssim


# --------------------------------------------------
# Load images
# --------------------------------------------------

MRI_PATH = "results/mri_normalized.nii.gz"
PET_PATH = "results/pet_registered.nii.gz"
FUSED_PATH = "results/pca_fused_image.nii.gz"


print("Loading MRI...")
mri = nib.load(MRI_PATH).get_fdata()

print("Loading registered PET...")
pet = nib.load(PET_PATH).get_fdata()

print("Loading PCA fused image...")
fused = nib.load(FUSED_PATH).get_fdata()


print("\nShapes:")
print("MRI   :", mri.shape)
print("PET   :", pet.shape)
print("Fused :", fused.shape)


# --------------------------------------------------
# Normalize images
# --------------------------------------------------

def normalize(image):
    image = image.astype(np.float32)

    minimum = np.min(image)
    maximum = np.max(image)

    if maximum - minimum == 0:
        return np.zeros_like(image)

    return (image - minimum) / (maximum - minimum)


mri = normalize(mri)
pet = normalize(pet)
fused = normalize(fused)


# --------------------------------------------------
# Select middle slice
# --------------------------------------------------

slice_index = fused.shape[2] // 2

mri_slice = mri[:, :, slice_index]
pet_slice = pet[:, :, slice_index]
fused_slice = fused[:, :, slice_index]


# --------------------------------------------------
# Calculate basic statistics
# --------------------------------------------------

print("\n========== IMAGE STATISTICS ==========")

print("\nMRI")
print("Minimum :", np.min(mri_slice))
print("Maximum :", np.max(mri_slice))
print("Mean    :", np.mean(mri_slice))
print("Std     :", np.std(mri_slice))

print("\nPET")
print("Minimum :", np.min(pet_slice))
print("Maximum :", np.max(pet_slice))
print("Mean    :", np.mean(pet_slice))
print("Std     :", np.std(pet_slice))

print("\nFUSED")
print("Minimum :", np.min(fused_slice))
print("Maximum :", np.max(fused_slice))
print("Mean    :", np.mean(fused_slice))
print("Std     :", np.std(fused_slice))


# --------------------------------------------------
# Entropy calculation
# --------------------------------------------------

def calculate_entropy(image):

    histogram, _ = np.histogram(
        image.flatten(),
        bins=256,
        range=(0, 1),
        density=True
    )

    histogram = histogram[histogram > 0]

    probability = histogram / np.sum(histogram)

    entropy = -np.sum(probability * np.log2(probability))

    return entropy


mri_entropy = calculate_entropy(mri_slice)
pet_entropy = calculate_entropy(pet_slice)
fused_entropy = calculate_entropy(fused_slice)


print("\n========== ENTROPY ==========")

print("MRI entropy   :", mri_entropy)
print("PET entropy   :", pet_entropy)
print("Fused entropy :", fused_entropy)


# --------------------------------------------------
# Structural similarity
# --------------------------------------------------

mri_ssim = ssim(
    mri_slice,
    fused_slice,
    data_range=1.0
)

pet_ssim = ssim(
    pet_slice,
    fused_slice,
    data_range=1.0
)


print("\n========== SSIM ==========")

print("MRI vs Fused :", mri_ssim)
print("PET vs Fused :", pet_ssim)


# --------------------------------------------------
# Display results
# --------------------------------------------------

plt.figure(figsize=(15, 5))


plt.subplot(1, 3, 1)
plt.imshow(mri_slice.T, cmap="gray", origin="lower")
plt.title("MRI")
plt.axis("off")


plt.subplot(1, 3, 2)
plt.imshow(pet_slice.T, cmap="hot", origin="lower")
plt.title("Registered PET")
plt.axis("off")


plt.subplot(1, 3, 3)
plt.imshow(fused_slice.T, cmap="gray", origin="lower")
plt.title("PCA Fused")
plt.axis("off")


plt.tight_layout()

plt.savefig(
    "results/pca_fusion_comparison.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


print("\nComparison image saved:")
print("results/pca_fusion_comparison.png")