import matplotlib.pyplot as plt
import numpy as np


# ============================================================
# DATA FROM YOUR FUSION COMPARISON
# ============================================================

methods = [
    "Weighted",
    "PCA",
    "Wavelet",
    "Improved Wavelet"
]

entropy = [
    2.9407,
    3.0393,
    2.9879,
    3.1772
]

mri_ssim = [
    0.7906,
    0.8069,
    0.2867,
    0.2697
]

pet_ssim = [
    0.6763,
    0.8065,
    0.2694,
    0.2621
]

spatial_frequency = [
    0.0929,
    0.0748,
    0.0775,
    0.0807
]


# ============================================================
# ENTROPY
# ============================================================

plt.figure(figsize=(9, 5))

plt.bar(methods, entropy)

plt.title("Entropy Comparison")
plt.ylabel("Entropy")
plt.xlabel("Fusion Method")

plt.tight_layout()

plt.savefig(
    "results/entropy_comparison.png",
    dpi=300
)

plt.show()


# ============================================================
# SSIM
# ============================================================

x = np.arange(len(methods))
width = 0.35

plt.figure(figsize=(9, 5))

plt.bar(
    x - width / 2,
    mri_ssim,
    width,
    label="MRI vs Fused"
)

plt.bar(
    x + width / 2,
    pet_ssim,
    width,
    label="PET vs Fused"
)

plt.xticks(x, methods)

plt.title("SSIM Comparison")
plt.ylabel("SSIM")
plt.xlabel("Fusion Method")

plt.legend()

plt.tight_layout()

plt.savefig(
    "results/ssim_comparison.png",
    dpi=300
)

plt.show()


# ============================================================
# SPATIAL FREQUENCY
# ============================================================

plt.figure(figsize=(9, 5))

plt.bar(methods, spatial_frequency)

plt.title("Spatial Frequency Comparison")
plt.ylabel("Spatial Frequency")
plt.xlabel("Fusion Method")

plt.tight_layout()

plt.savefig(
    "results/spatial_frequency_comparison.png",
    dpi=300
)

plt.show()


print("\n======================================")
print("Comparison graphs generated!")
print("======================================")

print("\nSaved:")
print("results/entropy_comparison.png")
print("results/ssim_comparison.png")
print("results/spatial_frequency_comparison.png")