import nibabel as nib

# -----------------------------
# File paths
# -----------------------------

MRI_PATH = r"E:\PET_MRI_Fusion\dataset\subject04\t1.nii.gz"
PET_PATH = r"E:\PET_MRI_Fusion\dataset\subject04\image_0.nii.gz"


# -----------------------------
# Load images
# -----------------------------

mri = nib.load(MRI_PATH)
pet = nib.load(PET_PATH)


# -----------------------------
# Print basic information
# -----------------------------

print("\n========== MRI INFORMATION ==========")

print("Shape:")
print(mri.shape)

print("\nVoxel spacing:")
print(mri.header.get_zooms())

print("\nAffine matrix:")
print(mri.affine)


print("\n========== PET INFORMATION ==========")

print("Shape:")
print(pet.shape)

print("\nVoxel spacing:")
print(pet.header.get_zooms())

print("\nAffine matrix:")
print(pet.affine)