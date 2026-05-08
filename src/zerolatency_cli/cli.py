"""CLI interface for 0latency wrapper."""

import click
from zerolatency_cli import __version__

@click.group()
@click.version_option(version=__version__, prog_name="0latency-cli")
def main():
    """0latency CLI - Verbatim capture wrapper for AI coding agents."""
    pass

if __name__ == "__main__":
    main()
