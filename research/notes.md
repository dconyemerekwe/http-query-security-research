# Research Notes

## Experiment 1: Information Disclosure

**Research question:** Does HTTP QUERY reduce sensitive information exposure compared with GET?

**Hypothesis (to test):** GET places parameters in the request line, which servers log by default. QUERY (like POST) places them in the request body, which default access logs do not record, so QUERY should reduce URI-based exposure. However, the exposure may move to other places (e.g. application logs that record request bodies) rather than disappear.

### Observation 1: GET query string in the Uvicorn access log (baseline)

**Environment:** Local machine, Python 3.15.0, FastAPI 0.163.1, Uvicorn 0.54.0, default logging config, request sent from browser (VS Code Simple Browser)

**Request:** Browser → `GET http://127.0.0.1:8000/health?card=4111111111111111`
  (4111… is a standard test card number, not real data)

**Route behaviour:** `/health` does not declare or read a `card` parameter.

**Evidence (Uvicorn terminal):**
  `INFO:     127.0.0.1:3828 - "GET /health?card=4111111111111111 HTTP/1.1" 200 OK`

**Observation:** The test card number was logged in plain text in Uvicorn’s access log, even though the route never read the card parameter (`show_health()` takes no parameters - confirmed in Swagger, at `/docs`, where route lists no parameters).

**Interpretation:** The query string is part of the request line, which the server receives and parses before application code runs, and records in its access log regardless of how the route handles it.

### Precondition check: Does the server stack accept QUERY?

**Method:** `curl.exe -i -X QUERY` & a GET control, against a GET-only route, under `--http httptools` and `http h11`

**Result:** 
| Parser | Implementation | `QUERY /health` | `GET /health` (control) | Layer that answered QUERY |
|---|---|---|---|---|
| httptools | C (llhttp, as used by Node.js); Uvicorn default when installed | 405, `Allow: GET` | 200 | FastAPI routing |
| h11 | Pure Python; Uvicorn fallback or `--http h11` | 405, `Allow: GET` | 200 | FastAPI routing |

- **Why both were tested:**
    - Independent implementations: llhttp recognises methods from a fixed list, h11 accepts any valid method token, so results could differ.
    - Which parser runs depends on deployment (whether httptools is installed), so testing both covers either Uvicorn configuration.
    - Identical 405 responses show the rejection came from FastAPI routing, not from either parser.

- **Limitation:** requests sent without a body; body handling on QUERY not yet tested.

**Interpretation:** both parsers pass QUERY through, and the rejection comes from FastAPI routing (405 with `Allow: GET`)
- _RFC 9110 requires 405 responses to include an `Allow` header listing supported methods, but it enables method enumeration & route enumeration (405 resource confirmation vs 404 path non-existant)_

**Open items:**
1. repeat with a request body
2. test whether 405 is returned before authentication