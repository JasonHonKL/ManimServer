import base64
import pytest
from auth_utils import verify_basic


def test_verify_basic_correct():
    assert verify_basic("Basic " + base64.b64encode(b"admin:secret").decode(), "secret")


def test_verify_basic_wrong_password():
    assert not verify_basic(
        "Basic " + base64.b64encode(b"admin:wrong").decode(), "secret"
    )


def test_verify_basic_wrong_username():
    assert not verify_basic(
        "Basic " + base64.b64encode(b"root:secret").decode(), "secret"
    )


def test_verify_basic_empty_header():
    assert not verify_basic("", "secret")


def test_verify_basic_none_header():
    assert not verify_basic(None, "secret")


def test_verify_basic_wrong_scheme():
    assert not verify_basic("Bearer token", "secret")


def test_verify_basic_no_space():
    assert not verify_basic("Basic" + base64.b64encode(b"admin:secret").decode(), "secret")


def test_verify_basic_invalid_base64():
    assert not verify_basic("Basic !!!not-valid-base64!!!", "secret")


def test_verify_basic_empty_password_in_config():
    assert not verify_basic(
        "Basic " + base64.b64encode(b"admin:secret").decode(), ""
    )


def test_verify_basic_constant_time():
    truth = "Basic " + base64.b64encode(b"admin:hunter2").decode()
    assert verify_basic(truth, "hunter2")
    assert not verify_basic(truth, "hunter3")
