# Data Model 015 — Campaigns and Broadcast Messaging

## campaigns

```text
id
tenant_id
solution_code nullable
name
description nullable
campaign_type
message_type
status
send_mode
scheduled_at nullable
timezone
message_body
target_channel_policy
audience_type
audience_filters
estimated_recipients
eligible_recipients
blocked_recipients
created_by
approved_by nullable
approved_at nullable
sent_at nullable
cancelled_at nullable
created_at
updated_at
```

## campaign_audiences

```text
id
campaign_id
audience_type
filters
estimated_recipients
eligible_recipients
blocked_by_consent
blocked_by_channel_policy
blocked_by_missing_contact
created_at
updated_at
```

## campaign_recipients

```text
id
campaign_id
recipient_type
recipient_id
contact_id nullable
display_name nullable
channel_type
channel_address
consent_status
eligibility_status
eligibility_reason nullable
created_at
```

## campaign_deliveries

```text
id
campaign_id
campaign_recipient_id
recipient_type
recipient_id
channel_type
channel_address
status
provider_message_id nullable
error_code nullable
error_message nullable
queued_at nullable
sent_at nullable
delivered_at nullable
read_at nullable
failed_at nullable
created_at
updated_at
```

## contact_preferences

```text
id
tenant_id
solution_code nullable
contact_type
contact_id
channel_type
allow_transactional
allow_operational
allow_marketing
opted_out_at nullable
opt_out_reason nullable
source
created_at
updated_at
```

## campaign_templates

```text
id
tenant_id
solution_code nullable
name
description nullable
campaign_type
message_type
channel_type nullable
body_template
variables
status
created_by
created_at
updated_at
```

## campaign_events

```text
id
campaign_id
event_type
previous_status nullable
new_status nullable
actor_type
actor_id nullable
metadata
created_at
```

## Indexes recomendados

```text
campaigns(tenant_id, status)
campaigns(tenant_id, solution_code)
campaigns(tenant_id, scheduled_at)
campaign_deliveries(campaign_id, status)
campaign_deliveries(tenant_id, status) if tenant_id is denormalized
contact_preferences(tenant_id, contact_type, contact_id, channel_type)
```
