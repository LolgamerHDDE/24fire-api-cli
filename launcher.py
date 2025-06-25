import sys
import os
import atexit

def should_pause():
    """Check if we should pause on exit."""
    # Only pause if running as a PyInstaller executable
    if not getattr(sys, 'frozen', False):
        return False
    
    # Don't pause if help arguments are present
    help_args = ['-h', '--help', '-s', '-S', '-r', '--start', '--stop', '--restart']
    for arg in sys.argv[1:]:
        if arg in help_args:
            return False
    
    return True

def pause_on_exit():
    if should_pause():
        try:
            input("Press any key to exit...")
        except (EOFError, KeyboardInterrupt):
            pass

# Add pause on exit for frozen executables
if getattr(sys, 'frozen', False):
    atexit.register(pause_on_exit)
    
    # Also handle uncaught exceptions
    original_excepthook = sys.excepthook
    
    def exception_handler(exc_type, exc_value, exc_traceback):
        original_excepthook(exc_type, exc_value, exc_traceback)
        if should_pause():
            try:
                input("Press any key to exit...")
            except (EOFError, KeyboardInterrupt):
                pass
    
    sys.excepthook = exception_handler

# Import and run the main application
if __name__ == "__main__":
    import main
    try:
        main.main(main.API_KEY)
    except SystemExit:
        pass
