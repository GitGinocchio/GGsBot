To add a filter for certain loggers with specific names, you can create a custom `Filter` class and apply it to the desired loggers.

Here's an example of how you can do this:
```py
class LoggerNameFilter(logging.Filter):
    def __init__(self, allowed_loggers=None):
        self.allowed_loggers = allowed_loggers if allowed_loggers else []

    def filter(self, record):
        logger_name = record.name
        return logger_name in self.allowed_loggers

# Create a filter for loggers named "my_app" and "another_app"
my_filter = LoggerNameFilter(allowed_loggers=["my_app", "another_app"])

# Apply the filter to the desired loggers
logger1 = getlogger("my_app")
logger2 = getlogger("another_app")

for logger in [logger1, logger2]:
    logger.addFilter(my_filter)
```
In this example, we define a `LoggerNameFilter` class that takes an optional list of allowed logger names. The `filter()` method checks if the logger name matches one of the allowed names and returns `True` if it does, or `False` otherwise.

We then create a filter instance with the desired allowed loggers and apply it to the two specific loggers (`logger1` and `logger2`) using the `addFilter()` method.

Note that you can also use this filter class to filter out log messages from certain loggers by passing an empty list of allowed loggers. For example:
```py
my_filter = LoggerNameFilter(allowed_loggers=[])
```
This would prevent any log messages from being processed for loggers with names matching the allowed loggers.

You can also use this filter class to filter out log messages based on other criteria, such as log levels or message contents. For example:
```py
class MessageContentFilter(logging.Filter):
    def __init__(self, allowed_message_contents=None):
        self.allowed_message_contents = allowed_message_contents if allowed_message_contents else []

    def filter(self, record):
        return any(msg in record.msg for msg in self.allowed_message_contents)
```
This `MessageContentFilter` class filters out log messages that do not contain specific message contents. You can apply this filter to a logger using the same `addFilter()` method.