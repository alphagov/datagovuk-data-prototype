import csv
import logging
import os

from flask import current_app

logger = logging.getLogger(__name__)


def load_data(filename, encoding="utf-8"):
    path = os.path.join(current_app.config["PROJECT_ROOT"], "data", filename)
    logger.info(path)
    with open(path, encoding=encoding) as f:
        return list(csv.DictReader(f))
