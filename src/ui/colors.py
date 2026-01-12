"""ANSI color codes for terminal output."""


class Colors:
    """ANSI escape codes for terminal colors."""

    # reset
    RESET = "\033[0m"

    # text colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    # bright text colors
    BRIGHT_BLACK = "\033[90m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"

    # background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    # text styles
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    REVERSE = "\033[7m"

    # Game-specific colors
    CARD_RED = RED
    CARD_BLACK = BRIGHT_WHITE
    CARD_BACK = BRIGHT_BLACK
    SUCCESS = GREEN
    ERROR = RED
    WARNING = YELLOW
    INFO = CYAN
    HIGHLIGHT = BRIGHT_YELLOW

    @classmethod
    def colorize(cls, text: str, color: str) -> str:
        """
        Wrap text with a color code.

        Args:
            text: Text to colorize.
            color: Color code (e.g., Colors.RED).

        Returns:
            Colorized string.
        """
        return f"{color}{text}{cls.RESET}"

    @classmethod
    def bold(cls, text: str) -> str:
        """Make text bold."""
        return f"{cls.BOLD}{text}{cls.RESET}"

    @classmethod
    def success(cls, text: str) -> str:
        """Format text as success (green)."""
        return cls.colorize(text, cls.SUCCESS)

    @classmethod
    def error(cls, text: str) -> str:
        """Format text as error (red)."""
        return cls.colorize(text, cls.ERROR)

    @classmethod
    def warning(cls, text: str) -> str:
        """Format text as warning (yellow)."""
        return cls.colorize(text, cls.WARNING)

    @classmethod
    def info(cls, text: str) -> str:
        """Format text as info (cyan)."""
        return cls.colorize(text, cls.INFO)

    @classmethod
    def highlight(cls, text: str) -> str:
        """Highlight text (bright yellow)."""
        return cls.colorize(text, cls.HIGHLIGHT)


def strip_colors(text: str) -> str:
    """Remove ANSI color codes from a string."""
    import re
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)
