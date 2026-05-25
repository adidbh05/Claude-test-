import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import base64, os

# ── Data ────────────────────────────────────────────────────────────────────
categories = ['Predictive\nAccuracy', 'Explanation\nVerifiability', 'Explanation\nAccessibility']
N = len(categories)

models = {
    'Linear Regression':            {'scores': [0.65, 1.00, 0.30], 'color': '#4A90D9', 'mae': '£290,965'},
    'Gradient Boosting + SHAP':     {'scores': [1.00, 0.60, 0.50], 'color': '#27AE60', 'mae': '£228,774'},
    'LLM — Gemini 2.5 Flash':       {'scores': [0.45, 0.00, 1.00], 'color': '#E74C3C', 'mae': '£349,162'},
}

# Angles: evenly spaced, starting at top (90°)
angles = np.linspace(np.pi / 2, np.pi / 2 + 2 * np.pi, N, endpoint=False).tolist()
angles_closed = angles + [angles[0]]  # close polygon

grid_levels = [0.2, 0.4, 0.6, 0.8, 1.0]


def build_chart(dark: bool) -> plt.Figure:
    bg     = '#1a1a2e'  if dark else '#ffffff'
    fg     = '#ffffff'  if dark else '#111111'
    subfg  = '#aaaacc'  if dark else '#555566'
    gridc  = '#444466'  if dark else '#ccccdd'
    ringc  = '#888899'  if dark else '#999aaa'
    legbg  = '#222244'  if dark else '#f0f0f8'
    fnotec = '#888899'  if dark else '#666677'

    fig = plt.figure(figsize=(10, 10), facecolor=bg)
    ax  = fig.add_subplot(111, polar=True, facecolor=bg)

    # ── Grid rings ────────────────────────────────────────────────────────
    ax.set_ylim(0, 1.0)
    ax.set_yticks(grid_levels)
    ax.set_yticklabels(
        [str(v) for v in grid_levels],
        color=ringc, fontsize=9, va='center'
    )
    ax.yaxis.set_tick_params(pad=28)

    ax.set_xticks(angles)
    ax.set_xticklabels([])  # we draw custom labels below

    ax.spines['polar'].set_visible(False)
    ax.grid(color=gridc, linewidth=0.8, linestyle='--', alpha=0.6)

    # Redraw circular grid rings with our colour
    for level in grid_levels:
        ring_angles = np.linspace(0, 2 * np.pi, 360)
        ax.plot(ring_angles, [level] * 360, color=gridc, lw=0.7, alpha=0.5)

    # Radial axis lines (spokes)
    for ang in angles:
        ax.plot([ang, ang], [0, 1.0], color=gridc, lw=0.9, alpha=0.5)

    # ── Draw each model ───────────────────────────────────────────────────
    for name, info in models.items():
        scores_closed = info['scores'] + [info['scores'][0]]
        c = info['color']

        ax.fill(angles_closed, scores_closed, color=c, alpha=0.25)
        ax.plot(angles_closed, scores_closed, color=c, lw=2.2, solid_capstyle='round')

        for ang, score in zip(angles, info['scores']):
            ax.plot(ang, score, 'o', color=c, markersize=8, zorder=5)

    # ── Axis labels (offset 15 % beyond 1.0) ─────────────────────────────
    label_r = 1.20
    label_texts = ['Predictive\nAccuracy', 'Explanation\nVerifiability', 'Explanation\nAccessibility']
    ha_map = {0: 'center', 1: 'right', 2: 'left'}

    for i, (ang, label) in enumerate(zip(angles, label_texts)):
        x = label_r * np.cos(ang)
        y = label_r * np.sin(ang)
        ha = ha_map.get(i, 'center')
        ax.text(
            ang, label_r, label,
            ha=ha, va='center',
            color=fg, fontsize=14, fontweight='bold',
            transform=ax.transData
        )

    # ── Title & subtitle ──────────────────────────────────────────────────
    fig.text(
        0.5, 0.96,
        'Three-Paradigm Comparison: Accuracy — Verifiability — Accessibility',
        ha='center', va='top',
        color=fg, fontsize=16, fontweight='bold'
    )
    fig.text(
        0.5, 0.925,
        'No single model dominates across all three dimensions',
        ha='center', va='top',
        color=subfg, fontsize=12
    )

    # ── Legend ────────────────────────────────────────────────────────────
    legend_elements = [
        mpatches.Patch(
            facecolor=info['color'], edgecolor=info['color'],
            alpha=0.8,
            label=f'{name}  (MAE: {info["mae"]})'
        )
        for name, info in models.items()
    ]
    leg = ax.legend(
        handles=legend_elements,
        loc='lower center',
        bbox_to_anchor=(0.5, -0.28),
        frameon=True,
        framealpha=0.7,
        facecolor=legbg,
        edgecolor='none',
        fontsize=11,
        labelcolor=fg,
        handlelength=1.6,
        handleheight=1.2,
        borderpad=0.9,
        labelspacing=0.6
    )

    # ── Footnote ──────────────────────────────────────────────────────────
    fig.text(
        0.5, 0.022,
        'Scores normalised: Accuracy to GB MAE; Verifiability and Accessibility to Table 4 ratings (Bhuiyan, 2026)',
        ha='center', va='bottom',
        color=fnotec, fontsize=8.5, style='italic'
    )

    # ── Score justification text box ─────────────────────────────────────
    justification = (
        'Accuracy normalised to GB MAE (£228,774 = 1.0).\n'
        'Verifiability from Table 4 faithfulness ratings.\n'
        'Accessibility from Table 4 readability ratings.'
    )
    tb_fc = '#222244' if dark else '#f0f0f8'
    tb_ec = '#444466' if dark else '#ccccdd'
    fig.text(
        0.015, 0.5, justification,
        ha='left', va='center',
        color=subfg, fontsize=8,
        rotation=90,
        bbox=dict(boxstyle='round,pad=0.5', facecolor=tb_fc, edgecolor=tb_ec, alpha=0.75)
    )

    plt.tight_layout(rect=[0.05, 0.08, 0.95, 0.92])
    return fig


# ── Render both versions ─────────────────────────────────────────────────────
out_dir = '/home/user/Claude-test-'

fig_dark = build_chart(dark=True)
dark_path = os.path.join(out_dir, 'radar_chart_three_models.png')
fig_dark.savefig(dark_path, dpi=300, bbox_inches='tight', facecolor=fig_dark.get_facecolor())
plt.close(fig_dark)
print(f'✓ Dark version saved → {dark_path}')

fig_light = build_chart(dark=False)
light_path = os.path.join(out_dir, 'radar_chart_three_models_white.png')
fig_light.savefig(light_path, dpi=300, bbox_inches='tight', facecolor=fig_light.get_facecolor())
plt.close(fig_light)
print(f'✓ White version saved → {light_path}')

# ── Encode images to base64 for HTML ─────────────────────────────────────────
def b64(path):
    with open(path, 'rb') as f:
        return base64.b64encode(f.read()).decode()

dark_b64  = b64(dark_path)
light_b64 = b64(light_path)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Three-Paradigm Comparison — House Price Prediction Transparency</title>
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    body {{
      background: #0f0f1a;
      color: #e0e0f0;
      font-family: 'Segoe UI', system-ui, sans-serif;
      min-height: 100vh;
    }}

    header {{
      background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
      padding: 2.5rem 2rem 2rem;
      text-align: center;
      border-bottom: 1px solid #333366;
    }}
    header h1 {{
      font-size: 1.6rem;
      font-weight: 700;
      color: #ffffff;
      letter-spacing: 0.02em;
      margin-bottom: 0.4rem;
    }}
    header p {{
      color: #aaaacc;
      font-size: 0.95rem;
    }}

    .tab-bar {{
      display: flex;
      justify-content: center;
      gap: 0.5rem;
      padding: 1.2rem 1rem;
      background: #131325;
      border-bottom: 1px solid #2a2a4a;
    }}
    .tab-btn {{
      background: #1e1e3a;
      color: #aaaacc;
      border: 1px solid #333366;
      border-radius: 8px;
      padding: 0.55rem 1.4rem;
      font-size: 0.9rem;
      cursor: pointer;
      transition: background 0.2s, color 0.2s, border-color 0.2s;
    }}
    .tab-btn:hover  {{ background: #2a2a4a; color: #e0e0ff; }}
    .tab-btn.active {{
      background: #3a3a6e;
      color: #ffffff;
      border-color: #6666cc;
      font-weight: 600;
    }}

    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}

    .chart-wrap {{
      max-width: 900px;
      margin: 2.5rem auto;
      padding: 0 1.5rem;
      text-align: center;
    }}
    .chart-wrap img {{
      width: 100%;
      height: auto;
      border-radius: 12px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.6);
    }}

    /* white tab — invert page bg */
    #tab-white {{ background: #f4f4fc; }}
    #tab-white .chart-wrap img {{
      box-shadow: 0 8px 40px rgba(0,0,0,0.18);
    }}

    .caption {{
      margin-top: 1rem;
      font-size: 0.82rem;
      color: #888899;
      font-style: italic;
    }}
    #tab-white .caption {{ color: #666677; }}

    .scores-table {{
      max-width: 680px;
      margin: 0 auto 2rem;
      border-collapse: collapse;
      font-size: 0.88rem;
      color: #ccccee;
    }}
    #tab-white .scores-table {{ color: #222244; }}
    .scores-table th, .scores-table td {{
      border: 1px solid #333355;
      padding: 0.55rem 1rem;
      text-align: center;
    }}
    #tab-white .scores-table th,
    #tab-white .scores-table td {{ border-color: #cccce0; }}
    .scores-table th {{
      background: #1e1e3a;
      color: #ffffff;
      font-weight: 600;
    }}
    #tab-white .scores-table th {{ background: #3a3a6e; }}
    .scores-table tr:nth-child(even) td {{ background: #1a1a30; }}
    #tab-white .scores-table tr:nth-child(even) td {{ background: #eeeef8; }}

    .section-title {{
      text-align: center;
      font-size: 1rem;
      font-weight: 600;
      color: #9999cc;
      margin: 0 auto 1rem;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }}
    #tab-white .section-title {{ color: #555577; }}

    footer {{
      text-align: center;
      padding: 1.5rem;
      font-size: 0.78rem;
      color: #555566;
      border-top: 1px solid #1e1e36;
    }}
    #tab-white footer {{ color: #9999aa; border-color: #ccccdd; }}

    .dl-btn {{
      display: inline-block;
      margin-top: 1rem;
      padding: 0.5rem 1.2rem;
      background: #3a3a6e;
      color: #e0e0ff;
      text-decoration: none;
      border-radius: 6px;
      font-size: 0.85rem;
      border: 1px solid #6666cc;
      transition: background 0.2s;
    }}
    .dl-btn:hover {{ background: #4a4a8e; }}
    #tab-white .dl-btn {{
      background: #e8e8f8;
      color: #333366;
      border-color: #9999cc;
    }}
    #tab-white .dl-btn:hover {{ background: #d8d8ee; }}
  </style>
</head>
<body>

<header>
  <h1>Three-Paradigm Comparison: Accuracy — Verifiability — Accessibility</h1>
  <p>House Price Prediction Transparency · Dissertation Results · Bhuiyan (2026)</p>
</header>

<div class="tab-bar">
  <button class="tab-btn active" onclick="switchTab('dark',this)">Dark (Presentation)</button>
  <button class="tab-btn"        onclick="switchTab('white',this)">White (Print)</button>
  <button class="tab-btn"        onclick="switchTab('data',this)">Score Data</button>
</div>

<!-- ═══ DARK TAB ═══════════════════════════════════════════════════════════ -->
<div id="tab-dark" class="tab-panel active">
  <div class="chart-wrap">
    <img src="data:image/png;base64,{dark_b64}" alt="Radar chart — dark theme"/>
    <p class="caption">
      Scores normalised: Accuracy to GB MAE (£228,774 = 1.0); Verifiability and Accessibility
      to Table&nbsp;4 ratings (Bhuiyan, 2026).
    </p>
    <a class="dl-btn" download="radar_chart_three_models.png"
       href="data:image/png;base64,{dark_b64}">⬇ Download PNG (300 DPI)</a>
  </div>
  <footer>Generated with Python · matplotlib 3.x · 300 DPI · Bhuiyan Dissertation 2026</footer>
</div>

<!-- ═══ WHITE TAB ══════════════════════════════════════════════════════════ -->
<div id="tab-white" class="tab-panel">
  <div class="chart-wrap">
    <img src="data:image/png;base64,{light_b64}" alt="Radar chart — white/print theme"/>
    <p class="caption">
      Print-ready version. Same data as the dark theme above.
    </p>
    <a class="dl-btn" download="radar_chart_three_models_white.png"
       href="data:image/png;base64,{light_b64}">⬇ Download PNG (300 DPI)</a>
  </div>
  <footer>Generated with Python · matplotlib 3.x · 300 DPI · Bhuiyan Dissertation 2026</footer>
</div>

<!-- ═══ DATA TAB ═══════════════════════════════════════════════════════════ -->
<div id="tab-data" class="tab-panel">
  <div class="chart-wrap" style="padding-top:2rem;">
    <p class="section-title">Normalised Score Matrix</p>
    <table class="scores-table">
      <thead>
        <tr>
          <th>Model</th>
          <th>Predictive Accuracy</th>
          <th>Explanation Verifiability</th>
          <th>Explanation Accessibility</th>
          <th>MAE (£)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Linear Regression</td>
          <td>0.65</td><td>1.00</td><td>0.30</td>
          <td>290,965</td>
        </tr>
        <tr>
          <td>Gradient Boosting + SHAP</td>
          <td>1.00</td><td>0.60</td><td>0.50</td>
          <td>228,774</td>
        </tr>
        <tr>
          <td>LLM — Gemini 2.5 Flash</td>
          <td>0.45</td><td>0.00</td><td>1.00</td>
          <td>349,162</td>
        </tr>
      </tbody>
    </table>
    <p class="caption" style="margin-top:0.6rem;">
      Accuracy normalised to GB MAE (£228,774 = 1.0). Verifiability from Table&nbsp;4
      faithfulness ratings. Accessibility from Table&nbsp;4 readability ratings.
    </p>
  </div>
  <footer>Bhuiyan (2026) · Dissertation on House Price Prediction Transparency</footer>
</div>

<script>
  function switchTab(id, btn) {{
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.getElementById('tab-' + id).classList.add('active');
    btn.classList.add('active');
    // apply body bg for white tab
    document.body.style.background = id === 'white' ? '#f4f4fc' : '#0f0f1a';
  }}
</script>
</body>
</html>"""

html_path = os.path.join(out_dir, 'radar_chart_viewer.html')
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f'✓ HTML viewer saved  → {html_path}')
print('\nAll three files written successfully.')
