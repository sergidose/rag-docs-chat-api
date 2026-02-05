from src.config import APP_NAME


def test_sanity():
    assert isinstance(APP_NAME, str)
    assert APP_NAME
