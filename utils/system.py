from typing import Literal
import platform

OS : Literal['Windows','Linux'] = platform.platform().split('-')[0]

ARCH = Literal['x64','x32'] = 'x64' if '64' in platform.architecture()[0] else 'x32'