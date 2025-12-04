"""
Language schemas package.

This package contains all language-related schemas including
request/response schemas for language operations.
"""

# Request/Response schemas
from .request import ChangeLanguageRequest, ChangeLanguageResponse, LanguageInfo, SupportedLanguagesResponse

__all__ = [
    # Request schemas
    "ChangeLanguageRequest",
    # Response schemas
    "LanguageInfo",
    "SupportedLanguagesResponse",
    "ChangeLanguageResponse",
]
