/**
 * PET–MRI Brain Image Fusion — Application Logic
 * Handles: theme, uploads, image viewing, fusion pipeline, metrics, charts, exports
 */

(function () {
  'use strict';

  // ============================================================
  // CONFIG
  // ============================================================
  const API_BASE = window.location.origin + '/api';

  // ============================================================
  // STATE
  // ============================================================
  const state = {
    mriUploaded: false,
    petUploaded: false,
    mriMeta: null,
    petMeta: null,
    fusionResult: null,
    comparisonResult: null,
    selectedMethod: 'Weighted Fusion',
    viewers: {
      mri:   { axis: 'axial', maxSlices: { axial: 100, coronal: 100, sagittal: 100 } },
      pet:   { axis: 'axial', maxSlices: { axial: 100, coronal: 100, sagittal: 100 } },
      fused: { axis: 'axial', maxSlices: { axial: 100, coronal: 100, sagittal: 100 } },
    },
  };

  // ============================================================
  // DOM REFERENCES
  // ============================================================
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => document.querySelectorAll(sel);

  // ============================================================
  // THEME
  // ============================================================
  function initTheme() {
    const saved = localStorage.getItem('pet-mri-theme') || 'light';
    setTheme(saved);
  }

  function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('pet-mri-theme', theme);
    
    // Sync the checkbox switch state
    const cb = $('#themeToggleCheckbox');
    if (cb) {
      cb.checked = (theme === 'dark');
    }
  }

  function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme');
    setTheme(current === 'dark' ? 'light' : 'dark');
  }

  // ============================================================
  // TOAST NOTIFICATIONS
  // ============================================================
  let toastTimer = null;
  function showToast(message, type = 'success') {
    const toast = $('#toast');
    const icon = $('#toastIcon');
    const msg = $('#toastMessage');

    toast.className = 'toast toast--' + type;
    const icons = { success: '✓', error: '✕', warning: '⚠', info: 'ℹ' };
    icon.textContent = icons[type] || '✓';
    msg.textContent = message;

    toast.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toast.classList.remove('show'), 4000);
  }

  // ============================================================
  // HELP MODAL
  // ============================================================
  function openHelp() {
    $('#helpBackdrop').classList.add('active');
    $('#helpModal').classList.add('active');
  }

  function closeHelp() {
    $('#helpBackdrop').classList.remove('active');
    $('#helpModal').classList.remove('active');
  }

  // ============================================================
  // MOBILE NAV
  // ============================================================
  function toggleMobileNav() {
    $('#navMenu').classList.toggle('open');
  }

  // ============================================================
  // SMOOTH NAV
  // ============================================================
  function initNavigation() {
    const links = $$('.navbar__link');
    
    // Smooth scrolling on click
    links.forEach(link => {
      link.addEventListener('click', (e) => {
        const href = link.getAttribute('href');
        
        // Validation: Don't allow navigating to results if fusion hasn't been run
        if (href === '#results' && !state.fusionResult) {
          e.preventDefault();
          showToast('Please upload images and run fusion first', 'warning');
          return;
        }

        links.forEach(l => l.classList.remove('active'));
        link.classList.add('active');
        $('#navMenu').classList.remove('open');
      });
    });

    // ScrollSpy to update active link on scroll
    window.addEventListener('scroll', () => {
      let current = '';
      const sections = $$('section');
      
      sections.forEach(section => {
        // Ignore hidden sections (like #results before fusion)
        if (section.classList.contains('hidden') || section.offsetHeight === 0) return;

        const sectionTop = section.offsetTop;
        if (window.scrollY >= (sectionTop - 200)) {
          current = section.getAttribute('id');
        }
      });

      links.forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href').includes(current)) {
          link.classList.add('active');
        }
      });
    });
  }

  // ============================================================
  // FILE SIZE FORMATTING
  // ============================================================
  function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  // ============================================================
  // FILE UPLOAD
  // ============================================================
  function initUpload(type) {
    const dropzone = $(`#${type}Dropzone`);
    const fileInput = $(`#${type}FileInput`);
    const removeBtn = $(`#${type}Remove`);

    // Drag events
    ['dragenter', 'dragover'].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
      });
    });
    ['dragleave', 'drop'].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
      });
    });

    dropzone.addEventListener('drop', (e) => {
      const files = e.dataTransfer.files;
      if (files.length > 0) handleFileUpload(type, files[0]);
    });

    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) handleFileUpload(type, e.target.files[0]);
    });

    removeBtn.addEventListener('click', () => removeFile(type));
  }

  async function handleFileUpload(type, file) {
    const name = file.name.toLowerCase();
    if (!name.endsWith('.nii') && !name.endsWith('.nii.gz') && !name.endsWith('.gz')) {
      showToast('Please upload a .nii or .nii.gz file', 'error');
      return;
    }

    // Show loading
    showToast(`Uploading ${type.toUpperCase()} scan...`, 'info');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const resp = await fetch(`${API_BASE}/upload/${type}`, {
        method: 'POST',
        body: formData,
      });

      const data = await resp.json();
      if (!resp.ok) {
        showError(type, data.error || 'Upload failed');
        return;
      }

      // Update state
      if (type === 'mri') {
        state.mriUploaded = true;
        state.mriMeta = data;
      } else {
        state.petUploaded = true;
        state.petMeta = data;
      }

      // Update UI
      showUploadSuccess(type, file, data);
      updateSliceRange(type, data);
      loadSlice(type, state.viewers[type].axis, Math.floor(data.shape[2] / 2));

      showToast(`${type.toUpperCase()} scan uploaded successfully`, 'success');

      // Check if both uploaded
      checkBothUploaded();

    } catch (err) {
      showToast('Upload failed: ' + err.message, 'error');
    }
  }

  function showUploadSuccess(type, file, data) {
    $(`#${type}Dropzone`).classList.add('hidden');
    $(`#${type}Success`).classList.add('active');
    $(`#${type}FileName`).textContent = file.name;
    $(`#${type}FileSize`).textContent = formatBytes(file.size);

    // Build metadata table
    const meta = $(`#${type}Meta`);
    const rows = [
      ['Dimensions', data.shape ? data.shape.join(' × ') : '—'],
      ['Voxel Spacing', data.voxel_spacing ? data.voxel_spacing.map(v => v.toFixed(2)).join(' × ') + ' mm' : '—'],
      ['Intensity Range', data.intensity_min != null ? `${data.intensity_min.toFixed(1)} — ${data.intensity_max.toFixed(1)}` : '—'],
      ['Mean', data.mean != null ? data.mean.toFixed(4) : '—'],
      ['Std Dev', data.std != null ? data.std.toFixed(4) : '—'],
      ['Data Type', data.dtype || '—'],
    ];
    meta.innerHTML = rows.map(([label, value]) =>
      `<tr><td>${label}</td><td>${value}</td></tr>`
    ).join('');
  }

  function removeFile(type) {
    $(`#${type}Dropzone`).classList.remove('hidden');
    $(`#${type}Success`).classList.remove('active');
    $(`#${type}FileInput`).value = '';

    if (type === 'mri') {
      state.mriUploaded = false;
      state.mriMeta = null;
    } else {
      state.petUploaded = false;
      state.petMeta = null;
    }

    // Clear canvas
    const canvas = $(`#${type}Canvas`);
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    checkBothUploaded();
    showToast(`${type.toUpperCase()} scan removed`, 'info');
  }

  function showError(type, message) {
    showToast(message, 'error');
  }

  function checkBothUploaded() {
    const both = state.mriUploaded && state.petUploaded;

    // Show/hide sections
    if (both) {
      $('#previewSection').classList.remove('hidden');
      $('#methodSection').classList.remove('hidden');
      $('#emptyState').classList.add('hidden');
      $('#runFusionBtn').disabled = false;
      $('#runAllFusionBtn').disabled = false;
    } else {
      $('#previewSection').classList.add('hidden');
      $('#methodSection').classList.add('hidden');
      $('#emptyState').classList.remove('hidden');
      $('#runFusionBtn').disabled = true;
      $('#runAllFusionBtn').disabled = true;
    }
  }

  // ============================================================
  // IMAGE VIEWER — SLICE LOADING
  // ============================================================
  function updateSliceRange(type, data) {
    if (!data.shape) return;
    state.viewers[type].maxSlices = {
      axial: data.shape[2] - 1,
      coronal: data.shape[1] - 1,
      sagittal: data.shape[0] - 1,
    };

    const axis = state.viewers[type].axis;
    const slider = $(`#${type}SliceSlider`);
    if (slider) {
      slider.max = state.viewers[type].maxSlices[axis];
      slider.value = Math.floor(state.viewers[type].maxSlices[axis] / 2);
      $(`#${type}SliceNum`).textContent = slider.value;
    }
  }

  async function loadSlice(type, axis, index) {
    try {
      const resp = await fetch(`${API_BASE}/slice/${type}/${axis}/${index}`);
      if (!resp.ok) return;
      const data = await resp.json();
      renderSliceToCanvas(`${type}Canvas`, data.image);
    } catch (err) {
      // Silently fail for slice loading
    }
  }

  function renderSliceToCanvas(canvasId, base64Data) {
    const canvas = $(`#${canvasId}`);
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const img = new Image();
    img.onload = () => {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
    };
    img.src = 'data:image/png;base64,' + base64Data;
  }

  function initViewerControls() {
    // Axis tabs
    $$('.viewer__axis-tabs').forEach(tabGroup => {
      const viewerType = tabGroup.dataset.viewer;
      tabGroup.querySelectorAll('.viewer__axis-tab').forEach(tab => {
        tab.addEventListener('click', () => {
          // Update active tab
          tabGroup.querySelectorAll('.viewer__axis-tab').forEach(t => t.classList.remove('active'));
          tab.classList.add('active');

          const axis = tab.dataset.axis;
          state.viewers[viewerType].axis = axis;

          // Update slider range
          const slider = $(`#${viewerType}SliceSlider`);
          if (slider) {
            slider.max = state.viewers[viewerType].maxSlices[axis];
            const mid = Math.floor(state.viewers[viewerType].maxSlices[axis] / 2);
            slider.value = mid;
            $(`#${viewerType}SliceNum`).textContent = mid;
            loadSlice(viewerType, axis, mid);
          }
        });
      });
    });

    // Slice sliders
    ['mri', 'pet', 'fused'].forEach(type => {
      const slider = $(`#${type}SliceSlider`);
      if (slider) {
        slider.addEventListener('input', () => {
          const val = parseInt(slider.value);
          $(`#${type}SliceNum`).textContent = val;
          loadSlice(type, state.viewers[type].axis, val);
        });
      }
    });

    // Comparison sync slider
    const compSlider = $('#compSliceSlider');
    if (compSlider) {
      compSlider.addEventListener('input', () => {
        const val = parseInt(compSlider.value);
        $('#compSliceNum').textContent = val;
        loadComparisonSlices('axial', val);
      });
    }
  }

  async function loadComparisonSlices(axis, index) {
    try {
      const [mriResp, petResp, fusedResp] = await Promise.all([
        fetch(`${API_BASE}/slice/mri/${axis}/${index}`),
        fetch(`${API_BASE}/slice/pet/${axis}/${index}`),
        fetch(`${API_BASE}/slice/fused/${axis}/${index}`),
      ]);

      if (mriResp.ok) {
        const d = await mriResp.json();
        renderSliceToCanvas('compMriCanvas', d.image);
      }
      if (petResp.ok) {
        const d = await petResp.json();
        renderSliceToCanvas('compPetCanvas', d.image);
      }
      if (fusedResp.ok) {
        const d = await fusedResp.json();
        renderSliceToCanvas('compFusedCanvas', d.image);
      }
    } catch (err) {
      // Silently fail
    }
  }

  // ============================================================
  // FULLSCREEN VIEWER
  // ============================================================
  function initFullscreen() {
    $('#fusedFullscreen').addEventListener('click', () => {
      const src = $('#fusedCanvas');
      const fs = $('#fullscreenCanvas');
      const ctx = fs.getContext('2d');
      fs.width = src.width;
      fs.height = src.height;
      ctx.drawImage(src, 0, 0);
      $('#fullscreenViewer').classList.add('active');
    });

    $('#fullscreenClose').addEventListener('click', () => {
      $('#fullscreenViewer').classList.remove('active');
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        $('#fullscreenViewer').classList.remove('active');
        closeHelp();
      }
    });
  }

  // ============================================================
  // FUSION METHOD SELECTION
  // ============================================================
  function initMethodSelection() {
    $$('.method-card').forEach(card => {
      card.addEventListener('click', () => {
        $$('.method-card').forEach(c => c.classList.remove('selected'));
        card.classList.add('selected');
        state.selectedMethod = card.dataset.method;
      });
    });
  }

  // ============================================================
  // PROCESSING PIPELINE
  // ============================================================
  const PIPELINE_STEPS = [
    { key: 'load-mri', name: 'Loading MRI', icon: '🧲' },
    { key: 'load-pet', name: 'Loading PET', icon: '☢️' },
    { key: 'validate', name: 'Validating dimensions', icon: '📐' },
    { key: 'normalize', name: 'Normalizing images', icon: '📊' },
    { key: 'register', name: 'Registering PET → MRI', icon: '🔗' },
    { key: 'fuse', name: 'Performing fusion', icon: '⚡' },
    { key: 'evaluate', name: 'Calculating metrics', icon: '📈' },
  ];

  function showProcessingOverlay(title) {
    $('#processingTitle').textContent = title || 'Processing PET–MRI Fusion';
    const stepsEl = $('#processingSteps');
    stepsEl.innerHTML = PIPELINE_STEPS.map(s =>
      `<div class="processing-modal__step" data-pstep="${s.key}">
        <span class="processing-modal__step-icon">○</span>
        <span>${s.name}</span>
      </div>`
    ).join('');
    $('#processingOverlay').classList.add('active');
  }

  function updateProcessingStep(stepKey, status) {
    // Update overlay
    const stepEl = $(`[data-pstep="${stepKey}"]`);
    if (stepEl) {
      stepEl.className = 'processing-modal__step';
      const icon = stepEl.querySelector('.processing-modal__step-icon');
      if (status === 'done') {
        stepEl.classList.add('processing-modal__step--done');
        icon.textContent = '✓';
      } else if (status === 'active') {
        stepEl.classList.add('processing-modal__step--active');
        icon.textContent = '●';
      } else {
        icon.textContent = '○';
      }
    }

    // Update pipeline card
    const pipeStep = $(`.pipeline__step[data-step="${stepKey}"]`);
    if (pipeStep) {
      pipeStep.className = 'pipeline__step';
      const statusEl = pipeStep.querySelector('.pipeline__step-status');
      if (status === 'done') {
        pipeStep.classList.add('pipeline__step--done');
        pipeStep.querySelector('.pipeline__step-icon').textContent = '✓';
        statusEl.textContent = 'Completed';
      } else if (status === 'active') {
        pipeStep.classList.add('pipeline__step--active');
        statusEl.textContent = 'Processing...';
      } else {
        pipeStep.classList.add('pipeline__step--pending');
        statusEl.textContent = 'Waiting';
      }
    }
  }

  function hideProcessingOverlay() {
    $('#processingOverlay').classList.remove('active');
  }

  async function simulatePipelineProgress(stepKeys) {
    for (let i = 0; i < stepKeys.length; i++) {
      updateProcessingStep(stepKeys[i], 'active');
      await sleep(300);
      updateProcessingStep(stepKeys[i], 'done');
    }
  }

  function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // ============================================================
  // RUN FUSION
  // ============================================================
  async function runFusion() {
    if (!state.mriUploaded || !state.petUploaded) {
      showToast('Please upload both MRI and PET scans first', 'warning');
      return;
    }

    // Show results section
    $('#results').classList.remove('hidden');
    showProcessingOverlay(`Processing ${state.selectedMethod}`);

    // Animate first steps
    const earlySteps = ['load-mri', 'load-pet', 'validate', 'normalize'];
    for (const s of earlySteps) {
      updateProcessingStep(s, 'active');
      await sleep(400);
      updateProcessingStep(s, 'done');
    }
    updateProcessingStep('register', 'active');

    try {
      const resp = await fetch(`${API_BASE}/fuse`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method: state.selectedMethod }),
      });

      // Handle non-JSON responses (like 502 Bad Gateway or 504 Gateway Timeout HTML pages from Render)
      const contentType = resp.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await resp.text();
        hideProcessingOverlay();
        showToast(`Server error (${resp.status}): The server may have run out of memory or timed out.`, 'error');
        console.error('Non-JSON response:', text);
        return;
      }

      const data = await resp.json();
      if (!resp.ok) {
        hideProcessingOverlay();
        showToast(data.error || 'Fusion failed', 'error');
        return;
      }

      state.fusionResult = data;

      // Complete remaining steps
      updateProcessingStep('register', 'done');
      updateProcessingStep('fuse', 'active');
      await sleep(400);
      updateProcessingStep('fuse', 'done');
      updateProcessingStep('evaluate', 'active');
      await sleep(400);
      updateProcessingStep('evaluate', 'done');

      hideProcessingOverlay();
      showToast('Fusion completed successfully!', 'success');

      // Display results
      displayFusionResults(data);

    } catch (err) {
      hideProcessingOverlay();
      showToast('Fusion failed: ' + err.message, 'error');
    }
  }

  function displayFusionResults(data) {
    // Update fused viewer
    if (data.fused_shape) {
      state.viewers.fused.maxSlices = {
        axial: data.fused_shape[2] - 1,
        coronal: data.fused_shape[1] - 1,
        sagittal: data.fused_shape[0] - 1,
      };
      const slider = $('#fusedSliceSlider');
      slider.max = data.fused_shape[2] - 1;
      const mid = Math.floor(data.fused_shape[2] / 2);
      slider.value = mid;
      $('#fusedSliceNum').textContent = mid;
      loadSlice('fused', 'axial', mid);
    }

    // Show sections
    $('#fusedResultCard').classList.remove('hidden');
    $('#comparisonCard').classList.remove('hidden');
    $('#regInfoCard').classList.remove('hidden');
    $('#metricsSection').classList.remove('hidden');
    $('#imageInfoSection').classList.remove('hidden');
    $('#exportSection').classList.remove('hidden');

    // Comparison sync slider
    if (data.fused_shape) {
      const compSlider = $('#compSliceSlider');
      compSlider.max = data.fused_shape[2] - 1;
      const mid = Math.floor(data.fused_shape[2] / 2);
      compSlider.value = mid;
      $('#compSliceNum').textContent = mid;
      loadComparisonSlices('axial', mid);
    }

    // Registration info
    displayRegistrationInfo(data.registration);

    // Metrics
    displayMetrics(data.metrics, state.selectedMethod);

    // Image info
    displayImageInfo(data);

    // Export buttons
    displayExportButtons(data.downloads);

    // Scroll to results
    setTimeout(() => {
      $('#fusedResultCard').scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 300);
  }

  // ============================================================
  // REGISTRATION INFO
  // ============================================================
  function displayRegistrationInfo(reg) {
    if (!reg) return;
    const grid = $('#regInfoGrid');
    const items = [
      { label: 'Status', value: reg.status === 'success' ? '✓ Registration Completed' : '✕ Failed' },
      { label: 'Method', value: 'Mattes Mutual Information' },
      { label: 'Final Metric', value: reg.metric_value != null ? reg.metric_value.toFixed(6) : '—' },
      { label: 'Iterations', value: reg.iterations != null ? reg.iterations : '—' },
      { label: 'MRI Dimensions', value: state.mriMeta ? state.mriMeta.shape.join(' × ') : '—' },
      { label: 'PET Dimensions', value: state.petMeta ? state.petMeta.shape.join(' × ') : '—' },
    ];

    grid.innerHTML = items.map(item =>
      `<div class="reg-info__item">
        <div class="reg-info__item-label">${item.label}</div>
        <div class="reg-info__item-value">${item.value}</div>
      </div>`
    ).join('');
  }

  // ============================================================
  // METRICS DISPLAY
  // ============================================================
  function displayMetrics(metrics, methodName) {
    if (!metrics) return;
    const grid = $('#metricsGrid');

    const cards = [
      {
        icon: '📊', label: 'Entropy', value: metrics.entropy.toFixed(4),
        sub: 'Information content',
        rows: [
          { label: 'MRI', value: metrics.mri_entropy ? metrics.mri_entropy.toFixed(4) : '—' },
          { label: 'PET', value: metrics.pet_entropy ? metrics.pet_entropy.toFixed(4) : '—' },
          { label: 'Fused', value: metrics.entropy.toFixed(4) },
        ]
      },
      {
        icon: '🔗', label: 'SSIM (MRI)', value: metrics.mri_ssim.toFixed(4),
        sub: 'Structural similarity to MRI',
      },
      {
        icon: '🔗', label: 'SSIM (PET)', value: metrics.pet_ssim.toFixed(4),
        sub: 'Structural similarity to PET',
      },
      {
        icon: '📈', label: 'Std Deviation', value: metrics.std.toFixed(4),
        sub: 'Image contrast',
        rows: [
          { label: 'MRI', value: metrics.mri_std ? metrics.mri_std.toFixed(4) : '—' },
          { label: 'PET', value: metrics.pet_std ? metrics.pet_std.toFixed(4) : '—' },
          { label: 'Fused', value: metrics.std.toFixed(4) },
        ]
      },
      {
        icon: '🌊', label: 'Spatial Frequency', value: metrics.spatial_frequency.toFixed(4),
        sub: 'Detail preservation',
        rows: [
          { label: 'MRI', value: metrics.mri_sf ? metrics.mri_sf.toFixed(4) : '—' },
          { label: 'PET', value: metrics.pet_sf ? metrics.pet_sf.toFixed(4) : '—' },
          { label: 'Fused', value: metrics.spatial_frequency.toFixed(4) },
        ]
      },
    ];

    grid.innerHTML = cards.map(card => {
      let rowsHtml = '';
      if (card.rows) {
        rowsHtml = `<div class="metric-card__row">
          ${card.rows.map(r => `
            <div class="metric-card__row-item">
              <div class="metric-card__row-label">${r.label}</div>
              <div class="metric-card__row-value">${r.value}</div>
            </div>
          `).join('')}
        </div>`;
      }
      return `
        <div class="glass-card metric-card">
          <div class="metric-card__icon">${card.icon}</div>
          <div class="metric-card__label">${card.label}</div>
          <div class="metric-card__value">${card.value}</div>
          <div class="metric-card__sub">${card.sub}</div>
          ${rowsHtml}
        </div>
      `;
    }).join('');
  }

  // ============================================================
  // IMAGE INFO ACCORDIONS
  // ============================================================
  function displayImageInfo(data) {
    const container = $('#imageInfoAccordions');
    const infos = [];

    if (state.mriMeta) {
      infos.push({ title: '🧲 MRI Image Information', meta: state.mriMeta });
    }
    if (state.petMeta) {
      infos.push({ title: '☢️ PET Image Information', meta: state.petMeta });
    }

    container.innerHTML = infos.map((info, i) => {
      const m = info.meta;
      const rows = [
        ['Dimensions', m.shape ? m.shape.join(' × ') : '—'],
        ['Voxel Spacing', m.voxel_spacing ? m.voxel_spacing.map(v => v.toFixed(3)).join(' × ') + ' mm' : '—'],
        ['Data Type', m.dtype || '—'],
        ['Min Intensity', m.intensity_min != null ? m.intensity_min.toFixed(4) : '—'],
        ['Max Intensity', m.intensity_max != null ? m.intensity_max.toFixed(4) : '—'],
        ['Mean', m.mean != null ? m.mean.toFixed(4) : '—'],
        ['Std Dev', m.std != null ? m.std.toFixed(4) : '—'],
        ['Orientation', m.orientation || '—'],
      ];

      return `
        <div class="info-accordion ${i === 0 ? 'open' : ''}">
          <button class="info-accordion__header" onclick="this.parentElement.classList.toggle('open')">
            <span>${info.title}</span>
            <span class="info-accordion__chevron">▼</span>
          </button>
          <div class="info-accordion__body">
            <div class="info-accordion__content">
              <table class="file-meta">
                ${rows.map(([l, v]) => `<tr><td>${l}</td><td>${v}</td></tr>`).join('')}
              </table>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }

  // ============================================================
  // EXPORT BUTTONS
  // ============================================================
  function displayExportButtons(downloads) {
    const grid = $('#exportGrid');
    const buttons = [
      { key: 'fused_nifti', icon: '🧠', label: 'Fused NIfTI', sub: 'Fused brain volume (.nii.gz)' },
      { key: 'registered_pet', icon: '☢️', label: 'Registered PET', sub: 'Registered PET volume (.nii.gz)' },
      { key: 'metrics_report', icon: '📊', label: 'Metrics Report', sub: 'Quality metrics (.json)' },
      { key: 'png_fused', icon: '🖼️', label: 'Fused PNG', sub: 'Middle slice visualization' },
    ];

    grid.innerHTML = buttons.map(btn =>
      `<button class="export-btn" onclick="downloadFile('${btn.key}')">
        <div class="export-btn__icon">${btn.icon}</div>
        <div class="export-btn__text">
          <span class="export-btn__label">${btn.label}</span>
          <span class="export-btn__sub">${btn.sub}</span>
        </div>
      </button>`
    ).join('');
  }

  // Global download function
  window.downloadFile = async function (key) {
    try {
      const resp = await fetch(`${API_BASE}/download/${key}`);
      if (!resp.ok) {
        showToast('Download failed', 'error');
        return;
      }

      const blob = await resp.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;

      // Get filename from content-disposition or use default
      const disp = resp.headers.get('content-disposition');
      if (disp && disp.includes('filename=')) {
        a.download = disp.split('filename=')[1].replace(/"/g, '');
      } else {
        a.download = key;
      }

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      showToast('Download started', 'success');
    } catch (err) {
      showToast('Download failed: ' + err.message, 'error');
    }
  };

  // ============================================================
  // RUN ALL FUSIONS (COMPARISON)
  // ============================================================
  async function runAllFusions() {
    if (!state.mriUploaded || !state.petUploaded) {
      showToast('Please upload both MRI and PET scans first', 'warning');
      return;
    }

    // Show results section
    $('#results').classList.remove('hidden');
    showProcessingOverlay('Comparing All Fusion Methods');

    // Animate early steps
    const earlySteps = ['load-mri', 'load-pet', 'validate', 'normalize', 'register'];
    for (const s of earlySteps) {
      updateProcessingStep(s, 'active');
      await sleep(300);
      updateProcessingStep(s, 'done');
    }
    updateProcessingStep('fuse', 'active');

    try {
      const resp = await fetch(`${API_BASE}/fuse/all`, {
        method: 'POST',
      });

      const data = await resp.json();
      if (!resp.ok) {
        hideProcessingOverlay();
        showToast(data.error || 'Comparison failed', 'error');
        return;
      }

      state.comparisonResult = data;

      // Also set the first method result as main
      const firstMethod = Object.keys(data.results)[0];
      if (firstMethod && data.results[firstMethod]) {
        state.fusionResult = data.results[firstMethod];
        state.fusionResult.fused_shape = data.fused_shape;
        state.fusionResult.registration = data.registration;
        state.fusionResult.downloads = data.downloads;
      }

      updateProcessingStep('fuse', 'done');
      updateProcessingStep('evaluate', 'active');
      await sleep(400);
      updateProcessingStep('evaluate', 'done');

      hideProcessingOverlay();
      showToast('All fusion methods completed!', 'success');

      // Display results
      if (state.fusionResult) {
        displayFusionResults({
          ...state.fusionResult,
          metrics: data.results[firstMethod].metrics,
          fused_shape: data.fused_shape,
          registration: data.registration,
          downloads: data.downloads,
        });
      }

      // Display comparison
      displayComparison(data.results);

    } catch (err) {
      hideProcessingOverlay();
      showToast('Comparison failed: ' + err.message, 'error');
    }
  }

  // ============================================================
  // COMPARISON CHARTS
  // ============================================================
  let charts = {};

  function displayComparison(results) {
    $('#fusionComparisonSection').classList.remove('hidden');

    const methods = Object.keys(results);
    const metrics = methods.map(m => results[m].metrics);

    // Determine best values
    const entropyVals = metrics.map(m => m.entropy);
    const mriSsimVals = metrics.map(m => m.mri_ssim);
    const petSsimVals = metrics.map(m => m.pet_ssim);
    const stdVals = metrics.map(m => m.std);
    const sfVals = metrics.map(m => m.spatial_frequency);

    // Chart colors
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    const textColor = isDark ? '#94A3B8' : '#475569';
    const gridColor = isDark ? 'rgba(51,65,85,0.3)' : 'rgba(226,232,240,0.6)';

    const barColors = [
      'rgba(22, 163, 74, 0.8)',
      'rgba(34, 197, 94, 0.8)',
      'rgba(74, 222, 128, 0.8)',
      'rgba(21, 128, 61, 0.8)',
    ];

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        x: {
          ticks: { color: textColor, font: { size: 11, family: 'Inter' } },
          grid: { display: false },
        },
        y: {
          ticks: { color: textColor, font: { size: 11, family: 'Inter' } },
          grid: { color: gridColor },
        },
      },
    };

    // Destroy existing charts
    Object.values(charts).forEach(c => c.destroy());
    charts = {};

    // Entropy chart
    charts.entropy = new Chart($('#entropyChart'), {
      type: 'bar',
      data: {
        labels: methods,
        datasets: [{
          data: entropyVals,
          backgroundColor: barColors,
          borderRadius: 6,
          borderSkipped: false,
        }],
      },
      options: chartOptions,
    });

    // SSIM chart (grouped)
    charts.ssim = new Chart($('#ssimChart'), {
      type: 'bar',
      data: {
        labels: methods,
        datasets: [
          {
            label: 'SSIM (MRI)',
            data: mriSsimVals,
            backgroundColor: 'rgba(59, 130, 246, 0.7)',
            borderRadius: 6,
            borderSkipped: false,
          },
          {
            label: 'SSIM (PET)',
            data: petSsimVals,
            backgroundColor: 'rgba(245, 158, 11, 0.7)',
            borderRadius: 6,
            borderSkipped: false,
          },
        ],
      },
      options: {
        ...chartOptions,
        plugins: {
          legend: {
            display: true,
            labels: { color: textColor, font: { size: 11, family: 'Inter' } },
          },
        },
      },
    });

    // Std chart
    charts.std = new Chart($('#stdChart'), {
      type: 'bar',
      data: {
        labels: methods,
        datasets: [{
          data: stdVals,
          backgroundColor: barColors,
          borderRadius: 6,
          borderSkipped: false,
        }],
      },
      options: chartOptions,
    });

    // SF chart
    charts.sf = new Chart($('#sfChart'), {
      type: 'bar',
      data: {
        labels: methods,
        datasets: [{
          data: sfVals,
          backgroundColor: barColors,
          borderRadius: 6,
          borderSkipped: false,
        }],
      },
      options: chartOptions,
    });

    // Comparison table
    buildComparisonTable(methods, metrics);
  }

  function buildComparisonTable(methods, metricsArr) {
    const tbody = $('#comparisonTableBody');

    // Find best for each metric
    const bestIdx = {
      entropy: 0, mri_ssim: 0, pet_ssim: 0, std: 0, spatial_frequency: 0,
    };
    for (const key of Object.keys(bestIdx)) {
      let best = -Infinity;
      metricsArr.forEach((m, i) => {
        if (m[key] > best) { best = m[key]; bestIdx[key] = i; }
      });
    }

    tbody.innerHTML = methods.map((method, i) => {
      const m = metricsArr[i];
      const cell = (key) => {
        const val = m[key].toFixed(4);
        return i === bestIdx[key] ? `<td class="best-value">${val}</td>` : `<td>${val}</td>`;
      };

      return `<tr>
        <td><strong>${method}</strong></td>
        ${cell('entropy')}
        ${cell('mri_ssim')}
        ${cell('pet_ssim')}
        ${cell('std')}
        ${cell('spatial_frequency')}
      </tr>`;
    }).join('');
  }

  // ============================================================
  // INITIALIZATION
  // ============================================================
  function init() {
    initTheme();
    initNavigation();
    initUpload('mri');
    initUpload('pet');
    initViewerControls();
    initMethodSelection();
    initFullscreen();

    // Button events
    if ($('#themeToggleCheckbox')) {
      $('#themeToggleCheckbox').addEventListener('change', toggleTheme);
    }
    $('#helpBtn').addEventListener('click', openHelp);
    $('#helpClose').addEventListener('click', closeHelp);
    $('#helpBackdrop').addEventListener('click', closeHelp);
    $('#menuToggle').addEventListener('click', toggleMobileNav);
    $('#runFusionBtn').addEventListener('click', runFusion);
    $('#runAllFusionBtn').addEventListener('click', runAllFusions);
  }

  // Start on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

})();
