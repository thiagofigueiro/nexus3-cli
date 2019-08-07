# -*- coding: utf-8 -*-
import logging
import os

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING').upper()

logging.basicConfig(level=LOG_LEVEL)
logging.getLogger(__name__).setLevel(LOG_LEVEL)
logging.getLogger(__name__).addHandler(logging.NullHandler())
