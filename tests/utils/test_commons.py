import pytest

from src.utils.commons import hex_to_rgb, getbaseurl

@pytest.mark.parametrize("hex, expected", [
    ("#FF0000", (255, 0, 0)),
    ("#00FF00", (0, 255, 0)),
    ("#0000FF", (0, 0, 255))
])
def test_hex_to_rgb(hex : str, expected : str):
    assert hex_to_rgb(hex) == expected

@pytest.mark.parametrize("url, expected", [
    ("https://example.com/some/kind/of/page", "https://example.com")
])
def test_getbaseurl(url : str, expected : str):
    assert getbaseurl(url) == expected