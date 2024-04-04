import platform


def getos():
    print(platform.architecture())
    print(platform.platform())
    print(platform.machine())
    print(platform.processor())