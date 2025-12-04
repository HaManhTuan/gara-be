"""
Internationalization (i18n) utilities for handling multiple languages.

This module provides functions to load and retrieve translated messages
from JSON files based on the user's language preference.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from app.utils.tracing import get_trace_logger

logger = get_trace_logger("i18n")

# Supported languages
SUPPORTED_LANGUAGES = ["en", "jp"]
DEFAULT_LANGUAGE = "en"

# Cache for loaded translations
_translation_cache: Dict[str, Dict[str, Any]] = {}


def get_locales_path() -> Path:
    """Get the path to the locales directory."""
    return Path(__file__).parent.parent.parent / "locales"


def load_translations(language: str) -> Dict[str, Any]:
    """
    Load translations for a specific language.

    Args:
        language: Language code (e.g., 'en', 'es', 'fr', 'vi')

    Returns:
        Dictionary containing all translations for the language
    """
    if language not in SUPPORTED_LANGUAGES:
        logger.warning(f"Unsupported language: {language}, falling back to {DEFAULT_LANGUAGE}")
        language = DEFAULT_LANGUAGE

    # Check cache first
    if language in _translation_cache:
        return _translation_cache[language]

    locales_path = get_locales_path()
    messages_file = locales_path / language / "LC_MESSAGES" / "messages.json"

    if not messages_file.exists():
        logger.error(f"Translation file not found: {messages_file}")
        # Fallback to default language
        if language != DEFAULT_LANGUAGE:
            return load_translations(DEFAULT_LANGUAGE)
        return {}

    try:
        with open(messages_file, "r", encoding="utf-8") as f:
            translations = json.load(f)
            _translation_cache[language] = translations
            logger.debug(f"Loaded translations for language: {language}")
            return translations  # type: ignore[no-any-return]
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading translations for {language}: {str(e)}")
        # Fallback to default language
        if language != DEFAULT_LANGUAGE:
            return load_translations(DEFAULT_LANGUAGE)
        return {}


def get_message(key: str, language: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """
    Get a translated message by key.

    Args:
        key: Message key in dot notation (e.g., 'auth.login_success')
        language: Language code
        **kwargs: Variables to interpolate in the message

    Returns:
        Translated message string

    Examples:
        >>> get_message('auth.login_success', 'en')
        'Login successful'
        >>> get_message('auth.login_success', 'es')
        'Inicio de sesión exitoso'
    """
    translations = load_translations(language)

    # Navigate through nested keys
    keys = key.split(".")
    message: Any = translations

    try:
        for k in keys:
            message = message[k]
    except (KeyError, TypeError):
        logger.warning(f"Translation key not found: {key} for language: {language}")
        # Fallback to default language
        if language != DEFAULT_LANGUAGE:
            return get_message(key, DEFAULT_LANGUAGE, **kwargs)
        return key  # Return the key itself as fallback

    # Handle string interpolation if kwargs are provided
    if kwargs and isinstance(message, str):
        try:
            return message.format(**kwargs)
        except (KeyError, ValueError) as e:
            logger.warning(f"Error formatting message '{key}': {str(e)}")
            return message

    return str(message) if message is not None else key


def get_supported_languages() -> list[str]:
    """Get list of supported language codes."""
    return SUPPORTED_LANGUAGES.copy()


def is_language_supported(language: str) -> bool:
    """Check if a language is supported."""
    return language in SUPPORTED_LANGUAGES


def get_default_language() -> str:
    """Get the default language code."""
    return DEFAULT_LANGUAGE


def clear_translation_cache() -> None:
    """Clear the translation cache. Useful for testing or reloading translations."""
    global _translation_cache
    _translation_cache.clear()
    logger.debug("Translation cache cleared")


def reload_translations(language: Optional[str] = None) -> None:
    """
    Reload translations for a specific language or all languages.

    Args:
        language: Language code to reload, or None to reload all
    """
    if language:
        if language in _translation_cache:
            del _translation_cache[language]
        load_translations(language)
    else:
        clear_translation_cache()
        for lang in SUPPORTED_LANGUAGES:
            load_translations(lang)
    logger.debug(f"Reloaded translations for: {language or 'all languages'}")


# Convenience functions for common message categories
def get_auth_message(key: str, language: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Get an authentication-related message."""
    return get_message(f"auth.{key}", language, **kwargs)


def get_user_message(key: str, language: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Get a user-related message."""
    return get_message(f"user.{key}", language, **kwargs)


def get_validation_message(key: str, language: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Get a validation-related message."""
    return get_message(f"validation.{key}", language, **kwargs)


def get_general_message(key: str, language: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Get a general message."""
    return get_message(f"general.{key}", language, **kwargs)


def get_optimistic_lock_message(key: str, language: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Get an optimistic locking-related message."""
    return get_message(f"optimistic_lock.{key}", language, **kwargs)


def get_language_message(key: str, language: str = DEFAULT_LANGUAGE, **kwargs: Any) -> str:
    """Get a language-related message."""
    return get_message(f"language.{key}", language, **kwargs)


def __(key: str, **kwargs: Any) -> str:
    """
    Convenience function to get translated message using current language.

    This is the main function to use for translations. It automatically
    detects the current language from context and returns the translated message.

    Args:
        key: Message key in dot notation (e.g., 'auth.login_success')
        **kwargs: Variables to interpolate in the message

    Returns:
        Translated message string

    Examples:
        >>> __("auth.login_success")
        'Login successful'  # or 'ログインに成功しました' if current language is 'jp'
        >>> __("user.welcome", name="John")
        'Welcome John!'  # with interpolation
    """
    from app.middlewares.language_middleware import get_current_language

    current_lang = get_current_language()
    return get_message(key, current_lang, **kwargs)


# Convenience functions using current language (no need to pass language parameter)
def auth_message(key: str, **kwargs: Any) -> str:
    """Get an authentication-related message using current language."""
    return __(f"auth.{key}", **kwargs)


def user_message(key: str, **kwargs: Any) -> str:
    """Get a user-related message using current language."""
    return __(f"user.{key}", **kwargs)


def validation_message(key: str, **kwargs: Any) -> str:
    """Get a validation-related message using current language."""
    return __(f"validation.{key}", **kwargs)


def general_message(key: str, **kwargs: Any) -> str:
    """Get a general message using current language."""
    return __(f"general.{key}", **kwargs)


def optimistic_lock_message(key: str, **kwargs: Any) -> str:
    """Get an optimistic locking-related message using current language."""
    return __(f"optimistic_lock.{key}", **kwargs)


def language_message(key: str, **kwargs: Any) -> str:
    """Get a language-related message using current language."""
    return __(f"language.{key}", **kwargs)
