import os
import sys


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import ultraclick as click


@click.main_group(name="json_output")
class JsonOutput:
    """Fixture for a --json option that switches to JsonOutputFormatter."""

    @click.option("--json", "json_output", is_flag=True, help="Print results as JSON")
    def __init__(self, json_output=False):
        if json_output:
            click.use_formatter(click.JsonOutputFormatter)

    @click.command()
    def windows(self):
        return [{"id": 1, "title": "Editor"}, {"id": 2, "title": None}]

    @click.command()
    def title(self):
        return "Editor"

    @click.command()
    def close(self):
        click.output.success("closed")


if __name__ == "__main__":
    JsonOutput()
