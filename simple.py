#!/bin/env python

import ultraclick as click

class SimpleApp():
    def __run__(self):
        click.output.success('Success')

if __name__ == "__main__":
   click.group_from_class(SimpleApp)()
