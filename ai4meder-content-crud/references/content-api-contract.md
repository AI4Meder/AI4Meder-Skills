# AI4Meder Published Content CRUD API

This contract is for admin-owned API keys only. It manages public
`status = "published"` content and bypasses the public submission queue.

## Auth

Send one of:

```text
Authorization: Bearer <admin-api-key>
X-AI4Meder-API-Key: <admin-api-key>
```

Verify identity first:

```text
GET /api/profile/api-keys/whoami
```

Expected `user.role` is `admin`.

## Contract Metadata

```text
GET /api/skills
```

Returns available AI4Meder skill/API surfaces and supported collections.

## Collections

- `papers`
- `datasets`
- `competitions`
- `calls`
- `talks`

## CLI Sequence

Use the bundled helper instead of hand-writing HTTP calls when possible:

```bash
export AI4MEDER_BASE_URL="https://www.ai4meder.com"
export AI4MEDER_ADMIN_API_KEY="<admin-api-key>"
python3 scripts/ai4meder_content_api.py whoami --expected-admin-email "<admin-email>"
python3 scripts/ai4meder_content_api.py list --collection datasets --limit 20
python3 scripts/ai4meder_content_api.py get datasets <id-or-slug>
python3 scripts/ai4meder_content_api.py update datasets <id-or-slug> item.json --expected-admin-email "<admin-email>"
```

PowerShell:

```powershell
$env:AI4MEDER_BASE_URL = "https://www.ai4meder.com"
$env:AI4MEDER_ADMIN_API_KEY = "<admin-api-key>"
python scripts\ai4meder_content_api.py whoami --expected-admin-email "<admin-email>"
python scripts\ai4meder_content_api.py list --collection datasets --limit 20
python scripts\ai4meder_content_api.py get datasets <id-or-slug>
python scripts\ai4meder_content_api.py update datasets <id-or-slug> item.json --expected-admin-email "<admin-email>"
```

Delete requires explicit confirmation in the helper:

```bash
python3 scripts/ai4meder_content_api.py delete datasets <id-or-slug> --expected-admin-email "<admin-email>" --yes
```

## List

```text
GET /api/skills/content
GET /api/skills/content?collection=papers&limit=20&q=foundation
```

Response:

```json
{
  "source": "supabase",
  "status": "published",
  "collection": "papers",
  "content": []
}
```

When `collection` is omitted, `content` is an object keyed by collection.

## Get

```text
GET /api/skills/content/{collection}/{idOrSlug}
```

Response:

```json
{
  "source": "supabase",
  "status": "published",
  "collection": "papers",
  "item": {}
}
```

## Create

```text
POST /api/skills/content/{collection}
Content-Type: application/json
```

Body is the content item JSON object. `collection` must match the route. The
server stores it as `status = "published"` even if the body contains another
status.

## Update

```text
PUT /api/skills/content/{collection}/{idOrSlug}
Content-Type: application/json
```

Body is the full replacement content item JSON object. `item.id` must match the
existing item's canonical id. Use `GET` first if the route target is a slug.
The server stores it as `status = "published"`.

## Delete

```text
DELETE /api/skills/content/{collection}/{idOrSlug}
```

Deletes the published content row. This is real deletion, not archive. Use only
when the operator explicitly asked to remove the item.

## Minimal Payload Shapes

Common fields for all collections:

```json
{
  "id": "stable-id",
  "slug": "stable-slug",
  "collection": "papers",
  "status": "published",
  "title": "Title",
  "summary": "Chinese summary",
  "tags": ["medical AI"],
  "primaryDirections": ["med_imaging"],
  "links": [{ "label": "Source", "href": "https://example.com", "kind": "external" }],
  "metrics": [],
  "surfaces": [],
  "displayOrder": 100,
  "updatedAt": "2026-05-04"
}
```

Papers add:

```json
{
  "authors": ["A. Author"],
  "authorLine": "A. Author",
  "venue": "arXiv",
  "publishedAt": "2026-05-04",
  "year": 2026,
  "category": "Medical imaging",
  "abstract": "Abstract"
}
```

Datasets/resources add:

```json
{
  "resourceType": "dataset",
  "modality": "CT",
  "category": "Segmentation",
  "sizeLabel": "100 cases",
  "license": "research use",
  "access": "open",
  "tasks": ["segmentation"],
  "source": "Official source"
}
```

Competitions add:

```json
{
  "statusLabel": "Open",
  "competitionStatus": "ongoing",
  "taskType": "Segmentation",
  "modality": "MRI",
  "prize": "TBA",
  "deadline": "2026-08-01",
  "deadlineTimezone": "Asia/Shanghai",
  "organizer": "Organizer"
}
```

Calls add:

```json
{
  "kind": "conference-cfp",
  "venue": "Conference",
  "deadline": "2026-08-01",
  "deadlineTimezone": "Asia/Shanghai",
  "eventDates": "2026-10-01 to 2026-10-03",
  "location": "City",
  "manuscriptTypes": ["full paper"]
}
```

Talks add:

```json
{
  "kind": "talk",
  "speakers": [{ "name": "Speaker" }],
  "level": "advanced",
  "durationMinutes": 60
}
```
