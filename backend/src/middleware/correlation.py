import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram
from src.logging.correlation import set_correlation_id
from src.logging.logger import get_logger

logger = get_logger(__name__, 'api')

http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code']
)


class CorrelationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get('X-Correlation-ID')
        if not correlation_id:
            correlation_id = set_correlation_id()
        else:
            set_correlation_id(correlation_id)

        request.state.correlation_id = correlation_id

        start_time = time.time()
        method = request.method
        path = request.url.path

        logger.info(
            f'{method} {path} - Request started',
            extra={
                'correlation_id': correlation_id,
                'method': method,
                'path': path,
                'endpoint': f'{method} {path}',
            }
        )

        try:
            response = await call_next(request)
            duration = time.time() - start_time
            status_code = response.status_code
            endpoint = f'{method} {path}'

            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).observe(duration)

            logger.info(
                f'{method} {path} - Request completed',
                extra={
                    'correlation_id': correlation_id,
                    'method': method,
                    'path': path,
                    'endpoint': endpoint,
                    'status_code': status_code,
                    'duration': duration * 1000,
                }
            )

            response.headers['X-Correlation-ID'] = correlation_id
            return response

        except Exception as e:
            duration = time.time() - start_time
            endpoint = f'{method} {path}'
            status_code = 500

            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).observe(duration)

            logger.error(
                f'{method} {path} - Request failed: {str(e)}',
                extra={
                    'correlation_id': correlation_id,
                    'method': method,
                    'path': path,
                    'endpoint': endpoint,
                    'duration': duration * 1000,
                },
                exc_info=True,
            )
            raise
