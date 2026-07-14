from __future__ import annotations

import argparse
import getpass
import os
import sys
from uuid import UUID

from app.auth.bootstrap import ALLOWED_ADMIN_ROLES, AdminBootstrapError, AdminUserBootstrapService
from app.db.session import get_session_factory

PASSWORD_ENV_VAR = "TOTALCHAT_BOOTSTRAP_ADMIN_PASSWORD"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Bootstrap a tenant administrative user without exposing public endpoints.")
    tenant = parser.add_mutually_exclusive_group(required=True)
    tenant.add_argument("--tenant-slug", help="Active tenant slug in public.tenants.")
    tenant.add_argument("--tenant-id", type=UUID, help="Active tenant UUID in public.tenants.")
    parser.add_argument("--email", required=True, help="Administrative user email.")
    parser.add_argument("--full-name", required=True, help="Administrative user full name.")
    parser.add_argument("--role", choices=sorted(ALLOWED_ADMIN_ROLES), default="owner", help="Tenant role to assign; defaults to owner.")
    return parser


def read_password() -> str:
    env_password = os.environ.get(PASSWORD_ENV_VAR)
    if env_password:
        return env_password
    first = getpass.getpass("Admin password: ")
    second = getpass.getpass("Confirm admin password: ")
    if first != second:
        raise AdminBootstrapError("Passwords do not match.")
    return first


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        password = read_password()
        session_factory = get_session_factory()
        with session_factory() as session:
            result = AdminUserBootstrapService(session).bootstrap_admin_user(
                tenant_slug=args.tenant_slug,
                tenant_id=args.tenant_id,
                email=args.email,
                full_name=args.full_name,
                password=password,
                role=args.role,
            )
    except AdminBootstrapError as exc:
        print(f"Admin bootstrap failed: {exc}", file=sys.stderr)
        return 2

    actions: list[str] = []
    if result.user_created:
        actions.append("user_created")
    if result.user_updated:
        actions.append("user_updated")
    if result.user_reactivated:
        actions.append("user_reactivated")
    if result.link_created:
        actions.append("tenant_link_created")
    if result.link_reactivated:
        actions.append("tenant_link_reactivated")
    if result.link_updated:
        actions.append("tenant_link_updated")
    if not actions:
        actions.append("no_changes")

    print("Admin user bootstrap completed")
    print(f"email={result.email}")
    print(f"tenant={result.tenant_slug} ({result.tenant_name})")
    print(f"role={result.role}")
    print(f"actions={','.join(actions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
