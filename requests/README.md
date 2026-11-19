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

| File | Tests | Result |
|---|---|---|
| `filter-u002-current.json` | two filters (AND) | `acc-003`, `acc-005` |
| `filter-u001.json` | one filter | `acc-001`, `acc-002` |
| `filter-min-balance-1m.json` | balance ≥ 1,000,000 | `acc-004` |
| `filter-empty.json` | no filters | all 5 |
| `filter-invalid-balance.json` | `"abc"` for a number | 422 Unprocessable Content |
| `filter-string-number.json` | `"1000000"` as a string | converted or rejected? |
| `filter-unknown-field.json` | extra `is_admin` field | Ignored (200 OK) |

## Each time, check

- Status code
- Right account IDs?
- Uvicorn log line vs the GET version: what shows, what doesn't?