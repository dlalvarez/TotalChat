from app.tenancy.migrate_existing_tenants import PendingTenantMigration, apply_pending_migrations_to_schema, discover_tenant_schemas

class FakeInspector:
    def __init__(self, _connection): pass
    def get_schema_names(self): return ["public", "tenant_alpha", "tenant_beta", "bad-name", "information_schema"]

class RecordingConnection:
    def __init__(self): self.sql=[]; self.versions=set()
    def execute(self, statement, params=None):
        text=str(statement); self.sql.append(text)
        if "SELECT 1" in text:
            version = params["version"]
            return Result(version in self.versions)
        if "VALUES ('007_booking_notes')" in text:
            self.versions.add("007_booking_notes")
        if "VALUES ('008_virtual_appointment_links')" in text:
            self.versions.add("008_virtual_appointment_links")
        return Result(False)

class Result:
    def __init__(self, has): self.has=has
    def first(self): return (1,) if self.has else None

def test_discover_tenant_schemas_filters_invalid(monkeypatch):
    monkeypatch.setattr("app.tenancy.migrate_existing_tenants.inspect", lambda connection: FakeInspector(connection))
    assert discover_tenant_schemas(object()) == ["tenant_alpha", "tenant_beta"]

def test_apply_pending_booking_notes_migration_is_idempotent():
    connection=RecordingConnection()
    applied = apply_pending_migrations_to_schema(connection, "tenant_alpha", (PendingTenantMigration("007_booking_notes", lambda conn, schema: conn.execute("VALUES ('007_booking_notes')")),))
    again = apply_pending_migrations_to_schema(connection, "tenant_alpha", (PendingTenantMigration("007_booking_notes", lambda conn, schema: conn.execute("VALUES ('007_booking_notes')")),))
    assert applied == ["007_booking_notes"]
    assert again == []

def test_apply_pending_rejects_invalid_schema():
    try:
        apply_pending_migrations_to_schema(RecordingConnection(), "public", ())
    except ValueError as exc:
        assert "Invalid tenant schema name" in str(exc)
    else:
        raise AssertionError("expected invalid schema rejection")
