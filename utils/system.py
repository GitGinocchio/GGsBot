from typing import Literal
import platform

OS = platform.platform().split('-')[0]

ARCH = 'x64' if '64' in platform.architecture()[0] else 'x32'