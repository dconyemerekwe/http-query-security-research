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

**Request:** `curl.exe -i -X QUERY "http://127.0.0.1:8000/accounts" -H "Content-Type: application/json" --data "@requests/<file>.json"`

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

### Observation 1: Inconsistent Authentication Across Methods

Before authentication, any client could read any account through any method.

**Evidence (protected GET, unprotected QUERY):**
```
  GET   /accounts?owner_id=u-002&account_type=current  401
  QUERY /accounts?owner_id=u-002&account_type=current  200: Bob's acc-003, acc-005, IBANs
```

**After authentication was implemented on all routes:**
 | No token | Wrong token | Alice's token
|---|---|---|
GET | 401 | 401 | 200 (`acc-001`, `acc-002`)
POST | 401 | 200 (`acc-001`, `acc-002`)
QUERY | 401 | 200 (`acc-001`, `acc-002`)

### Observation 2: Authentication-only Enforcement Still Leaves BOLA

Request (all routes) | Result
|---|---|
`/accounts?owner_id=u-002` + Alice's token | **200**: Bob's `acc-003`, `acc-004`, `acc-005`
`/accounts?owner_id=u-002` + Alice's token | **405** with an `allow: QUERY`


**Observation:** Authentication without object-level authoirsation.
- Alice's identity was verified, yet she read another user's financial records.
- Unauthenticated users can still discover that the route exists and which methods it accepts, because routing happens before the auth dependency runs.
- The owner is chosen by a client-controlled filter, and the server never compares it with the authenticated identity.
- Authentication answers who is asking. It doesn't decide what they may see (OWASP API1:2023).

### Observation 3: BOLA Resolution with Object-level Ownership
Request (Alice's token) | Result
|---|---|
`/accounts?owner_id=u-002` (all methods) | `200 []`
No filters (all methods) | 200: `acc-001`, `acc-002`

**The fix:** object-level ownership with an intersect implementation: the client's `owner_id` is treated as an ordinary filter combined with an enforced ownership condition, so responses always truthfully answer the request as sent and never contain another user's data. Done with a helper function, `search_owned_accounts`, that every route calls, taking the owner from the token and return `[]` when the client asks for a different owner.

## Experiment 2: Cache Security

Can incorrect QUERY cache implementation introduce cache confusion or cross-user information disclosure?

RFC 10008 makes QUERY cacheable. Because every QUERY to the same resource shares one URI, a cache that keys on the URI alone (the default for GET-oriented caches) will serve one request's response to a different request — including a different user's.

**Environment:** Docker Compose running Nginx 1.30.8 with Varnish 9.1 between it and the FastAPI/Uvicorn (Python 3.15.0, FastAPI 0.163.1, Uvicorn 0.54.0) app. 

### Observation 1: Nginx cannot cache QUERY
**Ran:** `proxy_cache_methods GET HEAD QUERY;` then `nginx -t` (Nginx 1.30.8)
**Returned:** `nginx: [emerg] invalid value "QUERY" in ...nginx.conf:15`
**Interpretation:** `proxy_cache_methods` only accepts GET, HEAD and POST, and the default cache key is URI-based. Consistent with RFC 10008, which forbids caches that cannot key on the request body from caching QUERY. Nginx fails safe: QUERY passes through uncached, and QUERY's cacheability benefit is unavailable. 

### Observation 2: Naive "cache QUERY" rule - method rewritten, body dropped
**Config (only change):**
```vcl
sub vcl_recv {
    if (req.method == "QUERY") {
        return (hash);
    }
}
```
**Ran:** Alice, `QUERY /accounts` + `filter-current.json` (`{"account_type": "current"}`), empty cache
**Returned:** `200`, `X-Varnish: 2`, `Age: 0` (miss) — body contained `acc-001` **and** `acc-002` (filter ignored)
**Evidence:**
- Nginx log: `"QUERY /accounts HTTP/1.1" 200 283`
- App log: `172.22.0.3:48180 - "GET /accounts HTTP/1.1" 200 OK`
**Observation:** The client sent QUERY with a body; the app received GET with no body and no parameters.
**Interpretation:** On a cache miss, Varnish fetched from the backend as GET and discarded the body — default behaviour designed for GET caching. The app answered the wrong question correctly. The cache corrupted the request before the application saw it.

### Observation 3: Different bodies share one cache entry (cross-query false hit)
**Ran:** Alice, `QUERY /accounts` + `filter-savings.json` (`{"account_type": "savings"}`), 55 s after Observation 3
**Returned:** `200`, `X-Varnish: 5 3`, `Age: 54` (hit) — the same cached response as Observation 3
**Evidence:** No new app log line; Nginx logged a second `QUERY /accounts`.
**Interpretation:** The default cache key (URL + host) ignores the body. Every QUERY to `/accounts` maps to one entry, regardless of what was asked.

### Observation 4: Bob receives Alice's accounts (cross-user disclosure)
**Ran:** Bob (`bob-test-token-2`), `QUERY /accounts` + `filter-current.json`
**Returned:** `200`, `X-Varnish: 32770 3`, `Age: 72` (hit) — **Alice's** `acc-001` and `acc-002`, including IBANs and balances
**Evidence:** Nginx logged 3 QUERY requests in total; the app logged only 1 (Observation 3).
**Interpretation:** Bob's request never reached the app, so the ownership check from Stage 4 never ran. Returning early from `vcl_recv` also skipped Varnish's built-in rule that refuses to cache requests carrying `Authorization`. Application-level authorisation does not protect data served by a cache in front of it.

### Interpretation (Experiment 3 so far)
- Both mainstream caches tested fail safe by default: neither caches QUERY.
- The risk appears when a developer enables QUERY caching with a minimal rule. Every failure observed (method rewrite, body drop, URL-only key, skipped Authorization rule) is the cache's own default behaviour, designed for GET, where the URI identifies the response.
- QUERY breaks that assumption: the URI no longer identifies the response, the body does. 

### Observation 5: Corrected VCL config - no false hits, caching preserved
**Config changes (vs. Observation 3):**
- `vcl_recv`: `std.cache_req_body(100KB)` stores the body; if it can't be stored, `return (pass)` (fail safe, per RFC 10008). Original method saved in `X-Orig-Method` (client-supplied copies removed).
- `vcl_hash`: key = method + `Content-Type` + `Authorization` + request body (`bodyaccess.hash_req_body()`) + URL + host.
- `vcl_backend_fetch`: restores `bereq.method = "QUERY"` on misses, so the body is forwarded.

**Ran:** same sequence as Observations 2-4, plus a repeat of Alice `current`, empty cache.
**Returned:**
| # | Request | X-Varnish / Age | Body |
|---|---|---|---|
| 1 | Alice, current | `2` / `0` (miss) | `acc-001` |
| 2 | Alice, savings | `32770` / `0` (miss) | `acc-002` |
| 3 | Bob, current | `5` / `0` (miss) | `acc-003`, `acc-005` |
| 4 | Alice, current (repeat) | `8 3` / `14` (hit) | `acc-001` |

**Evidence:** Nginx logged 4 `QUERY /accounts`; the app logged 3 `QUERY /accounts` (misses only, all as QUERY).
**Interpretation:** Each failure from Observations 2-4 maps to one missing key component or fetch behaviour. With the body, request metadata and user identity in the key - and QUERY preserved on misses - Varnish caches QUERY safely: distinct queries and distinct users get distinct entries, and identical requests still hit.

### Conclusion (Experiment 2)
QUERY's cacheability is real but not automatic. Mainstream caches fail safe by default (Nginx cannot cache QUERY; Varnish does not by default). Enabling QUERY caching with a minimal rule produced request corruption (QUERY → GET, body dropped), cross-query false hits, and cross-user disclosure that bypassed application authorisation. A safe configuration must: store and forward the body, include body + method + content type in the key (RFC 10008), separate users (or not cache authenticated responses, RFC 9111), and refuse to cache when the body cannot be keyed.

### Limitations
- Keying on the raw `Authorization` header gives per-token entries: safe, but a new token means a cold cache.
- Body hashing is byte-exact: semantically identical JSON with different whitespace or key order gets separate entries (false misses — a performance cost, not a security risk; RFC 10008 leaves normalisation optional).
- Bodies over 100KB are not cached (deliberate fail-safe).
- One cache product (Varnish 9.1) and one configuration style tested.