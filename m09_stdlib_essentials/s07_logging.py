"""
Module: Logging — Production-grade Diagnostics

Key Insights:
1. Don't use 'print' for diagnostics; use 'logging'.
2. Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL.
3. Use the module-level logger (__name__) rather than the root logger.
"""

import logging

# 1. Basic Configuration
# In a real app, this should be done once at the entry point.
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(),  # Log to console
        logging.FileHandler("app.log")  # Log to file
    ]
)

# 2. Get a logger for the current module
logger = logging.getLogger(__name__)

def divide(a, b):
    logger.debug(f"Attempting to divide {a} by {b}")
    try:
        result = a / b
    except ZeroDivisionError:
        logger.error("Division by zero occurred!")
        return None
    except Exception as e:
        # 'exc_info=True' adds the stack trace to the log
        logger.exception("Unexpected error occurred")
        return None
    else:
        logger.info("Division successful")
        return result

# Usage
divide(10, 2)
divide(10, 0)

if __name__ == "__main__":
    pass
