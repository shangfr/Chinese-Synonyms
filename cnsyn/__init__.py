from __future__ import absolute_import, unicode_literals

__version__ = '0.0.1'
__license__ = 'Apache License 2.0'

import marshal
import re
import tempfile
import threading
import time
from hashlib import md5
from math import log

from . import finalseg
from ._compat import *


DEFAULT_DICT = None
DEFAULT_DICT_NAME = "dict.txt"

log_console = logging.StreamHandler(sys.stderr)
default_logger = logging.getLogger(__name__)
default_logger.setLevel(logging.DEBUG)
default_logger.addHandler(log_console)

def setLogLevel(log_level):
    default_logger.setLevel(log_level)

