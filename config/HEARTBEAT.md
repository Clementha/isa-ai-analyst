# HEARTBEAT.md - Scheduler Configuration

Automated reports are triggered by the Python scheduler at these times:

- 08:30
- 17:30

The scheduler handles all execution automatically. During heartbeat checks, reply HEARTBEAT_OK unless the user has sent a specific message requiring your attention. Do NOT run the math engine on heartbeat.