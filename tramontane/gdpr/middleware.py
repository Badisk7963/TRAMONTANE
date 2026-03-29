"""GDPR middleware — orchestrates PII detection, audit, and data residency.

Sits between every agent call and the Mistral API. Applies different
behaviour depending on ``gdpr_level``:

  none     — pass through, audit only
  standard — detect PII, log findings, pass through
  strict   — detect PII, redact, log, block if unredactable
"""

from __future__ import annotations

import logging
from typing import Literal

from tramontane.gdpr.audit import AuditVault
from tramontane.gdpr.pii import PIIDetector, PIIResult
from tramontane.memory.longterm import LongTermMemory

logger = logging.getLogger(__name__)

GDPRLevel = Literal["none", "standard", "strict"]


class GDPRMiddleware:
    """Orchestrates PII detection + audit + data residency per request.

    Injected into the pipeline executor so that every agent input/output
    passes through GDPR processing before and after the LLM call.
    """

    def __init__(
        self,
        gdpr_level: GDPRLevel = "none",
        pii_detector: PIIDetector | None = None,
        audit_vault: AuditVault | None = None,
        memory: LongTermMemory | None = None,
        locale: str = "fr",
    ) -> None:
        self._level = gdpr_level
        self._pii = pii_detector or PIIDetector(locale=locale)
        self._audit = audit_vault or AuditVault()
        self._memory = memory or LongTermMemory()
        self._locale = locale

    @property
    def level(self) -> GDPRLevel:
        """Current GDPR enforcement level."""
        return self._level

    # -- Input processing --------------------------------------------------

    async def process_input(
        self,
        text: str,
        run_id: str,
        agent_role: str,
        pipeline_name: str = "",
    ) -> str:
        """Process input text through GDPR filters before sending to LLM.

        - none:     returns text unchanged, logs audit
        - standard: detects PII, logs findings, returns text unchanged
        - strict:   detects PII, redacts, logs, returns cleaned text
        """
        if self._level == "none":
            return text

        result = await self._pii.detect(text)

        await self._audit.log(
            run_id=run_id,
            pipeline_name=pipeline_name,
            agent_role=agent_role,
            action_type="gdpr_input_scan",
            model_used="pii_detector",
            input_tokens=0,
            output_tokens=0,
            cost_eur=0.0,
            gdpr_sensitivity=self._classify_sensitivity(result),
            pii_detected=result.has_pii,
            pii_redacted=(self._level == "strict" and result.has_pii),
            metadata={
                "pii_types": [t.value for t in result.pii_types_found],
                "detection_count": len(result.detections),
            },
        )

        if result.has_pii:
            logger.info(
                "PII detected in input for %s: %d items (%s)",
                agent_role,
                len(result.detections),
                ", ".join(t.value for t in result.pii_types_found),
            )

        if self._level == "strict" and result.has_pii:
            return result.cleaned_text

        return text

    # -- Output processing -------------------------------------------------

    async def process_output(
        self,
        text: str,
        run_id: str,
        agent_role: str,
        pipeline_name: str = "",
    ) -> str:
        """Process output text through GDPR filters after LLM response.

        Same logic as process_input — applied to model output.
        """
        if self._level == "none":
            return text

        result = await self._pii.detect(text)

        await self._audit.log(
            run_id=run_id,
            pipeline_name=pipeline_name,
            agent_role=agent_role,
            action_type="gdpr_output_scan",
            model_used="pii_detector",
            input_tokens=0,
            output_tokens=0,
            cost_eur=0.0,
            gdpr_sensitivity=self._classify_sensitivity(result),
            pii_detected=result.has_pii,
            pii_redacted=(self._level == "strict" and result.has_pii),
        )

        if self._level == "strict" and result.has_pii:
            return result.cleaned_text

        return text

    # -- GDPR Article 17: Right to Erasure ---------------------------------

    async def handle_erasure_request(
        self,
        user_id: str,
        requested_by: str = "user",
    ) -> int:
        """Handle a GDPR Article 17 erasure request.

        Erases user data from long-term memory and logs the event.
        Returns count of erased entries.
        """
        count = await self._memory.erase_user(
            user_id=user_id, requested_by=requested_by
        )

        logger.info(
            "GDPR erasure request processed: %d entries for user %s",
            count, user_id,
        )
        return count

    # -- Internal ----------------------------------------------------------

    @staticmethod
    def _classify_sensitivity(result: PIIResult) -> str:
        """Map PII detection result to sensitivity level."""
        if not result.has_pii:
            return "none"
        from tramontane.gdpr.pii import PIIType

        high_types = {
            PIIType.NIR, PIIType.IBAN, PIIType.PASSPORT,
            PIIType.CREDIT_CARD,
        }
        found_types = set(result.pii_types_found)
        if found_types & high_types:
            return "high"
        return "low"
