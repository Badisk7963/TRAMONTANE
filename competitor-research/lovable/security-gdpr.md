# Lovable — Security & GDPR Analysis
> Sources: lovable.dev/security, lovable.dev/data-processing-agreement (scraped 2026-03-30)

## Certifications & Compliance
- **SOC 2 Type II** — maintained for duration of agreement
- **ISO 27001:2022** — maintained for duration of agreement
- **GDPR compliant**
- Trust center: https://trust.lovable.dev/

## Data Residency
- **EU, US, and Australia** supported regions
- Data stays in selected region, does not move across regions by default
- Transparent about infrastructure and subprocessors

## AI & Data Training
- **Customer data NOT used for training** Lovable models
- Third-party AI providers have contractual agreements restricting training/retention
- "Your work stays your work"

## Access & Identity Controls
- SAML and OIDC (Okta, Azure AD, Google)
- SCIM for automated provisioning/deprovisioning
- Role-based access (view, edit, approve, publish) — server-side enforcement
- 2FA support
- SSO on Business+
- Least-privilege access supported

## Platform Security
- Workspace and project logical isolation
- WAF controls, network isolation, encrypted storage
- Adaptive rate limiting (IP, user, workspace level)
- Automatic security scanning (code, dependencies, configs)
- Continuous monitoring and abuse detection

## Publishing Controls
- Editing, approval, publishing are **separate permissions**
- Server-side enforcement (can't bypass via client)
- All publishing events logged with user attribution

## Secrets Management
- Encrypted at rest, access-controlled by role
- Not exposed in plaintext in logs or interfaces
- Environment-scoped, rotatable without redeployment

## DPA Details (Data Processing Agreement)
- Available on Business and Enterprise plans
- **Entity:** Lovable Labs Incorporated, 1111b South Governors Avenue, Dover, DE 19904
- **Swedish entity:** Lovable Labs AB, Box 190, 101 23, Stockholm, Sweden
- **DPO:** dpo@lovable.dev (Representative: Assenteo Ltd)
- Customer = Controller, Lovable = Processor
- EU SCCs Module Two (Controller to Processor) for ex-EEA transfers
- UK Addendum for ex-UK transfers
- No automated decision-making with legal effects
- Personal Data Breach notification "without undue delay"
- Sub-processor list at lovable.dev/subprocessors, updated annually
- Data return/deletion within 30 days of termination
- Section 10: **No AI/ML training on Customer Personal Data**
- Service Data (anonymized/aggregated) may be used for analytics, security, billing, product development

## Key GDPR Gaps/Concerns for ArkhosAI Differentiation
- DPA only on Business/Enterprise plans (not Pro)
- US entity (Delaware) as primary — Swedish entity secondary
- Sub-processor list requires request (not publicly visible on page)
- "Service Data" clause allows training on de-identified data (Section 9.1.c)
- No mention of data sovereignty beyond region selection
- CCPA compliance included but US-focused
