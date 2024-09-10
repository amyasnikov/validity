# Webhooks

NetBox has a built-in feature called [Event Rules](https://netboxlabs.com/docs/netbox/en/stable/models/extras/eventrule/) and [Webhooks](https://netboxlabs.com/docs/netbox/en/stable/models/extras/webhook/). This feature allows a user to provision a webhook to a custom endpoint when some NetBox model is created/updated/deleted.

The webhook may be provisioned to capture Compliance Report creation. Using this approach you can notify some third party system (OSS/BSS/Monitoring/etc.) about the overall compliance state of your network.

Let's create a webhook and an event rule using [pynetbox](https://github.com/netbox-community/pynetbox) library.

You may do the same thing using web GUI (`Other > Webhooks` menu)

```python
from pynetbox.core.api import Api

token = 'get api token via web gui and place it here'

nb = Api(url='http://127.0.0.1:8000', token=token)

webhook = nb.extras.webhooks.create(
    name='sample_webhook',
    payload_url='http://localhost:9000/api/webhook/',
    http_method='POST',
    ssl_verification=False,
)

nb.extras.event_rules.create(
    name="sample_event",
    object_types=["validity.compliancereport"],
    event_types=["object_created"],
    action_type="webhook",
    action_object_type="extras.webhook",
    action_object=webhook.id
)

```

It's done. Now when Run Compliance Tests script finishes its work, it will trigger the webhook to the `http://localhost:9000/api/webhook/` handle.


Here is the example contents of the webhook configured above:

```console
[1] Wed, 12 Apr 2023 19:36:37 GMT 127.0.0.1 "POST /api/webhook/ HTTP/1.1" 200 -
Host: localhost:9000
Accept-Encoding: identity
Content-Type: application/json
Content-Length: 772
User-Agent: python-urllib3/1.26.15

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
        "low_passed": 0,
        "low_count": 0,
        "middle_passed": 5,
        "middle_count": 8,
        "high_passed": 0,
        "high_count": 0,
        "results_url": "/api/plugins/validity/test-results/?report_id=29",
        "custom_fields": {},
        "created": "2023-04-12T19:36:33.690567Z",
        "last_updated": "2023-04-12T19:36:33.690588Z"
    },
    "snapshots": {
        "prechange": null,
        "postchange": {
            "created": "2023-04-12T19:36:33.690Z",
            "last_updated": "2023-04-12T19:36:33.690Z",
            "custom_fields": {}
        }
    }
}
Completed request #1
```

As you see the "data" property is just a serialized Report instance. It contains some statistics and the link to the results associated with this report.

Results itself are not included in the data because there may be plenty of results, so the body of the webhook may become too large.

If you need it, you may download the results using the link provided in the webhook and possibly calculate your own statistics based on the raw results data.

!!! info
    Someone may ask why email notifications are not implemented. The answer is simple: NetBox itself has no email delivery subsystem, and it's just not a purpose of Validity: to build this subsystem from scratch

    You always can set up some other system for sending emails triggered by an incoming webhook from NetBox.
