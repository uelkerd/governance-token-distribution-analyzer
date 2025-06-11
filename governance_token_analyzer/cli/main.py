"""
Main CLI entrypoint for the governance token analyzer.
"""

import click

from .historical_analysis import historical


@click.group()
def cli():
    """Governance Token Distribution Analyzer CLI."""
    pass


# Add commands
cli.add_command(historical)


# Add other commands here
# ...


if __name__ == '__main__':
    cli() 