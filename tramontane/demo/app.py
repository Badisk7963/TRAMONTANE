"""Tramontane Router Demo — Gradio Space.

Demonstrates the Mistral model router in OFFLINE mode (no API key needed).
Deploy to HuggingFace Spaces under BleuCommerce-Apps/tramontane-demo.
"""

from __future__ import annotations

import gradio as gr
import pandas as pd

from tramontane.router.classifier import ClassificationMode, TaskClassifier
from tramontane.router.models import MISTRAL_MODELS
from tramontane.router.router import MistralRouter


def _build_fleet_df() -> pd.DataFrame:
    """Build the model fleet as a DataFrame."""
    rows = []
    for alias, m in MISTRAL_MODELS.items():
        rows.append({
            "Model": alias,
            "Tier": m.tier,
            "Strengths": ", ".join(m.strengths[:3]),
            "EUR/1M in": f"{m.cost_per_1m_input_eur:.2f}",
            "EUR/1M out": f"{m.cost_per_1m_output_eur:.2f}",
            "Local": "ollama" if m.local_ollama else "-",
            "Modality": m.modality,
        })
    return pd.DataFrame(rows)


FLEET_DF = _build_fleet_df()

classifier = TaskClassifier(mode=ClassificationMode.OFFLINE)
router = MistralRouter()


def route_task(
    task: str, budget: float, locale: str,
) -> tuple[dict[str, object], str, pd.DataFrame]:
    """Route a task and return the decision, explanation, and fleet table."""
    if not task.strip():
        return {}, "Please describe a task.", FLEET_DF

    decision = router.route_sync(task, budget=budget, locale=locale)
    explanation = MistralRouter.explain(decision)

    decision_dict = {
        "primary_model": decision.primary_model,
        "function_calling_model": decision.function_calling_model,
        "reasoning_model": decision.reasoning_model,
        "task_type": decision.classification.task_type,
        "complexity": decision.classification.complexity,
        "language": decision.classification.language,
        "estimated_cost_eur": round(decision.estimated_cost_eur, 6),
        "budget_constrained": decision.budget_constrained,
        "downgrade_applied": decision.downgrade_applied,
        "local_mode": decision.local_mode,
    }

    md = (
        f"### {explanation}\n\n"
        f"**Task type:** {decision.classification.task_type} "
        f"(complexity {decision.classification.complexity}/5)\n\n"
        f"**Language detected:** {decision.classification.language}\n\n"
        f"**Estimated cost:** EUR {decision.estimated_cost_eur:.6f}\n\n"
    )
    if decision.downgrade_applied:
        md += f"**Downgrade:** {decision.downgrade_reason}\n\n"

    return decision_dict, md, FLEET_DF


CSS = """
.gradio-container { font-family: 'DM Sans', sans-serif; }
h1, h2, h3 { font-family: 'Syne', sans-serif; }
.primary-btn { background: #00D4EE !important; }
footer { font-size: 0.85em; color: #4A6480; }
"""

with gr.Blocks(theme=gr.themes.Base(primary_hue="cyan"), css=CSS) as demo:
    gr.Markdown(
        "# TRAMONTANE — Mistral Router Demo\n"
        "See which Mistral model gets selected for your task. "
        "No API key needed — runs in OFFLINE classifier mode."
    )

    with gr.Row():
        with gr.Column(scale=2):
            task_input = gr.Textbox(
                label="Describe your task",
                placeholder="Write a Python function to parse JSON...",
                lines=3,
            )
            with gr.Row():
                budget_slider = gr.Slider(
                    0.001, 0.50, value=0.05, step=0.001,
                    label="Budget (EUR)",
                )
                locale_dropdown = gr.Dropdown(
                    ["en", "fr", "de", "es", "it"], value="en",
                    label="Locale",
                )
            route_btn = gr.Button("Route", variant="primary")

        with gr.Column(scale=3):
            decision_json = gr.JSON(label="Routing Decision")
            explanation_md = gr.Markdown(label="Explanation")

    fleet_table = gr.DataFrame(label="Mistral Model Fleet", value=FLEET_DF)

    route_btn.click(
        fn=route_task,
        inputs=[task_input, budget_slider, locale_dropdown],
        outputs=[decision_json, explanation_md, fleet_table],
    )

    gr.Markdown(
        "---\n"
        "Built with **Tramontane v0.1.0** · "
        "[GitHub](https://github.com/bleucommerce/tramontane) · "
        "Mistral-native agent orchestration · "
        "Made in Orleans, France by Bleucommerce SAS"
    )

if __name__ == "__main__":
    demo.launch()
