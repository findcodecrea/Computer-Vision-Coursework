# utils.py
import logging
import os
import sys


def setup_logging():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def check_file(filename):
    if not os.path.isfile(filename):
        logging.error(f"The file {filename} does not exist.")
        return False
    if not os.access(filename, os.R_OK):
        logging.error(f"The file {filename} is not readable.")
        return False
    return True


def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception
