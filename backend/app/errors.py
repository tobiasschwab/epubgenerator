from __future__ import annotations


class DomainError(Exception):
    """Basisklasse für fachliche Fehler mit stabilem Code und HTTP-Status."""

    code = "domain_error"
    status_code = 400

    def __init__(self, detail: str) -> None:
        super().__init__(detail)
        self.detail = detail


class NotFoundError(DomainError):
    code = "not_found"
    status_code = 404


class ValidationError(DomainError):
    code = "validation_error"
    status_code = 422


class ConflictError(DomainError):
    code = "conflict"
    status_code = 409


class AIUnavailableError(DomainError):
    """KI ist nicht konfiguriert (kein API-Key) oder der Anbieter schlug fehl."""

    code = "ai_unavailable"
    status_code = 503
