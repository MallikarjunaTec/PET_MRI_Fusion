import nibabel as nib
import numpy as np
import pywt
import matplotlib.pyplot as plt


# ==========================================
# FILE PATHS
# ==========================================

MRI_PATH = "dataset/subject04/t1.nii.gz"
PET_PATH = "results/pet_registered.nii.gz"

OUTPUT_PATH = "results/wavelet_fused_v2.nii.gz"


# ==========================================
# LOAD IMAGES
# ==========================================

print("Loading MRI...")
mri_img = nib.load(MRI_PATH)
mri = mri_img.get_fdata().astype(np.float32)

print("Loading registered PET...")
pet = nib.load(PET_PATH).get_fdata().astype(np.float32)


# ==========================================
# CHECK SHAPE
# ==========================================

print("\nMRI shape:", mri.shape)
print("PET shape:", pet.shape)

if mri.shape != pet.shape:
    raise ValueError("MRI and PET dimensions do not match!")

print("MRI and PET dimensions match.")


# ==========================================
# NORMALIZATION
# ==========================================

def normalize(image):

    minimum = np.min(image)
    maximum = np.max(image)

    if maximum == minimum:
        return np.zeros_like(image)

    return (image - minimum) / (maximum - minimum)


print("\nNormalizing images...")

mri = normalize(mri)
pet = normalize(pet)

print("Normalization complete.")


# ==========================================
# WAVELET FUSION FUNCTION
# ==========================================

def fuse_slice(mri_slice, pet_slice):

    # 2-level 2D wavelet decomposition
    mri_coeffs = pywt.wavedec2(
        mri_slice,
        wavelet="db2",
        level=2
    )

    pet_coeffs = pywt.wavedec2(
        pet_slice,
        wavelet="db2",
        level=2
    )

    fused_coeffs = []

    # --------------------------------------
    # Approximation coefficients
    # --------------------------------------

    mri_low = mri_coeffs[0]
    pet_low = pet_coeffs[0]

    # Average low-frequency information
    fused_low = (
        0.5 * mri_low +
        0.5 * pet_low
    )

    fused_coeffs.append(fused_low)


    # --------------------------------------
    # Detail coefficients
    # --------------------------------------

    for level in range(1, len(mri_coeffs)):

        mri_details = mri_coeffs[level]
        pet_details = pet_coeffs[level]

        fused_details = []

        for mri_detail, pet_detail in zip(
            mri_details,
            pet_details
        ):

            # Energy of each coefficient
            mri_energy = np.abs(mri_detail)
            pet_energy = np.abs(pet_detail)

            # Select coefficient with stronger detail
            mask = mri_energy >= pet_energy

            fused_detail = np.where(
                mask,
                mri_detail,
                pet_detail
            )

            fused_details.append(fused_detail)

        fused_coeffs.append(tuple(fused_details))


    # --------------------------------------
    # Reconstruct image
    # --------------------------------------

    fused = pywt.waverec2(
        fused_coeffs,
        wavelet="db2"
    )

    # Make sure reconstructed size matches
    fused = fused[
        :mri_slice.shape[0],
        :mri_slice.shape[1]
    ]

    return fused


# ==========================================
# PROCESS ALL SLICES
# ==========================================

print("\nStarting improved wavelet fusion...")

fused = np.zeros_like(mri)

total_slices = mri.shape[2]

for i in range(total_slices):

    fused[:, :, i] = fuse_slice(
        mri[:, :, i],
        pet[:, :, i]
    )

    # Progress
    if (i + 1) % 20 == 0:
        print(
            f"Processed {i + 1}/{total_slices} slices"
        )


# ==========================================
# NORMALIZE FINAL RESULT
# ==========================================

fused = normalize(fused)


# ==========================================
# SAVE NIFTI
# ==========================================

fused_img = nib.Nifti1Image(
    fused,
    mri_img.affine,
    mri_img.header
)

nib.save(
    fused_img,
    OUTPUT_PATH
)

print("\n==========================================")
print("Improved wavelet fusion completed!")
print("Saved:")
print(OUTPUT_PATH)
print("==========================================")


# ==========================================
# DISPLAY MIDDLE SLICE
# ==========================================

middle = fused.shape[2] // 2

plt.figure(figsize=(15, 5))

plt.subplot(1, 3, 1)
plt.imshow(mri[:, :, middle], cmap="gray")
plt.title("MRI")
plt.axis("off")

plt.subplot(1, 3, 2)
plt.imshow(pet[:, :, middle], cmap="hot")
plt.title("Registered PET")
plt.axis("off")

plt.subplot(1, 3, 3)
plt.imshow(fused[:, :, middle], cmap="gray")
plt.title("Improved Wavelet Fusion")
plt.axis("off")

plt.tight_layout()
plt.show()