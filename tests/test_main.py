from ast import arg
from src.main import run, run_webserver_only
from argparse import Namespace
import signal
import pytest
import time

"""

@pytest.mark.parametrize("kwargs, expected_result", [
    ({ "bot" : False },     "Running bot and webserver"),
    ({ "bot" : True },      "Running bot only")
])
def test_run(kwargs: dict, expected_result: str):
    with pytest.raises(TimeoutError) as e:
        signal.signal(signal.CTRL_C_EVENT, lambda signum, frame: None)
        run(Namespace(**kwargs))

    #assert e.type == TimeoutError, e.type
    #assert str(e.value) == 0

@pytest.mark.parametrize("kwargs, expected_result", [
    ({"address" : "127.0.0.1", "port" : 8080, "proto" : "http", "debug" : True}, "Running webserver")
])
def test_run_webserver_only(kwargs: dict, expected_result: str):
    with pytest.raises(TimeoutError) as e:
        signal.signal(signal.SIGABRT, lambda signum, frame: None)
        run_webserver_only(Namespace(**kwargs))
    
    #assert e.type == TimeoutError, e.type
    #assert str(e.value) == 1

"""