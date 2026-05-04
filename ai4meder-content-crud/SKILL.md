---
name: ai4meder-content-crud
description: Manage already-published AI4Meder website content through the production API with an admin API key. Use when Codex needs to list, get, create, update, or delete published papers, datasets/resources, competitions/deadlines, calls/opportunities, or courses/talks directly, instead of using the public submission review queue.
---

# AI4Meder Content CRUD

Use this skill for direct published-content operations on AI4Meder.

Use `ai4meder-submission-review` instead when the task is guest submission,
normal-user submission, pending-submission review, or contribution-point review.

## Tool

Use `scripts/ai4meder_content_api.py` for deterministic API calls. Set the
target site with `AI4MEDER_BASE_URL` or `--base-url`; production is
`https://www.ai4meder.com`.

Never put API keys in files. Pass an admin key with:

- `AI4MEDER_ADMIN_API_KEY`
- or `--api-key`

Always verify the key owner before mutating content:

```powershell
python scripts/ai4meder_content_api.py --base-url https://www.ai4meder.com whoami --expected-admin-email '<admin-email>'
```

```bash
python3 scripts/ai4meder_content_api.py --base-url https://www.ai4meder.com whoami --expected-admin-email '<admin-email>'
```

## Collections

Allowed collections:

- `papers`
- `datasets`
- `competitions`
- `calls`
- `talks`

The API only operates on `status = "published"` content. `create` and `update`
force `status` to `published`; draft/review workflows belong to the submission
or admin research pipelines.

## Workflow

1. Set `AI4MEDER_BASE_URL` to the site you want to mutate.
2. Set `AI4MEDER_ADMIN_API_KEY` or pass `--api-key`.
3. Run `whoami` and confirm `user.role == admin`.
4. Use `list`, `get`, `create`, `update`, or `delete`.
5. For `delete`, pass `--yes` in the CLI wrapper and make sure the operator
   really wants a permanent removal.

For updates, run `get` first, save or reconstruct the full content item JSON,
edit the necessary fields, and pass the full JSON object to `update`. Do not
send partial patch bodies. Prefer `get` before `update` when the operator gives
a slug rather than a stable id.

## Commands

Read the published API contract exposed by the site:

```bash
python3 scripts/ai4meder_content_api.py contract
```

List published items:

```bash
python3 scripts/ai4meder_content_api.py list --collection papers --limit 20
```

Get one item by `id` or `slug`:

```bash
python3 scripts/ai4meder_content_api.py get papers <id-or-slug>
```

Create one published item from a JSON file:

```bash
python3 scripts/ai4meder_content_api.py create datasets item.json --expected-admin-email '<admin-email>'
```

Update one published item:

```bash
python3 scripts/ai4meder_content_api.py update papers <id-or-slug> item.json --expected-admin-email '<admin-email>'
```

Verify the final state after create or update:

```bash
python3 scripts/ai4meder_content_api.py get papers <id-or-slug>
```

Delete one published item:

```bash
python3 scripts/ai4meder_content_api.py delete calls <id-or-slug> --expected-admin-email '<admin-email>' --yes
```

## Contract

Read `references/content-api-contract.md` before constructing payloads. Payloads
are normal AI4Meder content JSON objects and must match the target collection.

Direct deletion removes the public item. Prefer updating `status` through a
review/admin flow only when the operator explicitly wants archival semantics;
this skill's delete command is for real deletion.
