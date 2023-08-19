"""A simple bot what for to talk to 🤖❤️✨"""
__version__ = "v0.1.5"

from jonbot.system.configure_logging import configure_logging, LogLevel

configure_logging(LogLevel.TRACE)


def get_logger():
    import logging
    return logging.getLogger(__name__)
