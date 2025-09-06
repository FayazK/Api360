"""Common service exceptions"""

class ServiceError(Exception):
    """Base exception for service layer errors"""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ServiceError):
    """Exception for validation errors in service layer"""
    
    def __init__(self, message: str, field: str = None, value=None):
        super().__init__(message, "VALIDATION_ERROR")
        if field:
            self.details["field"] = field
        if value is not None:
            self.details["value"] = str(value)


class NotFoundError(ServiceError):
    """Exception for when a requested resource is not found"""
    
    def __init__(self, resource_type: str, identifier: str = None):
        message = f"{resource_type} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, "NOT_FOUND")
        self.details["resource_type"] = resource_type
        if identifier:
            self.details["identifier"] = identifier


class ConfigurationError(ServiceError):
    """Exception for configuration-related errors"""
    
    def __init__(self, message: str, config_key: str = None):
        super().__init__(message, "CONFIGURATION_ERROR")
        if config_key:
            self.details["config_key"] = config_key


class ExternalServiceError(ServiceError):
    """Exception for external service errors"""
    
    def __init__(self, message: str, service_name: str, status_code: int = None):
        super().__init__(message, "EXTERNAL_SERVICE_ERROR")
        self.details["service_name"] = service_name
        if status_code:
            self.details["status_code"] = status_code