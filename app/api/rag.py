from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class DocumentCreate(BaseModel):
    title: str
    content: str


class Document(DocumentCreate):
    id: int


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    results: list[Document]
    answer: str


documents: list[Document] = []


@router.post("/documents", response_model=Document)
def create_document(payload: DocumentCreate) -> Document:
    doc = Document(
        id=len(documents) + 1,
        title=payload.title,
        content=payload.content,
    )
    documents.append(doc)
    return doc


@router.post("/query", response_model=QueryResponse)
def query(payload: QueryRequest) -> QueryResponse:
    results = [
        doc for doc in documents
        if payload.query in doc.content or payload.query in doc.title
    ]
    answer = results[0].content if results else "該当する情報が見つかりませんでした。"

    return QueryResponse(
        query=payload.query,
        results=results,
        answer=answer,
    )
