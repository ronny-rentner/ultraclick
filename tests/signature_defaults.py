import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import ultraclick as click


@click.main_group(name="app")
class App:
    """Show option and argument values."""

    # Each declaration form names the parameter differently from its first declaration.
    @click.option('-e', '--env')
    @click.option('--dry-run/--no-dry-run')
    @click.option('--region', 'zone')
    def __init__(self, env='development', dry_run=True, zone='eu'):
        self.env = env
        self.dry_run = dry_run
        self.zone = zone

    @click.command()
    def show(self):
        """Show the option values."""
        return f"env={self.env} dry_run={self.dry_run} zone={self.zone}"

    @click.command()
    @click.argument('NAME')
    def greet(self, name='world'):
        """Greet someone."""
        return f"Hello {name}"


if __name__ == '__main__':
    App()
