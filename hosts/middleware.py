import logging
import time

logger = logging.getLogger(__name__)


class RequestCostTimeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.perf_counter()
        response = self.get_response(request)
        cost_time = time.perf_counter() - start_time
        response["X-Request-Cost-Time"] = f"{cost_time:.3f}s"

        logger.info(
            "request_cost_time method=%s path=%s status=%s cost_time=%.3fs",
            request.method,
            request.path,
            response.status_code,
            cost_time,
        )
        return response
