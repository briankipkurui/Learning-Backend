import logging
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

# Create loggers
access_logger = logging.getLogger("app.access")
app_logger = logging.getLogger("app")

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.time()
        
        client_ip = request.client.host if request.client else "unknown"
        
        app_logger.info(f"Request started: {request.method} {request.url.path} from {client_ip}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            access_logger.info(
                f'{client_ip} - "{request.method} {request.url.path}" '
                f'{response.status_code} - {process_time:.3f}s'
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            
            # Log error
            app_logger.error(
                f"Request failed: {request.method} {request.url.path} from {client_ip} - "
                f"Error: {str(e)} - {process_time:.3f}s",
                exc_info=True
            )
            raise
