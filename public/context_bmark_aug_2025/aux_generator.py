import json
import plotly.graph_objects as go
import plotly.colors as pcolors
import numpy as np

# Load the data from the JSON file
with open('data.json', 'r') as f:
    data = json.load(f)

# --- Mappings with Official Brand Colors (Updated) ---
VENDOR_PALETTE = {
    "OpenAI": "#FFFFFF",    # White
    "Google": "#DB4437",    # Google Red
    "Anthropic": "#d4a37f", # Earthy Tone
    "Meta": "#0082fb",      # Meta Blue
    "xAI": "#8A2BE2",      # Blue Violet
    "DeepSeek": "#4F6BFD",  # Dodger Blue
    "Qwen": "#FF6701",      # Alibaba Orange
    "Minimax": "#E21680",   # Pink
    "GLM": "#3498DB",      # Generic Blue
    "Other": "#95A5A6",     # Gray
}

def get_vendor_and_color(model_name):
    model_lower = model_name.lower()
    if 'gpt' in model_lower or 'chatgpt' in model_lower or model_lower.startswith('o3') or model_lower.startswith('o4'):
        return "OpenAI", VENDOR_PALETTE["OpenAI"]
    if 'gemini' in model_lower or 'gemma' in model_lower: return "Google", VENDOR_PALETTE["Google"]
    if 'claude' in model_lower: return "Anthropic", VENDOR_PALETTE["Anthropic"]
    if 'llama' in model_lower: return "Meta", VENDOR_PALETTE["Meta"]
    if 'grok' in model_lower: return "xAI", VENDOR_PALETTE["xAI"]
    if 'deepseek' in model_lower: return "DeepSeek", VENDOR_PALETTE["DeepSeek"]
    if 'qwen' in model_lower or 'qwq' in model_lower: return "Qwen", VENDOR_PALETTE["Qwen"]
    if 'minimax' in model_lower: return "Minimax", VENDOR_PALETTE["Minimax"]
    if 'glm' in model_lower: return "GLM", VENDOR_PALETTE["GLM"]
    return "Other", VENDOR_PALETTE["Other"]

# --- 1. Area Under the Curve (AUC) Calculation ---
def calculate_auc(x, y):
    if len(x) < 2: return 0
    log_x = np.log10(np.array(x) + 1)
    return np.trapz(y, log_x)

model_metrics = {}
for model_name, model_data in data.items():
    vendor, color = get_vendor_and_color(model_name)
    x_values, y_values = [], []
    for k, v in model_data.items():
        if v is not None:
            x_values.append(int(k.replace('k', '000')) if 'k' in k else int(k))
            y_values.append(v)
    
    if not x_values: continue
    sorted_points = sorted(zip(x_values, y_values))
    x_sorted, y_sorted = zip(*sorted_points)
    
    auc = calculate_auc(x_sorted, y_sorted)
    peak_score = max(y_sorted) if y_sorted else 0
    long_context_score = y_sorted[-1] if y_sorted else 0
    stability = (long_context_score / peak_score) * 100 if peak_score > 0 else 0
    
    model_metrics[model_name] = {'auc': auc, 'stability': stability, 'vendor': vendor, 'color': color}

# --- 2. Tier Ranking ---
max_auc = max(m['auc'] for m in model_metrics.values())
for name, metrics in model_metrics.items():
    norm_auc = (metrics['auc'] / max_auc) * 100
    composite_score = (0.7 * norm_auc) + (0.3 * metrics['stability'])
    metrics['composite_score'] = composite_score
    if composite_score >= 90: metrics['tier'] = 'S'
    elif composite_score >= 80: metrics['tier'] = 'A'
    elif composite_score >= 70: metrics['tier'] = 'B'
    else: metrics['tier'] = 'C'

# --- 3. Create Visualizations ---
sorted_by_auc = sorted(model_metrics.items(), key=lambda item: item[1]['auc'], reverse=True)
sorted_by_stability = sorted(model_metrics.items(), key=lambda item: item[1]['stability'], reverse=True)
sorted_by_tier = sorted(model_metrics.items(), key=lambda item: item[1]['composite_score'], reverse=True)

fig_auc = go.Figure(go.Bar(x=[m[0] for m in sorted_by_auc], y=[m[1]['auc'] for m in sorted_by_auc], marker_color=[m[1]['color'] for m in sorted_by_auc]))
fig_auc.update_layout(title='Model Performance: Area Under Curve (AUC)', template='plotly_dark')

fig_stability = go.Figure(go.Bar(x=[m[0] for m in sorted_by_stability], y=[m[1]['stability'] for m in sorted_by_stability], marker_color=[m[1]['color'] for m in sorted_by_stability]))
fig_stability.update_layout(title='Long-Context Stability', template='plotly_dark')

fig_table = go.Figure(go.Table(
    header=dict(values=['Rank', 'Model', 'Vendor', 'Tier', 'Composite Score'], fill_color='#2c3e50', font=dict(color='white')),
    cells=dict(
        values=[list(range(1, len(sorted_by_tier) + 1)), [m[0] for m in sorted_by_tier], [m[1]['vendor'] for m in sorted_by_tier], [m[1]['tier'] for m in sorted_by_tier], [f"{m[1]['composite_score']:.2f}" for m in sorted_by_tier]],
        fill_color='darkslategray',
        font=dict(color=['white', [m[1]['color'] for m in sorted_by_tier], 'white', 'white', 'white']),
        align='left'
    )
))
fig_table.update_layout(title='Overall Model Performance Tiers', template='plotly_dark')

with open("aux.html", 'w') as f:
    f.write("""
    <html><head><title>Auxiliary Model Evaluations</title>
    <style>body { font-family: sans-serif; background-color: #111; color: #eee; } h1, h2, p { text-align: center; }</style></head>
    <body>
        <h1>Auxiliary Model Evaluations</h1>
        <div><h2>Overall Performance Tiers</h2><p>Models ranked by a composite score (70% AUC, 30% Stability).</p>
    """)
    f.write(fig_table.to_html(full_html=False, include_plotlyjs='cdn'))
    f.write("""</div><div><h2>Area Under Curve (AUC) Analysis</h2><p>Total performance across all context lengths.</p>""")
    f.write(fig_auc.to_html(full_html=False, include_plotlyjs=False))
    f.write("""</div><div><h2>Long-Context Stability Analysis</h2><p>How well a model maintains performance at max context vs. its peak.</p>""")
    f.write(fig_stability.to_html(full_html=False, include_plotlyjs=False))
    f.write("""</div></body></html>""")

print("Auxiliary evaluations HTML file 'aux.html' with updated brand colors created successfully.")