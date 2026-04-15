import os
import sys
from pathlib import Path


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import ultraclick as click


@click.main_group(name="generate_icon_overview")
class GenerateIconOverview:
    """Generate an HTML overview from SVG files using pure string concatenation."""

    # Keep the command shape close to the real script: one required path plus one optional slug.
    labels_root = Path(__file__).resolve().parent.parent
    template_path = labels_root / 'templates' / 'icon-overview-template.html'

    @click.argument('input_dir')
    @click.argument('slug', required=False)
    @click.option('--title')
    def __init__(self, input_dir, slug=None, title='Icon Overview'):
        # Store parsed values so the command remains valid if the test ever executes it without help.
        self.input_dir = Path(input_dir)
        self.slug = slug
        self.title = title


if __name__ == '__main__':
    GenerateIconOverview()
