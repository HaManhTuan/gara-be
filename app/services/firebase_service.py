"""Firebase Admin SDK service for token verification"""

import json
from typing import Dict, Optional

import firebase_admin
from firebase_admin import auth, credentials
from fastapi import HTTPException, status

from app.config.settings import settings
from app.utils.logger import get_logger

logger = get_logger("firebase-service")


class FirebaseService:
    """Service for Firebase Admin SDK operations"""

    def __init__(self) -> None:
        self._initialized = False
        self._initialize_firebase()

    def _initialize_firebase(self) -> None:
        """Initialize Firebase Admin SDK"""
        try:
            if not self._initialized:
                # Check if already initialized
                if not firebase_admin._apps:
                    # Try to load from service account file
                    if settings.FIREBASE_SERVICE_ACCOUNT_PATH:
                        try:
                            cred = credentials.Certificate(settings.FIREBASE_SERVICE_ACCOUNT_PATH)
                            firebase_admin.initialize_app(cred)
                            logger.info("Firebase Admin SDK initialized from service account file")
                            self._initialized = True
                        except FileNotFoundError:
                            logger.warning(
                                f"Firebase service account file not found: {settings.FIREBASE_SERVICE_ACCOUNT_PATH}"
                            )
                    # Try to load from JSON string in environment variable
                    elif settings.FIREBASE_SERVICE_ACCOUNT_JSON:
                        service_account_info = json.loads(settings.FIREBASE_SERVICE_ACCOUNT_JSON)
                        cred = credentials.Certificate(service_account_info)
                        firebase_admin.initialize_app(cred)
                        logger.info("Firebase Admin SDK initialized from environment variable")
                        self._initialized = True
                    else:
                        logger.warning(
                            "Firebase credentials not configured. "
                            "Set FIREBASE_SERVICE_ACCOUNT_PATH or FIREBASE_SERVICE_ACCOUNT_JSON"
                        )
                        return

                if self._initialized:
                    logger.info("Firebase service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firebase Admin SDK: {str(e)}")
            # Don't raise - allow app to start without Firebase

    async def verify_firebase_token(self, id_token: str) -> Dict[str, any]:
        """
        Verify Firebase ID token and return decoded token data

        Args:
            id_token: Firebase ID token from client

        Returns:
            Dict containing user information from Firebase token

        Raises:
            HTTPException: If token is invalid or verification fails
        """
        if not self._initialized:
            logger.error("Firebase service not initialized")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Firebase service not configured",
            )

        try:
            # Verify the token
            decoded_token = auth.verify_id_token(id_token)

            logger.info(f"Firebase token verified successfully for user: {decoded_token.get('uid')}")

            return {
                "uid": decoded_token.get("uid"),
                "email": decoded_token.get("email"),
                "email_verified": decoded_token.get("email_verified", False),
                "name": decoded_token.get("name"),
                "picture": decoded_token.get("picture"),
                "phone_number": decoded_token.get("phone_number"),
                "provider_id": decoded_token.get("firebase", {}).get("sign_in_provider"),
            }

        except auth.InvalidIdTokenError:
            logger.warning("Invalid Firebase ID token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Firebase token",
            )
        except auth.ExpiredIdTokenError:
            logger.warning("Expired Firebase ID token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Firebase token has expired",
            )
        except auth.RevokedIdTokenError:
            logger.warning("Revoked Firebase ID token")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Firebase token has been revoked",
            )
        except auth.CertificateFetchError:
            logger.error("Error fetching Firebase certificates")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying Firebase token",
            )
        except Exception as e:
            logger.error(f"Unexpected error verifying Firebase token: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error verifying Firebase token",
            )

    async def get_user_by_uid(self, uid: str) -> Optional[Dict[str, any]]:
        """
        Get Firebase user by UID

        Args:
            uid: Firebase user UID

        Returns:
            Dict containing user information or None
        """
        try:
            user_record = auth.get_user(uid)
            return {
                "uid": user_record.uid,
                "email": user_record.email,
                "email_verified": user_record.email_verified,
                "display_name": user_record.display_name,
                "phone_number": user_record.phone_number,
                "photo_url": user_record.photo_url,
                "disabled": user_record.disabled,
            }
        except auth.UserNotFoundError:
            logger.warning(f"Firebase user not found: {uid}")
            return None
        except Exception as e:
            logger.error(f"Error fetching Firebase user: {str(e)}")
            return None


# Create singleton instance
firebase_service = FirebaseService()
