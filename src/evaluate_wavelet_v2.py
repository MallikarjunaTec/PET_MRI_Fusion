import nibabel as nib
import numpy as np
from skimage.metrics import structural_similarity as ssim
from scipy.stats import entropy


# ==========================================
# FILE PATHS
# ==========================================

MRI_PATH = "dataset/subject04/t1.nii.gz"
PET_PATH = "results/pet_registered.nii.gz"
FUSED_PATH = "results/wavelet_fused_v2.nii.gz"


# ==========================================
# LOAD IMAGES
# ==========================================

print("Loading MRI...")
mri = nib.load(MRI_PATH).get_fdata()

print("Loading registered PET...")
pet = nib.load(PET_PATH).get_fdata()

print("Loading improved Wavelet fused image...")
fused = nib.load(FUSED_PATH).get_fdata()


# ==========================================
# CHECK SHAPES
# ==========================================

print("\nShapes:")
print("MRI   :", mri.shape)
print("PET   :", pet.shape)
print("Fused :", fused.shape)

if mri.shape != pet.shape or mri.shape != fused.shape:
    raise ValueError("Image dimensions do not match!")

print("\nAll image dimensions match.")


# ==========================================
# NORMALIZATION
# ==========================================

def normalize(image):

    image = image.astype(np.float32)

    minimum = np.min(image)
    maximum = np.max(image)

    if maximum - minimum == 0:
        return image

    return (image - minimum) / (maximum - minimum)


print("\nNormalizing images...")

mri = normalize(mri)
pet = normalize(pet)
fused = normalize(fused)

print("Normalization complete.")


# ==========================================
# ENTROPY
# ==========================================

def calculate_entropy(image):

    image_uint8 = (image * 255).astype(np.uint8)

    histogram = np.bincount(
        image_uint8.flatten(),
        minlength=256
    )

    probability = histogram / histogram.sum()

    probability = probability[probability > 0]

    return entropy(probability, base=2)


print("\nCalculating entropy...")

mri_entropy = calculate_entropy(mri)
pet_entropy = calculate_entropy(pet)
fused_entropy = calculate_entropy(fused)


# ==========================================
# SSIM
# ==========================================

def calculate_ssim(image1, image2):

    scores = []

    print("Calculating SSIM slice-by-slice...")

    for i in range(image1.shape[2]):

        score = ssim(
            image1[:, :, i],
            image2[:, :, i],
            data_range=1.0
        )

        scores.append(score)

    return np.mean(scores)


mri_ssim = calculate_ssim(mri, fused)
pet_ssim = calculate_ssim(pet, fused)


# ==========================================
# RESULTS
# ==========================================

print("\n==========================================")
print("     IMPROVED WAVELET FUSION RESULTS")
print("==========================================")

print("\n========== ENTROPY ==========")

print("MRI entropy   :", mri_entropy)
print("PET entropy   :", pet_entropy)
print("Fused entropy :", fused_entropy)

print("\n========== SSIM ==========")

print("MRI vs Fused :", mri_ssim)
print("PET vs Fused :", pet_ssim)


# ==========================================
# SAVE RESULTS
# ==========================================

output_file = "results/wavelet_v2_metrics.txt"

with open(output_file, "w") as file:

    file.write("IMPROVED WAVELET PET-MRI FUSION\n")
    file.write("================================\n\n")

    file.write(f"MRI entropy   : {mri_entropy}\n")
    file.write(f"PET entropy   : {pet_entropy}\n")
    file.write(f"Fused entropy : {fused_entropy}\n\n")

    file.write(f"MRI vs Fused SSIM : {mri_ssim}\n")
    file.write(f"PET vs Fused SSIM : {pet_ssim}\n")


print("\nResults saved:")
print(output_file)