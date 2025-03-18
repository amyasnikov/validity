# Webhooks

NetBox provides built-in support for [Event Rules](https://netboxlabs.com/docs/netbox/en/stable/models/extras/eventrule/) and [Webhooks](https://netboxlabs.com/docs/netbox/en/stable/models/extras/webhook/). These features allow you to trigger an external HTTP request whenever a NetBox model is created, updated, or deleted.

This is useful for integrating NetBox with external systems like OSS/BSS, monitoring tools, or automation platforms. For example, you can configure a webhook to notify an external service whenever a Compliance Report is generated.

## Creating a Webhook and Event Rule

You can create a webhook and an event rule programmatically using the [pynetbox](https://github.com/netbox-community/pynetbox) library or via the NetBox web UI (`Other > Webhooks` menu).

### Using `pynetbox`

The following example demonstrates how to create a webhook and an event rule using `pynetbox`:

```python
from pynetbox.core.api import Api

# Replace with your API token retrieved from the NetBox UI
token = 'your_api_token_here'

# Initialize the NetBox API client
nb = Api(url='http://127.0.0.1:8000', token=token)

# Create a webhook that sends a POST request to the specified URL
webhook = nb.extras.webhooks.create(
    name='sample_webhook',
    payload_url='http://localhost:9000/api/webhook/',
    http_method='POST',
    ssl_verification=False,
)

# Create an event rule that triggers the webhook when a Compliance Report is created
nb.extras.event_rules.create(
    name="sample_event",
    object_types=["validity.compliancereport"],
    event_types=["object_created"],
    action_type="webhook",
    action_object_type="extras.webhook",
    action_object=webhook.id
)
```

Once configured, when a Compliance Report is generated, the webhook will send an HTTP POST request to `http://localhost:9000/api/webhook/`.

## Example Webhook Payload

When triggered, the webhook sends a payload like the following:

```json
{
    "event": "created",
    "timestamp": "2023-04-12 19:36:37.739906+00:00",
    "model": "compliancereport",
    "username": "admin",
    "request_id": "fc577b60-3f63-4402-8661-547adfefdd87",
    "data": {
        "id": 29,
        "url": "/api/plugins/validity/reports/29/",
        "display": "report-29",
        "device_count": 3,
        "test_count": 3,
        "total_passed": 5,
        "total_count": 8,
        "results_url": "/api/plugins/validity/test-results/?report_id=29",
        "created": "2023-04-12T19:36:33.690567Z"
    },
    "snapshots": {
        "prechange": null,
        "postchange": {
            "created": "2023-04-12T19:36:33.690Z"
        }
    }
}
```

The `data` field contains information about the Compliance Report, including statistics and a link to detailed results. Since results can be large, they are not included in the payload but can be retrieved using the `results_url`.

## Testing Your Webhook

Before deploying your webhook in production, you should test it to verify the payload and behavior. You can use tools like:

- **[Beeceptor](https://beeceptor.com/)** – Set up a custom endpoint and inspect webhook requests in real time.
- **[Pipedream RequestBin](https://pipedream.com/requestbin)** – Capture and debug webhook requests.

To test, configure your webhook with one of these services and trigger an event in NetBox. You’ll be able to inspect the request headers, body, and response status.

## Why No Email Notifications?

NetBox does not have a built-in email delivery system. If you need email alerts, you can set up an external service to send emails when a webhook is received.

For example, you can use a simple serverless function or a webhook-to-email service to process webhook payloads and send notifications.

By leveraging NetBox webhooks, you can integrate with external systems and automate workflows efficiently.
