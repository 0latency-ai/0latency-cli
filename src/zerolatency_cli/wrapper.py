"""PTY-based stdio interception for agent wrapping."""

import os
import sys
import pty
import select
import signal
import termios
import tty
import struct
import fcntl
from typing import Callable, Optional
from zerolatency_cli.prompts import is_interactive_prompt

class PTYWrapper:
    """Wraps a command in a PTY, capturing all I/O while maintaining transparency."""
    
    def __init__(self, command: list[str], on_data: Optional[Callable[[bytes], None]] = None):
        """
        Args:
            command: Command and arguments to wrap (e.g., ['claude', '--help'])
            on_data: Callback for captured stdout data (receives raw bytes)
        """
        self.command = command
        self.on_data = on_data or (lambda data: None)
        self.master_fd = None
        self.original_tty = None
        
    def _save_tty_settings(self):
        """Save original terminal settings for restoration on exit."""
        try:
            self.original_tty = termios.tcgetattr(sys.stdin)
        except termios.error:
            # Not a TTY (piped input)
            self.original_tty = None
    
    def _restore_tty_settings(self):
        """Restore terminal to original state."""
        if self.original_tty is not None:
            try:
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.original_tty)
            except termios.error:
                pass
    
    def _handle_sigwinch(self, signum, frame):
        """Handle terminal window resize and propagate to child PTY."""
        if self.master_fd is None:
            return
        try:
            # Get current window size
            s = struct.pack('HHHH', 0, 0, 0, 0)
            size = fcntl.ioctl(sys.stdout.fileno(), termios.TIOCGWINSZ, s)
            # Set PTY window size
            fcntl.ioctl(self.master_fd, termios.TIOCSWINSZ, size)
        except (OSError, AttributeError):
            pass
    
    def run(self) -> int:
        """
        Run the wrapped command in a PTY.
        
        Returns:
            The exit code of the wrapped command.
        """
        # Save terminal settings
        self._save_tty_settings()
        
        # Set up SIGWINCH handler
        old_sigwinch = signal.signal(signal.SIGWINCH, self._handle_sigwinch)
        
        try:
            # Fork with PTY
            pid, self.master_fd = pty.fork()
            
            if pid == 0:
                # Child process - exec the target command
                os.execvp(self.command[0], self.command)
            
            # Parent process - tee I/O
            return self._parent_loop(pid)
        
        finally:
            # Restore terminal state
            self._restore_tty_settings()
            signal.signal(signal.SIGWINCH, old_sigwinch)
    
    def _parent_loop(self, pid: int) -> int:
        """
        Main I/O loop in parent process.
        
        Args:
            pid: Child process PID
            
        Returns:
            Child exit code
        """
        # Set master_fd to non-blocking
        flags = fcntl.fcntl(self.master_fd, fcntl.F_GETFL)
        fcntl.fcntl(self.master_fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
        
        # Set stdin to raw mode if it's a TTY
        if self.original_tty is not None:
            tty.setraw(sys.stdin.fileno())
        
        # Trigger initial SIGWINCH to sync window size
        self._handle_sigwinch(None, None)
        
        while True:
            try:
                # Wait for data on stdin or master_fd
                readable, _, _ = select.select([sys.stdin, self.master_fd], [], [])
                
                if sys.stdin in readable:
                    # User input -> send to child
                    try:
                        data = os.read(sys.stdin.fileno(), 1024)
                        if data:
                            os.write(self.master_fd, data)
                    except OSError:
                        pass
                
                if self.master_fd in readable:
                    # Child output -> display and capture
                    try:
                        data = os.read(self.master_fd, 1024)
                        if data:
                            # Write to stdout (user sees it)
                            os.write(sys.stdout.fileno(), data)
                            # Check if this is an interactive prompt
                            if is_interactive_prompt(data):
                                # Skip capture - pass through transparently
                                pass
                            else:
                                # Callback for capture
                                self.on_data(data)
                    except OSError as e:
                        # EIO means child has exited
                        if e.errno == 5:  # EIO
                            break
                        raise
            
            except KeyboardInterrupt:
                # Ctrl-C should go to the child, not kill the wrapper
                pass
        
        # Wait for child to exit and get status
        _, status = os.waitpid(pid, 0)
        
        # Extract exit code
        if os.WIFEXITED(status):
            return os.WEXITSTATUS(status)
        elif os.WIFSIGNALED(status):
            return 128 + os.WTERMSIG(status)
        else:
            return 1


def wrap_command(command: list[str], on_data: Optional[Callable[[bytes], None]] = None) -> int:
    """
    Convenience function to wrap a command.
    
    Args:
        command: Command and arguments to wrap
        on_data: Optional callback for captured output
        
    Returns:
        Exit code of the wrapped command
    """
    wrapper = PTYWrapper(command, on_data)
    return wrapper.run()
