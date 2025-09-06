"""Base service class providing common functionality"""

from abc import ABC
from typing import Any, Dict, Optional
import logging

from .exceptions import ServiceError, ValidationError


class BaseService(ABC):
    """
    Base service class that provides common functionality for all services.
    
    Features:
    - Consistent error handling patterns
    - Logging integration
    - Validation helpers
    """
    
    def __init__(self, service_name: str = None):
        self.service_name = service_name or self.__class__.__name__
        self.logger = logging.getLogger(f"services.{self.service_name}")
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: list) -> None:
        """
        Validate that required fields are present in data
        
        Args:
            data: Dictionary to validate
            required_fields: List of required field names
            
        Raises:
            ValidationError: If any required field is missing
        """
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}",
                field=missing_fields[0] if len(missing_fields) == 1 else None
            )
    
    def validate_field_type(self, value: Any, expected_type: type, field_name: str) -> None:
        """
        Validate that a field has the expected type
        
        Args:
            value: Value to validate
            expected_type: Expected type
            field_name: Name of the field for error messages
            
        Raises:
            ValidationError: If type doesn't match
        """
        if not isinstance(value, expected_type):
            raise ValidationError(
                f"Field '{field_name}' must be of type {expected_type.__name__}",
                field=field_name,
                value=value
            )
    
    def handle_error(self, error: Exception, operation: str = "operation") -> None:
        """
        Standard error handling with logging
        
        Args:
            error: The exception that occurred
            operation: Description of the operation that failed
            
        Raises:
            ServiceError: Re-raises as ServiceError if not already one
        """
        self.logger.error(f"Error during {operation}: {str(error)}")
        
        if isinstance(error, ServiceError):
            raise error
        
        # Convert unknown errors to ServiceError
        raise ServiceError(
            f"Unexpected error during {operation}: {str(error)}",
            error_code="INTERNAL_ERROR",
            details={"original_error": str(error)}
        )
    
    def log_operation(self, operation: str, details: Dict[str, Any] = None) -> None:
        """
        Log service operations for debugging and monitoring
        
        Args:
            operation: Operation name
            details: Optional additional details
        """
        message = f"{self.service_name}: {operation}"
        if details:
            message += f" - {details}"
        self.logger.info(message)
    
    def sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename for safe storage
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        import re
        # Remove or replace unsafe characters
        filename = re.sub(r'[^\w\-_.]', '_', filename)
        # Limit length
        if len(filename) > 100:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:95] + ('.' + ext if ext else '')
        return filename.lower()
    
    def validate_enum_value(self, value: str, enum_values: list, field_name: str) -> None:
        """
        Validate that a value is in a list of allowed enum values
        
        Args:
            value: Value to validate
            enum_values: List of allowed values
            field_name: Name of the field for error messages
            
        Raises:
            ValidationError: If value is not in allowed list
        """
        if value not in enum_values:
            raise ValidationError(
                f"Field '{field_name}' must be one of: {', '.join(enum_values)}",
                field=field_name,
                value=value
            )