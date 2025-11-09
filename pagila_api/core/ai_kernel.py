from __future__ import annotations

from pathlib import Path
import json
from typing import Any

import pydantic.networks as _pydantic_networks
from pydantic import AnyUrl

if not hasattr(_pydantic_networks, "Url"):
    _pydantic_networks.Url = AnyUrl                              

from .config import Settings

_kernel: Any | None = None


def get_kernel(settings: Settings):
    """Lazily create the Semantic Kernel, importing SK only when needed.

    This avoids import-time errors if SK has optional dependency mismatches
    and lets non-AI endpoints run without SK installed.
    """
    global _kernel
    if _kernel is not None:
        return _kernel

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY must be set to initialise the Semantic Kernel.")

                                                
    from semantic_kernel import Kernel
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.functions.kernel_plugin_collection import KernelPluginCollection
    from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion

    try:
        KernelFunction.model_rebuild()
        KernelPluginCollection.model_rebuild()
        Kernel.model_rebuild()
    except Exception:
                                                         
        pass

    kernel = Kernel()
    kernel.add_service(
        OpenAIChatCompletion(
            ai_model_id=settings.openai_model,
            api_key=settings.openai_api_key,
            service_id="openai",
        )
    )
    _kernel = kernel
    return kernel


def load_prompt_config(path: Path) -> dict[str, Any]:
    """Return a dict containing both the template string and config settings.

    The returned shape is: {"template": str, "config": dict}
    """
    config_path = path / "config.json"
    prompt_path = path / "prompt.skprompt"
    if not config_path.exists() or not prompt_path.exists():
        raise FileNotFoundError(f"Prompt resources missing in {path}")

    cfg = json.loads(config_path.read_text(encoding="utf-8"))
    template = prompt_path.read_text(encoding="utf-8")
    return {"template": template, "config": cfg}
