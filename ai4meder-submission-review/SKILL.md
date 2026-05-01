---
name: ai4meder-submission-review
description: Submit and review content for AI4Meder, a medical AI resource aggregation platform. Use when Codex needs to prepare or post AI4Meder papers, datasets/resources, competitions/deadlines, calls/opportunities, short courses/talks, or review pending submissions through the production website API with guest submission, normal-user API-key submission, or admin API-key review workflows.
---

# AI4Meder Submission Review

Use this skill to submit and review AI4Meder website content through the API.
AI4Meder is a medical AI resource aggregation platform for papers,
datasets/resources, competitions/deadlines, calls/opportunities, and short
courses/talks.

## Platform Scope

Every submitted item must be mapped to at least one of the 8 primary medical AI
directions in `directionTags`:

- `med_imaging` - 医学影像计算
- `clinical_nlp` - 临床语言智能
- `ehr_prediction` - EHR 与临床预测
- `medical_multimodal` - 医疗多模态
- `medical_llm_agent` - 医疗大模型与 Agent
- `surgical_intervention` - 手术与介入智能
- `trustworthy_safe_private` - 可信、安全、公平与隐私
- `clinical_translation` - 临床转化与部署

Use `draftFields.keywordTags` for more granular topic labels. Do not put
non-primary categories in `directionTags`.

## Tool

Use `scripts/ai4meder_api.py` for deterministic API calls. Set the target site
with `AI4MEDER_BASE_URL` or `--base-url`; the production site is
`https://www.ai4meder.com`.

Never put API keys in files. Pass keys with environment variables:

- `AI4MEDER_API_KEY` for normal user submission.
- `AI4MEDER_ADMIN_API_KEY` for admin review.

## Workflows

1. Guest submission:

   ```powershell
   python scripts/ai4meder_api.py --base-url https://www.ai4meder.com submit payload.json
   ```

2. Normal user API-key submission:

   ```powershell
   $env:AI4MEDER_API_KEY='<user-api-key>'
   python scripts/ai4meder_api.py --base-url https://www.ai4meder.com submit payload.json
   ```

3. Admin API-key review:

   ```powershell
   $env:AI4MEDER_ADMIN_API_KEY='<admin-api-key>'
   python scripts/ai4meder_api.py --base-url https://www.ai4meder.com whoami --api-key $env:AI4MEDER_ADMIN_API_KEY
   python scripts/ai4meder_api.py --base-url https://www.ai4meder.com list --status pending --expected-admin-email '<admin-email>'
   python scripts/ai4meder_api.py --base-url https://www.ai4meder.com review <submission-id> --status approved --review-note 'Verified source.' --expected-admin-email '<admin-email>'
   ```

## Payloads

Read `references/api-contract.md` when constructing payloads or debugging API
responses. Required `draftFields` differ by content type:

- `paper`: authors, venue, published date, category, abstract.
- Dataset-like resources: category, modality/resource shape, size/version,
  license, tasks, source.
- `challenge`: competition status fields and at least one date.
- `cfp`: venue plus deadline unless long-running.
- `talk`: speakers, level, duration.

## Review Rules

Always verify admin identity before review with `whoami` or
`--expected-admin-email`. A normal user API key may submit but must not be used
for admin list/review.

When the API receives `status=approved`, AI4Meder approves the submission and
publishes the matching draft content in the same review action. There is no
separate publish command in this skill. Approved API-key-backed submissions
award contribution credit according to website rules, with duplicate approvals
and self-review handled by the API.
