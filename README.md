# AI4Meder Skills

Agent skills for [AI4Meder](https://www.ai4meder.com), a medical AI resource
aggregation platform for papers, datasets/resources, competitions/deadlines,
calls/opportunities, and short courses/talks.

This repository currently provides two Codex skills:

| Skill | Use When | API Key |
| --- | --- | --- |
| `ai4meder-submission-review` | Submit new content into the review queue, list pending submissions, or approve/reject/return submitted items. | Guest or `AI4MEDER_API_KEY` for submit; `AI4MEDER_ADMIN_API_KEY` for review. |
| `ai4meder-content-crud` | Directly list, get, create, update, or delete already-published content. | `AI4MEDER_ADMIN_API_KEY` only. |

Use `ai4meder-submission-review` for normal contribution workflows. Use
`ai4meder-content-crud` only when an operator explicitly wants to mutate live
published content outside the review queue.

## Install

macOS/Linux:

```bash
git clone https://github.com/AI4Meder/AI4Meder-Skills.git
mkdir -p ~/.codex/skills
cp -R AI4Meder-Skills/ai4meder-submission-review ~/.codex/skills/
cp -R AI4Meder-Skills/ai4meder-content-crud ~/.codex/skills/
```

Windows PowerShell:

```powershell
git clone https://github.com/AI4Meder/AI4Meder-Skills.git
New-Item -ItemType Directory -Force "$env:USERPROFILE\.codex\skills" | Out-Null
Copy-Item -Recurse AI4Meder-Skills\ai4meder-submission-review "$env:USERPROFILE\.codex\skills\"
Copy-Item -Recurse AI4Meder-Skills\ai4meder-content-crud "$env:USERPROFILE\.codex\skills\"
```

## Common Setup

Set the target site. Use production unless testing a local server:

```bash
export AI4MEDER_BASE_URL="https://www.ai4meder.com"
```

```powershell
$env:AI4MEDER_BASE_URL = "https://www.ai4meder.com"
```

For local testing:

```bash
export AI4MEDER_BASE_URL="http://127.0.0.1:4173"
```

API keys are generated from the website `/profile` page. Never put keys in
payload JSON, skill files, docs, git commits, or shell history snippets that
will be shared.

## Use With Codex

Ask Codex to use the skill by name:

```text
Use $ai4meder-submission-review to submit this medical AI paper to AI4Meder.
```

```text
Use $ai4meder-submission-review to list pending submissions and approve only source-verified items.
```

```text
Use $ai4meder-content-crud to update this published dataset item on AI4Meder.
```

## Quick Flows

If you are not sure which skill to pick, use this rule:

- New submission or pending review: `ai4meder-submission-review`
- Already-published content change: `ai4meder-content-crud`

Submission flow:

1. Set `AI4MEDER_BASE_URL`.
2. Add `AI4MEDER_API_KEY` only when the submitter has a user key.
3. Run `submit payload.json`.
4. If you are an admin, run `whoami`, then `list --status pending`, then `review`.

Published-content CRUD flow:

1. Set `AI4MEDER_BASE_URL`.
2. Set `AI4MEDER_ADMIN_API_KEY`.
3. Run `whoami`.
4. Run `list` or `get` to confirm the target item.
5. Edit the full JSON document, then run `update`.
6. Run `get` again to confirm the final state.
7. Use `delete --yes` only when the operator explicitly wants permanent removal.

## Submit New Content

Use `ai4meder-submission-review/scripts/ai4meder_api.py`.

Guest submission:

```bash
python3 ai4meder-submission-review/scripts/ai4meder_api.py submit payload.json
```

```powershell
python ai4meder-submission-review\scripts\ai4meder_api.py submit payload.json
```

Normal user API-key submission:

```bash
export AI4MEDER_API_KEY="<user-api-key>"
python3 ai4meder-submission-review/scripts/ai4meder_api.py submit payload.json
```

```powershell
$env:AI4MEDER_API_KEY = "<user-api-key>"
python ai4meder-submission-review\scripts\ai4meder_api.py submit payload.json
```

Minimum submission payload:

```json
{
  "submissionType": "paper",
  "title": "Paper title",
  "sourceUrl": "https://example.com/source",
  "summary": "Chinese summary for AI4Meder readers.",
  "directionTags": ["med_imaging"],
  "contactEmail": "submitter@example.com",
  "draftFields": {
    "authors": ["A. Author"],
    "venue": "arXiv",
    "publishedAt": "2026-05-04",
    "category": "Medical imaging",
    "abstract": "Paper abstract."
  }
}
```

Read `ai4meder-submission-review/references/api-contract.md` before building
payloads for datasets, competitions, CFPs, talks, jobs, models, tools, or
templates.

## Review Submissions

Use an admin API key. Always check identity first.

```bash
export AI4MEDER_ADMIN_API_KEY="<admin-api-key>"
python3 ai4meder-submission-review/scripts/ai4meder_api.py whoami --api-key "$AI4MEDER_ADMIN_API_KEY"
python3 ai4meder-submission-review/scripts/ai4meder_api.py list --status pending --expected-admin-email "<admin-email>"
python3 ai4meder-submission-review/scripts/ai4meder_api.py review <submission-id> --status approved --review-note "Source verified." --expected-admin-email "<admin-email>"
```

```powershell
$env:AI4MEDER_ADMIN_API_KEY = "<admin-api-key>"
python ai4meder-submission-review\scripts\ai4meder_api.py whoami --api-key $env:AI4MEDER_ADMIN_API_KEY
python ai4meder-submission-review\scripts\ai4meder_api.py list --status pending --expected-admin-email "<admin-email>"
python ai4meder-submission-review\scripts\ai4meder_api.py review <submission-id> --status approved --review-note "Source verified." --expected-admin-email "<admin-email>"
```

Allowed review statuses:

- `approved`: approves the submission and publishes the matching draft content.
- `needs_edit`: returns the submission for correction and does not publish.
- `rejected`: rejects the submission and does not publish.

## Published Content CRUD

Use `ai4meder-content-crud/scripts/ai4meder_content_api.py` for direct live
content management. This API only operates on `status = "published"` rows.

Check the website skill/API contract:

```bash
python3 ai4meder-content-crud/scripts/ai4meder_content_api.py contract
```

Verify admin identity:

```bash
export AI4MEDER_ADMIN_API_KEY="<admin-api-key>"
python3 ai4meder-content-crud/scripts/ai4meder_content_api.py whoami --expected-admin-email "<admin-email>"
```

```powershell
$env:AI4MEDER_ADMIN_API_KEY = "<admin-api-key>"
python ai4meder-content-crud\scripts\ai4meder_content_api.py whoami --expected-admin-email "<admin-email>"
```

List published items:

```bash
python3 ai4meder-content-crud/scripts/ai4meder_content_api.py list --collection papers --limit 20
python3 ai4meder-content-crud/scripts/ai4meder_content_api.py list --collection datasets --q "MedGemma"
```

Get one published item:

```bash
python3 ai4meder-content-crud/scripts/ai4meder_content_api.py get datasets <id-or-slug>
```

Create one published item:

```bash
python3 ai4meder-content-crud/scripts/ai4meder_content_api.py create datasets item.json --expected-admin-email "<admin-email>"
```

Update one published item:

```bash
python3 ai4meder-content-crud/scripts/ai4meder_content_api.py update datasets <id-or-slug> item.json --expected-admin-email "<admin-email>"
```

Delete one published item. This is real deletion, so `--yes` is required:

```bash
python3 ai4meder-content-crud/scripts/ai4meder_content_api.py delete datasets <id-or-slug> --expected-admin-email "<admin-email>" --yes
```

Read `ai4meder-content-crud/references/content-api-contract.md` before writing
published content payloads.

## Primary Direction IDs

Every submission must include at least one canonical AI4Meder primary direction
ID in `directionTags`. Published content should use the same IDs in
`primaryDirections`.

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

Use detailed labels such as modality, method, disease, dataset, venue, or task
names in `draftFields.keywordTags`, `tags`, `taskTags`, or `modalityTags`.

## Security Rules

- Do not commit API keys, passwords, cookies, database URLs, or local auth state.
- Use `AI4MEDER_API_KEY` only for normal-user submissions.
- Use `AI4MEDER_ADMIN_API_KEY` only for admin review and published-content CRUD.
- Verify admin identity with `whoami` before approval, create, update, or delete.
- Prefer the submission review skill for public contributions; use content CRUD
  only when live published content should change immediately.

## Repository Layout

```text
AI4Meder-Skills/
  ai4meder-submission-review/
    SKILL.md
    agents/openai.yaml
    references/api-contract.md
    scripts/ai4meder_api.py
  ai4meder-content-crud/
    SKILL.md
    agents/openai.yaml
    references/content-api-contract.md
    scripts/ai4meder_content_api.py
```
