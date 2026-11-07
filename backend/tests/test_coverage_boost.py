"""
Additional tests targeting edge cases, filters, and error handlers to achieve >75% coverage.
"""
import pytest
from httpx import AsyncClient
from app.services.storage_service import storage_service
from app.pipelines.orchestrator import pipeline_orchestrator
from app.core.security import verify_password, decode_access_token
from scripts.seed_demo import generate_sample_pdf


@pytest.mark.asyncio
async def test_storage_service_methods(tmp_path):
    path = await storage_service.save_file("test_store.txt", b"Storage Content")
    content = await storage_service.read_file(path)
    assert content == b"Storage Content"

    deleted = await storage_service.delete_file(path)
    assert deleted is True

    # Reading deleted file raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        await storage_service.read_file(path)


@pytest.mark.asyncio
async def test_auth_invalid_credentials_and_tokens(client: AsyncClient):
    # Invalid login credentials
    bad_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@company.com", "password": "wrongpassword"}
    )
    assert bad_login.status_code == 401

    # Unauthorized access to /me
    bad_me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"}
    )
    assert bad_me.status_code == 401


def test_security_utilities():
    assert verify_password("plain", "not-a-valid-hash") is False
    assert decode_access_token("not-a-valid-jwt-token") is None


@pytest.mark.asyncio
async def test_orchestrator_non_existent_document():
    success = await pipeline_orchestrator.process_document("non-existent-id-0000")
    assert success is False


@pytest.mark.asyncio
async def test_document_upload_edge_cases(client: AsyncClient):
    # Empty file
    empty_res = await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("empty.pdf", b"", "application/pdf"))]
    )
    assert empty_res.status_code == 202
    assert len(empty_res.json()["failed"]) == 1

    # Unsupported format
    invalid_res = await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("bad.exe", b"MZbinaryheader", "application/octet-stream"))]
    )
    assert invalid_res.status_code == 202
    assert len(invalid_res.json()["failed"]) == 1


@pytest.mark.asyncio
async def test_document_listing_filters(client: AsyncClient, tmp_path):
    pdf_path = str(tmp_path / "filter_test.pdf")
    generate_sample_pdf(pdf_path)
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("filter_test.pdf", file_bytes, "application/pdf"))]
    )

    # Filter by needs_review
    res1 = await client.get("/api/v1/documents?needs_review=false")
    assert res1.status_code == 200

    # Filter by supplier
    res2 = await client.get("/api/v1/documents?supplier=Acme")
    assert res2.status_code == 200
