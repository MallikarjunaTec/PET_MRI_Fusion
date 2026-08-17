import nibabel as nib
import numpy as np
from skimage.metrics import structural_similarity as ssim
from scipy.stats import entropy


# ============================================================
# PATHS
# ============================================================

MRI_PATH = "results/mri_normalized.nii.gz"
PET_PATH = "results/pet_registered.nii.gz"

FUSIONS = {
    "Weighted": "results/fused_image.nii.gz",
    "PCA": "results/pca_fused_image.nii.gz",
    "Wavelet": "results/wavelet_fused_image.nii.gz",
    "Improved Wavelet": "results/wavelet_fused_v2.nii.gz",
}


# ============================================================
# LOAD IMAGE
# ============================================================

def load_image(path):
    return nib.load(path).get_fdata().astype(np.float32)


# ============================================================
# NORMALIZATION
# ============================================================

def normalize(image):
    image = image - np.min(image)

    max_value = np.max(image)

    if max_value > 0:
        image = image / max_value

    return image


# ============================================================
# ENTROPY
# ============================================================

def calculate_entropy(image):

    image = normalize(image)

    hist, _ = np.histogram(
        image,
        bins=256,
        range=(0, 1),
        density=True
    )

    hist = hist + 1e-10

    return entropy(hist)


# ============================================================
# SSIM
# ============================================================

def calculate_ssim(reference, fused):

    reference = normalize(reference)
    fused = normalize(fused)

    scores = []

    for z in range(reference.shape[2]):

        score = ssim(
            reference[:, :, z],
            fused[:, :, z],
            data_range=1.0
        )

        scores.append(score)

    return np.mean(scores)


# ============================================================
# STANDARD DEVIATION
# ============================================================

def calculate_std(image):
    image = normalize(image)
    return np.std(image)


# ============================================================
# SPATIAL FREQUENCY
# ============================================================

def calculate_spatial_frequency(image):

    image = normalize(image)

    rf = np.diff(image, axis=0)
    cf = np.diff(image, axis=1)

    rf = np.mean(rf ** 2)
    cf = np.mean(cf ** 2)

    return np.sqrt(rf + cf)


# ============================================================
# LOAD MRI AND PET
# ============================================================

print("Loading MRI...")
mri = load_image(MRI_PATH)

print("Loading registered PET...")
pet = load_image(PET_PATH)

print("\nMRI shape:", mri.shape)
print("PET shape:", pet.shape)


mri = normalize(mri)
pet = normalize(pet)


# ============================================================
# RESULTS
# ============================================================

results = []


print("\n==============================================")
print("       PET-MRI FUSION COMPARISON")
print("==============================================")


for name, path in FUSIONS.items():

    print(f"\nEvaluating {name} fusion...")

    fused = load_image(path)

    fused = normalize(fused)

    entropy_value = calculate_entropy(fused)

    mri_ssim = calculate_ssim(mri, fused)

    pet_ssim = calculate_ssim(pet, fused)

    std_value = calculate_std(fused)

    spatial_frequency = calculate_spatial_frequency(fused)

    results.append({
        "Method": name,
        "Entropy": entropy_value,
        "MRI SSIM": mri_ssim,
        "PET SSIM": pet_ssim,
        "STD": std_value,
        "Spatial Frequency": spatial_frequency
    })


# ============================================================
# PRINT RESULTS
# ============================================================

print("\n\n==============================================================")
print("                 FINAL COMPARISON")
print("==============================================================")

print(
    f"{'Method':<20}"
    f"{'Entropy':<12}"
    f"{'MRI SSIM':<12}"
    f"{'PET SSIM':<12}"
    f"{'STD':<12}"
    f"{'Spatial Freq':<15}"
)

print("-" * 81)


for result in results:

    print(
        f"{result['Method']:<20}"
        f"{result['Entropy']:<12.4f}"
        f"{result['MRI SSIM']:<12.4f}"
        f"{result['PET SSIM']:<12.4f}"
        f"{result['STD']:<12.4f}"
        f"{result['Spatial Frequency']:<15.4f}"
    )


# ============================================================
# SAVE RESULTS
# ============================================================

output_file = "results/fusion_comparison.txt"

with open(output_file, "w") as f:

    f.write("PET-MRI FUSION METHOD COMPARISON\n")
    f.write("=" * 80 + "\n\n")

    for result in results:

        f.write(f"Method: {result['Method']}\n")
        f.write(f"Entropy: {result['Entropy']:.6f}\n")
        f.write(f"MRI SSIM: {result['MRI SSIM']:.6f}\n")
        f.write(f"PET SSIM: {result['PET SSIM']:.6f}\n")
        f.write(f"Standard Deviation: {result['STD']:.6f}\n")
        f.write(f"Spatial Frequency: {result['Spatial Frequency']:.6f}\n")
        f.write("-" * 60 + "\n")


print("\nComparison saved:")
print(output_file)