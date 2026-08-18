"""
ui.py — Premium dark medical imaging UI theme and component functions.

Enterprise-grade research workstation aesthetic:
- Deep navy / near-black background
- Soft cyan and blue accents
- Subtle violet/purple highlights
- Glassmorphism panels
- Professional Inter typography
"""

import base64
from pathlib import Path
import streamlit as st

# Resolve background image path relative to this file's location
_HERE = Path(__file__).resolve().parent
_BG_PATH = _HERE.parent.parent / "website" / "assets" / "bg.jpg"


# ════════════════════════════════════════════════════════════════
# PREMIUM DARK MEDICAL CSS THEME
# ════════════════════════════════════════════════════════════════

PREMIUM_THEME_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── CSS Variables ── */
:root {
  --bg-0:          #06121C;
  --bg-1:          #081722;
  --bg-2:          #0B1B28;
  --bg-elevated:   #102534;
  --bg-glass:      rgba(11, 27, 40, 0.75);
  --bg-glass-lt:   rgba(16, 37, 52, 0.5);
  --border:        #1B3445;
  --border-accent: rgba(41, 217, 255, 0.22);
  --cyan:          #29D9FF;
  --cyan-dim:      rgba(41, 217, 255, 0.1);
  --blue:          #4C8DFF;
  --violet:        #A855F7;
  --violet-dim:    rgba(168, 85, 247, 0.1);
  --teal:          #16C6B7;
  --teal-dim:      rgba(22, 198, 183, 0.1);
  --green:         #27D7A0;
  --green-dim:     rgba(39, 215, 160, 0.1);
  --amber:         #fbbf24;
  --red:           #f87171;
  --text-1:        #EAF4F8;
  --text-2:        #8FA8B8;
  --text-3:        #60798A;
  --r-sm:          8px;
  --r-md:          14px;
  --r-lg:          18px;
  --r-xl:          24px;
  --shadow-md:     0 4px 24px rgba(0, 0, 0, 0.3);
  --shadow-lg:     0 8px 40px rgba(0, 0, 0, 0.5);
  --glow-cyan:     0 0 24px rgba(41, 217, 255, 0.12);
  --glow-mri:      0 0 24px rgba(76, 141, 255, 0.15);
  --glow-pet:      0 0 24px rgba(168, 85, 247, 0.15);
  --transition:    all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ── Base / Streamlit Overrides ── */
html {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  background-color: var(--bg-0);   /* fallback — overridden by inject_theme() */
  color: var(--text-1) !important;
  min-height: 100vh;
}
body, .stApp {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
  background-color: transparent !important;  /* let html background show through */
  color: var(--text-1) !important;
}
.stApp > div, .stApp > div > div {
  background-color: transparent !important;
}

/* Hide Streamlit chrome */
[data-testid="stHeader"]          { display: none !important; }
[data-testid="stToolbar"]         { display: none !important; }
[data-testid="collapsedControl"]  { display: none !important; }
#MainMenu                         { visibility: hidden !important; }
footer                            { visibility: hidden !important; }
button[kind="header"]             { display: none !important; }
[data-testid="stSidebar"]         { display: none !important; }
section[data-testid="stSidebar"]  { display: none !important; }

/* Main content area */
.main .block-container,
[data-testid="stMainBlockContainer"] {
  background:    transparent !important;
  padding-top:   0 !important;
  padding-bottom: 3rem !important;
  max-width:     1440px !important;
  padding-left:  2rem !important;
  padding-right: 2rem !important;
}

/* Columns */
[data-testid="column"] { background: transparent !important; }

/* Global text overrides */
.stMarkdown p,
.stMarkdown li,
.stMarkdown span,
[data-testid="stMarkdownContainer"] p {
  color: var(--text-2) !important;
  font-family: 'Inter', sans-serif !important;
}
h1, h2, h3, h4 {
  color: var(--text-1) !important;
  font-family: 'Inter', sans-serif !important;
}
label {
  color: var(--text-2) !important;
  font-family: 'Inter', sans-serif !important;
}


/* ════════════════════════════════
   TOP NAVIGATION
════════════════════════════════ */
.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 2rem;
  height: 58px;
  background: rgba(6, 18, 28, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border);
  position: relative;
  z-index: 1000;
  margin: 0 -2rem 0 -2rem;
}
.top-nav-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
}
.logo-mark {
  width: 34px; height: 34px;
  background: linear-gradient(135deg, var(--cyan) 0%, var(--teal) 100%);
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
  flex-shrink: 0;
  box-shadow: 0 2px 10px rgba(8, 145, 178, 0.3);
}
.logo-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: var(--text-1) !important;
  letter-spacing: 0.2px;
  line-height: 1.2;
}
.logo-sub {
  font-size: 0.62rem;
  color: var(--text-3) !important;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  font-weight: 500;
}
.top-nav-links {
  display: flex;
  align-items: center;
  gap: 2px;
}
.top-nav-links a {
  padding: 6px 14px;
  border-radius: var(--r-sm);
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-2) !important;
  text-decoration: none;
  transition: var(--transition);
  letter-spacing: 0.2px;
}
.top-nav-links a:hover {
  color: var(--text-1) !important;
  background: rgba(255, 255, 255, 0.06);
}
.top-nav-links a.active {
  color: var(--teal) !important;
  background: var(--teal-dim);
}
.top-nav-right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.nav-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  background: var(--green-dim);
  border: 1px solid rgba(52, 211, 153, 0.2);
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--green) !important;
  letter-spacing: 0.3px;
}
.nav-status .dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--green);
  animation: pulse-dot 2.5s ease-in-out infinite;
  flex-shrink: 0;
}
.nav-icon-btn {
  width: 32px; height: 32px;
  border-radius: var(--r-sm);
  display: flex; align-items: center; justify-content: center;
  color: var(--text-2) !important;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  cursor: pointer;
  transition: var(--transition);
  font-size: 14px;
}
.nav-icon-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: var(--text-1) !important;
}

/* Settings button — fixed in top-right nav, beside the ○ user icon */
#settings-btn-wrap {
  position: fixed;
  top: 10px;
  right: 52px;
  z-index: 9999;
  height: 0;          /* take no layout space */
  overflow: visible;
}
#settings-btn-wrap > div {
  height: 0 !important;
  overflow: visible !important;
}
#settings-btn-wrap [data-testid="stVerticalBlock"] {
  height: 0 !important;
  gap: 0 !important;
}
#settings-btn-wrap .stButton {
  height: 32px !important;
}
#settings-btn-wrap .stButton > button {
  width: 32px !important;
  height: 32px !important;
  min-width: 32px !important;
  padding: 0 !important;
  border-radius: 8px !important;
  background: rgba(255, 255, 255, 0.04) !important;
  border: 1px solid rgba(255,255,255,0.10) !important;
  color: rgba(148,163,184,0.9) !important;
  font-size: 15px !important;
  line-height: 1 !important;
  box-shadow: none !important;
  transition: all 0.2s ease !important;
}
#settings-btn-wrap .stButton > button:hover {
  background: rgba(255, 255, 255, 0.10) !important;
  color: #f0f9ff !important;
  transform: rotate(35deg) scale(1.05) !important;
  border-color: rgba(34,211,238,0.35) !important;
}

/* Settings dialog styling */
[data-testid="stDialog"] {
  background: var(--bg-1) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-lg) !important;
  box-shadow: 0 24px 64px rgba(0,0,0,0.55) !important;
}
[data-testid="stDialog"] > div {
  background: var(--bg-1) !important;
}
.settings-section-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.8px;
  text-transform: uppercase;
  color: var(--cyan);
  margin: 1rem 0 0.5rem 0;
  padding-bottom: 0.3rem;
  border-bottom: 1px solid var(--border);
}


/* ════════════════════════════════
   WORKSPACE HEADER
════════════════════════════════ */
.workspace-header {
  padding: 2.2rem 0 1.8rem 0;
  border-bottom: 1px solid var(--border);
  margin-bottom: 2rem;
}
.ws-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 11px;
  background: var(--cyan-dim);
  border: 1px solid var(--border-accent);
  border-radius: 999px;
  font-size: 0.66rem;
  font-weight: 700;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: var(--cyan) !important;
  margin-bottom: 0.8rem;
}
.workspace-header h1 {
  font-size: 1.9rem;
  font-weight: 700;
  letter-spacing: -0.5px;
  color: var(--text-1) !important;
  margin: 0 0 0.35rem 0;
  line-height: 1.2;
}
.ws-subtitle {
  font-size: 0.9rem;
  color: var(--text-2) !important;
  font-weight: 400;
  letter-spacing: 0.1px;
  margin: 0;
}
.ws-status-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 0.9rem;
}
.ws-status {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.72rem;
  font-weight: 600;
  color: var(--green) !important;
  letter-spacing: 0.3px;
}
.ws-status .dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--green);
  animation: pulse-dot 2.5s ease-in-out infinite;
}
.ws-tech-tags {
  display: flex;
  gap: 5px;
}
.ws-tech-tag {
  font-size: 0.62rem;
  padding: 2px 7px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  border-radius: 4px;
  color: var(--text-3) !important;
  font-weight: 500;
  letter-spacing: 0.3px;
}


/* ════════════════════════════════
   SECTION TITLES
════════════════════════════════ */
.section-title-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 1.8rem 0 1rem 0;
}
.section-num {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: var(--text-3) !important;
  font-variant-numeric: tabular-nums;
  min-width: 20px;
}
.section-label {
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 1.8px;
  text-transform: uppercase;
  color: var(--text-3) !important;
}
.section-line {
  flex: 1;
  height: 1px;
  background: var(--border);
}


/* ════════════════════════════════
   UPLOAD PANELS
════════════════════════════════ */
.upload-panel {
  background: var(--bg-glass);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.6rem;
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1), box-shadow 0.25s, border-color 0.25s;
  position: relative;
  overflow: hidden;
  min-height: 120px;
}
.upload-panel:hover {
  transform: translateY(-2px);
}
.upload-panel.mri:hover {
  border-color: rgba(76, 141, 255, 0.3);
  box-shadow: var(--glow-mri);
}
.upload-panel.pet:hover {
  border-color: rgba(168, 85, 247, 0.3);
  box-shadow: var(--glow-pet);
}
.upload-panel.mri.loaded {
  border-color: rgba(76, 141, 255, 0.2);
}
.upload-panel.pet.loaded {
  border-color: rgba(168, 85, 247, 0.2);
}
.upload-panel-top-line {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  opacity: 0;
  transition: opacity 0.3s ease;
}
.upload-panel.mri .upload-panel-top-line {
  background: linear-gradient(90deg, transparent 0%, rgba(76, 141, 255, 0.4) 50%, transparent 100%);
}
.upload-panel.pet .upload-panel-top-line {
  background: linear-gradient(90deg, transparent 0%, rgba(168, 85, 247, 0.4) 50%, transparent 100%);
}
.upload-panel:hover .upload-panel-top-line { opacity: 1; }
.upload-panel-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 1rem;
}
.upload-type-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
  transition: var(--transition);
}
.upload-type-icon.mri {
  background: var(--mri-blue-dim);
  border: 1px solid rgba(76, 141, 255, 0.2);
  color: var(--cyan);
  box-shadow: 0 0 12px rgba(41, 217, 255, 0.1);
}
.upload-type-icon.pet {
  background: var(--pet-purple-dim);
  border: 1px solid rgba(168, 85, 247, 0.2);
  color: var(--violet);
  box-shadow: 0 0 12px rgba(168, 85, 247, 0.1);
}
.upload-panel.mri:hover .upload-type-icon.mri {
  box-shadow: 0 0 16px rgba(41, 217, 255, 0.3);
}
.upload-panel.pet:hover .upload-type-icon.pet {
  box-shadow: 0 0 16px rgba(168, 85, 247, 0.3);
}
.upload-type-label {
  font-size: 0.98rem;
  font-weight: 700;
  color: var(--text-1) !important;
  letter-spacing: -0.1px;
  line-height: 1.2;
}
.upload-type-sub {
  font-size: 0.74rem;
  color: var(--text-3) !important;
  margin-top: 3px;
  font-weight: 400;
}
.upload-format-row {
  display: flex;
  gap: 5px;
  margin-bottom: 0.9rem;
  flex-wrap: wrap;
}
.upload-fmt-tag {
  padding: 2px 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid var(--border);
  border-radius: 4px;
  font-size: 0.64rem;
  font-weight: 600;
  color: var(--text-3) !important;
  letter-spacing: 0.4px;
  font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
  transition: var(--transition);
}
.upload-panel.mri:hover .upload-fmt-tag {
  border-color: rgba(76, 141, 255, 0.2);
  color: rgba(76, 141, 255, 0.8) !important;
}
.upload-panel.pet:hover .upload-fmt-tag {
  border-color: rgba(168, 85, 247, 0.2);
  color: rgba(168, 85, 247, 0.8) !important;
}
.upload-hint {
  font-size: 0.7rem;
  color: var(--text-3) !important;
  margin-top: 0.4rem;
  letter-spacing: 0.1px;
}

/* File info row (post-upload) */
.file-info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0.55rem 0.8rem;
  background: rgba(52, 211, 153, 0.06);
  border: 1px solid rgba(52, 211, 153, 0.18);
  border-radius: var(--r-sm);
  margin-top: 0.5rem;
}
.fi-icon { font-size: 14px; flex-shrink: 0; }
.fi-name {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-1) !important;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}
.fi-size {
  font-size: 0.7rem;
  color: var(--text-3) !important;
  white-space: nowrap;
  flex-shrink: 0;
}
.fi-badge {
  padding: 2px 8px;
  background: rgba(52, 211, 153, 0.12);
  border: 1px solid rgba(52, 211, 153, 0.28);
  border-radius: 5px;
  font-size: 0.62rem;
  font-weight: 700;
  color: var(--green) !important;
  letter-spacing: 0.4px;
  white-space: nowrap;
  flex-shrink: 0;
  text-transform: uppercase;
}
.fi-badge.error {
  background: rgba(248, 113, 113, 0.1);
  border-color: rgba(248, 113, 113, 0.25);
  color: var(--red) !important;
}

/* Validation row */
.val-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 0.5rem 0.8rem;
  border-radius: var(--r-sm);
  font-size: 0.76rem;
  font-weight: 500;
  margin-top: 0.4rem;
  line-height: 1.4;
}
.val-row.ok {
  background: rgba(52, 211, 153, 0.06);
  border: 1px solid rgba(52, 211, 153, 0.18);
  color: var(--green) !important;
}
.val-row.err {
  background: rgba(248, 113, 113, 0.06);
  border: 1px solid rgba(248, 113, 113, 0.18);
  color: var(--red) !important;
}
.val-row.warn {
  background: rgba(251, 191, 36, 0.06);
  border: 1px solid rgba(251, 191, 36, 0.18);
  color: var(--amber) !important;
}

/* Empty state for upload panels */
.upload-empty-state {
  text-align: center;
  padding: 1.5rem 0.5rem 0.5rem 0.5rem;
  color: var(--text-3) !important;
}
.upload-empty-icon {
  font-size: 2rem;
  opacity: 0.3;
  margin-bottom: 0.5rem;
}
.upload-empty-text {
  font-size: 0.78rem;
  color: var(--text-3) !important;
}


/* ════════════════════════════════
   SCAN PANELS (Image Viewer)
════════════════════════════════ */
.scan-panel {
  background: #010c15;
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  overflow: hidden;
  position: relative;
  transition: var(--transition);
}
.scan-panel:hover {
  border-color: rgba(34, 211, 238, 0.12);
}
.scan-panel-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 7px 12px;
  background: rgba(11, 28, 44, 0.9);
  border-bottom: 1px solid var(--border);
}
.scan-label-text {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 1.8px;
  text-transform: uppercase;
  color: var(--cyan) !important;
}
.scan-type-badge {
  font-size: 0.6rem;
  padding: 2px 7px;
  border-radius: 4px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.scan-type-badge.mri {
  background: rgba(56, 189, 248, 0.1);
  color: var(--blue) !important;
  border: 1px solid rgba(56, 189, 248, 0.2);
}
.scan-type-badge.pet {
  background: rgba(251, 191, 36, 0.08);
  color: var(--amber) !important;
  border: 1px solid rgba(251, 191, 36, 0.18);
}
.scan-type-badge.fused {
  background: var(--violet-dim);
  color: var(--violet) !important;
  border: 1px solid rgba(129, 140, 248, 0.2);
}
.scan-type-badge.overlay {
  background: rgba(34, 211, 238, 0.08);
  color: var(--cyan) !important;
  border: 1px solid var(--border-accent);
}


/* ════════════════════════════════
   VIEWER CONTROLS BAR
════════════════════════════════ */
.viewer-controls-bar {
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 0.9rem 1.2rem;
  margin-bottom: 0.8rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  flex-wrap: wrap;
}
.viewer-ctrl-label {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-3) !important;
}


/* ════════════════════════════════
   FUSION CONTROLS PANEL
════════════════════════════════ */
.fusion-ctrl-panel {
  background: var(--bg-glass);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 1.5rem 1.6rem;
  margin: 1rem 0;
  position: relative;
  overflow: hidden;
}
.fusion-ctrl-panel::before {
  content: '';
  position: absolute;
  left: 0; top: 0; bottom: 0;
  width: 3px;
  background: linear-gradient(180deg, var(--cyan), var(--violet));
  border-radius: 2px 0 0 2px;
}
.fcp-title {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 1.8px;
  text-transform: uppercase;
  color: var(--text-3) !important;
  margin-bottom: 1.2rem;
}


/* ════════════════════════════════
   PIPELINE DIAGRAM
════════════════════════════════ */
.pipeline-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 0;
  padding: 1rem 0;
}
.pip-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  padding: 7px 14px;
  background: var(--bg-1);
  border: 1px solid var(--border);
  border-radius: 9px;
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--text-3) !important;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: var(--transition);
  white-space: nowrap;
}
.pip-step.done {
  background: rgba(52, 211, 153, 0.07);
  border-color: rgba(52, 211, 153, 0.25);
  color: var(--green) !important;
}
.pip-step.active {
  background: var(--cyan-dim);
  border-color: var(--border-accent);
  color: var(--cyan) !important;
  box-shadow: 0 0 16px rgba(34, 211, 238, 0.1);
}
.pip-connector {
  width: 20px;
  height: 1px;
  background: var(--border);
  flex-shrink: 0;
}
.pip-connector.done {
  background: rgba(52, 211, 153, 0.35);
}


/* ════════════════════════════════
   METRIC CARDS (Scientific)
════════════════════════════════ */
.metric-sci {
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 1.2rem 1.4rem;
  transition: var(--transition);
  position: relative;
  overflow: hidden;
}
.metric-sci::before {
  content: '';
  position: absolute;
  top: 0; left: 0;
  width: 3px; height: 100%;
  background: var(--cyan);
  border-radius: 2px 0 0 2px;
}
.metric-sci:nth-child(2)::before { background: var(--blue); }
.metric-sci:nth-child(3)::before { background: var(--violet); }
.metric-sci:nth-child(4)::before { background: var(--green); }
.metric-sci:hover {
  border-color: var(--border-accent);
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}
.m-label {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--text-3) !important;
  margin-bottom: 0.5rem;
}
.m-value {
  font-size: 1.7rem;
  font-weight: 700;
  color: var(--text-1) !important;
  letter-spacing: -1px;
  line-height: 1;
  font-variant-numeric: tabular-nums;
}
.m-unit {
  font-size: 0.75rem;
  color: var(--text-3) !important;
  font-weight: 400;
  margin-left: 3px;
  letter-spacing: 0;
}
.m-desc {
  font-size: 0.7rem;
  color: var(--text-3) !important;
  margin-top: 0.5rem;
  line-height: 1.45;
}
.m-bar-bg {
  height: 2px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 2px;
  margin-top: 0.9rem;
  overflow: hidden;
}
.m-bar-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(90deg, var(--cyan), var(--blue));
}


/* ════════════════════════════════
   INFO CARDS
════════════════════════════════ */
.info-item {
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border);
}
.info-item:last-child { border-bottom: none; }
.info-label {
  font-size: 0.62rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-3) !important;
  font-weight: 600;
  margin-bottom: 2px;
}
.info-value {
  font-size: 0.85rem;
  color: var(--text-1) !important;
  font-weight: 500;
  font-variant-numeric: tabular-nums;
}


/* ════════════════════════════════
   EXPORT SECTION
════════════════════════════════ */
.export-wrap {
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 1.2rem 1.6rem;
  margin: 0.5rem 0;
}
.export-title {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 1.5px;
  text-transform: uppercase;
  color: var(--text-3) !important;
  margin-bottom: 0.8rem;
}


/* ════════════════════════════════
   REGISTRATION STATUS
════════════════════════════════ */
.reg-panel {
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: var(--r-md);
  padding: 1rem 1.4rem;
}
.reg-ok  { color: var(--green) !important; font-weight: 600; }
.reg-fail { color: var(--red) !important; font-weight: 600; }


/* ════════════════════════════════
   STATUS PILL
════════════════════════════════ */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 14px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  background: var(--green-dim);
  color: var(--green) !important;
  border: 1px solid rgba(52, 211, 153, 0.22);
}
.status-pill .dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--green);
  animation: pulse-dot 2.5s ease-in-out infinite;
}


/* ════════════════════════════════
   EMPTY / INFO STATES
════════════════════════════════ */
.empty-state-panel {
  background: var(--bg-glass);
  border: 1px solid var(--border);
  border-radius: var(--r-lg);
  padding: 3rem 2rem;
  text-align: center;
  margin: 1rem 0;
}
.es-icon {
  font-size: 2.8rem;
  margin-bottom: 0.8rem;
  opacity: 0.35;
}
.es-title {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-2) !important;
  margin-bottom: 0.5rem;
}
.es-desc {
  font-size: 0.8rem;
  color: var(--text-3) !important;
  line-height: 1.6;
  max-width: 340px;
  margin: 0 auto;
}


/* ════════════════════════════════
   SECTION DIVIDER
════════════════════════════════ */
.section-divider {
  border: none;
  border-top: 1px solid var(--border);
  margin: 1.5rem 0;
}


/* ════════════════════════════════
   DISCLAIMER
════════════════════════════════ */
.disclaimer-bar {
  margin-top: 2.5rem;
  padding: 0.85rem 1.4rem;
  background: rgba(251, 191, 36, 0.03);
  border: 1px solid rgba(251, 191, 36, 0.1);
  border-radius: var(--r-md);
  text-align: center;
  font-size: 0.72rem;
  color: rgba(251, 191, 36, 0.55) !important;
  letter-spacing: 0.15px;
  line-height: 1.6;
}
.disclaimer-bar strong {
  color: rgba(251, 191, 36, 0.75) !important;
  font-weight: 600;
}

/* Footer */
.app-footer {
  margin-top: 1rem;
  padding: 0.6rem 0;
  text-align: center;
  font-size: 0.66rem;
  color: var(--text-3) !important;
  letter-spacing: 0.3px;
}


/* ════════════════════════════════
   STREAMLIT COMPONENT OVERRIDES
════════════════════════════════ */

/* Buttons */
.stButton > button {
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  border-radius: 10px !important;
  letter-spacing: 0.3px !important;
  transition: all 0.22s ease !important;
}
.stButton > button[kind="primary"],
.stButton > button[data-testid="baseButton-primary"] {
  background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%) !important;
  color: #f0f9ff !important;
  border: none !important;
  box-shadow: 0 2px 14px rgba(8, 145, 178, 0.28) !important;
}
.stButton > button[kind="primary"]:hover {
  box-shadow: 0 4px 28px rgba(34, 211, 238, 0.28) !important;
  transform: translateY(-1px) !important;
}
.stButton > button[kind="secondary"],
.stButton > button[data-testid="baseButton-secondary"] {
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--text-2) !important;
  border: 1px solid var(--border) !important;
}
.stButton > button[kind="secondary"]:hover {
  background: rgba(255, 255, 255, 0.08) !important;
  border-color: var(--border-accent) !important;
  color: var(--text-1) !important;
}

/* Download buttons */
.stDownloadButton > button {
  font-family: 'Inter', sans-serif !important;
  font-weight: 500 !important;
  border-radius: 10px !important;
  background: rgba(255, 255, 255, 0.04) !important;
  color: var(--text-2) !important;
  border: 1px solid var(--border) !important;
  transition: all 0.22s ease !important;
}
.stDownloadButton > button:hover {
  background: var(--cyan-dim) !important;
  color: var(--cyan) !important;
  border-color: var(--border-accent) !important;
}

/* File uploader */
[data-testid="stFileUploader"] {
  background: transparent !important;
}
[data-testid="stFileUploaderDropzone"] {
  background: rgba(11, 28, 44, 0.4) !important;
  border: 1.5px dashed rgba(34, 211, 238, 0.22) !important;
  border-radius: 14px !important;
  transition: all 0.22s ease !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
  background: rgba(34, 211, 238, 0.04) !important;
  border-color: rgba(34, 211, 238, 0.45) !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] p,
[data-testid="stFileUploaderDropzone"] small,
[data-testid="stFileUploaderDropzone"] span {
  color: var(--text-3) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.82rem !important;
}
[data-testid="stFileUploaderDropzone"] svg {
  fill: var(--text-3) !important;
  opacity: 0.5;
}
[data-testid="stFileUploader"] button {
  background: rgba(34, 211, 238, 0.08) !important;
  color: var(--cyan) !important;
  border: 1px solid var(--border-accent) !important;
  border-radius: 8px !important;
  font-family: 'Inter', sans-serif !important;
  font-weight: 600 !important;
  font-size: 0.8rem !important;
  padding: 5px 14px !important;
}
[data-testid="stFileUploader"] button:hover {
  background: rgba(34, 211, 238, 0.14) !important;
}

/* Sliders */
[data-testid="stSlider"] > label,
[data-testid="stSlider"] label {
  color: var(--text-2) !important;
  font-size: 0.82rem !important;
  font-weight: 500 !important;
  font-family: 'Inter', sans-serif !important;
}
[data-testid="stSlider"] [data-testid="stSliderTrack"] {
  background: rgba(255, 255, 255, 0.08) !important;
}
[data-testid="stSlider"] [data-testid="stSliderTrackFill"] {
  background: var(--cyan) !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
  background: var(--cyan) !important;
  border-color: var(--cyan) !important;
  box-shadow: 0 0 10px rgba(34, 211, 238, 0.4) !important;
}
[data-testid="stSlider"] [data-testid="stTickBarMin"],
[data-testid="stSlider"] [data-testid="stTickBarMax"] {
  color: var(--text-3) !important;
  font-size: 0.72rem !important;
}

/* Select boxes */
[data-baseweb="select"] > div {
  background: var(--bg-1) !important;
  border-color: var(--border) !important;
  border-radius: 10px !important;
  color: var(--text-2) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.85rem !important;
}
[data-baseweb="select"] > div:hover {
  border-color: var(--border-accent) !important;
}
[data-baseweb="select"] [data-testid="stSelectboxVirtualDropdown"],
[data-baseweb="menu"] {
  background: var(--bg-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}
[data-baseweb="menu"] li {
  background: transparent !important;
  color: var(--text-2) !important;
  font-family: 'Inter', sans-serif !important;
  font-size: 0.83rem !important;
}
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [aria-selected="true"] {
  background: var(--cyan-dim) !important;
  color: var(--cyan) !important;
}
[data-baseweb="select"] [data-testid="stMarkdownContainer"] p {
  color: var(--text-2) !important;
}

/* Radio buttons */
[data-testid="stRadio"] > label {
  color: var(--text-3) !important;
  font-size: 0.75rem !important;
  font-weight: 600 !important;
  letter-spacing: 0.5px !important;
}
[data-testid="stRadio"] label {
  color: var(--text-2) !important;
  font-size: 0.85rem !important;
  font-family: 'Inter', sans-serif !important;
}

/* Expanders */
[data-testid="stExpander"] {
  background: var(--bg-glass) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  overflow: hidden !important;
}
[data-testid="stExpander"] > details > summary {
  padding: 0.75rem 1rem !important;
  background: transparent !important;
  color: var(--text-2) !important;
  font-weight: 500 !important;
  font-size: 0.85rem !important;
  font-family: 'Inter', sans-serif !important;
}
[data-testid="stExpander"] > details > summary:hover {
  color: var(--text-1) !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  gap: 4px !important;
  background: rgba(0, 0, 0, 0.25) !important;
  border-radius: 10px !important;
  padding: 3px !important;
  border: 1px solid var(--border) !important;
}
.stTabs [data-baseweb="tab"] {
  border-radius: 8px !important;
  font-weight: 600 !important;
  font-size: 0.82rem !important;
  color: var(--text-3) !important;
  background: transparent !important;
  border: none !important;
  padding: 6px 16px !important;
  font-family: 'Inter', sans-serif !important;
  transition: var(--transition) !important;
}
.stTabs [aria-selected="true"] {
  background: var(--bg-1) !important;
  color: var(--cyan) !important;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4) !important;
}
[data-baseweb="tab-highlight"] { display: none !important; }
[data-baseweb="tab-border"]    { display: none !important; }

/* Alerts / info boxes */
[data-testid="stAlert"] {
  background: var(--bg-glass) !important;
  border-radius: var(--r-md) !important;
  border: 1px solid var(--border) !important;
  color: var(--text-2) !important;
}
[data-testid="stAlert"] p { color: var(--text-2) !important; }

/* Status widget */
[data-testid="stStatusWidget"],
[data-testid="stStatus"] {
  background: var(--bg-1) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  color: var(--text-2) !important;
}

/* Spinner */
[data-testid="stSpinner"] > div > div {
  border-top-color: var(--cyan) !important;
}

/* Dataframe */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--r-md) !important;
  overflow: hidden !important;
}

/* Caption */
.stCaption,
[data-testid="stCaptionContainer"] p {
  color: var(--text-3) !important;
  font-size: 0.72rem !important;
  font-family: 'Inter', sans-serif !important;
}


/* ════════════════════════════════
   KEYFRAME ANIMATIONS
════════════════════════════════ */
@keyframes pulse-dot {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.45; transform: scale(0.82); }
}
@keyframes fade-in-up {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes shimmer {
  0%   { background-position: -200% center; }
  100% { background-position:  200% center; }
}

.fade-in { animation: fade-in-up 0.4s ease forwards; }

/* Skeleton */
.skeleton {
  background: linear-gradient(
    90deg,
    var(--bg-1) 25%,
    rgba(34, 211, 238, 0.05) 50%,
    var(--bg-1) 75%
  ) !important;
  background-size: 200% !important;
  animation: shimmer 1.8s infinite !important;
  border-radius: var(--r-sm) !important;
}


/* ════════════════════════════════
   RESPONSIVE
════════════════════════════════ */
@media (max-width: 900px) {
  .main .block-container,
  [data-testid="stMainBlockContainer"] {
    padding-left:  1.2rem !important;
    padding-right: 1.2rem !important;
  }
  .top-nav { margin: 0 -1.2rem; padding: 0 1.2rem; }
  .top-nav-links { display: none; }
  .workspace-header h1 { font-size: 1.5rem; }
  .pip-connector { width: 10px; }
  .pip-step { padding: 6px 10px; font-size: 0.62rem; }
}

@media (max-width: 480px) {
  .main .block-container,
  [data-testid="stMainBlockContainer"] {
    padding-left:  0.8rem !important;
    padding-right: 0.8rem !important;
  }
  .top-nav { margin: 0 -0.8rem; padding: 0 0.8rem; }
  .workspace-header h1 { font-size: 1.25rem; }
  .upload-panel { padding: 1.1rem; }
  .metric-sci { padding: 0.9rem 1rem; }
  .m-value { font-size: 1.4rem; }
}
</style>
"""


# ════════════════════════════════════════════════════════════════
# INJECT THEME
# ════════════════════════════════════════════════════════════════

def inject_theme():
    """Inject the premium dark medical CSS theme with background image."""
    st.markdown(PREMIUM_THEME_CSS, unsafe_allow_html=True)

    # Inject background image as base64 so Streamlit doesn't need to serve it
    if _BG_PATH.exists():
        b64 = base64.b64encode(_BG_PATH.read_bytes()).decode()
        mime = "image/jpeg"
        # Inject a fixed-position HTML background element — immune to Streamlit CSS overrides
        st.markdown(
            f"""
            <div id="pg-bg-layer" style="
                position: fixed;
                inset: 0;
                z-index: -1;
                pointer-events: none;
                overflow: hidden;
                background: #06121C;
            ">
              <!-- Glow behind brain -->
              <div style="
                position: absolute;
                right: 5%; top: 10%;
                width: 50%; height: 80%;
                background: radial-gradient(circle, rgba(41,217,255,0.08) 0%, transparent 60%);
                filter: blur(40px);
              "></div>
              <!-- Brain background image -->
              <img
                src="data:{mime};base64,{b64}"
                style="
                  position: absolute;
                  right: -2%; top: -2%;
                  width: 68%;
                  height: 104%;
                  object-fit: cover;
                  object-position: center left;
                  opacity: 0.50;
                  filter: blur(6px);
                "
              />
              <!-- Left dark vignette -->
              <div style="
                position: absolute;
                inset: 0;
                background: linear-gradient(
                  105deg,
                  #06121C 0%,
                  #06121C 22%,
                  rgba(6,18,28,0.92) 36%,
                  rgba(6,18,28,0.55) 52%,
                  rgba(6,18,28,0.18) 70%,
                  rgba(6,18,28,0.04) 100%
                );
              "></div>
              <!-- Bottom fade -->
              <div style="
                position: absolute;
                bottom: 0; left: 0; right: 0;
                height: 200px;
                background: linear-gradient(to top, #06121C 0%, transparent 100%);
              "></div>
              <!-- Top fade -->
              <div style="
                position: absolute;
                top: 0; left: 0; right: 0;
                height: 70px;
                background: linear-gradient(to bottom, rgba(6,18,28,0.85) 0%, transparent 100%);
              "></div>
            </div>

            <style>
            /* Root background — fallback colour */
            html, body {{
                background: #06121C !important;
            }}
            /* Strip background from ALL Streamlit containers */
            html body .stApp,
            html body .stApp > div,
            html body section.main,
            html body [data-testid="stAppViewContainer"],
            html body [data-testid="stMainBlockContainer"],
            html body .block-container,
            html body div.block-container {{
                background: transparent !important;
                background-color: transparent !important;
                background-image: none !important;
            }}
            /* Nav bar sits above everything */
            .top-nav {{
                position: relative !important;
                z-index: 1001 !important;
                background: rgba(6, 18, 28, 0.90) !important;
                backdrop-filter: blur(16px) !important;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
            }}
            /* Glass panels over the background - enhanced to pop out */
            .upload-panel,
            .fusion-ctrl-panel,
            .export-wrap,
            .empty-state-panel {{
                background: rgba(6, 16, 26, 0.88) !important;
                backdrop-filter: blur(18px) !important;
                -webkit-backdrop-filter: blur(18px) !important;
                position: relative !important;
                z-index: 1 !important;
                border: 1px solid rgba(41, 217, 255, 0.15) !important;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.6) !important;
            }}
            .metric-sci {{
                background: rgba(6, 16, 26, 0.85) !important;
                backdrop-filter: blur(12px) !important;
                position: relative !important;
                z-index: 1 !important;
                border: 1px solid rgba(255, 255, 255, 0.08) !important;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4) !important;
            }}
            [data-testid="stExpander"] {{
                background: rgba(6, 16, 26, 0.85) !important;
                backdrop-filter: blur(12px) !important;
                border: 1px solid rgba(255, 255, 255, 0.05) !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )


# ════════════════════════════════════════════════════════════════
# TOP NAVIGATION
# ════════════════════════════════════════════════════════════════

def render_top_nav():
    """Render the premium top navigation bar."""
    st.markdown(
        """
        <div class="top-nav">
          <div class="top-nav-logo">
            <div class="logo-mark">🧠</div>
            <div>
              <div class="logo-name">PET–MRI Fusion</div>
              <div class="logo-sub">Research Workstation</div>
            </div>
          </div>
          <div class="top-nav-links">
            <a href="#workspace" class="active">Workspace</a>
            <a href="#visualization">Visualization</a>
            <a href="#analysis">Analysis</a>
            <a href="#documentation">Documentation</a>
          </div>
          <div class="top-nav-right">
            <div class="nav-status">
              <span class="dot"></span>
              System Ready
            </div>
            <div class="nav-icon-btn" title="User">○</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Real Streamlit button positioned over the gear slot
    st.markdown('<div id="settings-btn-wrap">', unsafe_allow_html=True)
    clicked = st.button("⚙", key="_settings_gear_btn", help="Settings")
    st.markdown('</div>', unsafe_allow_html=True)
    if clicked:
        st.session_state["_settings_open"] = not st.session_state.get("_settings_open", False)


# ════════════════════════════════════════════════════════════════
# SETTINGS PANEL
# ════════════════════════════════════════════════════════════════

@st.dialog("⚙  Workspace Settings", width="large")
def _settings_dialog():
    """Settings dialog content."""

    st.markdown('<div class="settings-section-label">Display</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        cmap = st.selectbox(
            "Default colormap (MRI)",
            ["gray", "bone", "gist_gray", "magma", "inferno"],
            index=["gray", "bone", "gist_gray", "magma", "inferno"].index(
                st.session_state.get("settings_mri_cmap", "gray")
            ),
            key="_set_mri_cmap",
        )
    with col2:
        pet_cmap = st.selectbox(
            "Default colormap (PET)",
            ["hot", "jet", "plasma", "viridis", "YlOrRd"],
            index=["hot", "jet", "plasma", "viridis", "YlOrRd"].index(
                st.session_state.get("settings_pet_cmap", "hot")
            ),
            key="_set_pet_cmap",
        )

    default_axis = st.radio(
        "Default view axis",
        ["Axial", "Coronal", "Sagittal"],
        index=["Axial", "Coronal", "Sagittal"].index(
            st.session_state.get("settings_axis", "Axial")
        ),
        horizontal=True,
        key="_set_axis",
    )

    st.markdown('<div class="settings-section-label">Processing</div>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        reg_method = st.selectbox(
            "Registration method",
            ["Rigid (Fast)", "Affine (Accurate)", "BSpline (Deformable)"],
            index=["Rigid (Fast)", "Affine (Accurate)", "BSpline (Deformable)"].index(
                st.session_state.get("settings_reg", "Rigid (Fast)")
            ),
            key="_set_reg",
        )
    with col4:
        norm_method = st.selectbox(
            "Normalisation",
            ["Min-Max", "Z-Score", "Percentile (1–99)"],
            index=["Min-Max", "Z-Score", "Percentile (1–99)"].index(
                st.session_state.get("settings_norm", "Min-Max")
            ),
            key="_set_norm",
        )

    st.markdown('<div class="settings-section-label">About</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div style="font-size:0.78rem;color:var(--text-3);line-height:1.7;">
        <b style="color:var(--text-2);">PET–MRI Fusion Workstation</b><br>
        Research &amp; educational multimodal brain imaging platform.<br>
        <b style="color:var(--cyan);">Not a diagnostic medical device.</b><br><br>
        Libraries: NiBabel · SimpleITK · scikit-image · Plotly
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.divider()
    c1, c2 = st.columns([3, 1])
    with c2:
        if st.button("Save", type="primary", key="_set_save"):
            st.session_state["settings_mri_cmap"] = cmap
            st.session_state["settings_pet_cmap"] = pet_cmap
            st.session_state["settings_axis"] = default_axis
            st.session_state["settings_reg"] = reg_method
            st.session_state["settings_norm"] = norm_method
            st.session_state["_settings_open"] = False
            st.rerun()
    with c1:
        if st.button("Close", key="_set_close"):
            st.session_state["_settings_open"] = False
            st.rerun()


def render_settings_panel():
    """Open the settings dialog if the gear was clicked."""
    if st.session_state.get("_settings_open", False):
        _settings_dialog()


# ════════════════════════════════════════════════════════════════
# WORKSPACE HEADER
# ════════════════════════════════════════════════════════════════

def render_workspace_header():
    """Render the compact workspace hero header."""
    st.markdown(
        """
        <div class="workspace-header fade-in">
          <div class="ws-badge">◈ Multimodal Imaging</div>
          <h1>Multimodal Brain Imaging</h1>
          <p class="ws-subtitle">
            PET + MRI image registration, fusion and visualization workspace
          </p>
          <div class="ws-status-row">
            <div class="ws-status">
              <span class="dot"></span>
              System Ready
            </div>
            <div class="ws-tech-tags">
              <span class="ws-tech-tag">NiBabel</span>
              <span class="ws-tech-tag">SimpleITK</span>
              <span class="ws-tech-tag">scikit-image</span>
              <span class="ws-tech-tag">NIfTI</span>
            </div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
# SECTION TITLE
# ════════════════════════════════════════════════════════════════

def section_title(num: str, label: str, section_id: str = None):
    """Render a numbered section title with right-extending rule."""
    id_attr = f' id="{section_id}"' if section_id else ""
    st.markdown(
        f"""
        <div class="section-title-wrap"{id_attr}>
          <span class="section-num">{num}</span>
          <span class="section-label">{label}</span>
          <div class="section-line"></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
# SECTION DIVIDER
# ════════════════════════════════════════════════════════════════

def section_divider():
    """Render a thin horizontal divider."""
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# PIPELINE DIAGRAM
# ════════════════════════════════════════════════════════════════

def render_pipeline(current_step: int = 0):
    """
    Render the visual processing pipeline.

    Steps: Upload(1) → Validation(2) → Normalization(3) → Registration(4)
           → Fusion(5) → Evaluation(6)

    current_step: 0=none, 1-6 = currently on that step.
    All steps < current_step are marked 'done'.
    """
    steps = ["Upload", "Validate", "Normalize", "Register", "Fuse", "Evaluate"]
    parts = ['<div class="pipeline-wrap">']

    for i, name in enumerate(steps):
        step_num = i + 1

        if step_num < current_step:
            cls, prefix = "pip-step done", "✓ "
        elif step_num == current_step:
            cls, prefix = "pip-step active", "⟳ "
        else:
            cls, prefix = "pip-step", ""

        parts.append(f'<div class="{cls}">{prefix}{name}</div>')

        if i < len(steps) - 1:
            connector_cls = "pip-connector done" if step_num < current_step else "pip-connector"
            parts.append(f'<div class="{connector_cls}"></div>')

    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# DISCLAIMER
# ════════════════════════════════════════════════════════════════

def render_disclaimer():
    """Render the research-only disclaimer bar."""
    st.markdown(
        """
        <div class="disclaimer-bar">
          ⚠ This application is intended for
          <strong>research and educational purposes only</strong>
          and is <strong>not a diagnostic medical device</strong>.
          Results must not be used for clinical decision-making.
        </div>
        <div class="app-footer">
          PET–MRI Fusion Suite · Python · NiBabel · SimpleITK · scikit-image · Streamlit
        </div>
        """,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
# METRIC CARD
# ════════════════════════════════════════════════════════════════

def metric_card(label: str, value: str, unit: str = "", description: str = ""):
    """Render a scientific metric card with optional bar."""
    desc_html = f'<div class="m-desc">{description}</div>' if description else ""
    unit_html  = f'<span class="m-unit">{unit}</span>' if unit else ""
    st.markdown(
        f"""
        <div class="metric-sci">
          <div class="m-label">{label}</div>
          <div class="m-value">{value}{unit_html}</div>
          {desc_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
# INFO CARD
# ════════════════════════════════════════════════════════════════

def info_card(label: str, value: str):
    """Render a small info label-value pair."""
    st.markdown(
        f"""
        <div class="info-item">
          <div class="info-label">{label}</div>
          <div class="info-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ════════════════════════════════════════════════════════════════
# EMPTY STATE
# ════════════════════════════════════════════════════════════════

def render_empty_state(
    icon: str = "🧠",
    title: str = "Upload Brain Images to Begin",
    description: str = (
        "Upload both a Brain MRI and Brain PET NIfTI file "
        "(.nii or .nii.gz) using the panels above."
    ),
):
    """Render a styled empty state panel."""
    st.markdown(
        f"""
        <div class="empty-state-panel fade-in">
          <div class="es-icon">{icon}</div>
          <div class="es-title">{title}</div>
          <div class="es-desc">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
