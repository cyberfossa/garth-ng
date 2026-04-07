import sys
from unittest.mock import MagicMock

import pytest

from garth.cli import main


def test_help_flag(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["garth", "-h"])
    with pytest.raises(SystemExit) as excinfo:
        main()
    assert excinfo.value.code == 0
    out, err = capsys.readouterr()
    assert "usage:" in out.lower()


def test_no_args_prints_help(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["garth"])
    main()
    out, err = capsys.readouterr()
    assert "usage:" in out.lower()


def test_login_command(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["garth", "login"])
    fake_token_string = "fake_token_json_string"

    mock_login = MagicMock()
    monkeypatch.setattr("garth.login", mock_login)

    mock_dumps = MagicMock(return_value=fake_token_string)
    monkeypatch.setattr("garth.client.dumps", mock_dumps)

    mock_input = MagicMock(return_value="test@example.com")
    mock_getpass = MagicMock(return_value="password123")
    monkeypatch.setattr("builtins.input", mock_input)
    monkeypatch.setattr("getpass.getpass", mock_getpass)

    main()

    out, err = capsys.readouterr()
    assert fake_token_string in out
    mock_login.assert_called_once()
    args, kwargs = mock_login.call_args
    assert args == ("test@example.com", "password123")
    assert "prompt_mfa" in kwargs
    mfa_fn = kwargs["prompt_mfa"]
    assert callable(mfa_fn)
    mock_input.reset_mock()
    mock_input.return_value = "123456"
    assert mfa_fn() == "123456"
    mock_input.assert_called_once_with("Enter MFA code: ")
    mock_dumps.assert_called_once()
