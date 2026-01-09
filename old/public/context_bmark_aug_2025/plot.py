
import json
import plotly.graph_objects as go
import plotly.colors as pcolors

# Load the data from the JSON file
with open('data.json', 'r') as f:
    data = json.load(f)

# --- Flagship Model Definition ---
FLAGSHIP_MODELS = [
    'claude-opus-4:thinking',
    'deepseek-r1-0528:free',
    'gemini-2.5-pro-preview-06-05',
    'gpt-5', 'o3',
    'qwen3-235b-a22b-thinking-2507 [chutes]',
    'grok-4'
]

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

def is_open_model(model_name):
    model_lower = model_name.lower()
    open_model_identifiers = ['llama', 'qwen', 'qwq', 'deepseek', 'gemma', 'glm', 'minimax']
    return any(identifier in model_lower for identifier in open_model_identifiers)

# Create a figure
fig = go.Figure()

models_by_vendor = {}
for model_name, model_data in data.items():
    vendor, color = get_vendor_and_color(model_name)
    if vendor not in models_by_vendor: models_by_vendor[vendor] = []
    models_by_vendor[vendor].append({'name': model_name, 'data': model_data, 'color': color})

all_model_names_sorted = []
for vendor, models in sorted(models_by_vendor.items()):
    sorted_models = sorted(models, key=lambda x: x['name'])
    for i, model in enumerate(sorted_models):
        all_model_names_sorted.append(model['name'])
        model_name, model_data = model['name'], model['data']
        x_values, y_values = [], []
        for k, v in model_data.items():
            if v is not None:
                x_values.append(int(k.replace('k', '000')) if 'k' in k else int(k))
                y_values.append(v)
        if not x_values: continue
        sorted_points = sorted(zip(x_values, y_values))
        x_sorted, y_sorted = zip(*sorted_points)
        opacity = max(0.4, 1.0 - (i * 0.2))
        line_style = 'dash' if is_open_model(model_name) else 'solid'
        marker_symbol = 'diamond' if is_open_model(model_name) else 'circle'
        is_visible = True if model_name in FLAGSHIP_MODELS else 'legendonly'
        fig.add_trace(go.Scatter(
            x=x_sorted, y=y_sorted, name=model_name, mode='lines+markers',
            visible=is_visible, legendgroup=vendor, legendgrouptitle_text=vendor,
            line=dict(color=model['color'], dash=line_style),
            marker=dict(color=model['color'], opacity=opacity, symbol=marker_symbol),
            hovertemplate=(f'<b>{model_name}</b> ({vendor})<br>' + ('<i>Open Model</i><br>' if is_open_model(model_name) else '') + 'Context: %{x} tokens<br>' + 'Score: %{y:.2f}%' + '<extra></extra>')
        ))

updatemenus = [
    {'buttons': [{'label': "Flagship Models", 'method': "restyle", 'args': [{"visible": [m in FLAGSHIP_MODELS for m in all_model_names_sorted]}]},
                 {'label': "All Models", 'method': "restyle", 'args': [{"visible": [True] * len(all_model_names_sorted)}]}] + 
                [{'label': name, 'method': "restyle", 'args': [{"visible": [m == name for m in all_model_names_sorted]}]} for name in all_model_names_sorted],
     'direction': "down", 'pad': {"r": 10, "t": 10}, 'showactive': True, 'x': 0.05, 'xanchor': "left", 'y': 1.15, 'yanchor': "top"},
    {'buttons': [{'label': "Linear Y-Axis", 'method': "relayout", 'args': [{'yaxis.type': 'linear'}]},
                 {'label': "Log Y-Axis", 'method': "relayout", 'args': [{'yaxis.type': 'log'}]}],
     'type': "buttons", 'direction': "right", 'pad': {"r": 10, "t": 10}, 'showactive': True, 'x': 0.3, 'xanchor': "left", 'y': 1.15, 'yanchor': "top"}
]

fig.update_layout(
    title={'text': "Fiction.liveBench LLM Performance (July 25, 2025) - Flagship Models", 'y':0.9, 'x':0.5, 'xanchor': 'center', 'yanchor': 'top'},
    xaxis_title="Context Length (tokens)", yaxis_title="Accuracy Score (%)",
    legend_title="Vendors", template="plotly_dark", xaxis_type="log",
    xaxis_rangeslider_visible=True, updatemenus=updatemenus, hovermode='x unified',
    legend=dict(groupclick='toggleitem'),
    annotations=[dict(text="Style Key: Dashed Line / Diamond = Open Model", align='left', showarrow=False, xref='paper', yref='paper', x=1.0, y=1.15, bordercolor='gray', borderwidth=1)]
)

fig.write_html("plot.html")
print("Plotly HTML file 'plot.html' with updated brand colors created successfully.")
