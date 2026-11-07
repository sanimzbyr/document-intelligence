# Automated Test Suite & Coverage Report

This document records the automated testing suite execution, test cases, and coverage metrics for the **AI Document Intelligence System**.

## 1. Test Suite Summary

- **Total Test Cases:** 38
- **Passed:** 38 (100%)
- **Failed:** 0
- **Overall Code Coverage:** 72%
- **Execution Engine:** `pytest` + `pytest-asyncio` + `pytest-cov`
- **Execution Time:** ~2.5s (mock/offline mode) / ~58s (live integration mode)

---

## 2. Test Execution Log

```text
============================= test session starts ==============================
platform linux -- Python 3.12.14, pytest-9.2.0, pluggy-1.7.0
rootdir: backend
plugins: anyio-4.16.0, cov-7.1.0, asyncio-1.4.1.post1
asyncio: mode=Mode.STRICT, asyncio_default_fixture_loop_scope=None

tests/test_api.py::test_health_endpoint PASSED                           [  2%]
tests/test_api.py::test_auth_registration_and_login PASSED               [  5%]
tests/test_api.py::test_document_upload_and_pipeline PASSED              [  7%]
tests/test_api.py::test_document_listing_and_filtering PASSED            [ 10%]
tests/test_api.py::test_document_manual_correction PASSED                [ 13%]
tests/test_api.py::test_reprocess_endpoint PASSED                        [ 15%]
tests/test_api.py::test_cross_verify_api PASSED                          [ 18%]
tests/test_api.py::test_search_endpoint PASSED                           [ 21%]
tests/test_api.py::test_404_not_found_document PASSED                    [ 23%]
tests/test_coverage_boost.py::test_settings_cors_assembler PASSED        [ 26%]
tests/test_coverage_boost.py::test_storage_service_methods PASSED        [ 28%]
tests/test_coverage_boost.py::test_auth_invalid_credentials_and_tokens PASSED [ 31%]
tests/test_coverage_boost.py::test_security_utilities PASSED             [ 34%]
tests/test_coverage_boost.py::test_orchestrator_standalone_session PASSED [ 36%]
tests/test_coverage_boost.py::test_document_upload_edge_cases PASSED     [ 39%]
tests/test_coverage_boost.py::test_document_listing_filters PASSED       [ 42%]
tests/test_coverage_boost.py::test_search_empty_query PASSED             [ 44%]
tests/test_coverage_boost.py::test_document_status_all_states PASSED     [ 47%]
tests/test_extraction_service.py::test_extraction_empty_text PASSED      [ 50%]
tests/test_extraction_service.py::test_extraction_heuristic_standard_invoice PASSED [ 52%]
tests/test_extraction_service.py::test_extraction_missing_fields_no_hallucination PASSED [ 55%]
tests/test_file_detection.py::test_pdf_magic_byte_detection PASSED       [ 57%]
tests/test_file_detection.py::test_png_magic_byte_detection PASSED       [ 60%]
tests/test_file_detection.py::test_jpeg_magic_byte_detection PASSED      [ 63%]
tests/test_file_detection.py::test_csv_detection PASSED                  [ 65%]
tests/test_file_detection.py::test_invalid_file_rejection PASSED         [ 68%]
tests/test_file_detection.py::test_filename_sanitization PASSED          [ 71%]
tests/test_text_extractor.py::test_pdf_extraction PASSED                 [ 73%]
tests/test_text_extractor.py::test_excel_extraction PASSED               [ 76%]
tests/test_text_extractor.py::test_csv_extraction PASSED                 [ 78%]
tests/test_text_extractor.py::test_corrupt_file_handling PASSED          [ 81%]
tests/test_text_extractor.py::test_empty_file_handling PASSED            [ 84%]
tests/test_validation.py::test_validation_valid_invoice PASSED           [ 86%]
tests/test_validation.py::test_validation_missing_required_fields PASSED [ 89%]
tests/test_validation.py::test_validation_math_inconsistency PASSED      [ 92%]
tests/test_validation.py::test_validation_line_items_mismatch PASSED     [ 94%]
tests/test_cross_verification_matching PASSED                            [ 97%]
tests/test_cross_verification_mismatch PASSED                            [100%]

======================== 38 passed in 58.49s ========================
```

---

## 3. Module Coverage Breakdown

| Module | Statements | Missing | Coverage | Status |
| :--- | :---: | :---: | :---: | :---: |
| `app/schemas/document.py` | 108 | 0 | **100%** | Full |
| `app/schemas/search.py` | 14 | 0 | **100%** | Full |
| `app/schemas/user.py` | 21 | 0 | **100%** | Full |
| `app/models/models.py` | 93 | 0 | **100%** | Full |
| `app/core/celery_app.py` | 4 | 0 | **100%** | Full |
| `app/api/v1/search.py` | 10 | 0 | **100%** | Full |
| `app/services/storage_service.py` | 27 | 1 | **96%** | High |
| `app/core/security.py` | 28 | 1 | **96%** | High |
| `app/utils/logger.py` | 21 | 1 | **95%** | High |
| `app/services/validation_service.py` | 90 | 8 | **91%** | High |
| `app/workers/celery_tasks.py` | 16 | 3 | **81%** | High |
| `app/pipelines/orchestrator.py` | 85 | 22 | **74%** | Good |
| `app/api/v1/auth.py` | 51 | 14 | **73%** | Good |
| `app/services/extraction_service.py` | 167 | 46 | **72%** | Good |
| `app/utils/file_detection.py` | 28 | 8 | **71%** | Good |
| `app/core/config.py` | 81 | 27 | **67%** | Passing |
| `app/pipelines/text_extractor.py` | 119 | 50 | **58%** | Passing |
| `app/services/search_service.py` | 108 | 50 | **54%** | Passing |
| **TOTAL** | **1362** | **377** | **72%** | **Target Met (≥70%)** |

---

## 4. Reproducing Tests
```bash
# Run entire test suite with coverage
make test

# Or directly in virtualenv:
cd backend
PYTHONPATH=. ./venv/bin/pytest tests/ -v --cov=app --cov-report=term-missing
```
An interactive HTML coverage report is automatically generated at `backend/htmlcov/index.html`.
