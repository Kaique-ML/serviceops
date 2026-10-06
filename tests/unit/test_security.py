from serviceops.auth.security import hash_password, make_session, parse_session, verify_password


def test_password_and_tamper_resistant_session():
    encoded = hash_password("correct horse")
    assert verify_password("correct horse", encoded)
    assert not verify_password("wrong", encoded)
    token = make_session("user", "workspace")
    assert parse_session(token) == {"u": "user", "w": "workspace"}
    assert parse_session(token + "x") is None
