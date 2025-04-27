"""
Warframe Market GUI module entry point.
This file exists for backward compatibility with existing code.
New code should import directly from the gui package.
"""

from gui.app import main

# Make the main function directly callable
if __name__ == "__main__":
    main()
