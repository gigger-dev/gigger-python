from datetime import UTC, datetime, timedelta

from fastapi import HTTPException
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError
from pydantic import BaseModel, EmailStr, ValidationError


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str


class JWTUserInfo(BaseModel):
    uuid: str
    email: str
    sub: str
    exp: datetime | None = None


class JWTAuthenticator:
    # TODO Adjust the payload. Add more information.
    def __init__(
        self,
        secret_key: str,
        access_token_expire_minutes: int = 30,
        algorithm: str = "HS256",
        REFRESH_TOKEN_EXPIRE_DAYS: int = 7,
    ):
        """
        Initialize the JWTAuthenticator with configurable parameters.

        Args:
            secret_key (str): The secret key used for signing JWT tokens.
            access_token_expire_minutes (int): The expiration time for access tokens in minutes.
            algorithm (str): The algorithm used for signing JWT tokens.
        """
        self.secret_key = secret_key
        self.access_token_expire_minutes = access_token_expire_minutes
        self.algorithm = algorithm
        self.REFRESH_TOKEN_EXPIRE_DAYS = REFRESH_TOKEN_EXPIRE_DAYS

    def create_access_token(self, user_info: JWTUserInfo) -> str:
        """
        Create a new JWT access token.

        Args:
            user_info (dict): The user Info.

        Returns:
            str: The JWT access token.
        """
        # Calculate token expiration time
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.now(UTC) + expires_delta
        user_info.exp = expire
        # Create token payload
        __token_payload = user_info.model_dump()

        # Generate JWT access token
        __access_token = jwt.encode(
            __token_payload, self.secret_key, algorithm=self.algorithm
        )
        return __access_token

    def create_access_token_only_with_email(self, email: EmailStr) -> str:
        """
        Create a new JWT access token.

        Args:
            user_info (dict): The user Info.

        Returns:
            str: The JWT access token.
        """
        # Calculate token expiration time
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.now(UTC) + expires_delta

        # Create token payload
        __token_payload = {"sub": email, "exp": expire}

        # Generate JWT access token
        __access_token = jwt.encode(
            __token_payload, self.secret_key, algorithm=self.algorithm
        )
        return __access_token

    def verify_access_token_only_with_email(self, token: str) -> dict:
        """
        Verify and decode the JWT access token.

        Args:
            token (str): The JWT access token to verify.

        Returns:
            dict: The decoded token payload.
        """
        try:
            # Decode JWT access token
            return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

        except ExpiredSignatureError:
            # Token has expired
            return {"error": "Token has expired"}
        except JWTError as e:
            # Token is invalid
            return {"error": f"Invalid token, {e}"}

    def create_refresh_token(self, user_info: JWTUserInfo) -> str:
        """
        Create a new refresh token.

        Args:
            user_info (dict): The user ID.

        Returns:
            str: The refresh token.
        """
        expires_delta = timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)
        expire = datetime.now(UTC) + expires_delta
        user_info.exp = expire
        refresh_token_payload = user_info.model_dump()
        __refresh_token = jwt.encode(
            refresh_token_payload, self.secret_key, algorithm="HS256"
        )
        return __refresh_token

    def verify_access_token(self, token: str) -> JWTUserInfo | dict:
        """
        Verify and decode the JWT access token.

        Args:
            token (str): The JWT access token to verify.

        Returns:
            dict: The decoded token payload.
        """
        try:
            # Decode JWT access token
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return JWTUserInfo.model_validate(payload)
        except ValidationError:
            return {"error": "Invalid identifier"}
        except ExpiredSignatureError:
            # Token has expired
            return {"error": "Token has expired"}
        except JWTError as e:
            # Token is invalid
            return {"error": f"Invalid token, {e}"}

    def refresh_tokens(self, refresh_token: str) -> TokenOut:
        """
        Refresh access and refresh tokens.

        Args:
            refresh_token (str): The refresh token.

        Returns:
            dict: Dictionary containing new access and refresh tokens.
        """
        try:
            # Decode the refresh token to extract user information
            decoded_token = jwt.decode(
                refresh_token, self.secret_key, algorithms=[self.algorithm]
            )
            user_info_dict = decoded_token
            user_info = JWTUserInfo.model_validate(user_info_dict)

            # TODO: check if refresh token is about to expire update the token.

            # Generate new access and refresh tokens
            new_access_token = self.create_access_token(user_info)

            return TokenOut(access_token=new_access_token, refresh_token=refresh_token)
        except ValidationError:
            raise HTTPException(status_code=401, detail="Invalid identifier")
        except ExpiredSignatureError as e:
            # Handle expired token
            raise e
        except JWTError as e:
            # Handle invalid token
            raise e

    def create_tokens(self, user_info: JWTUserInfo) -> TokenOut:
        """
        create access_token and refresh_token from user info.
        :param user_info:
        :return: (dict)
        """
        access_token = self.create_access_token(user_info)
        refresh_token = self.create_refresh_token(user_info)
        return TokenOut(access_token=access_token, refresh_token=refresh_token)


"""
# Example usage
"""
# if __name__ == "__main__":
#     authenticator = JWTAuthenticator(
#         secret_key="your-secret-key", access_token_expire_minutes=30, algorithm="HS256"
#     )
#     _user_info = {"id": 123, "email_service": "test@test.com", "role": "admin"}
#     _access_token = authenticator.create_access_token(user_info=_user_info)
#     _refresh_token = authenticator.create_refresh_token(user_info=_user_info)
#     print("Access Token:", _access_token)
#     print("Refresh Token:", _refresh_token)
#     token_payload = authenticator.verify_access_token(_access_token)
#     _refresh_payload = authenticator.verify_access_token(_refresh_token)
#     print("Token Payload:", token_payload)
#     print("Refresh Payload:", _refresh_payload)
