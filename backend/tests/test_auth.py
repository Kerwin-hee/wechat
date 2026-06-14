"""测试认证模块"""

import pytest
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestSecurity:
    """安全模块测试"""

    def test_hash_and_verify_password(self):
        password = "test_password_123"
        hashed = hash_password(password)
        assert hashed != password
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)

    def test_create_and_decode_access_token(self):
        user_id = "test-user-123"
        token = create_access_token(user_id)
        assert token is not None

        payload = decode_token(token)
        assert payload is not None
        assert payload.sub == user_id
        assert payload.type == "access"

    def test_create_and_decode_refresh_token(self):
        user_id = "test-user-456"
        token = create_refresh_token(user_id)

        payload = decode_token(token)
        assert payload is not None
        assert payload.sub == user_id
        assert payload.type == "refresh"

    def test_decode_invalid_token(self):
        assert decode_token("invalid-token-string") is None

    def test_different_passwords_hash_differently(self):
        h1 = hash_password("pass1")
        h2 = hash_password("pass1")
        # bcrypt 每次生成不同的盐
        assert h1 != h2
        assert verify_password("pass1", h1)
        assert verify_password("pass1", h2)
