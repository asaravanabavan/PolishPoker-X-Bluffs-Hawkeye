#!/usr/bin/env python3
"""Polish Bluff Poker - CLI card game."""
import sys


def check_python_version():
    if sys.version_info < (3, 10):
        print("Error: Python 3.10 or higher is required.")
        print(f"Current version: {sys.version}")
        sys.exit(1)


def main():
    check_python_version()

    try:
        from src.ui import CLI

        game = CLI()
        game.run()

    except KeyboardInterrupt:
        print("\n\nGame interrupted. Thanks for playing!")
        sys.exit(0)

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please report this issue.")
        raise


if __name__ == "__main__":
    main()
