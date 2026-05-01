#!/usr/bin/env python3
"""Production AI4Meder submission and review CLI for skill workflows."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


JSON = dict[str, Any]
PRODUCTION_BASE_URL = "https://www.ai4meder.com"
PRIMARY_DIRECTION_IDS = {
    "med_imaging",
    "clinical_nlp",
    "ehr_prediction",
    "medical_multimodal",
    "medical_llm_agent",
    "surgical_intervention",
    "trustworthy_safe_private",
    "clinical_translation",
}


class ApiError(RuntimeError):
    def __init__(self, method: str, url: str, status: int, body: Any):
        super().__init__(f"{method} {url} failed with HTTP {status}: {body}")
        self.method = method
        self.url = url
        self.status = status
        self.body = body


def normalize_base_url(value: str | None) -> str:
    base_url = (value or os.environ.get("AI4MEDER_BASE_URL") or "").strip()
    if not base_url:
        raise SystemExit(
            "Missing AI4Meder site origin. Pass --base-url or set AI4MEDER_BASE_URL "
            f"(production: {PRODUCTION_BASE_URL})."
        )
    return base_url.rstrip("/")


def load_json_arg(value: str) -> Any:
    if value == "-":
        return json.load(sys.stdin)

    path = Path(value)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))

    return json.loads(value)


def dump_json(value: Any) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True))


def request_json(
    method: str,
    base_url: str,
    path: str,
    *,
    body: Any | None = None,
    api_key: str | None = None,
) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    url = f"{base_url}{path}"
    headers = {"Accept": "application/json"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            parsed: Any = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        raise ApiError(method, url, error.code, parsed) from error


def api_key_from_args(args: argparse.Namespace, env_name: str) -> str | None:
    explicit = getattr(args, "api_key", None)
    if explicit:
        return explicit
    return os.environ.get(env_name) or os.environ.get("AI4MEDER_API_KEY")


def require_api_key(args: argparse.Namespace, env_name: str) -> str:
    value = api_key_from_args(args, env_name)
    if not value:
        raise SystemExit(f"Missing API key. Pass --api-key or set {env_name}.")
    return value


def validate_submission_payload(payload: Any) -> None:
    if not isinstance(payload, dict):
        raise SystemExit("Submission payload must be a JSON object.")

    direction_tags = payload.get("directionTags")
    if not isinstance(direction_tags, list) or not direction_tags:
        raise SystemExit(
            "Submission payload must include directionTags with at least one "
            "AI4Meder primary direction ID."
        )

    invalid = [
        tag for tag in direction_tags if not isinstance(tag, str) or tag not in PRIMARY_DIRECTION_IDS
    ]
    if invalid:
        allowed = ", ".join(sorted(PRIMARY_DIRECTION_IDS))
        raise SystemExit(
            "directionTags must contain only AI4Meder primary direction IDs. "
            f"Invalid: {invalid}. Allowed: {allowed}. Put detailed labels in "
            "draftFields.keywordTags."
        )


def cmd_whoami(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    api_key = require_api_key(args, "AI4MEDER_API_KEY")
    dump_json(request_json("GET", base_url, "/api/profile/api-keys/whoami", api_key=api_key))


def cmd_submit(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    payload = load_json_arg(args.payload)
    validate_submission_payload(payload)
    api_key = api_key_from_args(args, "AI4MEDER_API_KEY")
    dump_json(request_json("POST", base_url, "/api/submissions", body=payload, api_key=api_key))


def ensure_admin_identity(
    base_url: str,
    api_key: str,
    expected_email: str | None,
    require_admin: bool,
) -> JSON:
    identity = request_json("GET", base_url, "/api/profile/api-keys/whoami", api_key=api_key)
    user = identity.get("user") or {}
    if require_admin and user.get("role") != "admin":
        raise SystemExit(f"API key owner is not admin: {user}")
    if expected_email and user.get("email", "").lower() != expected_email.lower():
        raise SystemExit(
            f"API key owner email mismatch: expected {expected_email}, got {user.get('email')}"
        )
    return identity


def cmd_list(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    api_key = require_api_key(args, "AI4MEDER_ADMIN_API_KEY")
    ensure_admin_identity(base_url, api_key, args.expected_admin_email, True)
    query = f"?status={urllib.parse.quote(args.status)}" if args.status else ""
    dump_json(request_json("GET", base_url, f"/api/admin/submissions{query}", api_key=api_key))


def validate_approved_review_response(response: Any) -> None:
    if not isinstance(response, dict):
        raise SystemExit("Approved review response must be a JSON object.")

    submission = response.get("submission") or {}
    content = response.get("content") or response.get("publishedContent") or {}
    if submission.get("status") != "approved":
        raise SystemExit(f"Approved review did not return submission.status=approved: {response}")
    if content.get("status") != "published":
        raise SystemExit(f"Approved review did not return content.status=published: {response}")
    if not (content.get("publishedAt") or content.get("published_at")):
        raise SystemExit(f"Approved review did not return publishedAt: {response}")


def cmd_review(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    api_key = require_api_key(args, "AI4MEDER_ADMIN_API_KEY")
    identity = ensure_admin_identity(base_url, api_key, args.expected_admin_email, True)
    body = {"status": args.status}
    if args.review_note:
        body["reviewNote"] = args.review_note
    response = request_json(
        "PATCH",
        base_url,
        f"/api/admin/submissions/{urllib.parse.quote(args.submission_id)}",
        body=body,
        api_key=api_key,
    )
    if args.status == "approved":
        validate_approved_review_response(response)
    dump_json({"reviewer": identity["user"], "response": response})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI4Meder production submission/review API helper")
    parser.add_argument("--base-url", default=None, help=f"AI4Meder site origin, e.g. {PRODUCTION_BASE_URL}")
    sub = parser.add_subparsers(dest="command", required=True)

    whoami = sub.add_parser("whoami", help="Identify an API key owner")
    whoami.add_argument("--api-key")
    whoami.set_defaults(func=cmd_whoami)

    submit = sub.add_parser("submit", help="Submit content as guest or API-key user")
    submit.add_argument("payload", help="JSON string, JSON file, or '-' for stdin")
    submit.add_argument("--api-key")
    submit.set_defaults(func=cmd_submit)

    list_cmd = sub.add_parser("list", help="List submissions as an admin API-key reviewer")
    list_cmd.add_argument("--api-key")
    list_cmd.add_argument("--expected-admin-email")
    list_cmd.add_argument("--status", choices=["pending", "approved", "rejected", "needs_edit"])
    list_cmd.set_defaults(func=cmd_list)

    review = sub.add_parser("review", help="Review one submission as an admin API-key reviewer")
    review.add_argument("submission_id")
    review.add_argument("--api-key")
    review.add_argument("--expected-admin-email")
    review.add_argument("--status", required=True, choices=["approved", "rejected", "needs_edit"])
    review.add_argument("--review-note")
    review.set_defaults(func=cmd_review)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
        return 0
    except ApiError as error:
        print(str(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
