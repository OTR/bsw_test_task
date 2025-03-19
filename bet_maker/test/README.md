# Get all active events

`GET /api/v1/events`

```bash
curl
```

Assert:

```json

```

# GET `/api/v1/bets`

```bash
curl -X 'GET' \
  'http://127.0.0.1:8081/api/v1/bets?limit=150&offset=0' \
  -H 'accept: application/json'
```

Assert:

```json

```

# GET `/api/v1/bets/{bet_id}`

```bash
curl -X 'GET' \
  'http://127.0.0.1:8081/api/v1/bets/4' \
  -H 'accept: application/json'
```