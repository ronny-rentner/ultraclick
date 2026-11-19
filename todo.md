# TODO

- `click.output.image()`: over SSH the terminal cannot read the file, so no image appears. Send the image data instead of the path (`t=d`).
- `click.output.image()`: terminals without the Kitty graphics protocol show nothing. Fall back to printing the path there.
