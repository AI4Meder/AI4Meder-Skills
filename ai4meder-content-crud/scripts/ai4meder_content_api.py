#!/usr/bin/env python3
"""AI4Meder published-content CRUD CLI for admin skill workflows."""

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
COLLECTIONS = {"papers", "datasets", "competitions", "calls", "talks"}


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
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    if body is not None:
        headers["Content-Type"] = "application/json"

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


def require_admin_api_key(args: argparse.Namespace) -> str:
    value = (getattr(args, "api_key", None) or os.environ.get("AI4MEDER_ADMIN_API_KEY") or "").strip()
    if not value:
        raise SystemExit("Missing admin API key. Pass --api-key or set AI4MEDER_ADMIN_API_KEY.")
    return value


def ensure_admin_identity(
    base_url: str,
    api_key: str,
    expected_email: str | None,
) -> JSON:
    identity = request_json("GET", base_url, "/api/profile/api-keys/whoami", api_key=api_key)
    if not isinstance(identity, dict):
        raise SystemExit(f"whoami response must be a JSON object: {identity}")
    user = identity.get("user") or {}
    if not isinstance(user, dict) or user.get("role") != "admin":
        raise SystemExit(f"API key owner is not admin: {user}")
    if expected_email and str(user.get("email", "")).lower() != expected_email.lower():
        raise SystemExit(
            f"API key owner email mismatch: expected {expected_email}, got {user.get('email')}"
        )
    return identity


def validate_collection(value: str) -> str:
    if value not in COLLECTIONS:
        allowed = ", ".join(sorted(COLLECTIONS))
        raise SystemExit(f"collection must be one of: {allowed}.")
    return value


def normalize_content_payload(payload: Any, collection: str, expected_id: str | None = None) -> JSON:
    if not isinstance(payload, dict):
        raise SystemExit("Content payload must be a JSON object.")

    item = dict(payload)
    item_id = str(item.get("id") or "").strip()
    if not item_id:
        raise SystemExit("Content payload must include non-empty id.")
    if expected_id and item_id != expected_id:
        raise SystemExit(f"Payload id mismatch: expected {expected_id}, got {item_id}.")

    item_collection = str(item.get("collection") or collection).strip()
    if item_collection != collection:
        raise SystemExit(
            f"Payload collection mismatch: expected {collection}, got {item_collection}."
        )

    item["collection"] = collection
    item["status"] = "published"
    return item


def quoted(value: str) -> str:
    return urllib.parse.quote(value, safe="")


def cmd_whoami(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    api_key = require_admin_api_key(args)
    dump_json(ensure_admin_identity(base_url, api_key, args.expected_admin_email))


def cmd_contract(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    dump_json(request_json("GET", base_url, "/api/skills", api_key=None))


def cmd_list(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    api_key = require_admin_api_key(args)
    if args.expected_admin_email:
        ensure_admin_identity(base_url, api_key, args.expected_admin_email)
    params: dict[str, str] = {}
    if args.collection:
        params["collection"] = validate_collection(args.collection)
    if args.limit:
        params["limit"] = str(args.limit)
    if args.q:
        params["q"] = args.q
    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    dump_json(request_json("GET", base_url, f"/api/skills/content{query}", api_key=api_key))


def cmd_get(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    api_key = require_admin_api_key(args)
    if args.expected_admin_email:
        ensure_admin_identity(base_url, api_key, args.expected_admin_email)
    collection = validate_collection(args.collection)
    dump_json(
        request_json(
            "GET",
            base_url,
            f"/api/skills/content/{quoted(collection)}/{quoted(args.id_or_slug)}",
            api_key=api_key,
        )
    )


def cmd_create(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    api_key = require_admin_api_key(args)
    ensure_admin_identity(base_url, api_key, args.expected_admin_email)
    collection = validate_collection(args.collection)
    payload = normalize_content_payload(load_json_arg(args.payload), collection)
    response = request_json(
        "POST",
        base_url,
        f"/api/skills/content/{quoted(collection)}",
        body=payload,
        api_key=api_key,
    )
    validate_published_item_response(response)
    dump_json(response)


def cmd_update(args: argparse.Namespace) -> None:
    base_url = normalize_base_url(args.base_url)
    api_key = require_admin_api_key(args)
    ensure_admin_identity(base_url, api_key, args.expected_admin_email)
    collection = validate_collection(args.collection)
    payload = normalize_content_payload(load_json_arg(args.payload), collection)
    response = request_json(
        "PUT",
        base_url,
        f"/api/skills/content/{quoted(collection)}/{quoted(args.id_or_slug)}",
        body=payload,
        api_key=api_key,
    )
    validate_published_item_response(response)
    dump_json(response)


def cmd_delete(args: argparse.Namespace) -> None:
    if not args.yes:
        raise SystemExit("Refusing to delete without --yes.")
    base_url = normalize_base_url(args.base_url)
    api_key = require_admin_api_key(args)
    ensure_admin_identity(base_url, api_key, args.expected_admin_email)
    collection = validate_collection(args.collection)
    dump_json(
        request_json(
            "DELETE",
            base_url,
            f"/api/skills/content/{quoted(collection)}/{quoted(args.id_or_slug)}",
            api_key=api_key,
        )
    )


def validate_published_item_response(response: Any) -> None:
    if not isinstance(response, dict):
        raise SystemExit(f"CRUD response must be a JSON object: {response}")
    item = response.get("item") or {}
    if not isinstance(item, dict) or item.get("status") != "published":
        raise SystemExit(f"CRUD response did not return item.status=published: {response}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI4Meder published-content CRUD API helper")
    parser.add_argument("--base-url", default=None, help=f"AI4Meder site origin, e.g. {PRODUCTION_BASE_URL}")
    sub = parser.add_subparsers(dest="command", required=True)

    whoami = sub.add_parser("whoami", help="Identify and verify an admin API key")
    whoami.add_argument("--api-key")
    whoami.add_argument("--expected-admin-email")
    whoami.set_defaults(func=cmd_whoami)

    contract = sub.add_parser("contract", help="Read the site skill/API contract metadata")
    contract.set_defaults(func=cmd_contract)

    list_cmd = sub.add_parser("list", help="List published content")
    list_cmd.add_argument("--api-key")
    list_cmd.add_argument("--expected-admin-email")
    list_cmd.add_argument("--collection", choices=sorted(COLLECTIONS))
    list_cmd.add_argument("--limit", type=int)
    list_cmd.add_argument("--q")
    list_cmd.set_defaults(func=cmd_list)

    get_cmd = sub.add_parser("get", help="Get one published item by id or slug")
    get_cmd.add_argument("collection", choices=sorted(COLLECTIONS))
    get_cmd.add_argument("id_or_slug")
    get_cmd.add_argument("--api-key")
    get_cmd.add_argument("--expected-admin-email")
    get_cmd.set_defaults(func=cmd_get)

    create = sub.add_parser("create", help="Create one published item from JSON")
    create.add_argument("collection", choices=sorted(COLLECTIONS))
    create.add_argument("payload", help="JSON string, JSON file, or '-' for stdin")
    create.add_argument("--api-key")
    create.add_argument("--expected-admin-email", required=True)
    create.set_defaults(func=cmd_create)

    update = sub.add_parser("update", help="Update one published item from JSON")
    update.add_argument("collection", choices=sorted(COLLECTIONS))
    update.add_argument("id_or_slug")
    update.add_argument("payload", help="JSON string, JSON file, or '-' for stdin")
    update.add_argument("--api-key")
    update.add_argument("--expected-admin-email", required=True)
    update.set_defaults(func=cmd_update)

    delete = sub.add_parser("delete", help="Delete one published item")
    delete.add_argument("collection", choices=sorted(COLLECTIONS))
    delete.add_argument("id_or_slug")
    delete.add_argument("--api-key")
    delete.add_argument("--expected-admin-email", required=True)
    delete.add_argument("--yes", action="store_true")
    delete.set_defaults(func=cmd_delete)

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
