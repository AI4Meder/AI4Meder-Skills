# AI4Meder Skills

Agent skills for [AI4Meder](https://www.ai4meder.com), a medical AI resource
aggregation platform for papers, datasets/resources, competitions/deadlines,
calls/opportunities, and short courses/talks.

This repository helps an agent submit and review AI4Meder content through the
production website API without repeating the platform prompt each time.

## Available Skill

| Skill | Purpose |
| --- | --- |
| `ai4meder-submission-review` | Submit AI4Meder content as a guest or API-key user, list pending submissions as an admin, and review submissions with an admin API key. |

## What The Skill Handles

- Guest submissions without an API key.
- Normal-user submissions with `AI4MEDER_API_KEY`.
- Admin identity checks with `whoami`.
- Admin pending-list and review workflows with `AI4MEDER_ADMIN_API_KEY`.
- Submission payloads for papers, datasets/resources, competitions/deadlines,
  calls/opportunities, and short courses/talks.
- Approved reviews that publish the matching draft content through the existing
  review API contract.

The production site is:

```text
https://www.ai4meder.com
```

## Primary Categories

Every submission must include at least one canonical AI4Meder primary direction
ID in `directionTags`.

| ID | Category |
| --- | --- |
| `med_imaging` | 医学影像计算 |
| `clinical_nlp` | 临床语言智能 |
| `ehr_prediction` | EHR 与临床预测 |
| `medical_multimodal` | 医疗多模态 |
| `medical_llm_agent` | 医疗大模型与 Agent |
| `surgical_intervention` | 手术与介入智能 |
| `trustworthy_safe_private` | 可信、安全、公平与隐私 |
| `clinical_translation` | 临床转化与部署 |

Use `draftFields.keywordTags` for detailed topics, modalities, methods,
diseases, datasets, venues, or source labels.

## Install

Clone the repository and place the skill folder where your Codex environment
loads custom skills.

```bash
git clone https://github.com/AI4Meder/AI4Meder-Skills.git
mkdir -p ~/.codex/skills
cp -R AI4Meder-Skills/ai4meder-submission-review ~/.codex/skills/
```

On Windows PowerShell:

```powershell
git clone https://github.com/AI4Meder/AI4Meder-Skills.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse AI4Meder-Skills\ai4meder-submission-review "$env:USERPROFILE\.codex\skills\"
```

## Use

Ask Codex to use `$ai4meder-submission-review`, or ask for an AI4Meder
submission/review task directly.

Example prompts:

```text
Use $ai4meder-submission-review to submit this medical AI paper to AI4Meder.
```

```text
Use $ai4meder-submission-review to list pending submissions and approve the verified one.
```

## CLI Helper

The skill includes a small Python helper:

```text
ai4meder-submission-review/scripts/ai4meder_api.py
```

Set the production site explicitly:

```bash
export AI4MEDER_BASE_URL="https://www.ai4meder.com"
```

Guest submission:

```bash
python3 ai4meder-submission-review/scripts/ai4meder_api.py submit payload.json
```

Normal-user API-key submission:

```bash
export AI4MEDER_API_KEY="<user-api-key>"
python3 ai4meder-submission-review/scripts/ai4meder_api.py submit payload.json
```

Admin review:

```bash
export AI4MEDER_ADMIN_API_KEY="<admin-api-key>"
python3 ai4meder-submission-review/scripts/ai4meder_api.py whoami --api-key "$AI4MEDER_ADMIN_API_KEY"
python3 ai4meder-submission-review/scripts/ai4meder_api.py list --status pending --expected-admin-email "<admin-email>"
python3 ai4meder-submission-review/scripts/ai4meder_api.py review <submission-id> --status approved --review-note "Verified source." --expected-admin-email "<admin-email>"
```

Windows PowerShell equivalents:

```powershell
$env:AI4MEDER_BASE_URL = "https://www.ai4meder.com"
$env:AI4MEDER_API_KEY = "<user-api-key>"
python ai4meder-submission-review\scripts\ai4meder_api.py submit payload.json
```

```powershell
$env:AI4MEDER_BASE_URL = "https://www.ai4meder.com"
$env:AI4MEDER_ADMIN_API_KEY = "<admin-api-key>"
python ai4meder-submission-review\scripts\ai4meder_api.py whoami --api-key $env:AI4MEDER_ADMIN_API_KEY
python ai4meder-submission-review\scripts\ai4meder_api.py list --status pending --expected-admin-email "<admin-email>"
python ai4meder-submission-review\scripts\ai4meder_api.py review <submission-id> --status approved --review-note "Verified source." --expected-admin-email "<admin-email>"
```

## Payload Contract

Read the bundled API contract when constructing payloads:

```text
ai4meder-submission-review/references/api-contract.md
```

At a high level, every payload needs:

- `submissionType`
- `title`
- `sourceUrl`
- `summary`
- `directionTags`
- type-specific `draftFields`

Guest submissions also need `contactEmail`. API-key submissions can omit
contact details because the contributor identity comes from the API key.

## Review Semantics

`PATCH /api/admin/submissions/{id}` with `status=approved` means:

1. The submission is marked `approved`.
2. The matching content draft is published.
3. The response includes the submission status and published content status.

The expected approved response includes:

```json
{
  "submission": { "status": "approved" },
  "content": { "status": "published", "publishedAt": "..." },
  "publishedContent": { "status": "published", "publishedAt": "..." }
}
```

## Security

- Do not commit API keys, passwords, cookies, database URLs, or local auth state.
- Use `AI4MEDER_API_KEY` only for normal-user submissions.
- Use `AI4MEDER_ADMIN_API_KEY` only for admin review workflows.
- Always verify the admin key owner with `whoami` before review actions.
- Guest submissions are allowed, but they do not earn contribution points.

## Repository Layout

```text
AI4Meder-Skills/
  ai4meder-submission-review/
    SKILL.md
    agents/openai.yaml
    references/api-contract.md
    scripts/ai4meder_api.py
```
