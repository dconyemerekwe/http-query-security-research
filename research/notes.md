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
- _RFC 9110 requires 405 responses to include an `Allow` header listing supported methods, but it enables method enumeration & route enumeration (405 resource confirmation vs 404 path non-existant)

### Observation 2: QUERY keeps parameters out of the access log (same as POST)

**Request:** `curl.exe` -i -X QUERY "http://127.0.0.1:8000/accounts" -H "Content-Type: application/json" --data "@requests/<file>.json"

**Route behaviour:** Like POST, the QUERY route reads `AccountFilter` from the request body, never from the query string.

**Evidence (access log, same search, three methods):**
```
  GET   /accounts?owner_id=u-002&account_type=current  200
  POST  /accounts/search                               200
  QUERY /accounts                                      200
```

**Observation:** Parameters appear in the log for GET only.

**Interpretation:** QUERY removes URI-based exposure in the default access log, but no more than POST does. Its advantage over POST is semantic, not confidentiality.

### Observation 3: POST and QUERY are functionally equivalent
**Evidence:** fixture table (7 fixtures, identical results) in requests/README.md
**Interpretation:** later differences can be attributed to the method, not the logic.

### Observation 4: QUERY with parameters in the URL — still logged, then rejected
**Evidence:** the three log lines (GET 200 / POST 405 / QUERY 422) + 422 body with `"loc":["body"]`
**Interpretation:** the method doesn't protect data; where the client puts it does.

### Observation 5: Framework and tooling support
- `hasattr(FastAPI(), 'query')` = `False` → `api_route` required
- Swagger UI doesn't list QUERY
- openapi.json: version 3.1.0, has a "query" key (invalid in 3.1), and no `requestBody`

### Observation 6: Incomplete Allow header
With GET and QUERY routes on `/accounts`, a `DELETE /accounts` returns 405 with `Allow` listing only the methods of the first-declared route (GET; QUERY when the order is swapped). The header never lists both. Cause: the router delegates the 405 to the first path-matching route. Not QUERY-specific, but QUERY adoption naturally produces this configuration (new method added to an existing GET path).

### Security note: validation errors echo input

**Ran:** `curl.exe -i -X QUERY "http://127.0.0.1:8000/accounts?owner_id=u-002&account_type=current"`

**Returned:** `{"detail":[{"type":"missing","loc":["body"],"msg":"Field required","input":null}]}`

**Observation:** the `input` field echoes what the client sent.

FastAPI includes the rejected value in the error response by default. Here it’s null is harmless. But if a client sends a mistyped sensitive value, such as a malformed IBAN or a token in the wrong field, it gets reflected in the response body. If something logs response bodies (some gateways and debugging middleware do), it also ends up in a log.

## Authentication & Authorisation

**Authentication vs Authorisation**

|  | What is asks | Failure status 
|---|---|---|
Authentication | _Who are you?_ | **401 Unauthorised** (unauthenticated)
Authorisation | _Are you allowed to do this?_ | **403 Forbidden** providing information leakage (or 404 which reveals nothing)

Both separate checks and most API vulnerabilities lie in the **second** one.

**Object-level authorisation**
Authorisation happens at two levels:
- **Functional:** checks whether a user can use a specific endpoint at all.
- **Object:** checks whether a user can access _a particular record._ 

**BOLA (Broken Object Level Authorisation):** the failure of the second check: the user is properly logged in and allowed to use the endpoint, but the server doesn’t verify that the requested object belongs to them. Changing an ID in the request (`acc-001 → acc-003`) returns someone else’s data. **It’s #1 in the OWASP API Security Top 10 (API1:2023).**

**"Safe" methods**
RFC 9110 defines **safe** as “doesn’t change server state”, and RFC 10008 makes QUERY safe and idempotent.
- **Safe describes side effects, not sensitivity** e.g. A read that returns Bob’s IBAN to Alice changes nothing on the server, yet it’s a data breach.
- BOLA is overwhelmingly a **read** vulnerability: viewing other users’ records.
- So QUERY needs exactly the same authorisation as GET.

### Open items
1. Test whether 405 is returned before authentication (Stage 4)