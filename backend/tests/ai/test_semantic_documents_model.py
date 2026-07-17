from app.ai.semantic_documents import SemanticDocument, Vector


def test_semantic_document_has_expected_fields():
    columns = SemanticDocument.__table__.columns
    for name in ["id", "source_type", "source_id", "title", "content", "embedding", "metadata", "status", "created_at", "updated_at"]:
        assert name in columns
    assert isinstance(columns["embedding"].type, Vector)


def test_semantic_document_does_not_include_schema_name():
    assert "schema_name" not in SemanticDocument.__table__.columns
    document = SemanticDocument(source_type="service", title="Doc", content="Content")
    assert "schema_name" not in document.__dict__
