"""Generate logs for all actions."""

import logging

class Logger:
    """Class (singleton) for logging both in file and console."""
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log_file="app.log", log_level=logging.DEBUG):
        if not hasattr(self, "_initialized"):
        # Creating logger.
            self.__logger = logging.getLogger("AppLogger")
            self.__logger.setLevel(log_level)

            if not self.__logger.hasHandlers():
                # Creating file handler.
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(log_level)

                # Creating stream (console) handler.
                console_handler = logging.StreamHandler()
                console_handler.setLevel(log_level)

                # Setting log format.
                formatter = logging.Formatter('%(asctime)s-[%(levelname)s] - %(threadName)s: %(message)s')
                file_handler.setFormatter(formatter)
                console_handler.setFormatter(formatter)
                self.__logger.addHandler(file_handler)
                self.__logger.addHandler(console_handler)
            
            self._initialized = True

    def log_debug(self, message):
        """Add debug log entry."""
        self.__logger.debug(message)

    def log_info(self, message):
        """Add info log entry."""
        self.__logger.info(message)

    def log_warning(self, message):
        """Add warning log entry."""
        self.__logger.warning(message)

    def log_error(self, message):
        """Add error log entry."""
        self.__logger.error(message)

    def close_handlers(self):
        """Close handlers."""
        for handler in self.__logger.handlers:
            handler.close()
