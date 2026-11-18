# Research Notes

## Experiment 1: Information Disclosure

**Research question:** Does HTTP QUERY reduce sensitive information exposure compared with GET?

**Hypothesis (to test):** GET places parameters in the request line, which servers log by default. QUERY (like POST) places them in the request body, which default access logs do not record, so QUERY should reduce URI-based exposure. However, the exposure may move to other places (e.g. application logs that record request bodies) rather than disappear.

### Observation 1: GET query string in the Uvicorn access log (baseline)

- **Environment:** Windows (home PC), Python 3.15.0, FastAPI 0.163.1, Uvicorn 0.54.0, default logging config, request sent from browser (VS Code Simple Browser)
- **Request:** Browser → `GET http://127.0.0.1:8000/health?card=4111111111111111`
  (4111… is a standard test card number, not real data)
- **Route behaviour:** `/health` does not declare or read a `card` parameter.
- **Evidence (Uvicorn terminal):**
  `INFO:     127.0.0.1:3828 - "GET /health?card=4111111111111111 HTTP/1.1" 200 OK`
- **Observation:** The test card number was logged in plain text in Uvicorn’s access log, even though the route never read the card parameter (`show_health()` takes no parameters - confirmed in Swagger, at `/docs`, where route lists no parameters).
- **Interpretation:** The query string is part of the request line, which the server receives and parses before application code runs, and records in its access log regardless of how the route handles it.