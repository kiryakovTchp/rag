# ADR 0005: Observability Stack with OpenTelemetry and Prometheus

## Status
**proposed**

## Context
PromoAI RAG нуждается в production-ready наблюдаемости для:
- Сквозной трассировки запросов через все компоненты (Cloudflare → API → Celery → Redis)
- Мониторинга производительности и здоровья системы
- Быстрого обнаружения и диагностики проблем
- Оперативного реагирования на деградации

## Decision
Внедрить полноценный стек наблюдаемости:
1. **OpenTelemetry** для трассировки и логов
2. **Prometheus** для метрик
3. **Grafana** для визуализации и алёртов
4. **Jaeger** для просмотра трасс

## Alternatives Considered

### Alternative A: Jaeger + Prometheus (без OTel)
- ✅ Простота настройки
- ❌ Нет стандартизации, сложно масштабировать
- ❌ Нет единого формата для трасс

### Alternative B: DataDog/New Relic (SaaS)
- ✅ Готовое решение, простота
- ❌ Дорого для production
- ❌ Vendor lock-in
- ❌ Проблемы с compliance

### Alternative C: ELK Stack
- ✅ Мощный поиск по логам
- ❌ Сложность настройки
- ❌ Нет встроенной трассировки
- ❌ Resource intensive

## Consequences

### Positive
- **Сквозная трассировка**: traceId проходит через все сервисы
- **Стандартизация**: OpenTelemetry как industry standard
- **Масштабируемость**: легко добавлять новые сервисы
- **Open Source**: полный контроль, нет vendor lock-in
- **Performance**: минимальное overhead на production

### Negative
- **Сложность**: больше компонентов для поддержки
- **Learning curve**: команда должна изучить OTel
- **Resource usage**: дополнительные сервисы (Jaeger, Grafana)

## Risks
- **Overhead**: OTel может замедлить API при неправильной настройке
- **Complexity**: сложность отладки при проблемах с трассировкой
- **Maintenance**: больше сервисов для мониторинга

## Implementation Details

### 1. OpenTelemetry Instrumentation
```python
# API
opentelemetry-instrumentation-fastapi
opentelemetry-instrumentation-logging
opentelemetry-instrumentation-redis
opentelemetry-instrumentation-sqlalchemy

# Workers
opentelemetry-instrumentation-celery
opentelemetry-instrumentation-redis
```

### 2. Trace Propagation
- **Cloudflare Workers**: генерируют traceId, передают в заголовках
- **FastAPI**: принимает traceId, создает span для API calls
- **Celery**: получает traceId, создает span для task execution
- **Redis**: инструментируется для показа Redis operations в трассах

### 3. Metrics Collection
```python
# API Metrics
query_latency_seconds{route,tenant}  # histogram
tenant_queries_total{tenant}         # counter
redis_publish_failures_total{tenant} # counter

# Worker Metrics  
ingest_job_duration_seconds          # histogram
embedding_duration_seconds           # histogram
queue_length{queue_name}             # gauge
```

### 4. Service Names
- `api` - FastAPI сервер
- `worker` - Celery workers
- `redis` - Redis operations
- `postgres` - Database operations

### 5. Export Configuration
```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://jaeger:4317
OTEL_SERVICE_NAME=api
OTEL_TRACES_SAMPLER=parentbased_traceidratio
OTEL_TRACES_SAMPLER_ARG=1.0
```

## Testing Strategy
1. **Unit tests**: проверка создания spans и метрик
2. **Integration tests**: проверка trace propagation через Redis
3. **E2E tests**: полная трасса от API до worker'а
4. **Load tests**: проверка overhead на производительность

## Monitoring & Alerting
- **Grafana Dashboards**: Ingest, Query, Realtime, Errors
- **Alerts**: P95 latency > 2.5s, error rate > 1%, Redis failures
- **SLOs**: 99.9% availability, P95 < 2s

## Migration Plan
1. **Phase 1**: Инструментация API (не breaking)
2. **Phase 2**: Инструментация workers (не breaking)  
3. **Phase 3**: Включение трассировки в production
4. **Phase 4**: Настройка алёртов и SLOs

## References
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Prometheus Python Client](https://github.com/prometheus/client_python)
- [Grafana Alerting](https://grafana.com/docs/grafana/latest/alerting/)
