import logging
import os
from typing import Optional

from loguru import logger


class InterceptHandler(logging.Handler):
    """Redirect standard logging records to Loguru.

    This allows modules using `logging.getLogger(...)` to flow into Loguru sinks.
    """

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        # Walk back to the original caller to preserve file/line in logs
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(storage_base_path: str, log_file_path: Optional[str] = None) -> None:
    """Configure Loguru and integrate with standard logging and Uvicorn.

    - Writes application logs to `storage/logs/fastapi.log` by default.
    - Intercepts Python logging (including Uvicorn/FastAPI) and routes to Loguru.
    - Ensures directory exists at runtime.
    """

    # Determine log file path
    logs_dir = os.path.join(storage_base_path, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    logfile = log_file_path or os.path.join(logs_dir, "fastapi.log")

    # Remove default Loguru handlers to avoid duplicate logs
    logger.remove()

    # Add file sink: capture everything; rotate to keep files manageable
    logger.add(
        logfile,
        level="DEBUG",
        rotation="10 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level:<8} | "
            "{name}:{function}:{line} | {message}"
        ),
    )

    # Intercept stdlib logging
    logging.captureWarnings(True)

    root_logger = logging.getLogger()
    for h in list(root_logger.handlers):
        root_logger.removeHandler(h)
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(InterceptHandler())

    # Uvicorn loggers
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers = [InterceptHandler()]
        uv_logger.propagate = False

