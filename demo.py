#!/usr/bin/env python
"""
ultraclick Demo Application

This demo systematically showcases ultraclick's main features:
1. Class-based CLI structure
2. Nested command groups
3. Automatic context sharing
4. Command aliases
5. Command abbreviations
6. Automatic return value handling
"""

import pathlib

import ultraclick as click


class ConfigCommand:
    """
    Configuration commands for the application.
    Demonstrates context sharing between subcommands.

    This command group shows help when called directly (default behavior).
    """
    @click.option("--config-dir", type=pathlib.Path, default="./config", help="Configuration directory")
    def __init__(self, config_dir):
        # Store parameters as instance variables
        self.config_dir = config_dir

        # Access shared data from parent command
        self.profile = click.ctx.meta["profile"]

        # Share this command's data with child commands
        click.ctx.meta["config_dir"] = config_dir

    @click.command()
    def show(self):
        """Display current configuration settings."""
        path_prefix = './' if not self.config_dir.is_absolute() else ''
        return (
            f"Active Profile: {self.profile}\n"
            f"Config Directory: {path_prefix}{self.config_dir}"
        )

    @click.command()
    @click.argument("name")
    @click.argument("value")
    def set(self, name, value):
        """Set a configuration value."""
        return f"Setting {name}={value} in profile '{self.profile}'"

    # Command alias demonstration
    update = click.alias(set)

    @click.command()
    @click.argument("name")
    def get(self, name):
        """Get a configuration value."""
        return f"Getting '{name}' from profile '{self.profile}'"

    # Another command alias
    fetch = click.alias(get)


class ResourceCommand:
    """
    Resource management commands.
    Demonstrates parameter handling and nested command structure.

    This command group performs an action when called directly (no help shown).
    """
    @click.option("--resource-type", type=click.Choice(['server', 'database', 'storage']),
                  default="server", help="Type of resource to manage")
    def __init__(self, resource_type):
        self.resource_type = resource_type

        # Access shared data from parent command
        self.profile = click.ctx.meta["profile"]

        # Custom behavior when no subcommand is provided
        if click.ctx.invoked_subcommand is None:
            # Prevent automatic help display
            click.ctx.meta['show_help_on_no_command'] = False

            # Show custom summary instead
            click.echo(
                f"Resource Management Summary:\n"
                f"• Current Resource Type: {self.resource_type}\n"
                f"• Available Types: server, database, storage\n"
                f"• Active Profile: {self.profile}"
            )

    @click.command()
    @click.argument("name")
    @click.option("--size", default="medium", help="Resource size (small, medium, large)")
    @click.option("--region", default="us-east", help="Deployment region")
    def create(self, name, size, region):
        """Create a new resource."""
        # Use the profile from instance state instead of context
        return (
            f"Creating {self.resource_type} '{name}'\n"
            f"Size: {size}\n"
            f"Region: {region}\n"
            f"Using profile: {self.profile}"
        )

    @click.command()
    @click.argument("name")
    def delete(self, name):
        """Delete a resource."""
        return f"Deleting {self.resource_type} '{name}'"

    @click.command()
    @click.argument("names", nargs=-1)
    def list(self, names):
        """List resources, optionally filtered by name."""
        # Use instance state for profile
        if not names:
            return f"Listing all {self.resource_type}s (Profile: {self.profile})"
        else:
            return f"Filtered {self.resource_type} list: {', '.join(names)} (Profile: {self.profile})"


class MainApp:
    """
    Main demo application showcasing ultraclick's features.
    """
    # Define nested command groups
    config = ConfigCommand
    resource = ResourceCommand

    @click.option("--verbose", is_flag=True, help="Enable verbose output")
    @click.option("--profile", default="default", help="Configuration profile to use")
    @click.option("--env", default="development",
                 type=click.Choice(['development', 'staging', 'production']),
                 help="Environment to run in")
    @click.version_option(version="1.0")
    def __init__(self, verbose, profile, env):
        # Store options as instance variables
        self.verbose = verbose
        self.profile = profile
        self.env = env

        # Share data with child commands
        click.ctx.meta["verbose"] = verbose
        click.ctx.meta["profile"] = profile
        click.ctx.meta["env"] = env

        if verbose:
            click.output.success(f"Verbose mode enabled in {env} environment")

    @click.command()
    def status(self):
        """Show application status."""
        return (
            f"Status: Running\n"
            f"Environment: {self.env}\n"
            f"Verbose: {self.verbose}\n"
            f"Profile: {self.profile}"
        )

    info=click.alias(status)

if __name__ == "__main__":
    click.group_from_class(MainApp, name="demo")()
