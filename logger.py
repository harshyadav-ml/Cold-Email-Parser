"""Root proxy for src.closer.audit.logger.

Delegates directly to src/closer/audit/logger.py while providing top-level
module compatibility as outlined in docs/implementation_plan.md.
"""
from src.closer.audit.logger import (
    FIELDNAMES,
    LOG_FILE,
    VALID_STATUSES,
    get_log_summary,
    log_entry,
)

__all__ = [
    "FIELDNAMES",
    "LOG_FILE",
    "VALID_STATUSES",
    "get_log_summary",
    "log_entry",
]
