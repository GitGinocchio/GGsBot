


def fromseconds(s : float):
    """convert from a given time in `seconds` to an `hours`, `minutes`, `seconds` and `milliseconds` format"""
    hours = int(s // 3600)
    minutes = int((s % 3600) // 60)
    seconds = int(s % 60)
    milliseconds = int((s % 1) * 1000)
    return (hours, minutes, seconds, milliseconds)