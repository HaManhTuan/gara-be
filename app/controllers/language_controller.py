"""
Language controller for handling language-related operations.

This controller manages language switching and provides information about
supported languages in the application.
"""

from fastapi import APIRouter

from app.exceptions import ValidationException
from app.middlewares.language_middleware import get_current_language, set_current_language
from app.schemas.common import ResponseBuilder, SuccessResponse
from app.schemas.languages import (
    ChangeLanguageRequest,
    ChangeLanguageResponse,
    LanguageInfo,
    SupportedLanguagesResponse,
)
from app.utils.i18n import __, get_supported_languages, is_language_supported
from app.utils.tracing import get_trace_logger

# Create router
router = APIRouter()

# Initialize logger
logger = get_trace_logger("language-controller")


@router.get("/supported", response_model=SuccessResponse[SupportedLanguagesResponse])  # type: ignore[misc]
async def get_supported_languages_endpoint() -> SuccessResponse[SupportedLanguagesResponse]:
    """
    Get list of supported languages with their information.

    Returns:
        SuccessResponse containing supported languages and current language info
    """
    logger.info("Retrieving supported languages")

    # Get supported languages with their details
    supported_languages = []
    for lang_code in get_supported_languages():
        # Map language codes to their display names
        lang_names = {
            "en": {"name": "English", "native_name": "English"},
            "jp": {"name": "Japanese", "native_name": "日本語"},
        }

        lang_info = lang_names.get(lang_code, {"name": lang_code.upper(), "native_name": lang_code.upper()})

        supported_languages.append(
            LanguageInfo(
                code=lang_code,
                name=lang_info["name"],
                native_name=lang_info["native_name"],
            )
        )

    response_data = SupportedLanguagesResponse(
        supported_languages=supported_languages,
        current_language=get_current_language(),
        message=__("language.current"),
    )

    return ResponseBuilder.success(message=__("language.supported_retrieved"), data=response_data)


@router.post("/change", response_model=SuccessResponse[ChangeLanguageResponse])  # type: ignore[misc]
async def change_language(
    language_request: ChangeLanguageRequest,
) -> SuccessResponse[ChangeLanguageResponse]:
    """
    Change the current application language.

    Args:
        language_request: Language change request data

    Returns:
        SuccessResponse containing the new language and success message

    Raises:
        ValidationException: If the requested language is not supported
    """
    language = language_request.language

    logger.info(f"Language change requested to: {language}")

    if not is_language_supported(language):
        logger.warning(f"Unsupported language requested: {language}")
        raise ValidationException(
            message=__("language.not_supported"),
            details={
                "requested_language": language,
                "supported_languages": get_supported_languages(),
            },
        )

    # Set the language in context
    set_current_language(language)

    logger.info(f"Language successfully changed to: {language}")

    response_data = ChangeLanguageResponse(language=language, message=__("language.changed"))

    return ResponseBuilder.success(message=__("language.change_success"), data=response_data)
