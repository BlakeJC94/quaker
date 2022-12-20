from unittest import mock

import pytest

from quaker.cli import run


@mock.patch("quaker.cli.download")
@pytest.mark.parametrize("args", ["-h", "--help", "", "download --help"])
def test_cli_help(mock_download, capsys, args):
    """Test that the help dialog is printed to stderr if given help flag."""
    with pytest.raises(SystemExit) as exc_info:
        run(args.split())
    assert exc_info.value.args[0] == 0
    assert "usage:" in capsys.readouterr().out
    mock_download.assert_not_called()


@mock.patch("quaker.cli.download")
@pytest.mark.parametrize(
    "args",
    [
        "foo bar",
        "--badarg foo bar",
        "--badarg",
        "download foo bar",
    ],
)
def test_cli_raise_invalid_args(mock_download, args):
    with pytest.raises(SystemExit) as exc_info:
        run(args.split())
    assert exc_info.value.args[0] == 2
    mock_download.assert_not_called()


@mock.patch("quaker.cli.download")
def test_cli_empty_query(mock_download):
    args = "download"
    run(args.split())
    mock_download.assert_called()


# TODO test single page query works
# TODO test multipage page query works
