# Test endpoints


## Negative test case for `Get event by ID`

Should be `/api/v1/event/{event_id}` valid positive integer


Act:
Make HTTP GET request with invalid event_id

```bash
curl -X GET "http://127.0.0.1:8080/api/v1/event/abcd" -H "Accept: application/json"
```

Assert:

Response is equal to:

```json
{
    "error": {
        "status_code": 400,
        "message": "[{'type': 'int_parsing', 'loc': ('path', 'event_id'), 'msg': 'Input should be a valid integer, unable to parse string as an integer', 'input': 'abcd'}]",
        "error_type": "RequestValidationError"
    }
}
```
