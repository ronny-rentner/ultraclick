import logging
import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import ultraclick as click


@click.main_group(name="logging_capture", capture_logs=os.environ.get("ULTRACLICK_TEST_CAPTURE_LOGS") != "0")
class LoggingCapture:
    """Fixture for logging capture behavior."""

    @click.command()
    def warn(self):
        logging.getLogger("fixture").warning("library warning")
        return "done"


if __name__ == "__main__":
    LoggingCapture()
