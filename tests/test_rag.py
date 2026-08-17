from app.api.rag import (
    DocumentCreate,
    QueryRequest,
    create_document,
    documents,
    query,
)


def setup_function() -> None:
    documents.clear()


def test_create_document() -> None:
    document = create_document(
        DocumentCreate(
            title="キッチン改修",
            content="キッチン交換と内装工事を実施しました",
        )
    )

    assert document.id == 1
    assert document.title == "キッチン改修"
    assert document.content == "キッチン交換と内装工事を実施しました"


def test_query_returns_matching_document() -> None:
    create_document(
        DocumentCreate(
            title="キッチン改修",
            content="キッチン交換と内装工事を実施しました",
        )
    )

    response = query(QueryRequest(query="キッチン"))

    assert len(response.results) == 1
    assert response.results[0].id == 1
    assert response.answer == "キッチン交換と内装工事を実施しました"


def test_query_returns_empty_result_when_not_found() -> None:
    response = query(QueryRequest(query="浴室"))

    assert response.results == []
    assert response.answer == "該当する情報が見つかりませんでした。"
