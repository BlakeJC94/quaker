from unittest import mock

import pytest

from quaker.cli import run


@mock.patch("quaker.Client.execute")
@pytest.mark.parametrize("args", ["-h", "--help", "", "download --help"])
def test_cli_help(mock_execute, capsys, args):
    """Test that the help dialog is printed to stderr if given help flag."""
    with pytest.raises(SystemExit) as exc_info:
        run(args.split())
    assert exc_info.value.args[0] == 0
    assert "usage:" in capsys.readouterr().out
    mock_execute.assert_not_called()


@mock.patch("quaker.Client.execute")
@pytest.mark.parametrize(
    "args",
    [
        "foo bar",
        "--badarg foo bar",
        "--badarg",
        "download foo bar",
    ],
)
def test_cli_raise_invalid_args(mock_execute, args):
    with pytest.raises(SystemExit) as exc_info:
        run(args.split())
    assert exc_info.value.args[0] == 2
    mock_execute.assert_not_called()


@mock.patch("quaker.Client.execute")
def test_cli_empty_query(mock_execute):
    args = "download"
    run(args.split())
    mock_execute.assert_called()


# TODO test single page query works
# TODO test multipage page query works
