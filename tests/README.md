# IFRDSS Test Suite

44 automated tests (33 unit + 11 integration), 98% statement coverage
across the backend. See `IFRDSS_Test_Report.docx` (in the project docs)
for the full report, or run it yourself:

```bash
cd ifrdss
pip install -r requirements.txt
cd tests
pytest -v                                    # run all tests, verbose
pytest --cov=../backend --cov-report=term-missing   # with coverage
```

| File | Covers |
|---|---|
| `test_detection.py` | Computer Vision Detection Module (`detection.py`) — SRS FR-2.x |
| `test_decision_support.py` | Decision Support Module (`decision_support.py`) — SRS FR-3.x |
| `test_api_integration.py` | Full REST API pipeline (`main.py`) — SRS FR-1.x, FR-4.4, FR-4.5 |

Integration tests use FastAPI's `TestClient` (in-process, no server needed)
and an isolated temporary SQLite database that is reset before every test.
