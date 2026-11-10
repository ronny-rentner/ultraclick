import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import ultraclick as click


@click.main_group(name="services")
class Services:
    """Manage services."""

    # Groups convert in alphabetical order: Api and Db before their base Service, Web after it.
    class Service:
        """Manage a service."""

        @click.option('--host')
        def __init__(self, host='localhost'):
            self.host = host

        @click.command()
        def status(self):
            """Show the service status."""
            return f"{type(self).__name__} on {self.host}"

        check = click.alias(status)

    class Api(Service):
        """Manage the API service."""

    class Db(Service):
        """Manage the database service."""

        @click.option('--port')
        def __init__(self, port='5432'):
            super().__init__()
            self.port = port

        @click.command()
        def status(self):
            """Show the database status."""
            return f"Db on port {self.port}"

    class Web(Service):
        """Manage the web service."""


if __name__ == '__main__':
    Services()
