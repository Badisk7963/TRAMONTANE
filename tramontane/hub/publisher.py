"""Publish Tramontane pipelines to HuggingFace Hub.

Pushes pipeline YAML + auto-generated README as an HF dataset
tagged ``tramontane-pipeline``.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel
from rich.console import Console

logger = logging.getLogger(__name__)

_CYAN = "#00D4EE"
_FROST = "#DCE9F5"
_STORM = "#4A6480"
_OK = "#22D68A"
_ERR = "#FF4560"
_RIM = "#1C2E42"
_console = Console()


class PublishConfig(BaseModel):
    """Configuration for publishing a pipeline to HF Hub."""

    pipeline_path: str
    repo_name: str
    description: str
    tags: list[str] = ["tramontane-pipeline"]
    private: bool = False


class PipelinePublisher:
    """Publishes Tramontane pipeline YAMLs to HuggingFace Hub."""

    def __init__(self, hf_token: str | None = None) -> None:
        self._token = hf_token or os.environ.get("HF_TOKEN")

    def publish(self, config: PublishConfig) -> str:
        """Validate, create repo, upload pipeline + README.

        Returns the HF URL on success.
        """
        # 1. Validate YAML
        _console.print(f"  [{_FROST}]Validating pipeline schema...[/]")
        pipeline_data = self._validate_yaml(config.pipeline_path)
        if pipeline_data is None:
            _console.print(f"  [{_ERR}]Validation failed[/]")
            return ""
        _console.print(f"  [{_OK}]\u2713[/] [{_FROST}]Pipeline valid[/]")

        try:
            from huggingface_hub import HfApi

            api = HfApi(token=self._token)

            # 2. Create repo
            _console.print(
                f"  [{_FROST}]Creating HF repo {config.repo_name}...[/]"
            )
            api.create_repo(
                config.repo_name,
                repo_type="dataset",
                private=config.private,
                exist_ok=True,
            )
            _console.print(
                f"  [{_OK}]\u2713[/] [{_FROST}]Repo ready[/]"
            )

            # 3. Upload pipeline YAML
            _console.print(f"  [{_FROST}]Uploading pipeline YAML...[/]")
            api.upload_file(
                path_or_fileobj=config.pipeline_path,
                path_in_repo="pipeline.yaml",
                repo_id=config.repo_name,
                repo_type="dataset",
            )
            _console.print(
                f"  [{_OK}]\u2713[/] [{_FROST}]YAML uploaded[/]"
            )

            # 4. Generate and upload README
            _console.print(f"  [{_FROST}]Generating README...[/]")
            readme = self._generate_readme(pipeline_data, config)
            api.upload_file(
                path_or_fileobj=readme.encode("utf-8"),
                path_in_repo="README.md",
                repo_id=config.repo_name,
                repo_type="dataset",
            )
            _console.print(
                f"  [{_OK}]\u2713[/] [{_FROST}]README uploaded[/]"
            )

            url = f"https://hf.co/datasets/{config.repo_name}"
            _console.print(
                f"\n  [{_OK}]\u2713 Published at {url}[/]\n"
            )
            return url

        except ImportError:
            _console.print(
                f"  [{_ERR}]huggingface_hub not installed[/]"
            )
            return ""
        except Exception as exc:
            _console.print(f"  [{_ERR}]Publish failed: {exc}[/]")
            logger.warning("Publish failed", exc_info=True)
            return ""

    @staticmethod
    def _validate_yaml(path: str) -> dict[str, Any] | None:
        """Load and validate pipeline YAML. Returns data or None."""
        try:
            data: dict[str, Any] = yaml.safe_load(
                Path(path).read_text(encoding="utf-8")
            )
            required = ["name", "agents", "handoffs"]
            for key in required:
                if key not in data:
                    logger.error("Pipeline YAML missing key: %s", key)
                    return None
            return data
        except Exception:
            logger.error("Failed to load YAML: %s", path, exc_info=True)
            return None

    @staticmethod
    def _generate_readme(
        pipeline_data: dict[str, Any],
        config: PublishConfig,
    ) -> str:
        """Generate a markdown README for the HF dataset page."""
        name = pipeline_data.get("name", config.repo_name)
        agents = pipeline_data.get("agents", [])
        agent_roles = [a.get("role", a.get("id", "?")) for a in agents]
        models = list({a.get("model", "auto") for a in agents})
        gdpr = pipeline_data.get("gdpr_level", "none")

        return f"""---
tags:
- tramontane-pipeline
---

# {name}

{config.description}

## Install

```bash
pip install tramontane
tramontane hub install {config.repo_name}
```

## Usage

```bash
tramontane run pipelines/{name}.yaml --input "your prompt here"
```

## Agents

{chr(10).join(f'- **{r}**' for r in agent_roles)}

## Models

{', '.join(f'`{m}`' for m in models)}

## GDPR Level

`{gdpr}`

---

*Published with [Tramontane](https://github.com/bleucommerce/tramontane)*
*Built in Orl\u00e9ans, France by Bleucommerce SAS*
"""
