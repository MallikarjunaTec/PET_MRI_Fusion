"""
metrics.py — Scientific metric cards and comparison chart components.

Professional medical imaging metric display with dark Plotly charts.
"""

import streamlit as st
import numpy as np
import plotly.graph_objects as go


# ════════════════════════════════════════════════════════════════
# RENDER METRIC CARDS — Scientific Style
# ════════════════════════════════════════════════════════════════

def render_metric_cards(metrics: dict, descriptions: dict = None):
    """
    Render a row of scientific-style metric cards.

    Parameters:
        metrics:      dict mapping metric_name -> value (float)
        descriptions: optional dict mapping metric_name -> tooltip text
    """
    labels_map = {
        "entropy":           ("Entropy",           "bits",  0.85),
        "mri_ssim":          ("MRI SSIM",          "",      1.0),
        "pet_ssim":          ("PET SSIM",          "",      1.0),
        "std":               ("Std Deviation",     "",      0.5),
        "spatial_frequency": ("Spatial Frequency", "",      0.5),
    }

    keys = list(metrics.keys())
    cols = st.columns(len(keys), gap="small")

    for i, key in enumerate(keys):
        label, unit, norm_max = labels_map.get(key, (key.replace("_", " ").title(), "", 1.0))
        value = metrics[key]
        desc  = descriptions.get(key, "") if descriptions else ""

        # Normalise to [0, 1] for bar
        bar_pct = min(float(value) / norm_max * 100, 100) if norm_max > 0 else 50

        desc_html = f'<div class="m-desc">{desc}</div>' if desc else ""
        unit_html = f'<span class="m-unit"> {unit}</span>' if unit else ""

        with cols[i]:
            st.markdown(
                f"""
                <div class="metric-sci fade-in">
                  <div class="m-label">{label}</div>
                  <div class="m-value">{value:.4f}{unit_html}</div>
                  {desc_html}
                  <div class="m-bar-bg">
                    <div class="m-bar-fill" style="width:{bar_pct:.1f}%;"></div>
                  </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ════════════════════════════════════════════════════════════════
# COMPARISON CHARTS — Dark Plotly Theme
# ════════════════════════════════════════════════════════════════

_DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94a3b8", size=11),
    margin=dict(t=52, b=36, l=50, r=20),
    bargap=0.38,
    xaxis=dict(
        tickfont=dict(size=10, color="#4a657a"),
        gridcolor="rgba(255,255,255,0.04)",
        zeroline=False,
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.05)",
        zeroline=False,
        tickfont=dict(size=10, color="#4a657a"),
    ),
)


def render_comparison_charts(
    comparison_results: list,
    selected_method: str = None,
):
    """
    Render dark bar charts comparing all fusion methods.

    Parameters:
        comparison_results: list of dicts with keys:
            Method, entropy, mri_ssim, pet_ssim, std, spatial_frequency
        selected_method: currently selected method to highlight
    """
    if not comparison_results:
        st.info("No comparison data available.")
        return

    methods = [r["Method"] for r in comparison_results]

    # Color scheme: highlight selected, dim others
    def bar_colors(highlight_idx=None):
        base   = "rgba(34, 211, 238, 0.4)"
        hi     = "#22d3ee"
        return [hi if (selected_method and m == selected_method) else base for m in methods]

    chart_configs = [
        ("Entropy",           "entropy",           "Information content — higher values indicate richer fusion"),
        ("MRI SSIM",          "mri_ssim",          "Structural similarity with MRI — closer to 1.0 is better"),
        ("PET SSIM",          "pet_ssim",          "Structural similarity with PET — closer to 1.0 is better"),
        ("Spatial Frequency", "spatial_frequency", "Edge detail preservation — higher indicates more structural detail"),
    ]

    col1, col2 = st.columns(2, gap="medium")
    cols = [col1, col2, col1, col2]

    for i, (title, key, subtitle) in enumerate(chart_configs):
        values = [r.get(key, 0) for r in comparison_results]
        colors = bar_colors()

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=methods,
            y=values,
            marker=dict(
                color=colors,
                line=dict(width=0)
            ),
            text=[f"{v:.4f}" for v in values],
            textposition="outside",
            textfont=dict(size=10, family="Inter", color="#94a3b8"),
        ))

        layout = dict(**_DARK_LAYOUT)
        layout["title"] = dict(
            text=f"<b style='color:#e2e8f0'>{title}</b><br>"
                 f"<span style='font-size:10px;color:#4a657a'>{subtitle}</span>",
            font=dict(size=13, family="Inter"),
            x=0,
            y=0.98,
        )
        layout["yaxis"]["title"] = dict(text=title, font=dict(size=10, color="#4a657a"))
        layout["height"] = 300

        fig.update_layout(**layout)

        with cols[i]:
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{key}")


# ════════════════════════════════════════════════════════════════
# COMPARISON TABLE
# ════════════════════════════════════════════════════════════════

def render_comparison_table(comparison_results: list):
    """Render a styled comparison results table."""
    if not comparison_results:
        return

    import pandas as pd

    df = pd.DataFrame(comparison_results)
    df = df.rename(columns={
        "Method":            "Fusion Method",
        "entropy":           "Entropy",
        "mri_ssim":         "MRI SSIM",
        "pet_ssim":         "PET SSIM",
        "std":              "Std Dev",
        "spatial_frequency": "Spatial Freq",
    })

    for col in ["Entropy", "MRI SSIM", "PET SSIM", "Std Dev", "Spatial Freq"]:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f"{x:.4f}")

    st.dataframe(df, use_container_width=True, hide_index=True)
