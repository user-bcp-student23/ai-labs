import pytest

from app.constants import TOKEN_AUDIENCE, TOKEN_ISSUER, TOKEN_SECRET_ENV
from app.main import create_app
from app.security import InvalidTokenError, load_token_secret, sign_claims, verify_token

SECRET = "unit-test-secret"
NOW = 1_700_000_000


def claims(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "sub": "student",
        "role": "STUDENT",
        "exp": NOW + 3600,
        "iss": TOKEN_ISSUER,
        "aud": TOKEN_AUDIENCE,
    }
    base.update(overrides)
    return base


def test_verifies_valid_signed_token() -> None:
    token = sign_claims(claims(), SECRET)
    assert verify_token(token, SECRET, now=NOW)["sub"] == "student"


def test_rejects_token_signed_with_other_secret() -> None:
    token = sign_claims(claims(), "other-secret")
    with pytest.raises(InvalidTokenError):
        verify_token(token, SECRET, now=NOW)


def test_rejects_token_without_separator() -> None:
    with pytest.raises(InvalidTokenError):
        verify_token("sin-firma", SECRET, now=NOW)


def test_rejects_altered_payload() -> None:
    token = sign_claims(claims(), SECRET)
    signature = token.partition(".")[2]
    forged = sign_claims(claims(role="TRAINER"), "other-secret").partition(".")[0]
    with pytest.raises(InvalidTokenError):
        verify_token(f"{forged}.{signature}", SECRET, now=NOW)


def test_rejects_non_object_payload() -> None:
    with pytest.raises(InvalidTokenError):
        verify_token(sign_claims(["no", "objeto"], SECRET), SECRET, now=NOW)


def test_rejects_wrong_issuer_or_audience() -> None:
    with pytest.raises(InvalidTokenError):
        verify_token(sign_claims(claims(iss="otro"), SECRET), SECRET, now=NOW)
    with pytest.raises(InvalidTokenError):
        verify_token(sign_claims(claims(aud="otro"), SECRET), SECRET, now=NOW)


def test_rejects_missing_subject_or_role() -> None:
    with pytest.raises(InvalidTokenError):
        verify_token(sign_claims(claims(sub=""), SECRET), SECRET, now=NOW)
    with pytest.raises(InvalidTokenError):
        verify_token(sign_claims(claims(role=None), SECRET), SECRET, now=NOW)


def test_rejects_expired_or_missing_exp() -> None:
    with pytest.raises(InvalidTokenError):
        verify_token(sign_claims(claims(exp=NOW - 1), SECRET), SECRET, now=NOW)
    with pytest.raises(InvalidTokenError):
        verify_token(sign_claims(claims(exp="manana"), SECRET), SECRET, now=NOW)


def test_load_token_secret_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(TOKEN_SECRET_ENV, SECRET)
    assert load_token_secret() == SECRET


def test_load_token_secret_fails_when_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(TOKEN_SECRET_ENV, raising=False)
    with pytest.raises(RuntimeError):
        load_token_secret()


def test_create_app_fails_without_secret(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.delenv(TOKEN_SECRET_ENV, raising=False)
    with pytest.raises(RuntimeError):
        create_app(str(tmp_path / "workshop.db"), str(tmp_path / "uploads"))
