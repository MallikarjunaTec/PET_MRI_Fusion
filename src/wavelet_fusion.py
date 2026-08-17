import nibabel as nib
import numpy as np
import pywt
import matplotlib.pyplot as plt


# --------------------------------------------------
# File paths
# --------------------------------------------------

MRI_PATH = "results/mri_normalized.nii.gz"
PET_PATH = "results/pet_registered.nii.gz"
OUTPUT_PATH = "results/wavelet_fused_image.nii.gz"


# --------------------------------------------------
# Load images
# --------------------------------------------------

print("Loading MRI...")
mri_img = nib.load(MRI_PATH)
mri = mri_img.get_fdata().astype(np.float32)

print("MRI shape:", mri.shape)

print("\nLoading registered PET...")
pet_img = nib.load(PET_PATH)
pet = pet_img.get_fdata().astype(np.float32)

print("PET shape:", pet.shape)


# --------------------------------------------------
# Check dimensions
# --------------------------------------------------

if mri.shape != pet.shape:
    raise ValueError("MRI and PET dimensions do not match!")

print("\nMRI and PET dimensions match.")


# --------------------------------------------------
# Normalize
# --------------------------------------------------

def normalize(image):

    minimum = np.min(image)
    maximum = np.max(image)

    if maximum - minimum == 0:
        return np.zeros_like(image)

    return (image - minimum) / (maximum - minimum)


print("\nNormalizing images...")

mri = normalize(mri)
pet = normalize(pet)

print("Normalization complete.")


# --------------------------------------------------
# Wavelet fusion function
# --------------------------------------------------

def wavelet_fusion(mri_slice, pet_slice):

    # Haar wavelet decomposition
    mri_coeff = pywt.dwt2(mri_slice, "haar")
    pet_coeff = pywt.dwt2(pet_slice, "haar")

    mri_LL, (mri_LH, mri_HL, mri_HH) = mri_coeff
    pet_LL, (pet_LH, pet_HL, pet_HH) = pet_coeff


    # --------------------------------------------------
    # Low-frequency fusion
    # Average MRI and PET
    # --------------------------------------------------

    fused_LL = (
        0.5 * mri_LL +
        0.5 * pet_LL
    )


    # --------------------------------------------------
    # High-frequency fusion
    # Select coefficient with larger absolute value
    # --------------------------------------------------

    fused_LH = np.where(
        np.abs(mri_LH) >= np.abs(pet_LH),
        mri_LH,
        pet_LH
    )

    fused_HL = np.where(
        np.abs(mri_HL) >= np.abs(pet_HL),
        mri_HL,
        pet_HL
    )

    fused_HH = np.where(
        np.abs(mri_HH) >= np.abs(pet_HH),
        mri_HH,
        pet_HH
    )


    # --------------------------------------------------
    # Reconstruct image
    # --------------------------------------------------

    fused = pywt.idwt2(
        (
            fused_LL,
            (fused_LH, fused_HL, fused_HH)
        ),
        "haar"
    )

    return fused


# --------------------------------------------------
# Apply fusion slice by slice
# --------------------------------------------------

print("\nStarting wavelet fusion...")

fused = np.zeros_like(mri, dtype=np.float32)

total_slices = mri.shape[2]

for i in range(total_slices):

    mri_slice = mri[:, :, i]
    pet_slice = pet[:, :, i]

    fused[:, :, i] = wavelet_fusion(
        mri_slice,
        pet_slice
    )

    if (i + 1) % 20 == 0:
        print(
            f"Processed {i + 1}/{total_slices} slices"
        )


# --------------------------------------------------
# Normalize final fused image
# --------------------------------------------------

fused = normalize(fused)


# --------------------------------------------------
# Save NIfTI
# --------------------------------------------------

fused_img = nib.Nifti1Image(
    fused,
    mri_img.affine,
    mri_img.header
)

nib.save(
    fused_img,
    OUTPUT_PATH
)

print("\nWavelet fusion completed!")

print("Wavelet fused image saved:")
print(OUTPUT_PATH)


# --------------------------------------------------
# Display middle slice
# --------------------------------------------------

middle = fused.shape[2] // 2

plt.figure(figsize=(15, 5))


plt.subplot(1, 3, 1)

plt.imshow(
    mri[:, :, middle].T,
    cmap="gray",
    origin="lower"
)

plt.title("MRI")
plt.axis("off")


plt.subplot(1, 3, 2)

plt.imshow(
    pet[:, :, middle].T,
    cmap="hot",
    origin="lower"
)

plt.title("Registered PET")
plt.axis("off")


plt.subplot(1, 3, 3)

plt.imshow(
    fused[:, :, middle].T,
    cmap="gray",
    origin="lower"
)

plt.title("Wavelet Fused")
plt.axis("off")


plt.tight_layout()

plt.savefig(
    "results/wavelet_fusion_comparison.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()