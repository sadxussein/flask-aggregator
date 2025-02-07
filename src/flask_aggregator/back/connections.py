from abc import ABC, abstractmethod

from ovirtsdk4 import Connection as ov_con
from ovirtsdk4 import ConnectionError as ov_con_err
from ovirtsdk4 import AuthError as ov_auth_err

from flask_aggregator.back.logger import Logger

class Connection(ABC):
    """Abstract connection class for various entities.
    
    Could be database, virtualization or any other endoint. This class
    provides interface for every type of connection for external source.
    """
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        logger: Logger=Logger()
    ) -> None:
        self._logger = logger
        self._url = url
        self._username = username
        self._password = password
        self._connection = None

    @property
    def connection(self):
        """Return connection object."""
        if self._connection is None:
            raise ValueError("Connection can't be 'None'.")
        return self._connection

    @abstractmethod
    def connect(self):
        """Initiate connection to target."""

    @abstractmethod
    def disconnect(self):
        """Disconnect from targer gracefully."""


class OvirtConnection(Connection):
    """Concrete Ovirt connection class."""
    def __init__(self, url, username, password, logger):
        super().__init__(url, username, password, logger)

    def connect(self):
        try:
            self._connection = ov_con(
                url=self._url,
                username=self._username,
                password=self._password,
                insecure=True,
                debug=True
            )
        except ov_con_err as e:
            self._logger.log_error(
                f"Failed to connect to {self._url} under user"
                f"{self._username}. Exception: {e}"
            )
        except ov_auth_err as e:
            self._logger.log_error(
                f"Failed to authenticate in oVirt Hosted Engine for URL: {e}."
            )

    def disconnect(self):
        if self._connection is None:
            raise ValueError("Connection can't be 'None'.")
        self._connection.close()

class VMWareConnection(Connection):
    """Concrete VMWare connection class."""

class VZConnection(Connection):
    """Concrete VZ connection class."""

class DBConnection(Connection):
    """Concrete database connection class."""
    def __init__(self, url, username, password, logger = Logger()):
        super().__init__(url, username, password, logger)

    def connect(self):
        pass