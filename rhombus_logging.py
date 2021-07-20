###################################################################################
# Copyright (c) 2021 Rhombus Systems                                              #
#                                                                                 # 
# Permission is hereby granted, free of charge, to any person obtaining a copy    #
# of this software and associated documentation files (the "Software"), to deal   #
# in the Software without restriction, including without limitation the rights    #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
# copies of the Software, and to permit persons to whom the Software is           #
# furnished to do so, subject to the following conditions:                        #
#                                                                                 # 
# The above copyright notice and this permission notice shall be included in all  #
# copies or substantial portions of the Software.                                 #
#                                                                                 # 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
# SOFTWARE.                                                                       #
###################################################################################

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
