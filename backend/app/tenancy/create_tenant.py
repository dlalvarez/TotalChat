from __future__ import annotations

import argparse
import sys

from app.db.session import get_session_factory
from app.tenancy.provisioning import TenantProvisioningError, TenantProvisioningService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Provision an active TotalChat tenant and its PostgreSQL schema.")
    parser.add_argument("--name", required=True, help="Human-readable tenant name.")
    parser.add_argument("--slug", required=True, help="Tenant slug used for public.tenants lookup and internal schema derivation.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        session_factory = get_session_factory()
        with session_factory() as session:
            result = TenantProvisioningService(session).provision_tenant_idempotently(name=args.name, slug=args.slug)
            session.commit()
    except (TenantProvisioningError, ValueError) as exc:
        print(f"Tenant provisioning failed: {exc}", file=sys.stderr)
        return 2

    print("Tenant provisioning completed")
    print(f"tenant_id={result.tenant_id}")
    print(f"slug={result.slug}")
    print(f"status={result.status}")
    print(f"actions={','.join(result.actions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
