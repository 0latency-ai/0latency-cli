"""CLI interface for 0latency wrapper."""

import sys
import uuid
import click
from zerolatency_cli import __version__
from zerolatency_cli.wrapper import wrap_command
from zerolatency_cli.profiles.claude_code import ClaudeCodeProfile
from zerolatency_cli.auth import device_code_flow
from zerolatency_cli.storage import write_atom, get_atom_count, get_unsynced_count, get_db_path
from zerolatency_cli.recovery import prompt_user_import, write_atom_to_buffer, cleanup_session_buffer
from zerolatency_cli.chunking import chunk_atom

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
    
    # Check for orphaned sessions before starting
    if not explain_mode:
        prompt_user_import()
    
    if explain_mode:
        click.echo("Would wrap claude with role detection profile:")
        click.echo("  Agent: Claude Code")
        storage_msg = "local (sqlite)" if local_mode else "cloud (with local fallback)"
        click.echo(f"  Storage: {storage_msg}")
        return
    
    # Generate session ID
    session_id = str(uuid.uuid4())
    agent_id = f"claude-code-{session_id}"
    
    # Extract user query if in --print mode
    user_query = None
    if "--print" in agent_args or "-p" in agent_args:
        # Find the query after --print/-p
        for i, arg in enumerate(agent_args):
            if arg in ("--print", "-p") and i + 1 < len(agent_args):
                user_query = agent_args[i + 1]
                break
    
    # Create profile
    profile = ClaudeCodeProfile(
        agent_id=agent_id,
        agent_version="2.1.136",  # Will be detected dynamically in P2
        user_query=user_query
    )
    
    # Collected atoms
    atoms = []
    
    def on_atom(atom):
        """Callback for emitted atoms."""
        # Chunk atom if it exceeds 64KB
        chunked = chunk_atom(atom)
        
        for chunked_atom in chunked:
            atoms.append(chunked_atom)
            # Write to rolling buffer for crash recovery
            write_atom_to_buffer(chunked_atom, session_id)
            # Write to storage (local or cloud based on auth state)
            write_atom(chunked_atom, force_local=local_mode)
    
    def on_data(data: bytes):
        """Callback for captured output data."""
        profile.parse_chunk(data, on_atom)
    
    # Build command
    command = ["claude"] + list(agent_args)
    
    # Run wrapped command
    exit_code = wrap_command(command, on_data)
    
    # Flush any remaining buffered data
    profile.flush(on_atom)
    
    # Clean shutdown - remove rolling buffer
    cleanup_session_buffer(session_id)
    
    # Flush complete - atoms written to storage
    
    sys.exit(exit_code)

@main.command()
def login():
    """Authenticate with 0Latency cloud via OAuth device-code flow.
    
    Opens browser for authentication and stores credentials at ~/.0latency/credentials.
    """
    success = device_code_flow()
    sys.exit(0 if success else 1)

@main.command()
def status():
    """Show authentication status, storage info, and sync state.
    
    Displays:
    - Auth state (logged in / not logged in)
    - Local database path and atom count
    - Unsynced atom count
    - Last successful cloud sync time
    """
    from zerolatency_cli.auth import load_credentials
    from zerolatency_cli import __version__
    
    click.echo(f"0latency CLI v{__version__}")
    
    # Auth state
    creds = load_credentials()
    if creds:
        tenant_id = creds.get("tenant_id", "unknown")[:8]
        issued_at = creds.get("issued_at", "unknown")
        click.echo(f"Auth: logged in as tenant {tenant_id}... (token issued {issued_at})")
    else:
        click.echo("Auth: not logged in (run  or use )")
    
    # Local DB stats
    db_path = get_db_path()
    total_atoms = get_atom_count()
    unsynced_atoms = get_unsynced_count()
    
    if total_atoms > 0:
        click.echo(f"Local DB: {db_path} ({total_atoms:,} atoms, {unsynced_atoms:,} unsynced)")
    else:
        click.echo(f"Local DB: {db_path} (empty)")

if __name__ == "__main__":
    main()
