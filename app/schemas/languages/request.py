"""
Language request and response schemas.

This module contains schemas for API requests and responses
for language-related operations.
"""

from typing import List

from pydantic import Field

from app.schemas.common.base_schema import BaseSchema

# ===== REQUEST SCHEMAS (Data In) =====


class ChangeLanguageRequest(BaseSchema):
    """Request schema for changing language"""

    language: str = Field(..., description="Language code to change to", min_length=2, max_length=5)


# ===== RESPONSE SCHEMAS (Data Out) =====


class LanguageInfo(BaseSchema):
    """Language information schema"""

    code: str = Field(..., description="Language code (e.g., 'en', 'jp')")
    name: str = Field(..., description="Language name (e.g., 'English', 'Japanese')")
    native_name: str = Field(..., description="Native language name")


class SupportedLanguagesResponse(BaseSchema):
    """Response schema for supported languages endpoint"""

    supported_languages: List[LanguageInfo] = Field(..., description="List of supported languages")
    current_language: str = Field(..., description="Current language code")
    message: str = Field(..., description="Response message")


class ChangeLanguageResponse(BaseSchema):
    """Response schema for language change"""

    language: str = Field(..., description="New language code")
    message: str = Field(..., description="Success message")
