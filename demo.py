#!/usr/bin/env python

import pathlib

import ultraclick as click


class GroupOne:
    """
    GroupOne subcommand
    """
    @click.option("--main")
    @click.option("--other", help="Future option to be used")
    def __init__(self, ctx, main, other="Not needed yet."):
        self.main = main
        self.other = other

    @click.command()
    @click.argument("name")
    def greet(self, ctx, name):
        env = ctx.meta.get("env", "unknown")
        return f"Greeting {name} in environment {env} with {self.main} ({self.other})."
        
    # Create an alias for the greet command
    hello = greet

    @click.command()
    @click.argument("name")
    def farewell(self, ctx, name="Unknown"):
        """Example subcommand: says goodbye."""
        env = ctx.meta.get("env", "unknown")
        return f"Goodbye {name} from GroupOne. Environment: {env}"

class GroupTwo:
    """
    GroupTwo subcommand
    """
    @click.command()
    def ping(self, ctx):
        return f"Pong from GroupTwo."

    @click.command()
    def version(self, ctx):
        return f"Version 1.0.0"

class MainGroup:
    """
    Main CLI group with top-level commands and subgroups.
    """
    group1 = GroupOne
    group2 = GroupTwo

    # These are generic options at the top level that will be passed as
    # keyword arguments to the __init__() function
    @click.option("--env", default="dev", help="Environment to use (e.g., dev, prod).")
    @click.option("--frontend-dir", default="./frontend", type=pathlib.Path, help="Frontend directory.")
    @click.option("--docker-dir", default="./docker", type=pathlib.Path, help="Docker directory.")
    @click.option("--docker-compose-file", default="./docker/docker-compose.yml", type=pathlib.Path, help="Docker compose file.")
    def __init__(self, ctx, **kwargs):

        # Assign all keyword arguments dynamically to ctx.meta to make them
        # available throughout all parts of the CLI application
        for key, value in kwargs.items():
            setattr(self, key, value)
            ctx.meta[key] = value

    @click.command()
    @click.argument("name")
    def status(self, ctx, name):
        """Display the current status."""
        return f"Name: {name}, Environment: {self.env}, Frontend dir: {self.frontend_dir}, Docker dir: {self.docker_dir}"

if __name__ == "__main__":
    click.group_from_class(MainGroup, name="cli")(prog_name="demo")
