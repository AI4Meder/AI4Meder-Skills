---
name: ai4meder-submission-review
description: Submit and review AI4Meder website content through the local or production API. Use when Codex needs to post AI4Meder papers, datasets, competitions/deadlines, calls/opportunities, courses/talks, or run guest, normal-user API-key, admin API-key submission and review workflows, including skills/scripts integration tests.
---

# AI4Meder Submission Review

Use this skill to interact with AI4Meder's public submission and admin review
APIs from scripts or agent workflows.

## Tool

Use `scripts/ai4meder_api.py` for deterministic API calls. It defaults to
`http://127.0.0.1:4173`; override with `AI4MEDER_BASE_URL` or `--base-url`.

Never put API keys or passwords in files. Pass keys with environment variables:

- `AI4MEDER_API_KEY` for normal user submission.
- `AI4MEDER_ADMIN_API_KEY` for admin review.
- `AI4MEDER_USER_PASSWORD` / `AI4MEDER_ADMIN_PASSWORD` only for local test key
  generation when the user explicitly provides disposable test credentials.

## Workflows

1. For guest submission, call:

   ```powershell
   python scripts/ai4meder_api.py submit payload.json
   ```

2. For normal user API-key submission, call:

   ```powershell
   $env:AI4MEDER_API_KEY='<user-api-key>'
   python scripts/ai4meder_api.py submit payload.json
   ```

3. For admin API-key review, first identify the key owner, then list/review:

   ```powershell
   $env:AI4MEDER_ADMIN_API_KEY='<admin-api-key>'
   python scripts/ai4meder_api.py whoami --api-key $env:AI4MEDER_ADMIN_API_KEY
   python scripts/ai4meder_api.py list --status pending --expected-admin-email '<admin-email>'
   python scripts/ai4meder_api.py review <submission-id> --status approved --review-note 'Verified source.' --expected-admin-email '<admin-email>'
   ```

4. For local end-to-end integration, use:

   ```powershell
   python scripts/ai4meder_api.py integration-test --admin-email '<admin-email>' --user-email '<user-email>'
   ```

   This command can generate temporary API keys by logging in with passwords
   supplied through environment variables, then tests guest submit, user-key
   submit, non-admin review denial, admin pending list, and admin review.

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

Always verify admin identity before review by using the script's
`--expected-admin-email` option or `whoami`. A normal user API key may submit
but must fail admin list/review with HTTP 403. Approving an API-key-backed
submission should award exactly one contribution point.
