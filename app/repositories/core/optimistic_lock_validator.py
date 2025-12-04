"""
Optimistic lock validator implementation following Single Responsibility Principle.

This module handles optimistic lock validation operations, separating this concern
from the main repository logic.
"""

from datetime import datetime

from fastapi import HTTPException, status

from app.repositories.core.interfaces import OptimisticLockValidator
from app.utils.i18n import __


class DefaultOptimisticLockValidator(OptimisticLockValidator):
    """Handles optimistic lock validation operations."""

    def parse_timestamp(self, timestamp_str: str) -> datetime:
        """
        Parse timestamp string with timezone handling.

        Args:
            timestamp_str: Timestamp string to parse

        Returns:
            Parsed datetime object

        Raises:
            HTTPException: If timestamp format is invalid
        """
        try:
            # Handle both with and without timezone info
            if timestamp_str.endswith("Z"):
                return datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            elif "+" in timestamp_str or timestamp_str.count("-") > 2:
                return datetime.fromisoformat(timestamp_str)
            else:
                # Assume UTC if no timezone info
                return datetime.fromisoformat(timestamp_str)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=__("optimistic_lock.invalid_timestamp"))

    def validate_optimistic_lock(
        self, expected_timestamp: str, actual_timestamp: datetime, record_id: str, model_name: str
    ) -> None:
        """
        Validate optimistic lock by comparing timestamps.

        Args:
            expected_timestamp: Expected timestamp string
            actual_timestamp: Actual timestamp from database
            record_id: Record ID for error messages
            model_name: Model name for error messages

        Raises:
            HTTPException: If optimistic lock validation fails
        """
        from app.utils.tracing import get_trace_logger

        logger = get_trace_logger("optimistic-lock-validator")

        expected_dt = self.parse_timestamp(expected_timestamp)
        if abs((actual_timestamp - expected_dt).total_seconds()) > 1:  # Allow 1 second tolerance
            logger.warning(f"Optimistic lock conflict for {model_name} {record_id}")
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=__("optimistic_lock.conflict"))
