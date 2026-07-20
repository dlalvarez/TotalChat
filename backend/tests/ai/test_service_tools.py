from dataclasses import asdict
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai.service_tools import ServiceListRequest, ServiceSearchRequest, ServiceTools
from app.models.tenant import (
    Organization,
    OrganizationPractitioner,
    Practitioner,
    PractitionerService,
    ServiceModality,
)


TABLES = [
    Organization.__table__,
    Practitioner.__table__,
    OrganizationPractitioner.__table__,
    PractitionerService.__table__,
    ServiceModality.__table__,
]


@pytest.fixture
def service_catalog() -> tuple[Session, UUID, UUID, UUID, UUID]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    for table in TABLES:
        table.create(engine)
    session = Session(engine)
    organization = Organization(name="Centro", organization_type="clinic", status="active")
    practitioner = Practitioner(full_name="Dra. Ana", status="active")
    other_practitioner = Practitioner(full_name="Dr. Luis", status="active")
    session.add_all([organization, practitioner, other_practitioner])
    session.flush()
    session.add_all(
        [
            OrganizationPractitioner(
                organization_id=organization.id,
                practitioner_id=practitioner.id,
                status="active",
            ),
            OrganizationPractitioner(
                organization_id=organization.id,
                practitioner_id=other_practitioner.id,
                status="active",
            ),
        ]
    )
    active = PractitionerService(
        organization_id=organization.id,
        practitioner_id=practitioner.id,
        name="Consulta psicológica",
        description="Consulta inicial de psicología",
        duration_minutes=50,
        status="active",
    )
    inactive = PractitionerService(
        organization_id=organization.id,
        practitioner_id=practitioner.id,
        name="Consulta psicológica antigua",
        duration_minutes=40,
        status="inactive",
    )
    other = PractitionerService(
        organization_id=organization.id,
        practitioner_id=other_practitioner.id,
        name="Consulta psicológica infantil",
        duration_minutes=30,
        status="active",
    )
    session.add_all([active, inactive, other])
    session.flush()
    session.add_all(
        [
            ServiceModality(practitioner_service_id=active.id, modality="virtual", status="active"),
            ServiceModality(practitioner_service_id=active.id, modality="in_person", status="inactive"),
            ServiceModality(practitioner_service_id=other.id, modality="in_person", status="active"),
        ]
    )
    session.commit()
    yield session, organization.id, practitioner.id, active.id, inactive.id
    session.close()
    engine.dispose()


def make_tools(session: Session) -> ServiceTools:
    return ServiceTools(tenant_id=uuid4(), session=session)


def test_search_returns_only_active_services(service_catalog) -> None:
    session, _organization_id, _practitioner_id, active_id, inactive_id = service_catalog

    result = make_tools(session).search_services(ServiceSearchRequest(text="psicológica"))

    result_ids = {service.service_id for service in result.services}
    assert active_id in result_ids
    assert inactive_id not in result_ids
    assert len(result.services) == 2


def test_search_respects_practitioner_and_modality_filters(service_catalog) -> None:
    session, _organization_id, practitioner_id, active_id, _inactive_id = service_catalog

    result = make_tools(session).search_services(
        ServiceSearchRequest(text="consulta", practitioner_id=practitioner_id, modality="virtual")
    )

    assert [service.service_id for service in result.services] == [active_id]
    assert result.services[0].modalities == ("virtual",)


def test_list_active_services_respects_organization_filter(service_catalog) -> None:
    session, organization_id, _practitioner_id, _active_id, _inactive_id = service_catalog

    result = make_tools(session).list_active_services(ServiceListRequest(organization_id=organization_id))

    assert len(result.services) == 2


def test_missing_or_inactive_service_detail_returns_none(service_catalog) -> None:
    session, _organization_id, _practitioner_id, active_id, inactive_id = service_catalog
    tools = make_tools(session)

    assert tools.get_service_detail(uuid4()) is None
    assert tools.get_service_detail(inactive_id) is None
    assert tools.get_service_detail(active_id) is not None


def test_tools_exclude_services_when_organization_practitioner_relation_is_inactive(service_catalog) -> None:
    session, organization_id, practitioner_id, active_id, _inactive_id = service_catalog
    relation = session.get(
        OrganizationPractitioner,
        {"organization_id": organization_id, "practitioner_id": practitioner_id},
    )
    assert relation is not None
    relation.status = "inactive"
    session.commit()
    tools = make_tools(session)

    search_result = tools.search_services(ServiceSearchRequest(text="psicológica"))
    list_result = tools.list_active_services()

    assert active_id not in {service.service_id for service in search_result.services}
    assert active_id not in {service.service_id for service in list_result.services}
    assert tools.get_service_detail(active_id) is None


def test_results_exclude_schema_price_and_availability(service_catalog) -> None:
    session, _organization_id, _practitioner_id, active_id, _inactive_id = service_catalog

    detail = make_tools(session).get_service_detail(active_id)

    assert detail is not None
    fields = asdict(detail)
    assert "schema_name" not in fields
    assert "price" not in fields
    assert "availability" not in fields
    assert "slots" not in fields


def test_tools_require_backend_tenant_context_and_local_data_source() -> None:
    with pytest.raises(ValueError, match="tenant-scoped repository or session"):
        ServiceTools(tenant_id=uuid4())

    constructor_fields = ServiceTools.__init__.__annotations__
    assert "schema_name" not in constructor_fields
    assert "llm" not in constructor_fields
    assert "client" not in constructor_fields


def test_separate_tenant_sessions_are_isolated() -> None:
    def tenant_session(service_name: str) -> tuple[Session, object]:
        engine = create_engine("sqlite+pysqlite:///:memory:")
        for table in TABLES:
            table.create(engine)
        session = Session(engine)
        organization = Organization(name="Org", organization_type="clinic", status="active")
        practitioner = Practitioner(full_name="Profesional", status="active")
        service = PractitionerService(
            organization=organization,
            practitioner=practitioner,
            name=service_name,
            duration_minutes=30,
            status="active",
        )
        session.add(service)
        session.flush()
        session.add(
            OrganizationPractitioner(
                organization_id=organization.id,
                practitioner_id=practitioner.id,
                status="active",
            )
        )
        session.commit()
        return session, engine

    first_session, first_engine = tenant_session("Servicio tenant uno")
    second_session, second_engine = tenant_session("Servicio tenant dos")
    try:
        first = make_tools(first_session).list_active_services()
        second = make_tools(second_session).list_active_services()
        assert [item.name for item in first.services] == ["Servicio tenant uno"]
        assert [item.name for item in second.services] == ["Servicio tenant dos"]
    finally:
        first_session.close()
        second_session.close()
        first_engine.dispose()
        second_engine.dispose()
