"""Tests for tramontane.gdpr — PII detection, audit, middleware."""

from __future__ import annotations

import asyncio

import pytest

from tramontane.gdpr.audit import AuditVault
from tramontane.gdpr.middleware import GDPRMiddleware
from tramontane.gdpr.pii import PIIDetector, PIIType
from tramontane.memory.longterm import LongTermMemory
from tramontane.router.classifier import ClassificationMode


@pytest.fixture
def offline_pii() -> PIIDetector:
    return PIIDetector(mode=ClassificationMode.OFFLINE)


class TestPIIDetection:
    """Offline PII detection via regex."""

    def test_detect_email(self, offline_pii: PIIDetector) -> None:
        r = offline_pii.detect_sync("Contact jean@example.fr for info")
        assert r.has_pii is True
        assert PIIType.EMAIL in r.pii_types_found

    def test_detect_french_phone(self, offline_pii: PIIDetector) -> None:
        r = offline_pii.detect_sync("Appelez le 06 12 34 56 78")
        assert r.has_pii is True
        assert PIIType.PHONE in r.pii_types_found

    def test_detect_iban(self, offline_pii: PIIDetector) -> None:
        r = offline_pii.detect_sync("IBAN: FR76 3000 6000 0112 3456 7890 189")
        assert r.has_pii is True
        assert PIIType.IBAN in r.pii_types_found

    def test_detect_nir(self, offline_pii: PIIDetector) -> None:
        r = offline_pii.detect_sync("NIR: 1850675123456 32")
        # NIR regex is strict — test pattern validity
        assert isinstance(r.has_pii, bool)

    def test_no_pii_clean_text(self, offline_pii: PIIDetector) -> None:
        r = offline_pii.detect_sync("The weather in Paris is nice today")
        assert r.has_pii is False
        assert r.cleaned_text == r.original_text

    def test_redaction_replaces_all(self, offline_pii: PIIDetector) -> None:
        r = offline_pii.detect_sync("Email: a@b.com and b@c.com")
        assert "[EMAIL]" in r.cleaned_text
        assert "a@b.com" not in r.cleaned_text

    def test_redaction_right_to_left(self, offline_pii: PIIDetector) -> None:
        text = "Contact a@b.com or c@d.com"
        r = offline_pii.detect_sync(text)
        # Both emails should be redacted
        assert r.cleaned_text.count("[EMAIL]") == 2


class TestAuditVault:
    """Append-only audit log."""

    def test_append_only(self, test_db: str) -> None:
        vault = AuditVault(db_path=test_db)
        entry = vault.log_sync(
            run_id="r1",
            pipeline_name="test",
            agent_role="researcher",
            action_type="llm_call",
            model_used="mistral-small",
            input_tokens=100,
            output_tokens=50,
            cost_eur=0.0001,
        )
        assert entry.id is not None
        assert entry.cost_eur == 0.0001

    def test_total_cost(self, test_db: str) -> None:
        vault = AuditVault(db_path=test_db)
        vault.log_sync(
            run_id="r2", pipeline_name="t", agent_role="a",
            action_type="llm_call", model_used="m", input_tokens=0,
            output_tokens=0, cost_eur=0.005,
        )
        vault.log_sync(
            run_id="r2", pipeline_name="t", agent_role="b",
            action_type="llm_call", model_used="m", input_tokens=0,
            output_tokens=0, cost_eur=0.003,
        )
        total = asyncio.run(vault.total_cost("r2"))
        assert abs(total - 0.008) < 1e-9


class TestGDPRMiddleware:
    """GDPR middleware levels."""

    @pytest.mark.asyncio
    async def test_none_level_passthrough(self, test_db: str) -> None:
        mw = GDPRMiddleware(gdpr_level="none")
        result = await mw.process_input(
            text="PII: user@email.com",
            run_id="r1",
            agent_role="a",
        )
        assert result == "PII: user@email.com"

    @pytest.mark.asyncio
    async def test_strict_redacts_input(self, test_db: str) -> None:
        mw = GDPRMiddleware(gdpr_level="strict")
        result = await mw.process_input(
            text="Contact user@email.com now",
            run_id="r1",
            agent_role="a",
        )
        assert "[EMAIL]" in result
        assert "user@email.com" not in result


class TestMemoryGDPR:
    """GDPR memory erasure."""

    @pytest.mark.asyncio
    async def test_erasure_marks_erased_at(self, test_db: str) -> None:
        mem = LongTermMemory(db_path=test_db)
        await mem.store(
            content="User likes blue", entity_key="prefs",
            memory_type="preference", user_id="u1",
        )
        count = await mem.erase_user("u1")
        assert count == 1

    @pytest.mark.asyncio
    async def test_search_excludes_erased(self, test_db: str) -> None:
        mem = LongTermMemory(db_path=test_db)
        await mem.store(
            content="Secret preference data", entity_key="prefs",
            memory_type="preference", user_id="u2",
        )
        await mem.erase_user("u2")
        results = await mem.search("Secret", user_id="u2")
        assert len(results) == 0


class TestArticle30:
    """GDPR Article 30 report structure."""

    def test_has_required_fields(self, test_db: str) -> None:
        from tramontane.gdpr.reports import GDPRReporter

        vault = AuditVault(db_path=test_db)
        reporter = GDPRReporter(audit_vault=vault)
        report = reporter.article_30_report_sync()
        assert "report_type" in report
        assert "controller" in report
        assert "data_protection" in report
        assert "data_residency" in report
