from app.security import hash_password, verify_password


def test_password_hash_verifies():
    hashed = hash_password("supersecret")
    assert verify_password("supersecret", hashed)


def test_wrong_password_fails():
    hashed = hash_password("supersecret")
    assert not verify_password("wrong", hashed)