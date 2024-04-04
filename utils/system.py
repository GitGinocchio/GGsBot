import platform


def getos():
    return platform.platform().split('-')[0]

def getarch():
    return 'x64' if '64' in platform.architecture()[0] else 'x32'