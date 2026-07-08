class DomainError(Exception):
    """Base class for domain-layer errors that API layers can map later."""


class DomainValidationError(DomainError):
    """Raised when service-level input is invalid or incomplete."""


ValidationError = DomainValidationError


class BusinessRuleViolation(DomainError):
    """Raised when a requested domain operation violates documented rules."""


class ResourceNotFound(DomainError):
    """Raised when a tenant-scoped resource cannot be found."""


class SlotNotAvailable(BusinessRuleViolation):
    """Raised when a requested booking slot cannot be reserved."""


class PricingNotFound(ResourceNotFound):
    """Raised when no active practitioner-service price matches the payer plan."""
