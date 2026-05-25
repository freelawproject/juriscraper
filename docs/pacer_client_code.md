# PACER Client Code Support

## Overview

Juriscraper supports optional PACER client codes for organizations that need to track usage across multiple users. The client code is included in authentication requests to PACER's API.

## What is a PACER Client Code?

A PACER client code is an optional identifier that organizations can use to track and manage PACER usage across their members. When provided, the client code is included in login requests to the PACER authentication API.

## Usage

### Basic Usage

To use a client code, simply pass it when creating a `PacerSession`:

```python
from juriscraper.pacer.http import PacerSession

# Create a session with client code
session = PacerSession(
    username="your_pacer_username",
    password="your_pacer_password",
    client_code="YOUR-CLIENT-CODE"
)

# Login to PACER
session.login()
```

### Without Client Code

If you don't have a client code, simply omit the parameter:

```python
from juriscraper.pacer.http import PacerSession

# Create a session without client code
session = PacerSession(
    username="your_pacer_username",
    password="your_pacer_password"
)

# Login to PACER
session.login()
```

### Using with Docket Reports

```python
from juriscraper.pacer.docket_report import DocketReport
from juriscraper.pacer.http import PacerSession

# Create session with client code
session = PacerSession(
    username="your_username",
    password="your_password",
    client_code="ORG-12345"
)

# Use the session with a docket report
report = DocketReport("ilnd", session)
report.query("123456")  # Query with pacer_case_id

# Access the parsed data
data = report.data
```

## Environment Variables

For security, it's recommended to store credentials and client codes in environment variables:

```python
import os
from juriscraper.pacer.http import PacerSession

session = PacerSession(
    username=os.environ.get("PACER_USERNAME"),
    password=os.environ.get("PACER_PASSWORD"),
    client_code=os.environ.get("PACER_CLIENT_CODE")  # Optional
)
```

## API Details

### PacerSession Constructor

```python
PacerSession(
    cookies=None,
    username=None,
    password=None,
    client_code=None,
    get_acms_tokens=False
)
```

**Parameters:**
- `cookies` (RequestsCookieJar, optional): Pre-existing cookies for the session
- `username` (str, optional): PACER account username
- `password` (str, optional): PACER account password  
- `client_code` (str, optional): PACER client code for organizational tracking
- `get_acms_tokens` (bool, optional): Enable ACMS authentication. Default: False

### Login Request Format

When a client code is provided, it's included in the JSON payload sent to PACER's authentication API:

```json
{
    "loginId": "username",
    "password": "password",
    "redactFlag": "1",
    "clientCode": "YOUR-CLIENT-CODE"
}
```

If no client code is provided, the `clientCode` field is omitted from the request.

## Testing

The client code functionality is tested in `tests/test_pacer_client_code.py`. Run the tests with:

```bash
python -m pytest tests/test_pacer_client_code.py -v
```

## References

- [PACER Authentication API User Guide](https://pacer.uscourts.gov/help/pacer/pacer-authentication-api-user-guide)
- Issue #192: Add PACER client code support

## Notes

- The client code is optional and only included in requests when explicitly provided
- Empty strings are treated as falsy and will not be included in requests
- Client codes are not logged or exposed in error messages for security
- The feature is backward compatible - existing code without client codes continues to work

