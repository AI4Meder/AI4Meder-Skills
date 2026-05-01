#!/usr/bin/env python3
"""AI4Meder submission and review CLI for skill workflows."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "http://127.0.0.1:4173"
JSON = dict[str, Any]


class ApiError(RuntimeError):
    def __init__(self, method: str, url: str, status: int, body: Any):
        super().__init__(f"{method} {url} failed with HTTP {status}: {body}")
        self.method = method
        self.url = url
        self.status = status
        self.body = body


def normalize_base_url(value: str | None) -> str:
    base_url = (value or os.environ.get("AI4MEDER_BASE_URL") or DEFAULT_BASE_URL).strip()
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
    opener: urllib.request.OpenerDirector | None = None,
) -> Any:
    data = None if body is None else json.dumps(body).encode("utf-8")
    url = f"{base_url}{path}"
    headers = {
        "Accept": "application/json",
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    opener = opener or urllib.request.build_opener()
    try:
        with opener.open(request, timeout=60) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw.strip() else None
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        try:
            parsed: Any = json.loads(raw)
        except json.JSONDecodeError:
            parsed = raw
        raise ApiError(method, url, error.code, parsed) from error


def cookie_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))


def create_api_key_via_login(
    base_url: str,
    email: str,
    password: str,
    name: str,
) -> JSON:
    opener = cookie_opener()
    csrf = request_json("GET", base_url, "/api/auth/csrf", opener=opener)
    csrf_token = csrf.get("csrfToken")
    if not csrf_token:
        raise RuntimeError("NextAuth CSRF token was not returned.")

    form = urllib.parse.urlencode(
        {
            "identifier": email,
            "password": password,
            "csrfToken": csrf_token,
            "json": "true",
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/api/auth/callback/credentials?",
        data=form,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with opener.open(request, timeout=60) as response:
            response.read()
    except urllib.error.HTTPError as error:
        raw = error.read().decode("utf-8", errors="replace")
        raise ApiError("POST", request.full_url, error.code, raw) from error

    return request_json(
        "POST",
        base_url,
        "/api/profile/api-keys",
        body={"name": name},
        opener=opener,
    )


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


def cmd_whoami(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    api_key = require_api_key(args, "AI4MEDER_API_KEY")
    dump_json(request_json("GET", base_url, "/api/profile/api-keys/whoami", api_key=api_key))


def cmd_create_key(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    password = args.password or os.environ.get(args.password_env)
    if not password:
        raise SystemExit(f"Missing password. Pass --password or set {args.password_env}.")
    response = create_api_key_via_login(base_url, args.email, password, args.name)
    dump_json(response)


def cmd_submit(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    payload = load_json_arg(args.payload)
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
    dump_json({"reviewer": identity["user"], "response": response})


def sample_payload(kind: str, suffix: str) -> JSON:
    common = {
        "title": f"AI4Meder skill integration {kind} {suffix}",
        "sourceUrl": f"https://example.com/ai4meder-skill/{kind}/{suffix}",
        "summary": f"Integration test submission for {kind}.",
        "directionTags": ["med_imaging"],
        "contactName": "AI4Meder Skill Test",
        "contactEmail": "skill-test@example.com",
        "notes": "Generated by ai4meder-submission-review integration-test.",
    }
    if kind == "paper":
        return {
            **common,
            "submissionType": "paper",
            "draftFields": {
                "authors": ["AI4Meder Skill"],
                "venue": "Integration Test",
                "publishedAt": "2026-05-02",
                "category": "Medical imaging",
                "abstract": "Integration test abstract.",
                "keywordTags": ["integration-test"],
            },
        }
    if kind == "dataset":
        return {
            **common,
            "submissionType": "dataset",
            "draftFields": {
                "category": "Medical imaging",
                "modality": "CT",
                "sizeLabel": "Test fixture",
                "license": "Test-only",
                "access": "restricted",
                "tasks": ["segmentation"],
                "source": "AI4Meder skill integration",
                "keywordTags": ["integration-test"],
            },
        }
    if kind == "challenge":
        return {
            **common,
            "submissionType": "challenge",
            "draftFields": {
                "statusLabel": "Integration",
                "competitionStatus": "upcoming",
                "taskType": "Segmentation",
                "modality": "CT",
                "prize": "Test-only",
                "organizer": "AI4Meder skill integration",
                "deadline": "2026-12-31",
                "keywordTags": ["integration-test"],
            },
        }
    if kind == "cfp":
        return {
            **common,
            "submissionType": "cfp",
            "draftFields": {
                "callKind": "conference-cfp",
                "venue": "AI4Meder Integration CFP",
                "deadline": "2026-12-31",
                "eventDates": "2027-01-15 to 2027-01-16",
                "location": "Online",
                "manuscriptTypes": ["full paper"],
                "keywordTags": ["integration-test"],
            },
        }
    if kind == "talk":
        return {
            **common,
            "submissionType": "talk",
            "draftFields": {
                "talkKind": "short-course",
                "speakers": ["AI4Meder Skill"],
                "level": "introductory",
                "durationMinutes": 45,
                "keywordTags": ["integration-test"],
            },
        }
    raise SystemExit(f"Unsupported sample kind: {kind}")


def cmd_integration_test(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    suffix = str(int(time.time()))
    results: JSON = {"baseUrl": base_url, "suffix": suffix}

    admin_key = args.admin_api_key or os.environ.get("AI4MEDER_ADMIN_API_KEY")
    if not admin_key and args.admin_email:
        admin_password = args.admin_password or os.environ.get(args.admin_password_env)
        if not admin_password:
            raise SystemExit(
                f"Missing admin password. Pass --admin-password or set {args.admin_password_env}."
            )
        created = create_api_key_via_login(
            base_url,
            args.admin_email,
            admin_password,
            f"skill-admin-{suffix}",
        )
        admin_key = created["apiKey"]
        results["adminKeyPreview"] = created["key"]["keyPreview"]
    if not admin_key:
        raise SystemExit("Missing admin API key or admin login credentials.")

    user_key = args.user_api_key or os.environ.get("AI4MEDER_USER_API_KEY")
    if not user_key and args.user_email:
        user_password = args.user_password or os.environ.get(args.user_password_env)
        if not user_password:
            raise SystemExit(
                f"Missing user password. Pass --user-password or set {args.user_password_env}."
            )
        created = create_api_key_via_login(
            base_url,
            args.user_email,
            user_password,
            f"skill-user-{suffix}",
        )
        user_key = created["apiKey"]
        results["userKeyPreview"] = created["key"]["keyPreview"]

    admin_identity = ensure_admin_identity(base_url, admin_key, args.admin_email, True)
    results["adminIdentity"] = admin_identity["user"]

    if user_key:
        user_identity = ensure_admin_identity(base_url, user_key, args.user_email, False)
        results["userIdentity"] = user_identity["user"]

    guest_submission = request_json(
        "POST",
        base_url,
        "/api/submissions",
        body=sample_payload("paper", f"guest-{suffix}"),
    )
    results["guestSubmission"] = {
        "id": guest_submission["submission"]["id"],
        "status": guest_submission["submission"]["status"],
        "contentDraft": guest_submission.get("contentDraft"),
    }

    if user_key:
        user_submission = request_json(
            "POST",
            base_url,
            "/api/submissions",
            body=sample_payload("dataset", f"user-{suffix}"),
            api_key=user_key,
        )
        results["userSubmission"] = {
            "id": user_submission["submission"]["id"],
            "status": user_submission["submission"]["status"],
            "contributorUserId": user_submission["submission"].get("contributorUserId"),
            "contributorApiKeyId": user_submission["submission"].get("contributorApiKeyId"),
        }
    else:
        user_submission = None

    try:
        request_json(
            "GET",
            base_url,
            "/api/admin/submissions?status=pending",
            api_key=user_key,
        )
        results["nonAdminReviewDenied"] = False
    except ApiError as error:
        results["nonAdminReviewDenied"] = error.status == 403
        results["nonAdminReviewStatus"] = error.status

    pending = request_json(
        "GET",
        base_url,
        "/api/admin/submissions?status=pending",
        api_key=admin_key,
    )
    ids = {item["id"] for item in pending.get("submissions", [])}
    expected = [guest_submission["submission"]["id"]]
    if user_submission:
        expected.append(user_submission["submission"]["id"])
    missing = [item for item in expected if item not in ids]
    if missing:
        raise RuntimeError(f"Submitted IDs are missing from admin pending list: {missing}")
    results["adminPendingContainsSubmitted"] = True

    reviewed_guest = request_json(
        "PATCH",
        base_url,
        f"/api/admin/submissions/{guest_submission['submission']['id']}",
        body={"status": "needs_edit", "reviewNote": "Integration test guest review."},
        api_key=admin_key,
    )
    results["guestReview"] = {
        "status": reviewed_guest["submission"]["status"],
        "reviewerUserId": reviewed_guest["submission"].get("reviewerUserId"),
        "reviewerApiKeyId": reviewed_guest["submission"].get("reviewerApiKeyId"),
    }

    if user_submission:
        reviewed_user = request_json(
            "PATCH",
            base_url,
            f"/api/admin/submissions/{user_submission['submission']['id']}",
            body={"status": "approved", "reviewNote": "Integration test API-key approval."},
            api_key=admin_key,
        )
        second_review = request_json(
            "PATCH",
            base_url,
            f"/api/admin/submissions/{user_submission['submission']['id']}",
            body={"status": "approved", "reviewNote": "Integration test repeat approval."},
            api_key=admin_key,
        )
        results["userReview"] = {
            "status": reviewed_user["submission"]["status"],
            "contributionAwardedAt": reviewed_user["submission"].get("contributionAwardedAt")
            or second_review["submission"].get("contributionAwardedAt"),
            "reviewerUserId": reviewed_user["submission"].get("reviewerUserId"),
            "reviewerApiKeyId": reviewed_user["submission"].get("reviewerApiKeyId"),
        }

    dump_json(results)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI4Meder submission/review API helper")
    parser.add_argument("--base-url", default=None, help="AI4Meder site origin")
    sub = parser.add_subparsers(dest="command", required=True)

    whoami = sub.add_parser("whoami", help="Identify an API key owner")
    whoami.add_argument("--api-key")
    whoami.set_defaults(func=cmd_whoami)

    create_key = sub.add_parser("create-key", help="Create an API key via credentials login")
    create_key.add_argument("--email", required=True)
    create_key.add_argument("--password")
    create_key.add_argument("--password-env", default="AI4MEDER_PASSWORD")
    create_key.add_argument("--name", default="skill-generated")
    create_key.set_defaults(func=cmd_create_key)

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

    integration = sub.add_parser("integration-test", help="Run guest/user/admin end-to-end checks")
    integration.add_argument("--admin-api-key")
    integration.add_argument("--admin-email")
    integration.add_argument("--admin-password")
    integration.add_argument("--admin-password-env", default="AI4MEDER_ADMIN_PASSWORD")
    integration.add_argument("--user-api-key")
    integration.add_argument("--user-email")
    integration.add_argument("--user-password")
    integration.add_argument("--user-password-env", default="AI4MEDER_USER_PASSWORD")
    integration.set_defaults(func=cmd_integration_test)

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
