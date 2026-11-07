"""
Integration tests for FastAPI REST API endpoints.
"""
import pytest
from httpx import AsyncClient
from scripts.seed_demo import generate_sample_pdf, generate_sample_excel


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_auth_registration_and_login(client: AsyncClient):
    # 1. Register
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@company.com", "password": "securepassword123"}
    )
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["email"] == "newuser@company.com"

    # 2. Duplicate registration fails
    dup_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@company.com", "password": "securepassword123"}
    )
    assert dup_res.status_code == 400

    # 3. Login
    login_res = await client.post(
        "/api/v1/auth/login",
        json={"email": "newuser@company.com", "password": "securepassword123"}
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"

    # 4. Access protected /me
    me_res = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login_data['access_token']}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "newuser@company.com"


@pytest.mark.asyncio
async def test_document_upload_and_pipeline(client: AsyncClient, tmp_path):
    pdf_path = str(tmp_path / "upload_test.pdf")
    generate_sample_pdf(pdf_path)

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    res = await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("upload_test.pdf", file_bytes, "application/pdf"))]
    )
    assert res.status_code == 202
    data = res.json()
    assert len(data["uploaded"]) == 1
    doc_id = data["uploaded"][0]["id"]
    assert doc_id is not None

    # Check status endpoint
    status_res = await client.get(f"/api/v1/documents/{doc_id}/status")
    assert status_res.status_code == 200
    assert status_res.json()["status"] in ["queued", "processing", "completed"]

    # Check document details
    detail_res = await client.get(f"/api/v1/documents/{doc_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["filename"] == "upload_test.pdf"
    assert detail_data["extracted_data"] is not None
    assert detail_data["extracted_data"]["invoice_number"] == "INV-2026-0042"


@pytest.mark.asyncio
async def test_document_listing_and_filtering(client: AsyncClient, tmp_path):
    pdf_path = str(tmp_path / "list_test.pdf")
    generate_sample_pdf(pdf_path)
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("list_test.pdf", file_bytes, "application/pdf"))]
    )

    list_res = await client.get("/api/v1/documents?page=1&page_size=10")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert len(list_data["items"]) >= 1

    # Filter by status
    filtered_res = await client.get("/api/v1/documents?status=completed")
    assert filtered_res.status_code == 200


@pytest.mark.asyncio
async def test_document_manual_correction(client: AsyncClient, tmp_path):
    pdf_path = str(tmp_path / "correction_test.pdf")
    generate_sample_pdf(pdf_path)

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    res = await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("correction_test.pdf", file_bytes, "application/pdf"))]
    )
    doc_id = res.json()["uploaded"][0]["id"]

    # Perform manual correction
    patch_res = await client.patch(
        f"/api/v1/documents/{doc_id}/extracted",
        json={"invoice_number": "INV-MODIFIED-999", "notes": "Manually verified by accountant"}
    )
    assert patch_res.status_code == 200
    updated_data = patch_res.json()
    assert updated_data["extracted_data"]["invoice_number"] == "INV-MODIFIED-999"
    assert len(updated_data["correction_history"]) >= 1


@pytest.mark.asyncio
async def test_reprocess_endpoint(client: AsyncClient, tmp_path):
    pdf_path = str(tmp_path / "reprocess_test.pdf")
    generate_sample_pdf(pdf_path)
    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    res = await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("reprocess_test.pdf", file_bytes, "application/pdf"))]
    )
    doc_id = res.json()["uploaded"][0]["id"]

    reprocess_res = await client.post(f"/api/v1/documents/{doc_id}/reprocess")
    assert reprocess_res.status_code == 200
    assert reprocess_res.json()["id"] == doc_id


@pytest.mark.asyncio
async def test_cross_verify_api(client: AsyncClient, tmp_path):
    pdf_path = str(tmp_path / "doc_1.pdf")
    generate_sample_pdf(pdf_path)
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    res1 = await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("doc_1.pdf", pdf_bytes, "application/pdf"))]
    )
    doc1_id = res1.json()["uploaded"][0]["id"]

    res2 = await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("doc_2.pdf", pdf_bytes, "application/pdf"))]
    )
    doc2_id = res2.json()["uploaded"][0]["id"]

    cross_res = await client.post(
        "/api/v1/documents/cross-verify",
        json={"primary_document_id": doc1_id, "reference_document_id": doc2_id}
    )
    assert cross_res.status_code == 200
    data = cross_res.json()
    assert data["is_match"] is True


@pytest.mark.asyncio
async def test_search_endpoint(client: AsyncClient, tmp_path):
    pdf_path = str(tmp_path / "searchable_invoice.pdf")
    generate_sample_pdf(pdf_path)

    with open(pdf_path, "rb") as f:
        file_bytes = f.read()

    await client.post(
        "/api/v1/documents/upload",
        files=[("files", ("searchable_invoice.pdf", file_bytes, "application/pdf"))]
    )

    # Search by keyword
    search_res = await client.get("/api/v1/search?q=Acme&mode=keyword")
    assert search_res.status_code == 200
    data = search_res.json()
    assert data["total"] >= 1
    assert any("searchable_invoice.pdf" in r["document"]["filename"] for r in data["results"])


@pytest.mark.asyncio
async def test_404_not_found_document(client: AsyncClient):
    res = await client.get("/api/v1/documents/non-existent-id")
    assert res.status_code == 404
