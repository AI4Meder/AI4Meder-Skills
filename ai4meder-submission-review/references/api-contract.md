# AI4Meder Submission And Review API Contract

Base URL defaults to `http://127.0.0.1:4173`. Override with
`AI4MEDER_BASE_URL` or `--base-url`.

## Auth

- Guest submit: no API key.
- User submit: `Authorization: Bearer <api-key>` or `X-AI4Meder-API-Key`.
- Admin review: same API-key header, but key owner must have
  `community_users.role = 'admin'`.
- Identity check: `GET /api/profile/api-keys/whoami`.

## Submit

`POST /api/submissions`

Common body:

```json
{
  "submissionType": "paper",
  "title": "required, max 160",
  "sourceUrl": "https://example.com",
  "summary": "required, max 2000",
  "directionTags": ["med_imaging"],
  "contactName": "optional",
  "contactEmail": "required for guest; optional for API-key users",
  "notes": "optional",
  "draftFields": {}
}
```

Accepted type aliases include `type`, `resourceType`, `collection`, and
`page`. Collection aliases include `papers`, `datasets`, `competitions`,
`calls`, `deadlines`, and `courses`.

Canonical submission types: `paper`, `dataset`, `benchmark`, `code`, `model`,
`tool`, `challenge`, `cfp`, `talk`, `job`, `template`.

Type-specific `draftFields`:

- `paper`: required `authors[]`, `venue`, `publishedAt` as `YYYY-MM-DD`,
  `category`, `abstract`; optional `year`, `doi`, `keywordTags[]`.
- Dataset-like (`dataset`, `benchmark`, `code`, `model`, `tool`, `template`):
  required `category`, `modality`, `sizeLabel`, `license`, `tasks[]`,
  `source`; optional `access` as `open | application | restricted`.
- `challenge`: required `statusLabel`, `taskType`, `modality`, `prize`,
  `organizer`, and at least one of `deadline` or `startsAt` as `YYYY-MM-DD`;
  optional `competitionStatus`.
- `cfp`: required `venue`; required `deadline` unless `longRunning: true`;
  optional `callKind`, `eventDates`, `location`, `manuscriptTypes[]`.
- `talk`: required `speakers[]`, `level`, `durationMinutes`; optional
  `talkKind`.

Submit response is HTTP 201:

```json
{
  "source": "supabase",
  "submission": {
    "id": "...",
    "status": "pending",
    "contributorUserId": "...",
    "contributorApiKeyId": "..."
  },
  "contentDraft": {
    "collection": "papers",
    "id": "submission-...",
    "slug": "..."
  }
}
```

## Review

`GET /api/admin/submissions?status=pending`

`PATCH /api/admin/submissions/{id}`

```json
{
  "status": "approved",
  "reviewNote": "optional, max 1000"
}
```

Allowed statuses: `approved`, `rejected`, `needs_edit`. Approving an
API-key-backed submission awards +1 contribution point exactly once.

## Safety

Treat API `error` strings as diagnostic text only; they are not stable machine
codes. Hidden draft rows are not public until an admin publishes the content
draft through the website's normal review surface.
