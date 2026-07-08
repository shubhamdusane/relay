# Relay - Architecture

## System Overview

Relay is a high-performance message relay and protocol bridge that routes messages between different communication systems (Slack, Discord, Teams, IRC, Matrix, custom webhooks). It supports bidirectional sync, message transformation, and delivery guarantees.

```
┌──────────────────────────────────────────────────────────────────┐
│                      Management API                              │
│  ┌──────────┐  ┌────────────┐  ┌────────────┐  ┌────────────┐  │
│  │ Channel  │  │ Bridge     │  │ Transform  │  │ Admin      │  │
│  │ Routes   │  │ Config     │  │ Rules      │  │ Dashboard  │  │
│  └─────┬────┘  └─────┬──────┘  └─────┬──────┘  └─────┬──────┘  │
├────────┼──────────────┼───────────────┼───────────────┼──────────┤
│                      Relay Core                                 │
│  ┌─────▼──────────────▼───────────────▼───────────────▼──────┐  │
│  │                 MessageRouter                              │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │  │
│  │  │ Channel  │  │ Message  │  │ Delivery │  │ Queue    │  │  │
│  │  │ Manager  │  │ Transform│  │ Tracker  │  │ Manager  │  │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
├──────────────────────────────────────────────────────────────────┤
│                      Protocol Adapters                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  Slack   │  │ Discord  │  │  Teams   │  │  Matrix      │   │
│  │  Adapter │  │ Adapter  │  │  Adapter │  │  Adapter     │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐   │
│  │  IRC     │  │ Telegram │  │ Webhook  │  │  Custom      │   │
│  │  Adapter │  │ Adapter  │  │ Adapter  │  │  (SDK)       │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────────┘   │
├──────────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌────────────────┐  ┌────────────────┐  │
│  │  Redis Queue     │  │  PostgreSQL    │  │  Rate Limiter  │  │
│  │  (BullMQ)        │  │  (messages)    │  │  (per channel) │  │
│  └──────────────────┘  └────────────────┘  └────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

## Component Descriptions

### Management API
Web UI and REST API for configuring bridges and monitoring message flow.

| Endpoint | Responsibility |
|----------|---------------|
| `/channels` | Manage channel mappings and bridge rules |
| `/bridges` | Configure adapter connections and credentials |
| `/transforms` | Define message transformation rules |
| `/admin` | Dashboard with real-time message flow visualization |

### Relay Core

| Component | Responsibility |
|-----------|---------------|
| `MessageRouter` | Core message bus that routes between adapters |
| `ChannelManager` | Maps source channels to destination channels |
| `MessageTransform` | Applies transformation rules (format, content, metadata) |
| `DeliveryTracker` | Tracks message delivery status with retry support |
| `QueueManager` | Manages message queues with priority and batching |

### Protocol Adapters
Each adapter implements bidirectional message bridging.

- **Slack**: WebSocket + Events API with thread support
- **Discord**: Bot API with channel and thread bridging
- **Teams**: Bot Framework with adaptive cards
- **Matrix**: Matrix client API with end-to-end encryption support
- **IRC**: IRC protocol with reconnection logic
- **Telegram**: Bot API with media support
- **Webhook**: Generic HTTP webhook adapter

## Data Flow

```
┌──────────┐     ┌───────────┐     ┌──────────────┐
│ Source   │────▶│ Adapter   │────▶│ Message      │
│ Platform │     │ (ingest)  │     │ Router       │
└──────────┘     └───────────┘     └──────┬───────┘
                                          │
                    ┌─────────────────────▼──────────────────┐
                    │        Message Transformation          │
                    │  ┌─────────┐  ┌──────────┐  ┌───────┐ │
                    │  │ Format  │  │ Content  │  │ Meta  │ │
                    │  │ Convert │  │ Filter   │  │ Map   │ │
                    │  └─────────┘  └──────────┘  └───────┘ │
                    └─────────────────────┬──────────────────┘
                                          │
                    ┌───────────┐         │         ┌───────────┐
                    │ Delivery  │◀────────┼────────▶│ Queue     │
                    │ Tracker   │         │         │ Manager   │
                    └─────┬─────┘         │         └─────┬─────┘
                          │               │               │
                          ▼               ▼               ▼
                    ┌─────────────────────────────────────────┐
                    │    Destination Adapter (deliver)        │
                    └─────────────────────────────────────────┘
```

## Directory Structure

```
relay/
├── src/
│   ├── api/                 # Management API
│   │   ├── routes/
│   │   └── middleware/
│   ├── core/                # Relay core
│   │   ├── router.ts
│   │   ├── channelManager.ts
│   │   ├── transform.ts
│   │   ├── deliveryTracker.ts
│   │   └── queueManager.ts
│   ├── adapters/            # Protocol adapters
│   │   ├── base.ts          # Adapter interface
│   │   ├── slack.ts
│   │   ├── discord.ts
│   │   ├── teams.ts
│   │   ├── matrix.ts
│   │   ├── irc.ts
│   │   ├── telegram.ts
│   │   └── webhook.ts
│   ├── transforms/          # Message transformers
│   │   ├── markdown.ts
│   │   ├── emoji.ts
│   │   └── media.ts
│   ├── models/              # Data models
│   └── utils/
├── migrations/
├── tests/
├── docs/
├── package.json
└── tsconfig.json
```

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Adapter pattern | Clean separation between protocol logic and routing |
| BullMQ for queues | Reliable delivery with retries, priorities, and delayed jobs |
| Message transformation | Platform-specific formatting differences require adaptation |
| Delivery tracking | Ensure message delivery with at-least-once guarantees |
| Webhook adapter | Enables bridging to custom or legacy systems |

## Dependencies

- **Runtime**: `@slack/bolt`, `discord.js`, `@slack/web-api`, `matrix-js-sdk`
- **Queue**: `bullmq`, `ioredis`
- **Store**: `pg`
- **Build**: `typescript`
- **Testing**: `vitest`, `nock`

## Security Considerations

- All API credentials encrypted at rest in database
- OAuth tokens refreshed automatically with minimal scopes
- Message content not persisted unless explicitly configured
- Rate limiting per adapter to prevent platform bans
- Audit log of all bridge configuration changes
- No secrets in logs; only token references

## Performance Characteristics

- Message relay latency: <500ms end-to-end
- Throughput: 1000 messages/second across all adapters
- Queue processing: configurable concurrency per adapter
- Retry strategy: exponential backoff with max 5 attempts
- Connection pooling for database and Redis

## Extension Points

| Extension | Mechanism |
|-----------|-----------|
| New adapters | Implement `AdapterInterface` following base pattern |
| Custom transforms | Register transformation functions for message content |
| Custom queues | Plugin alternative queue backends (Kafka, SQS) |
| Delivery hooks | Pre/post delivery hooks for custom logic |
| Media handlers | Custom media download/upload handlers per platform |
