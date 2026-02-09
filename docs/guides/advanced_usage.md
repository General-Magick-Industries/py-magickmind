# HTTP Client for Power Users

The `client.http` property provides direct access to the underlying authenticated HTTP client. This is intended for developers and power users who need more control or access to features not yet exposed through typed resources.

## Why Use Direct HTTP Access?

### For Bifrost Developers
- **Rapid Prototyping:** Test new endpoints immediately after they are deployed to Bifrost without waiting for SDK updates.
- **Beta Testing:** Experiment with experimental features in `/beta` or `/experimental` namespaces.
- **Deep Debugging:** Inspect raw response headers, status codes, and JSON payloads exactly as they come from the server.

### For Power Users
- **Custom Integrations:** Build specialized logic that requires direct manipulation of request parameters.
- **Feature Gap Filling:** Use new Bifrost capabilities as soon as they are available, even before they are added to the SDK's typed resources.
- **One-off Calls:** Perform maintenance or administrative tasks that don't justify a full resource implementation.

## Usage Examples

### Testing Experimental Endpoints
Access endpoints that aren't yet available in the stable SDK resources:

```python
# Test a hypothetical experimental AI agent endpoint
response = client.http.post(
    "/experimental/ai-agents",
    json={
        "task": "analyze-market-data",
        "parameters": {"depth": "high"}
    }
)

data = response.json()
print(f"Agent Task ID: {data['task_id']}")
```

### Mixing API Versions
The `client.http` property makes it easy to communicate with different versions of the API within the same application:

```python
# Use stable v1 for chat
v1_response = client.http.post("/v1/magickmind/chat", json={...})

# Use beta for new reasoning capabilities
beta_response = client.http.post("/beta/magickmind/chat", json={...})
```

## Automatic Features
Even when making direct calls, the HTTP client remains a "Smart Client" that handles the heavy lifting for you:

- **✅ Authentication Injection:** Automatically adds `Authorization: Bearer <token>` to every request.
- **✅ Token Lifecycle Management:** transparently handles token refresh if a request fails with a 401 due to expiration.
- **✅ Error Mapping:** Converts standard HTTP error codes into meaningful SDK exceptions (`ValidationError`, `ProblemDetailsException`, etc.).
- **✅ Shared Configuration:** Respects the `timeout`, `base_url`, and `verify_ssl` settings provided during `MagickMind` initialization.

## Best Practices
While powerful, direct HTTP access should be used judiciously:
1. **Prefer Typed Resources:** If a resource exists in `client.v1.*`, use it. It provides better type safety and validation.
2. **Handle Exceptions:** Always wrap direct calls in try/except blocks using the SDK's custom exceptions.
3. **Log Request IDs:** In case of errors, the `ProblemDetailsException` contains a `request_id`. Always log this for debugging with the Bifrost team.
