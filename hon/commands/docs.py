import click


def docs(ctx: click.Context):
    """
    Build documentation using Sphinx. No support for publishing docs as
    it is assumed you are using readthedocs (or similar) to publish docs
    directly from GitHub.
    """
