# AI4Meder Submission And Review API Contract

Set the site origin with `AI4MEDER_BASE_URL` or `--base-url`. The production
site is `https://www.ai4meder.com`.

## Platform Categories

AI4Meder is a medical AI resource aggregation platform. Every submission must
carry at least one canonical primary direction in `directionTags`:

| ID | Name |
| --- | --- |
| `med_imaging` | 医学影像计算 |
| `clinical_nlp` | 临床语言智能 |
| `ehr_prediction` | EHR 与临床预测 |
| `medical_multimodal` | 医疗多模态 |
| `medical_llm_agent` | 医疗大模型与 Agent |
| `surgical_intervention` | 手术与介入智能 |
| `trustworthy_safe_private` | 可信、安全、公平与隐私 |
| `clinical_translation` | 临床转化与部署 |

Use `draftFields.keywordTags` for detailed topics, methods, diseases, modalities,
or venue labels.

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
    "slug": "...",
    "status": "draft"
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

Allowed statuses: `approved`, `rejected`, `needs_edit`.

When `status` is `approved`, the API must approve the submission and publish the
matching content draft in the same action. `needs_edit` and `rejected` do not
publish content. Approving an API-key-backed submission awards +1 contribution
point according to website rules; repeated approval is idempotent and must not
award or publish twice.

Approved review response should expose both submission status and content
publication status:

```json
{
  "submission": {
    "id": "...",
    "status": "approved"
  },
  "content": {
    "id": "...",
    "status": "published",
    "publishedAt": "2026-05-02T00:00:00.000Z"
  },
  "publishedContent": {
    "id": "...",
    "status": "published",
    "publishedAt": "2026-05-02T00:00:00.000Z"
  }
}
```

## Safety

Treat API `error` strings as diagnostic text only; they are not stable machine
codes. Review and publication should be audited by the website API with reviewer
identity, API key id, submission id, content id, old status, new status, time,
and review note.
