# Request Payloads

JSON bodies for `POST /accounts/search` and `QUERY /accounts` 

## Running them

1. Terminal 1: `uvicorn app.main:app --reload` (watch this one for the access log)
2. Terminal 2, from project root:

```
curl.exe -i -X POST "http://127.0.0.1:8000/accounts/search" -H "Content-Type: application/json" --data "@requests/<file>.json"
```

For QUERY: swap `-X POST` → `-X QUERY` and the URL → `/accounts`.

Reminders:
- `@` before the filename = send the file contents
- 404 = route doesn't exist yet

## The files

| File | Tests | Result (POST) | Result (QUERY)
|---|---|---|---|
| `filter-u002-current.json` | Two filters (AND) | `acc-003`, `acc-005` | `acc-003`, `acc-005`
| `filter-u001.json` | One filter | `acc-001`, `acc-002` | `acc-001`, `acc-002`
| `filter-min-balance-1m.json` | Balance ≥ 1,000,000 | `acc-004` | `acc-004`
| `filter-empty.json` | No filters | All 5 | All 5
| `filter-invalid-balance.json` | `"abc"` for a number | Rejects and `msg` field returns `"unable to parse string as an integer"` (422) | Rejects and `msg` field returns `"unable to parse string as an integer"` (422)
| `filter-string-number.json` | `"1000000"` as a string | Converted into an integer (200) | Converted into an integer (200)
| `filter-unknown-field.json` | Extra `is_admin` field | `acc-001`, extra field is ignored (200) | `acc-001`, extra field is ignored (200)

## Each time, check

- Status code
- Right account IDs?
- Uvicorn log line vs the GET version: what shows, what doesn't?