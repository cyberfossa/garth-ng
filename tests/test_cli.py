import sys

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


@pytest.mark.skip(reason="deferred to Task 12")
def test_login_command(monkeypatch, capsys):
    pass
