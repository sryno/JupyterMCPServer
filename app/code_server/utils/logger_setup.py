import sys
import inspect
import logging
from loguru import logger


class InterceptHandler(logging.Handler):
    """
    Custom logging handler that intercepts standard logging and redirects to Loguru.

    This handler captures standard library logging records and redirects them to Loguru's
    logging system, maintaining consistent logging format and behavior throughout the application.
    """
    def emit(self, record: logging.LogRecord) -> None:
        """
        Process and emit a logging record through Loguru.

        Args:
            record (logging.LogRecord): The logging record to be processed and emitted.

        Returns:
            None

        The method determines the appropriate log level, finds the original caller's frame,
        and forwards the log message to Loguru with proper context and formatting.
        """
        # Get corresponding Loguru level if it exists.
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message.
        frame, depth = inspect.currentframe(), 0
        while frame:
            filename = frame.f_code.co_filename
            is_logging = filename == logging.__file__
            is_frozen = "importlib" in filename and "_bootstrap" in filename
            if depth > 0 and not (is_logging or is_frozen):
                break
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def configure_logging():
    """
    Configure the logging system with custom formatting and handlers.

    Sets up Loguru logger with custom formatting, including timestamps, log levels,
    and source location. Also configures the standard logging to use the InterceptHandler
    for consistent logging behavior across the application.

    Returns:
        None
    """
    logger.remove()
    logger.add(sys.stdout, colorize=True,
               format="<green>{time}</green> :: <level>{level}</level> :: <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
               level="INFO")
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)


def get_logger():
    """
    Create and return a logger instance for the current module.

    Returns:
        logging.Logger: A configured logger instance using the module's name.
    """
    logger = logging.getLogger(__name__)

    return logger
