import pytest

from bot.cogs.register import _failure_message, _is_valid_kanidm_name
from bot.kanidm import KanidmError


@pytest.mark.parametrize("name", ["jdoe", "j", "j.doe-1_x", "a" * 64])
def test_valid_names(name: str) -> None:
    assert _is_valid_kanidm_name(name)


@pytest.mark.parametrize(
    "name",
    [
        "",
        "1abc",
        ".abc",
        "JDoe",
        "j doe",
        "j@doe",
        "a" * 65,
        "root",
        "admin",
        "abcdef12-abcd-abcd-abcd-abcdef123456",
    ],
)
def test_invalid_names(name: str) -> None:
    assert not _is_valid_kanidm_name(name)


def test_failure_message_hides_kanidm_detail() -> None:
    conflict = _failure_message(KanidmError(409, "secret internals"))
    other = _failure_message(KanidmError(500, "secret internals"))
    assert "already taken" in conflict
    assert "secret internals" not in conflict + other
