import SimpleITK as sitk
import numpy as np
import matplotlib.pyplot as plt


# --------------------------------------------------
# File paths
# --------------------------------------------------

MRI_PATH = r"E:\PET_MRI_Fusion\results\mri_normalized.nii.gz"
PET_PATH = r"E:\PET_MRI_Fusion\results\pet_normalized.nii.gz"

OUTPUT_PATH = r"E:\PET_MRI_Fusion\results\pet_registered.nii.gz"


# --------------------------------------------------
# Load images
# --------------------------------------------------

print("Loading MRI...")
fixed_image = sitk.ReadImage(MRI_PATH, sitk.sitkFloat32)

print("Loading PET...")
moving_image = sitk.ReadImage(PET_PATH, sitk.sitkFloat32)


print("MRI size:", fixed_image.GetSize())
print("PET size:", moving_image.GetSize())


# --------------------------------------------------
# Initial alignment
# --------------------------------------------------

print("\nCreating initial alignment...")

initial_transform = sitk.CenteredTransformInitializer(
    fixed_image,
    moving_image,
    sitk.Euler3DTransform(),
    sitk.CenteredTransformInitializerFilter.GEOMETRY
)


# --------------------------------------------------
# Registration method
# --------------------------------------------------

registration = sitk.ImageRegistrationMethod()

# Similarity measurement
registration.SetMetricAsMattesMutualInformation(
    numberOfHistogramBins=50
)

# Interpolation
registration.SetInterpolator(sitk.sitkLinear)

# Optimizer
registration.SetOptimizerAsGradientDescent(
    learningRate=0.1,
    numberOfIterations=100,
    convergenceMinimumValue=1e-6,
    convergenceWindowSize=10
)

registration.SetOptimizerScalesFromPhysicalShift()

# Multi-resolution registration
registration.SetShrinkFactorsPerLevel(
    shrinkFactors=[4, 2, 1]
)

registration.SetSmoothingSigmasPerLevel(
    smoothingSigmas=[2, 1, 0]
)

registration.SmoothingSigmasAreSpecifiedInPhysicalUnitsOn()

registration.SetInitialTransform(
    initial_transform,
    inPlace=False
)


# --------------------------------------------------
# Perform registration
# --------------------------------------------------

print("\nStarting PET → MRI registration...")

final_transform = registration.Execute(
    fixed_image,
    moving_image
)

print("Registration completed!")

print(
    "Final metric value:",
    registration.GetMetricValue()
)

print(
    "Optimizer iterations:",
    registration.GetOptimizerIteration()
)


# --------------------------------------------------
# Resample PET into MRI space
# --------------------------------------------------

print("\nResampling PET...")

registered_pet = sitk.Resample(
    moving_image,
    fixed_image,
    final_transform,
    sitk.sitkLinear,
    0.0,
    moving_image.GetPixelID()
)


# --------------------------------------------------
# Save registered PET
# --------------------------------------------------

sitk.WriteImage(
    registered_pet,
    OUTPUT_PATH
)

print("\nRegistered PET saved:")
print(OUTPUT_PATH)


# --------------------------------------------------
# Display middle slice
# --------------------------------------------------

mri_array = sitk.GetArrayFromImage(fixed_image)
pet_array = sitk.GetArrayFromImage(registered_pet)

middle_slice = mri_array.shape[0] // 2

mri_slice = mri_array[middle_slice]
pet_slice = pet_array[middle_slice]


plt.figure(figsize=(15, 5))


# MRI
plt.subplot(1, 3, 1)

plt.imshow(
    mri_slice,
    cmap="gray"
)

plt.title("MRI")
plt.axis("off")


# Registered PET
plt.subplot(1, 3, 2)

plt.imshow(
    pet_slice,
    cmap="hot"
)

plt.title("Registered PET")
plt.axis("off")


# Overlay
plt.subplot(1, 3, 3)

plt.imshow(
    mri_slice,
    cmap="gray"
)

plt.imshow(
    pet_slice,
    cmap="hot",
    alpha=0.4
)

plt.title("MRI + Registered PET")
plt.axis("off")


plt.tight_layout()
plt.show()