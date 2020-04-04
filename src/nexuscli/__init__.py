# -*- coding: utf-8 -*-
import logging
import os

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING').upper()

ROOT_LOGGER = logging.getLogger(__name__)
ROOT_LOGGER.setLevel(LOG_LEVEL)
ROOT_LOGGER.addHandler(logging.NullHandler())
