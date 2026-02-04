import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

def clean_currency(x):
    if isinstance(x, str):
        return float(x.replace(',', ''))
    return x

def generate_visualization():
    # Load data
    df = pd.read_csv('data.csv')

    # Clean numeric columns
    numeric_cols = ['Prefill (tps)', 'Decode (tps)', 'time to process 100k and generate 2k']
    for col in numeric_cols:
        df[col] = df[col].apply(clean_currency)

    # Create a combined Model column for easier filtering
    df['Full Model Name'] = df['Model Name'] + ' ' + df['Model Size']

    # Get unique models
    models = df['Full Model Name'].unique()

    # Create figure
    fig = go.Figure()

    # Define a color map for devices to keep colors consistent
    devices = df['Device'].unique()
    colors = px.colors.qualitative.Plotly
    device_colors = {device: colors[i % len(colors)] for i, device in enumerate(devices)}

    # Determine global min and max batch size to set extent of horizontal lines
    min_batch = df['Batch Size'].min() * 0.8
    max_batch = df['Batch Size'].max() * 1.2

    # Add traces for each model (initially only show the first one)
    first_model = models[0]
    
    # We will keep track of how many traces belong to each model to build the buttons later
    model_trace_counts = {}

    for model in models:
        model_df = df[df['Full Model Name'] == model]
        # Sort by Batch Size for proper line plotting
        model_df = model_df.sort_values(by='Batch Size')
        
        traces_added_this_model = 0
        
        for device in model_df['Device'].unique():
            device_data = model_df[model_df['Device'] == device]
            
            visible = (model == first_model)
            color = device_colors[device]
            
            # 1. Main Data Trace (Lines + Markers)
            trace_data = go.Scatter(
                x=device_data['Batch Size'],
                y=device_data['time to process 100k and generate 2k'],
                mode='lines+markers',
                name=device,
                legendgroup=device,
                visible=visible,
                line=dict(color=color),
                customdata=device_data[['Prefill (tps)', 'Decode (tps)', 'Quantization', 'Engine']],
                hovertemplate="<br>".join([
                    "Device: %{x}",
                    "Batch Size: %{x}",
                    "Time: %{y:.2f}",
                    "Prefill: %{customdata[0]:.2f}",
                    "Decode: %{customdata[1]:.2f}",
                    "Quant: %{customdata[2]}",
                    "Engine: %{customdata[3]}"
                ])
            )
            fig.add_trace(trace_data)
            traces_added_this_model += 1
            
            # 2. Horizontal Reference Line (Best Time)
            best_time = device_data['time to process 100k and generate 2k'].min()
            
            trace_ref = go.Scatter(
                x=[min_batch, max_batch], 
                y=[best_time, best_time],
                mode='lines',
                name=f"{device} (Best)",
                legendgroup=device,
                visible=visible,
                line=dict(color=color, dash='dash', width=1),
                showlegend=True,
                hovertemplate=f"{device} (Best): {best_time:.2f}<extra></extra>"
            )
            fig.add_trace(trace_ref)
            traces_added_this_model += 1
            
        model_trace_counts[model] = traces_added_this_model

    # Create dropdown buttons
    buttons = []
    
    # We iterate through models again to build the visibility mask for each button
    # The traces are stored sequentially in fig.data
    
    current_trace_index = 0
    total_traces = len(fig.data)
    
    for model in models:
        count = model_trace_counts[model]
        
        # Create a visibility list where only the traces for this model are True
        visibility = [False] * total_traces
        
        for i in range(count):
            visibility[current_trace_index + i] = True
            
        buttons.append(dict(
            label=model,
            method="update",
            args=[{"visible": visibility},
                  {"title": f"Performance Comparison: {model} - Time to process 100k tokens and generate 2k tokens"}]
        ))
        
        current_trace_index += count

    # Update layout with menus
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=buttons,
                direction="down",
                pad={"r": 10, "t": 10},
                showactive=True,
                x=0.0, # Left aligned
                xanchor="left",
                y=1.15,
                yanchor="top"
            ),
        ],
        title=f"Performance Comparison: {first_model} - Time to process 100k tokens and generate 2k tokens",
        xaxis_title="Batch Size",
        yaxis_title="Time (s) - Lower is Better",
        xaxis=dict(
            type='log',
            dtick=0.30102999566,
            range=[np.log10(min_batch), np.log10(max_batch)] # Fix range so lines span across
        ),
        yaxis=dict(type='log'), 
        hovermode="x unified",
        template="plotly_white",
        margin=dict(b=150) # Increased bottom margin for footer
    )

    # Add source annotation
    source_text = 'Source: <a href="https://lmsys.org/blog/2025-10-13-nvidia-dgx-spark/">NVIDIA DGX Spark Blog</a> and <a href="https://docs.google.com/spreadsheets/d/1SF1u0J2vJ-ou-R_Ry1JZQ0iscOZL8UKHpdVFr85tNLU/edit?gid=0#gid=0">Data Spreadsheet</a>'
    
    fig.add_annotation(
        text=source_text,
        xref="paper", yref="paper",
        x=0.5, y=-0.25, # Moved further down
        showarrow=False,
        font=dict(size=12, color="gray"),
        align="center"
    )

    # Save to HTML
    fig.write_html("dgx_spark_performance.html")
    print("HTML visualization generated: dgx_spark_performance.html")

if __name__ == "__main__":
    generate_visualization()
