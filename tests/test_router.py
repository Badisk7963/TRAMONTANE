"""Tests for tramontane.router — classifier + router."""

from __future__ import annotations

from tramontane.router.classifier import ClassificationMode, TaskClassifier
from tramontane.router.router import MistralRouter


class TestClassifierOffline:
    """Offline keyword-heuristic classifier."""

    def test_code_task(self, offline_classifier: TaskClassifier) -> None:
        r = offline_classifier.classify_sync("write a Python function to sort a list")
        assert r.task_type == "code"
        assert r.has_code is True
        assert r.mode_used == ClassificationMode.OFFLINE

    def test_research_task(self, offline_classifier: TaskClassifier) -> None:
        r = offline_classifier.classify_sync("research the latest news about AI in France")
        assert r.task_type == "research"

    def test_bulk_task(self, offline_classifier: TaskClassifier) -> None:
        r = offline_classifier.classify_sync("list all")
        assert r.task_type == "bulk"

    def test_french_locale(self, offline_classifier: TaskClassifier) -> None:
        r = offline_classifier.classify_sync(
            "Recherchez les dernières nouvelles sur le marché français de l'IA"
        )
        assert r.language == "fr"

    def test_confidence_offline(self, offline_classifier: TaskClassifier) -> None:
        r = offline_classifier.classify_sync("hello world")
        assert r.confidence == 0.70

    def test_complexity_short_prompt(self, offline_classifier: TaskClassifier) -> None:
        r = offline_classifier.classify_sync("fix bug")
        assert r.complexity >= 1
        assert r.complexity <= 5


class TestRouter:
    """MistralRouter decision tree."""

    def test_code_routes_to_devstral_small(self, offline_router: MistralRouter) -> None:
        d = offline_router.route_sync("write a Python function")
        assert d.primary_model == "devstral-small"

    def test_code_complex_routes_to_devstral_2(self, offline_router: MistralRouter) -> None:
        # Long prompt pushes complexity >= 4
        prompt = "Refactor this entire monorepo architecture " * 50
        d = offline_router.route_sync(prompt)
        assert d.primary_model in ("devstral-2", "devstral-small")

    def test_budget_downgrades_model(self, offline_router: MistralRouter) -> None:
        d = offline_router.route_sync(
            "analyze the EU AI Act implications on enterprise SaaS",
            budget=0.0000001,
        )
        assert d.downgrade_applied is True
        assert d.budget_constrained is True

    def test_french_locale_prefers_multilingual(
        self, offline_router: MistralRouter,
    ) -> None:
        d = offline_router.route_sync(
            "recherchez les dernières nouvelles", locale="fr",
        )
        assert d.primary_model in ("mistral-small", "mistral-large", "ministral-7b")

    def test_explain_returns_string(self, offline_router: MistralRouter) -> None:
        d = offline_router.route_sync("write code")
        explanation = MistralRouter.explain(d)
        assert isinstance(explanation, str)
        assert "Routed to" in explanation

    def test_local_mode(self) -> None:
        r = MistralRouter(local_mode=True)
        d = r.route_sync("write code")
        assert d.local_mode is True
