import sys
import time

import logging
import logging.config
import logging.handlers


class RhombusFormatter(logging.Formatter):
    def __init__(self):
        super(RhombusFormatter, self).__init__(
            fmt="%(asctime)s [%(threadName)s] %(levelname)s %(name)s - %(message)s")

    def formatTime(self, record, datefmt=None):
        ct = self.converter(record.created)
        if datefmt:
            s = time.strftime(datefmt, ct)
        else:
            t = time.strftime("%Y-%m-%d %H:%M:%S", ct)
            s = "%s.%03d %s" % (t, record.msecs, time.strftime("%Z", ct))
        return s


# Initialize the root logger to use our formatter so that all loggers
# created have the same format.
# Also set our default log level to INFO.
__custom_handler = logging.StreamHandler(sys.stdout)
__custom_handler.setFormatter(RhombusFormatter())

__tmp_root_logger = logging.getLogger()
__tmp_root_logger.addHandler(__custom_handler)
__tmp_root_logger.setLevel("WARNING")
del __tmp_root_logger

__tmp_rhombus_logger = logging.getLogger("rhombus")
__tmp_rhombus_logger.setLevel("INFO")
del __tmp_rhombus_logger


# A simple wrapper to get loggers so that we can adjust
# if needed. This makes the way to get a logger:
# rhombus_logging.get_logger("name")
def get_logger(logger_name=None):
    return logging.getLogger(logger_name)