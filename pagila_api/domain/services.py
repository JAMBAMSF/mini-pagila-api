from __future__ import annotations

from collections.abc import AsyncIterator, Callable
from typing import Any

import orjson

try:
    from pydantic import AnyUrl
    import pydantic.networks as _pydantic_networks

    if not hasattr(_pydantic_networks, "Url"):
        _pydantic_networks.Url = AnyUrl  # type: ignore[attr-defined]
except Exception:
    # Leave untouched if pydantic internals differ; Semantic Kernel will import if available.
    pass

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

try:
    from semantic_kernel.functions.kernel_function_from_prompt import (
        kernel_function_from_prompt as _sk_kernel_function_from_prompt,
    )
except ImportError:  # pragma: no cover
    _sk_kernel_function_from_prompt = None


def kernel_function_from_prompt(
    prompt_template: str | None,
    prompt_template_config: PromptTemplateConfig | None,
    plugin_name: str,
    function_name: str,
) -> KernelFunction:
    """Unified helper that works across Semantic Kernel versions."""
    prompt_arg = prompt_template
    config_arg = prompt_template_config
    if config_arg is not None:
        template_value = getattr(config_arg, "template", None)
        if template_value in (None, "") and prompt_template:
            try:
                config_arg = config_arg.model_copy(update={"template": prompt_template})
            except AttributeError:  # pragma: no cover - pydantic v1 fallback
                config_arg = PromptTemplateConfig(**{**config_arg.model_dump(), "template": prompt_template})  # type: ignore[arg-type]
            prompt_arg = None

    return KernelFunction.from_prompt(
        function_name=function_name,
        plugin_name=plugin_name,
        prompt=prompt_arg,
        prompt_template_config=config_arg,
    )
from sqlalchemy.ext.asyncio import AsyncSession

from .models import (
    FilmListParams,
    FilmOut,
    Paginated,
    RentalCreate,
    RentalCreatedResponse,
    SummaryOut,
)
from .repositories import FilmRepository, RentalRepository


class DomainError(Exception):
    """Base domain exception."""


class NotFoundError(DomainError):
    def __init__(self, resource: str, identifier: Any):
        super().__init__(f"{resource} not found: {identifier}")
        self.resource = resource
        self.identifier = identifier


class MissingDependencyError(DomainError):
    """Raised when required dependencies are not configured."""


def _build_ask_prompt() -> KernelFunction:
    prompt_template = """
You are a helpful video store assistant. Answer the customer question clearly and concisely.
Question: {{$question}}
"""
    config_payload = {
        "schema": 1,
        "type": "completion",
        "description": "General purpose Q&A helper for video store staff.",
        "execution_settings": {
            "default": {
                "temperature": 0.6,
                "top_p": 0.9,
                "max_tokens": 400,
            }
        },
        "input_variables": [
            {"name": "question", "description": "Customer question", "required": True},
        ],
    }
    try:
        config = PromptTemplateConfig.model_validate(config_payload)
    except AttributeError:
        config = PromptTemplateConfig.from_dict(config_payload)  # type: ignore[attr-defined]
    return kernel_function_from_prompt(
        prompt_template,
        config,
        plugin_name="ai",
        function_name="ask",
    )


class FilmService:
    def __init__(self, session: AsyncSession):
        self._repo = FilmRepository(session)

    async def list_films(self, params: FilmListParams) -> Paginated[FilmOut]:
        return await self._repo.paginate(params)

    async def get_film_or_raise(self, film_id: int) -> FilmOut:
        film = await self._repo.get_film(film_id)
        if film is None:
            raise NotFoundError("film", film_id)
        return FilmOut(
            film_id=film.film_id,  # type: ignore[arg-type]
            title=film.title,
            description=film.description,
            rating=film.rating,
            rental_rate=film.rental_rate,
            category=None,
            streaming_available=film.streaming_available,
        )

    async def get_summary_context(self, film_id: int) -> dict[str, str]:
        film = await self._repo.get_film(film_id)
        if film is None:
            raise NotFoundError("film", film_id)
        rental_rate = f"{film.rental_rate:.2f}" if film.rental_rate is not None else "0.00"
        return {
            "title": film.title,
            "description": film.description or "No description available.",
            "rating": film.rating or "NR",
            "rental_rate": rental_rate,
        }

    async def find_by_title(self, title: str) -> FilmOut | None:
        return await self._repo.find_by_title(title)


class RentalService:
    def __init__(self, session: AsyncSession):
        self._repo = RentalRepository(session)

    async def create_rental(self, customer_id: int, payload: RentalCreate) -> RentalCreatedResponse:
        customer = await self._repo.get_customer(customer_id)
        if customer is None:
            raise NotFoundError("customer", customer_id)

        inventory = await self._repo.get_inventory(payload.inventory_id)
        if inventory is None:
            raise NotFoundError("inventory", payload.inventory_id)

        return await self._repo.create_rental(customer_id, payload)


class AIService:
    def __init__(
        self,
        kernel_provider: Callable[[], Kernel],
        summary_prompt: dict[str, Any],
        film_service: FilmService,
    ):
        self._kernel_provider = kernel_provider
        summary_config = summary_prompt["config"]  # type: ignore[index]
        try:
            cfg = PromptTemplateConfig.model_validate(summary_config)
        except AttributeError:
            cfg = PromptTemplateConfig.from_dict(summary_config)  # type: ignore[attr-defined]
        self._summary_prompt = kernel_function_from_prompt(
            summary_prompt["template"],  # type: ignore[index]
            cfg,
            plugin_name="ai",
            function_name="film_summary",
        )
        self._ask_prompt = _build_ask_prompt()
        self._film_service = film_service

    def _get_kernel(self) -> Kernel:
        kernel = self._kernel_provider()
        if kernel is None:
            raise MissingDependencyError("Semantic Kernel has not been initialised.")
        return kernel

    @staticmethod
    def _collect_text(payload: Any) -> list[str]:
        if isinstance(payload, str):
            return [payload]
        if isinstance(payload, FunctionResult):
            return AIService._collect_text(payload.value)
        if isinstance(payload, (list, tuple)):
            collected: list[str] = []
            for item in payload:
                collected.extend(AIService._collect_text(item))
            return collected
        text = getattr(payload, "content", None)
        return [text] if isinstance(text, str) else []

    def ensure_ready(self) -> None:
        """Validate that required dependencies are configured."""
        self._get_kernel()

    async def ask(self, question: str) -> AsyncIterator[str]:
        kernel = self._get_kernel()
        settings = PromptExecutionSettings(service_id="openai")
        stream_callable = getattr(self._ask_prompt, "invoke_stream", None)
        if callable(stream_callable):
            async for chunk in stream_callable(
                kernel=kernel,
                settings=settings,
                question=question,
            ):
                for piece in self._collect_text(chunk):
                    piece = piece.strip()
                    if piece:
                        yield piece
            return

        stream = await self._ask_prompt.invoke_stream_async(  # type: ignore[attr-defined]
            kernel=kernel,
            arguments={"question": question},
            settings=settings,
        )
        async for message in stream:
            for piece in self._collect_text(message):
                piece = piece.strip()
                if piece:
                    yield piece

    async def summary(self, film_id: int) -> SummaryOut:
        kernel = self._get_kernel()
        context = await self._film_service.get_summary_context(film_id)

        settings = PromptExecutionSettings(service_id="openai")
        try:
            settings.extension_data["response_format"] = {"type": "json_object"}  # type: ignore[index]
        except AttributeError:
            # Older SK versions may not expose extension_data; allow prompt rules to enforce JSON.
            pass

        invoke_callable = getattr(self._summary_prompt, "invoke", None)
        if callable(invoke_callable):
            result = await invoke_callable(
                kernel=kernel,
                settings=settings,
                **context,
            )
        else:
            result = await self._summary_prompt.invoke_async(  # type: ignore[attr-defined]
                kernel=kernel,
                arguments=context,
                settings=settings,
            )
        segments = self._collect_text(result)
        if not segments:
            raise DomainError("Semantic Kernel returned unexpected payload.")

        raw = "".join(segments)

        try:
            data = orjson.loads(raw)
        except orjson.JSONDecodeError as exc:
            raise DomainError("Semantic Kernel returned invalid JSON.") from exc

        return SummaryOut(**data)
