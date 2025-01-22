# ultraclick

**Warning: This is an early hack. There are no unit tests, yet. Maybe not stable!**

In contrast to plain version of [click](https://github.com/pallets/click), ultraclick allows you to define your CLI using Python classes. ultraclick is based on rich-click which is adding colors to click.


## Example
```
import pathlib

import ultraclick as click

class GroupOne:
    """
    Subcommands for group1.
    """
    def __init__(self, ctx, other):
        self.other = other

    @click.command()
    @click.argument("name")
    def greet(self, ctx, name):
        """Example subcommand: prints a greeting."""
        env = ctx.obj.get("env", "unknown")
        return f"Greeting {name} in environment '{env}' with other={self.other}."

    @click.command()
    def farewell(self, ctx):
        """Example subcommand: says goodbye."""
        env = ctx.obj.get("env", "unknown")
        return f"Goodbye from GroupOne. Environment: {env}"

class GroupTwo:
    """
    Subcommands for group2.
    """
    def __init__(self, ctx, docker_flag):
        ctx.obj = ctx.obj or {}
        self.docker_flag = docker_flag

    @click.command()
    def ping(self, ctx):
        """Ping subcommand."""
        return f"Pong from GroupTwo. Docker flag: {self.docker_flag}"

    @click.command()
    def version(self, ctx):
        """Show version info from GroupTwo."""
        return f"GroupTwo version 1.0.0"

class MainGroup:
    """
    Main CLI group with top-level commands and subgroups.
    """
    group1 = GroupOne
    group2 = GroupTwo

    @click.option("--env", default="dev", help="Environment to use (e.g., dev, prod).")
    @click.option("--frontend-dir", default="./frontend", type=pathlib.Path, help="Frontend directory.")
    @click.option("--docker-dir", default="./docker", type=pathlib.Path, help="Docker directory.")
    @click.option("--docker-compose-file", default="./docker/docker-compose.yml", type=pathlib.Path, help="Docker compose file.")
    def __init__(self, ctx, **kwargs):
        ctx.obj = ctx.obj or {}

        # Assign all keyword arguments dynamically to both self and ctx.obj
        for key, value in kwargs.items():
            setattr(self, key, value)
            ctx.obj[key] = value

    @click.command()
    @click.argument("name")
    def status(self, ctx, name):
        """Display the current status."""
        return f"Environment: {self.env}, Frontend dir: {self.frontend_dir}, Docker dir: {self.docker_dir}"



# -------------------------------
# CLI Entry Point
# -------------------------------

if __name__ == "__main__":
    try:
        # Create the CLI using MainGroup
        cli = click.group_from_class(MainGroup, name="cli")
        cli(prog_name="dm")
    except SystemExit:
        # Handle graceful exit without traceback
        pass

```
