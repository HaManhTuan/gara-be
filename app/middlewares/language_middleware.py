"""
Language detection middleware for FastAPI.

This middleware detects the user's preferred language from various sources
and stores it in the request context for use throughout the application.
"""

from contextvars import ContextVar
from typing import Any, Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.utils.i18n import DEFAULT_LANGUAGE, is_language_supported
from app.utils.tracing import get_trace_logger

logger = get_trace_logger("i18n-middleware")

# Context variable to store the current language
current_language: ContextVar[str] = ContextVar("current_language", default=DEFAULT_LANGUAGE)


def get_current_language() -> str:
    """Get the current language from context."""
    return current_language.get(DEFAULT_LANGUAGE)


def set_current_language(language: str) -> None:
    """Set the current language in context."""
    if is_language_supported(language):
        current_language.set(language)
    else:
        logger.warning(f"Unsupported language: {language}, using default: {DEFAULT_LANGUAGE}")
        current_language.set(DEFAULT_LANGUAGE)


class LanguageDetectionMiddleware(BaseHTTPMiddleware):
    """
    Middleware to detect and set the user's preferred language.

    Language detection priority:
    1. Query parameter 'lang' (e.g., ?lang=jp)
    2. Header 'Accept-Language' (e.g., Accept-Language: jp,en;q=0.9)
    3. Cookie 'language' (e.g., language=jp)
    4. Default language (en)
    """

    def __init__(self, app: Any, default_language: str = DEFAULT_LANGUAGE) -> None:
        super().__init__(app)
        self.default_language = default_language

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process the request and detect language."""
        language = self._detect_language(request)
        set_current_language(language)

        logger.debug(f"Detected language: {language} for request: {request.url.path}")

        response = await call_next(request)

        # Set language cookie for future requests
        response.set_cookie(
            key="language",
            value=language,
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=False,  # Allow client-side access
            samesite="lax",
        )

        return response

    def _detect_language(self, request: Request) -> str:
        """
        Detect the user's preferred language from various sources.

        Args:
            request: FastAPI request object

        Returns:
            Detected language code
        """
        # 1. Check query parameter
        lang_param = request.query_params.get("lang")
        if lang_param and is_language_supported(lang_param):
            logger.debug(f"Language detected from query parameter: {lang_param}")
            return lang_param  # type: ignore[no-any-return]

        # 2. Check Accept-Language header
        accept_language = request.headers.get("Accept-Language", "")
        if accept_language:
            detected_lang = self._parse_accept_language(accept_language)
            if detected_lang:
                logger.debug(f"Language detected from Accept-Language header: {detected_lang}")
                return detected_lang

        # 3. Check language cookie
        language_cookie = request.cookies.get("language")
        if language_cookie and is_language_supported(language_cookie):
            logger.debug(f"Language detected from cookie: {language_cookie}")
            return language_cookie  # type: ignore[no-any-return]

        # 4. Default language
        logger.debug(f"Using default language: {self.default_language}")
        return self.default_language

    def _parse_accept_language(self, accept_language: str) -> Optional[str]:
        """
        Parse Accept-Language header to find the best supported language.

        Args:
            accept_language: Accept-Language header value

        Returns:
            Best supported language code or None
        """
        # Parse Accept-Language header (e.g., "jp,en;q=0.9,fr;q=0.8")
        languages = []
        for lang_part in accept_language.split(","):
            lang_part = lang_part.strip()
            if ";" in lang_part:
                lang, q_value = lang_part.split(";", 1)
                lang = lang.strip()
                try:
                    # Extract quality value (e.g., "q=0.9" -> 0.9)
                    quality = float(q_value.split("=", 1)[1].strip())
                except (ValueError, IndexError):
                    quality = 1.0
            else:
                lang = lang_part.strip()
                quality = 1.0

            # Extract language code (e.g., "jp-JP" -> "jp")
            lang_code = lang.split("-")[0].lower()
            languages.append((lang_code, quality))

        # Sort by quality (highest first)
        languages.sort(key=lambda x: x[1], reverse=True)

        # Find the first supported language
        for lang_code, _ in languages:
            if is_language_supported(lang_code):
                return lang_code

        return None


def setup_language_middleware(app: Any, default_language: str = DEFAULT_LANGUAGE) -> None:
    """
    Setup language detection middleware for the FastAPI app.

    Args:
        app: FastAPI application instance
        default_language: Default language code
    """
    app.add_middleware(LanguageDetectionMiddleware, default_language=default_language)
    logger.info(f"Language detection middleware added with default language: {default_language}")
