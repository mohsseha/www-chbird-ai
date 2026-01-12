
# Figure Summaries for LLM Performance Benchmark Analysis

This document provides detailed descriptions of the figures generated in `plot.html` and `aux.html`. The goal is to provide sufficient context for a blog post or technical analysis of the July 25, 2025 Fiction.liveBench results.

---

## `plot.html`: Interactive LLM Performance Chart

### **Primary Figure: LLM Performance vs. Context Length**

*   **Purpose:** This is the main interactive line chart designed to visualize how the performance of various Large Language Models (LLMs) changes as the amount of context they must handle increases. It directly answers the question: "How well do these models maintain accuracy as the input text gets longer?"

*   **Axes:**
    *   **X-Axis (Logarithmic):** "Context Length (tokens)". This axis represents the size of the input data, ranging from 0 to over 192,000 tokens. The logarithmic scale allows for clear visualization of performance across both short and extremely long context windows.
    *   **Y-Axis (Linear/Log Toggle):** "Accuracy Score (%)". This represents the model's percentage score on the recall benchmark.

*   **Key Interactive Features & Insights:**
    *   **Vendor-Grouped Legend:** Models are grouped by their parent company (e.g., OpenAI, Google, Anthropic). This allows a user to click on a vendor's name to toggle the visibility of all its models simultaneously, making it easy to compare entire product families.
    *   **Flagship Models by Default:** The chart initially loads with only the premier "flagship" models from each major vendor visible. This provides an uncluttered, high-level overview of the top performers in the market. A dropdown menu allows users to view "All Models" or select any individual model.
    *   **Open-Source Model Identification:** Open-source models are clearly distinguished with a unique visual style (dashed lines and diamond markers). This allows for immediate visual comparison between open-source and closed-source ecosystems. A key in the top corner explains this styling.
    *   **Y-Axis Scale Toggle:** Users can switch the Y-axis between `Linear` and `Log` scales. The log scale is particularly useful for differentiating performance among the highest-scoring models, where small differences in accuracy are significant.
    *   **Brand-Consistent Coloring:** Each vendor is assigned a color based on their official brand guidelines, making the chart more intuitive and visually appealing.
    *   **Rich Hover Information:** Mousing over any point on a line reveals a tooltip with the specific model name, its vendor, the exact context length, and its accuracy score at that point.

---

## `aux.html`: Auxiliary Performance Metrics

This report contains three distinct figures that provide deeper, more analytical summaries of the data beyond the raw performance curves.

### **Figure 1: Overall Model Performance Tiers**

*   **Type:** Summary Table.
*   **Purpose:** To rank all models based on a holistic "Composite Score" and assign them a performance tier (S, A, B, C). This figure provides a single, at-a-glance assessment of a model's overall value.
*   **Methodology:** The ranking is not based on raw score alone. It uses a **Composite Score** weighted 70% by the model's overall performance (AUC) and 30% by its long-context reliability (Stability). This rewards models that are not only powerful but also robust.
*   **Insights:** This table is the executive summary. It helps identify which models are the best all-rounders (S-Tier) versus those that might excel in specific areas but have notable weaknesses (lower tiers). The vendor color-coding helps spot trends (e.g., "Which vendor has the most S-Tier models?").

### **Figure 2: Area Under Curve (AUC) Analysis**

*   **Type:** Bar Chart.
*   **Purpose:** To quantify and rank each model's total performance across *all* tested context lengths.
*   **Methodology:** The Area Under the Curve (AUC) is calculated for each model's performance line from the main plot. A higher AUC means the model maintained a higher accuracy score across the full spectrum of context lengths.
*   **Insights:** This chart moves beyond cherry-picking a single data point (like peak performance) and instead rewards consistency. A model that scores 95% everywhere will have a much higher AUC than a model that scores 100% on short context but drops to 60% on long context. It's a measure of overall workhorse capability.

### **Figure 3: Long-Context Stability Analysis**

*   **Type:** Bar Chart.
*   **Purpose:** To specifically measure and rank how well models resist performance degradation at very long context lengths.
*   **Methodology:** Stability is calculated as `(Score at Longest Context) / (Peak Score)`. A high stability score (closer to 100%) indicates the model performs nearly as well on its longest task as it does at its best.
*   **Insights:** This is a crucial metric for anyone needing a model for long-document analysis, full-codebase understanding, or extended conversations. It separates models that are merely good at short tasks from those that are truly reliable for enterprise-grade, long-context workloads.
