# 🧠 PET–MRI Multimodal Brain Image Fusion

A multimodal medical image fusion research project that combines structural information from MRI with metabolic information from PET using image registration, preprocessing, and multiple fusion algorithms.

---

## ⚠️ Disclaimer

**This project is intended for research and educational purposes only. It is not a diagnostic medical device and must not be used for clinical diagnosis or medical decision-making.**

---

## About the Project

MRI provides high-resolution structural and anatomical information of the brain, while PET provides metabolic and functional information. This project aligns PET scans with MRI reference images and generates a fused representation containing complementary information from both modalities.

### Overall Workflow

PET + MRI 
↓ 
Image Loading 
↓ 
Preprocessing 
↓ 
Normalization 
↓ 
PET → MRI Registration 
↓ 
Fusion 
↓ 
Quality Evaluation 
↓ 
Visualization 
↓ 
Export

---

## Currently Implemented Features

1. **NIfTI Image Loading**: Native support for loading 3D `.nii` and `.nii.gz` volumes.
2. **MRI Preprocessing**: Voxel intensity normalization (Min-Max/Z-score) for structural data.
3. **PET Preprocessing**: Intensity normalization for metabolic data.
4. **PET → MRI Registration**: Rigid spatial alignment of the PET moving image to the MRI fixed image using SimpleITK.
5. **Weighted Fusion**: Linear intensity blending of the two modalities.
6. **PCA Fusion**: Principal Component Analysis-based image fusion.
7. **Wavelet Fusion**: Multi-resolution frequency fusion using PyWavelets.
8. **Improved Wavelet Fusion**: Enhanced wavelet implementation with adaptive weighting rules.
9. **Fusion Quality Evaluation**: Automated calculation of quantitative metrics.
10. **Entropy**: Measurement of information distribution in the fused image.
11. **SSIM**: Structural similarity index computation for both MRI vs Fused and PET vs Fused.
12. **Standard Deviation**: Analysis of overall intensity variation.
13. **Spatial Frequency**: Measurement of spatial detail and activity levels.
14. **Fusion Method Comparison**: Side-by-side interactive comparison charts for all algorithms.
15. **Streamlit Visualization**: A dark-themed web interface for interactive image viewing across Axial, Coronal, and Sagittal planes.
16. **Download/Export Functionality**: Ability to export the fused NIfTI volume, PNG visualizations, and CSV metrics.

---

## Fusion Algorithms

### Weighted Fusion
MRI and PET are combined using a weighted intensity blending approach. 
Mathematically represented as: `Fused = α × MRI + β × PET`

### PCA Fusion
Principal Component Analysis is used to derive principal components from the source images to create a statistically informed fused representation.

### Wavelet Fusion
The source images are decomposed using discrete wavelet transforms (via PyWavelets). High and low-frequency components are combined using specific fusion rules before being reconstructed.

### Improved Wavelet Fusion
An alternative wavelet implementation utilizing specialized decomposition and adaptive weighting strategies for combining the frequency bands.

---

## PET → MRI Registration

- **Reference Space**: MRI is used as the fixed reference image.
- **Alignment**: The moving PET volume is spatially aligned to the MRI coordinate space.
- **Implementation**: Utilizes `SimpleITK` with Mattes Mutual Information metric and Gradient Descent optimization.
- **Purpose**: Ensures that anatomical structures in the MRI physically overlap with the corresponding metabolic activity in the PET scan before fusion occurs.

---

## Fusion Evaluation

Quantitative metrics are calculated dynamically from the processed images to evaluate fusion quality:

### Entropy
Measures the information content and statistical distribution of intensities in the fused image.

### SSIM
Measures structural similarity between the source images and the final fused image.
- **MRI vs Fused SSIM**
- **PET vs Fused SSIM**

### Standard Deviation
Measures the overall contrast and intensity variation in the fused volume.

### Spatial Frequency
Measures the overall spatial detail and high-frequency activity preserved in the fused result.

---

## Experimental Results

The project automatically evaluates and compares multiple fusion approaches. Results are calculated dynamically upon execution.

| Method | Entropy | MRI SSIM | PET SSIM | Standard Deviation | Spatial Frequency |
|---|---:|---:|---:|---:|---:|
| Weighted Fusion | Calculated | Calculated | Calculated | Calculated | Calculated |
| PCA Fusion | Calculated | Calculated | Calculated | Calculated | Calculated |
| Wavelet Fusion | Calculated | Calculated | Calculated | Calculated | Calculated |
| Improved Wavelet | Calculated | Calculated | Calculated | Calculated | Calculated |

---

## Web Application

The project features a modern, medical-research oriented, clean, and responsive Streamlit UI.

**Workflow:**
Upload MRI + Upload PET → Validate → Preview → Register → Select Fusion Algorithm → Generate Fusion → View Fused Image → Evaluate → Download

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Streamlit | Web interface |
| NumPy | Numerical processing |
| NiBabel | NIfTI image loading/saving |
| SimpleITK | Medical image processing and registration |
| SciPy | Scientific/image processing |
| scikit-image | Image processing and SSIM |
| PyWavelets | Wavelet-based fusion |
| Matplotlib | Visualization |
| Plotly | Interactive comparison charts |
| Pandas | Tables and metrics data handling |

---

## Project Structure

```text
PET_MRI_Fusion/
│
├── .streamlit/                 # Streamlit configuration (theme settings)
├── app/
│   ├── app.py                  # Main Streamlit application entry point
│   └── components/             # UI modular components (viewer, metrics, upload, ui)
│
├── src/                        # Core backend logic
│   ├── preprocessing.py        # Image normalization functions
│   ├── registration.py         # SimpleITK alignment algorithms
│   ├── fusion_methods.py       # Weighted, PCA, and Wavelet fusion implementations
│   ├── evaluation.py           # SSIM, Entropy, and Spatial Frequency calculations
│   └── ...                     # Additional utility scripts
│
├── dataset/                    # Directory for input medical data (ignored in git)
├── results/                    # Output directory for evaluations (ignored in git)
├── outputs/                    # Output directory for fused images (ignored in git)
├── website/                    # Static website assets for the UI background
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git exclusion rules
└── README.md                   # Project documentation
```

---

## Dataset

The project works with 3D PET and MRI NIfTI volumes.

**Supported formats:**
- `.nii`
- `.nii.gz`

**Dataset:** The medical imaging dataset is not included in this repository due to dataset licensing, distribution, and data-management considerations. Users should obtain the dataset from its authorized source and place the required NIfTI files in the `dataset/` directory.

*(Note: If the dataset's license explicitly permits redistribution, a small de-identified sample could be provided here. Always verify dataset terms before distributing medical images).*

---

## Installation

### Windows (Primary)

```powershell
# Clone the repository
git clone <repository-url>
cd PET_MRI_Fusion

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1

# Upgrade pip and install requirements
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### macOS / Linux

```bash
git clone <repository-url>
cd PET_MRI_Fusion
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Running the Project

To launch the Streamlit application:

```bash
streamlit run app/app.py
```

Streamlit will automatically open the application in your default web browser at:
`http://localhost:8501`

---

## Gitignore

The repository utilizes a `.gitignore` to exclude:
- Virtual environments (`.venv/`)
- Python cache (`__pycache__/`)
- Large generated NIfTI files and medical data (`dataset/`, `outputs/`, `results/`)
- Environment variables (`.env`)
- IDE-specific configurations

*Warning: Never commit private, sensitive, or restricted medical datasets to public version control.*

---

## Future Improvements

The following features are planned but **NOT currently implemented**:
- Better 3D volume visualization
- Interactive PET/MRI overlay
- More advanced fusion algorithms (e.g., Deep Learning models)
- GPU acceleration
- More comprehensive evaluation metrics
- Batch processing capabilities
- Integration with additional public datasets
- Docker deployment
- Cloud deployment
- Improved registration methods (e.g., non-rigid/deformable registration)
- More robust validation

---

## Limitations

- Fusion quality is heavily dependent on the quality of the input images.
- Registration accuracy fundamentally affects the final fusion outcome.
- Quantitative evaluation metrics should not be interpreted as clinical evidence.
- Different datasets and scanning protocols may produce varying results.
- The project is strictly intended for research and educational demonstrations.
- The system is not a diagnostic medical device.

---

## Author

**Mallikarjuna K**
- **Email**: [mallikamanu2003k@gmail.com](mailto:mallikamanu2003k@gmail.com)
- **LinkedIn**: [Mallikarjuna K](https://www.linkedin.com/in/mallikarjuna-k-b95881255/)

**Project**: PET–MRI Multimodal Brain Image Fusion

**Technology Areas**: Python, Medical Image Processing, Computer Vision, Image Registration, Multimodal Image Fusion, Streamlit.

---

## License

License information will be added.
