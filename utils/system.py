from typing import Literal
import platform

def getos() -> Literal['Windows','Linux']:
    return platform.platform().split('-')[0]

def getarch() -> Literal['x64','x32']:
    return 'x64' if '64' in platform.architecture()[0] else 'x32'