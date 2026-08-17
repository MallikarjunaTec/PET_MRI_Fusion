// -------------------------------------------------
// Intro → Dashboard transition
// -------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
    const intro = document.getElementById('intro');
    const dashboard = document.getElementById('dashboard');

    // After the intro animation finishes (≈2.8 s) hide it and show dashboard
    setTimeout(() => {
        intro.classList.add('hidden');
        dashboard.classList.remove('hidden');
    }, 3000);
});

// -------------------------------------------------
// Upload handling (drag‑&‑drop + preview)
// -------------------------------------------------
const uploadBoxes = document.querySelectorAll('.upload-box');
let files = { mri: null, pet: null };

uploadBoxes.forEach(box => {
    const input = box.querySelector('input');
    box.addEventListener('click', () => input.click());

    // Drag‑over styling
    ['dragenter', 'dragover'].forEach(ev => {
        box.addEventListener(ev, e => {
            e.preventDefault();
            box.classList.add('drag-over');
        });
    });
    ['dragleave', 'drop'].forEach(ev => {
        box.addEventListener(ev, e => {
            e.preventDefault();
            box.classList.remove('drag-over');
        });
    });

    // Drop handling
    box.addEventListener('drop', e => {
        const file = e.dataTransfer.files[0];
        handleFile(box, file);
    });

    // Regular file picker
    input.addEventListener('change', e => {
        const file = e.target.files[0];
        handleFile(box, file);
    });
});

function handleFile(box, file) {
    if (!file) return;
    const type = box.dataset.type; // "mri" or "pet"
    files[type] = file;
    box.innerHTML = `<p>${file.name}</p>`;
    validateReady();
}

function validateReady() {
    const fuseBtn = document.getElementById('fuse-btn');
    if (files.mri && files.pet) {
        fuseBtn.disabled = false;
        fuseBtn.classList.remove('disabled');
    }
}

// -------------------------------------------------
// Open upload section from hero CTA
// -------------------------------------------------
document.getElementById('open-upload').addEventListener('click', () => {
    document.getElementById('upload-section').scrollIntoView({ behavior: 'smooth' });
});

// -------------------------------------------------
// Fuse placeholder – simulate processing & render results
// -------------------------------------------------
document.getElementById('fuse-btn').addEventListener('click', () => {
    const fuseBtn = document.getElementById('fuse-btn');
    fuseBtn.disabled = true;
    fuseBtn.textContent = 'Processing…';
    // Simulate a short processing delay (2 seconds)
    setTimeout(() => {
        // Hide upload section, show visualization & metrics
        document.getElementById('upload-section').classList.add('hidden');
        document.getElementById('fusion-visualization').classList.remove('hidden');
        document.getElementById('analysis-section').classList.remove('hidden');

        // Populate dummy metric values (replace with real calculations later)
        document.getElementById('ssim').textContent = '0.92';
        document.getElementById('entropy').textContent = '5.41';
        document.getElementById('mi').textContent = '1.23';
        document.getElementById('psnr').textContent = '38.7 dB';
        document.getElementById('time').textContent = '2.0 s';

        // Render placeholder images on the canvases – a simple gray checkerboard
        const canvases = ['view-mri', 'view-pet', 'view-registered', 'view-fused'];
        canvases.forEach(id => drawPlaceholder(document.getElementById(id)));

        // Reset button UI
        fuseBtn.textContent = '✨ Fuse Images';
    }, 2000);
});

function drawPlaceholder(canvas) {
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const size = Math.min(canvas.parentElement.clientWidth, 250);
    canvas.width = size;
    canvas.height = size;
    // checkerboard pattern
    const step = 20;
    for (let y = 0; y < size; y += step) {
        for (let x = 0; x < size; x += step) {
            ctx.fillStyle = ((x/step + y/step) % 2 === 0) ? '#e0e0e0' : '#c0c0c0';
            ctx.fillRect(x, y, step, step);
        }
    }
    // overlay "Placeholder" text
    ctx.fillStyle = '#777';
    ctx.font = '14px Inter';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('Preview', size/2, size/2);
}
