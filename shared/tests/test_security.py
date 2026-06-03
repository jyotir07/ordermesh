from shared.security import hash_password, verify_password


def test_hash_is_not_plaintext_and_verifies():
    hashed = hash_password("s3cret-pw")
    assert hashed != "s3cret-pw"
    assert verify_password("s3cret-pw", hashed)
    assert not verify_password("wrong", hashed)
