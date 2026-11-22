# RA Contract Emulator

A deliberately small, stateful FastAPI emulator of the Registration Authority
(RA) API consumed by **RA Data Platform (RADP)**. It produces synthetic X.509
certificates, users, issuance requests, and revocation requests. It is for
local development, integration testing, and simulated lifecycle workflows,
**not** a real RA or a certificate management system.

## Quick start

Use Python 3.14 and `uv` (the existing lockfile is retained):

```sh
cp .env.example .env
uv sync --frozen
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Or run `docker compose up --build` after creating `.env`. Docker Compose binds
the port to the host's loopback interface by default. Open
`http://127.0.0.1:8000/docs` for the OpenAPI UI.

**First start:** the application initializes `data/emulator.sqlite3` and, if
that database is empty, imports existing `data/seeds/*.json` files when present,
or generates 100 synthetic certificates. The database **is not regenerated on
restart**; simulated approvals survive restarts.

To **deliberately discard all simulated data and regenerate** it:

```sh
uv run python -m app.dataset.generate
```

This replaces all records in the configured SQLite database. Back up your
database first if you need to keep existing workflow data.

## Configuration

Settings are loaded through `pydantic-settings` and cached by
`get_settings()` (`@lru_cache(maxsize=1)`). `create_app(settings=Settings(...))`
allows independent test applications to bypass the cache. Available variables:

| Environment variable | Default | Purpose |
| --- | --- | --- |
| `RADP_EMULATOR_API_ROOT` | `/api/ra` | API prefix |
| `RADP_EMULATOR_DATABASE_PATH` | `./data/emulator.sqlite3` under the project | Persistent SQLite path |
| `RADP_EMULATOR_CERTIFICATE_FOLDERS` | `default` | CSV folder names used **when first seeding** |
| `RADP_EMULATOR_LATENCY_MS` | `0` | Inject latency into RA API requests |
| `RADP_EMULATOR_FAILURE_RATE` | `0.0` | Probability of an injected RA API failure (0–1) |
| `RADP_EMULATOR_FAILURE_STATUS` | `503` | HTTP status used for injected failures |

Folder changes do not redistribute data already persisted in SQLite. Run the
explicit seed regeneration command if you want a different synthetic folder
distribution. In tests that mutate environment variables, call
`get_settings.cache_clear()` or pass an explicit `Settings` instance.

## Certificate folders and read contract

```http
GET /api/ra/certificates
GET /api/ra/certificates?folder=default
GET /api/ra/certificates?folder=archive
GET /api/ra/certificates?folder=default&value=1234
GET /api/ra/certificates/{certificate_id}
GET /api/ra/certRequests
GET /api/ra/users
```

Without a `folder` parameter, the certificates endpoint lists all folders in
legacy insertion order. Supplying `folder` restricts the collection. If there
is only one folder, `GET /certificates?folder=default` and
`GET /certificates` give identical items, page by page. Unknown folders return
an empty list; a certificate detail can be retrieved by UUID without specifying
its folder.

Collections use `items`, optional `_links.next.href`, and opaque `pageToken`
links. Default page size is **20**; search supports `q` and, for certificate and
revocation lists, `value` as an alias. Follow the returned next URL rather than
constructing offsets. Pagination links keep search and folder parameters.

## Revocation requests: paginated reads and simulated writes

```http
GET  /api/ra/revRequests
GET  /api/ra/revRequests?folder=default
GET  /api/ra/revRequests?folder=default&pageToken=...
GET  /api/ra/revRequests?value=1234
GET  /api/ra/revRequests/{revRequestId}
POST /api/ra/revRequests
POST /api/ra/revRequests/{revRequestId}/approve
POST /api/ra/revRequests/{revRequestId}/reject
```

The default 100-certificate seed generates **34 completed revocations**,
ensuring at least two pages. Completed seed requests link to corresponding
certificates with `status=Revoked`. New requests begin in `Pending` and have
no resolution timestamps until acted upon. Rejected requests leave the
certificate valid, allowing a later request; approved requests change the
linked certificate to `Revoked` and set its reason and `revokedWhen` in the
**same SQLite transaction** as resolving the request.

Create a request for an existing **valid** certificate:

```http
POST /api/ra/revRequests
Content-Type: application/json

{"certificateId":"REPLACE-WITH-CERTIFICATE-UUID","revocationReason":"KeyCompromise"}
```

The response is `201 Created` with `status=Pending` and a `revRequestId`.
Then approve or reject it:

```http
POST /api/ra/revRequests/{revRequestId}/approve
Content-Type: application/json

{}
```

The optional body can contain `{"resolverId":"UUID"}`. A double approval,
creation for a revoked certificate, or duplicate pending request returns `409`.
Unknown certificate or request IDs return `404`; invalid UUIDs or unsupported
reasons return `422`.

State transitions:

```text
  (create) -> Pending ---approve--> Completed [certificate -> Revoked]
                     \
                      \--reject----> Rejected  [certificate stays VALID]

  Rejected requests do not block a subsequent new request.
```

**Contract boundary:** `POST`, `approve`, `reject`, `Pending`, and `Rejected`
are **emulator-defined** for testing. They are not claimed to reproduce the
production RA's write endpoints or status vocabulary; use an anonymized
production API contract to adapt them if necessary. The existing GET fields
and camelCase naming are preserved.

**Security:** write endpoints are intentionally unauthenticated for local
simulation. Do not expose this emulator publicly or treat its database as
sensitive/production certificate infrastructure.

## Storage and older JSON seeds

`data/emulator.sqlite3` is the **active database**, not a JSON snapshot. It
holds `records` with kind, stable ordinal, ID, folder index, and JSON-encoded
Pydantic payload; SQLite transactions provide durable updates. This intentionally
avoids a heavyweight ORM for a small emulator while keeping flexible API
payloads. A separate `app.dataset.loader` supports one-time import of older
`users.json`, `cert_requests.json`, `certificates.json`, and optional
`rev_requests.json` from `data/seeds/` when SQLite is initially empty.

Legacy missing-folder records are placed into the first configured folder;
legacy placeholder revocation requests are ignored. After migration, the
SQLite database is authoritative, even if the old JSON files change. Do not
copy an active WAL database file using a bare file-copy operation; use SQLite's
backup API or stop the emulator first.

## Tests, API schema, and integration

```sh
uv run pytest
uv run python -m scripts.export_openapi
```

Contract and integration tests cover pagination, cross-entity consistency,
mutation state transitions, concurrency, restart durability, cached settings,
legacy JSON import, and failure injection. If using the combined RA stack,
run `python verify_alignment.py` in the archive root to exercise RADP's real
RA client against the emulator without PostgreSQL.

See [`ARCHITECTURE.md`](ARCHITECTURE.md) for the architectural assessment,
tradeoffs, and possible next steps.
