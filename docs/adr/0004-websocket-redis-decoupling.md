# ADR 0004: WebSocket Decoupling via Redis Pub/Sub

## Status
Accepted

## Context
В текущей архитектуре workers напрямую импортируют API модули для отправки WebSocket событий, что создает циклические зависимости и усложняет тестирование. Необходимо развязать workers и API через асинхронную коммуникацию.

## Decision
Использовать Redis Pub/Sub как Event Bus для асинхронной коммуникации между workers и WebSocket API.

## Alternatives Considered

### 1. Message Queue (Celery + Redis)
- **Pros**: Уже используется в проекте, надежная доставка
- **Cons**: Сложность для real-time событий, overhead для простых уведомлений
- **Почему нет**: Избыточно для статусных событий

### 2. gRPC Streaming
- **Pros**: Типизированные контракты, эффективная бинарная передача
- **Cons**: Сложность настройки, необходимость в proto схемах
- **Почему нет**: Overkill для простых статусных событий

### 3. WebSocket Server в Workers
- **Pros**: Прямая связь, минимальная задержка
- **Cons**: Дублирование WebSocket логики, сложность масштабирования
- **Почему нет**: Нарушает принцип единственной ответственности

## Consequences

### Positive
- ✅ Развязка workers и API
- ✅ Упрощение тестирования (можно тестировать изолированно)
- ✅ Масштабируемость (несколько API инстансов могут подписываться)
- ✅ Надежность (Redis гарантирует доставку)
- ✅ Real-time события с минимальной задержкой

### Negative
- ❌ Дополнительная зависимость от Redis
- ❌ Сложность отладки (события проходят через Redis)
- ❌ Потенциальная потеря событий при недоступности Redis

### Risks
- **Redis недоступность**: WebSocket не будет получать события
- **Mitigation**: Health checks, fallback к polling API
- **Производительность**: Redis может стать bottleneck при высокой нагрузке
- **Mitigation**: Мониторинг, горизонтальное масштабирование Redis

## Implementation

### Event Bus (`services/events/bus.py`)
```python
async def publish_event(topic: str, payload: dict) -> bool
async def subscribe_loop(topic: str, handler: Callable)
```

### Topic Format
`{tenant_id}.jobs` - изолированные каналы для каждого tenant

### Event Format
```json
{
  "event": "parse_started|parse_progress|parse_done|parse_failed",
  "job_id": 123,
  "document_id": 456,
  "type": "parse|chunk|embed",
  "progress": 50,
  "tenant_id": "tenant123",
  "ts": "2024-01-01T00:00:00Z"
}
```

### Workers
- Заменяют `from api.websocket import ...` на `from services.events.bus import publish_event`
- Публикуют события в `{tenant_id}.jobs`

### WebSocket API
- При подключении подписывается на `{tenant_id}.jobs`
- Ретранслирует события клиентам
- Поддерживает ping/pong и авто-reconnect

## Testing Strategy

### Unit Tests
- Mock Redis для изоляции компонентов
- Тестирование Event Bus логики

### Integration Tests
- Real Redis, изолированные тесты
- Проверка publish/subscribe

### E2E Tests
- Полный стек: FastAPI + Redis + WebSocket
- Таймаут ≤ 20s, CI с redis:7

## Monitoring

### Metrics
- Redis publish/subscribe latency
- WebSocket connection count per tenant
- Event delivery success rate

### Alerts
- Redis недоступность
- WebSocket connection failures
- Event delivery failures

## Migration

### Phase 1: Event Bus
- Создать `services/events/bus.py`
- Добавить aioredis dependency

### Phase 2: Workers
- Заменить импорты API на Event Bus
- Обновить все job_manager вызовы

### Phase 3: WebSocket API
- Переписать для работы с Redis Pub/Sub
- Добавить ping/pong и reconnect

### Phase 4: Testing
- Создать e2e тесты
- Обновить CI pipeline

## References
- [Redis Pub/Sub Documentation](https://redis.io/docs/manual/pubsub/)
- [aioredis Documentation](https://aioredis.readthedocs.io/)
- [FastAPI WebSocket](https://fastapi.tiangolo.com/advanced/websockets/)
