"""CLI interface for 0latency wrapper."""

import click
from zerolatency_cli import __version__

@click.group()
@click.option("--local", is_flag=True, help="Force local-only storage (override cloud writes)")
@click.option("--explain", is_flag=True, help="Dry-run mode: show what would be captured without running")
@click.version_option(version=__version__, prog_name="0latency-cli")
@click.pass_context
def main(ctx, local, explain):
    """0latency CLI - Verbatim capture wrapper for AI coding agents."""
    # Store flags in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["local"] = local
    ctx.obj["explain"] = explain

@main.command()
@click.argument("agent_args", nargs=-1, type=click.UNPROCESSED)
@click.pass_context
def claude(ctx, agent_args):
    """Wrap Claude Code session with verbatim capture.
    
    All arguments after 'claude' are passed through to the Claude Code binary.
    
    Examples:
        0latency claude
        0latency claude --print "what is 2+2"
        0latency --local claude
    """
    local_mode = ctx.obj.get("local", False)
    explain_mode = ctx.obj.get("explain", False)
    
    if explain_mode:
        click.echo("Would wrap claude with role detection profile:")
        click.echo("  Agent: Claude Code")
        storage_msg = "local (sqlite)" if local_mode else "cloud (with local fallback)"
        click.echo(f"  Storage: {storage_msg}")
        return
    
    # Task 3 will implement the wrapper
    click.echo("claude wrapper not yet implemented (Task 3)")
    click.echo(f"Would run: claude {' '.join(agent_args)}")
    click.echo(f"Local mode: {local_mode}")

@main.command()
def login():
    """Authenticate with 0Latency cloud via OAuth device-code flow.
    
    Opens browser for authentication and stores credentials at ~/.0latency/credentials.
    """
    click.echo("login not yet implemented (Task 5)")

@main.command()
def status():
    """Show authentication status, storage info, and sync state.
    
    Displays:
    - Auth state (logged in / not logged in)
    - Local database path and atom count
    - Unsynced atom count
    - Last successful cloud sync time
    """
    click.echo("status not yet implemented (Task 7)")

if __name__ == "__main__":
    main()
