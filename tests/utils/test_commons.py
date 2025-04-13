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
    # Base cases
    ("https://example.com/some/kind/of/page",   "https://example.com"),
    ("http://example.com/some/kind/of/page",    "http://example.com"),
    ("www.example.com/some/kind/of/page",       "www.example.com"),

    # Nessun path
    ("https://example.com",                     "https://example.com"),
    ("http://example.com",                      "http://example.com"),
    ("www.example.com",                         "www.example.com"),

    # Con porta
    ("https://example.com:8080/page",           "https://example.com:8080"),
    ("http://localhost:3000/home",              "http://localhost:3000"),

    # Con sottodomini
    ("https://sub.example.com/path",            "https://sub.example.com"),
    ("http://api.v1.example.com/resource",      "http://api.v1.example.com"),

    # Con query string e/o fragment
    ("https://example.com/path?query=1",        "https://example.com"),
    ("http://example.com/page#section",         "http://example.com"),

    # Con solo dominio e query
    ("https://example.com?key=value",           "https://example.com"),

    ("ftp://example.com/resource",              "ftp://example.com"),

    # URL malformato (fallback)
    ("not a real url",                          "not a real url"),
])
def test_getbaseurl(url : str, expected : str):
    assert getbaseurl(url) == expected