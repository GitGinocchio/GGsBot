import pytest
import json
import os

from src.utils.jsonfile import CustomDecoder, JsonFile, _JsonDict, _JsonList, cache



@pytest.fixture
def jsonfile():
    return JsonFile(fp='./config/config.json')

@pytest.fixture
def example_data():
    return """
    {
        "name": "John",
        // This is a single-line comment
        "age": 30,
        /* 
        * This is a multi-line comment
        * It can span multiple lines
        */ 
        "occupation" : {
            "type": "Developer"
            // This is another single-line comment
        },
        "languages": ["JavaScript", "Python", "Java"]
    }
    """

@pytest.fixture
def example_malformed_data():
    return """
    {
        "name": "John",
        // This is a single-line comment
        "age": 30   // HERE IS MISSING A COLON
        /* 
        * This is a multi-line comment
        * It can span multiple lines
        */ 
        "occupation" : {
            "type": "Developer"
            // This is another single-line comment
        },
        "languages": ["JavaScript", "Python", "Java"]
    }
    """

def test_jsonfile_creation(jsonfile : JsonFile):
    assert jsonfile.fp == os.path.realpath(os.path.normpath(jsonfile.fp)), f'Expected file path to be the same as the provided fp'
    assert cache.get(jsonfile.fp, None) is not None, f'Expected cache to contain the created JsonFile object'

    with pytest.raises(ValueError):
        _ = JsonFile('./file.txt')

def test_custom_decoder(jsonfile : JsonFile, example_data : str, example_malformed_data : str):
    decoded_data = CustomDecoder(jsonfile).decode(example_data)
    assert decoded_data == { "name": "John", "age": 30, "occupation": { "type": "Developer" }, "languages": ["JavaScript", "Python", "Java"]}
    assert isinstance(decoded_data['occupation'], _JsonDict)
    assert isinstance(decoded_data['languages'], _JsonList)
    assert type(decoded_data['name']) == str
    assert type(decoded_data['age']) == int
    

    with pytest.raises(json.decoder.JSONDecodeError):
        _ = CustomDecoder(jsonfile).decode(example_malformed_data)
