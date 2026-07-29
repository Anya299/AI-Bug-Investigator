import time
from logger import get_logger

logger = get_logger(__name__)


FAILURE_LIMIT = 5
RESET_TIME = 60   # seconds


failures = 0
last_failure_time = None


def record_failure():
    global failures, last_failure_time

    failures += 1
    last_failure_time = time.time()

    logger.warning(
        "LLM failure recorded. failures=%s",
        failures
    )


def record_success():
    global failures

    failures = 0


def is_circuit_open():
    global failures, last_failure_time

    if failures < FAILURE_LIMIT:
        return False

    if last_failure_time:
        elapsed = time.time() - last_failure_time

        if elapsed > RESET_TIME:
            logger.info(
                "Circuit breaker reset after cooldown"
            )
            failures = 0
            return False

    return True