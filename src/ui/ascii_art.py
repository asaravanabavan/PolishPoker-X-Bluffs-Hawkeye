"""ASCII art rendering for cards and game elements."""
from typing import Optional

from ..models import Card, Player, GridPosition, Rank, Suit
from .colors import Colors


class AsciiArt:
    """ASCII art generator for game display."""

    # card dimensions
    CARD_WIDTH = 11
    CARD_HEIGHT = 7

    @classmethod
    def render_card(
        cls,
        card: Optional[Card],
        show_face: bool = True,
        position_label: Optional[int] = None
    ) -> list[str]:
        """Render a single card as ASCII art."""
        if card is None:
            return cls._render_empty_slot(position_label)

        if not show_face or not card.face_up:
            return cls._render_card_back(position_label)

        if card.rank == Rank.JOKER:
            return cls._render_joker(position_label)

        return cls._render_card_face(card, position_label)

    @classmethod
    def _render_card_back(cls, label: Optional[int] = None) -> list[str]:
        lines = [
            "┌─────────┐",
            "│░░░░░░░░░│",
            "│░░░░░░░░░│",
            "│░░░░░░░░░│",
            "│░░░░░░░░░│",
            "│░░░░░░░░░│",
            "└─────────┘",
        ]
        if label is not None:
            lines.append(f"    [{label}]    ")
        return lines

    @classmethod
    def _render_empty_slot(cls, label: Optional[int] = None) -> list[str]:
        """Render an empty card slot."""
        lines = [
            "┌─────────┐",
            "│         │",
            "│         │",
            "│  EMPTY  │",
            "│         │",
            "│         │",
            "└─────────┘",
        ]
        if label is not None:
            lines.append(f"    [{label}]    ")
        return lines

    @classmethod
    def _render_joker(cls, label: Optional[int] = None) -> list[str]:
        """Render a Joker card."""
        lines = [
            "┌─────────┐",
            "│ ★     ★ │",
            "│  JOKER  │",
            "│   -2    │",
            "│  JOKER  │",
            "│ ★     ★ │",
            "└─────────┘",
        ]
        if label is not None:
            lines.append(f"    [{label}]    ")
        return lines

    @classmethod
    def _render_card_face(
        cls,
        card: Card,
        label: Optional[int] = None
    ) -> list[str]:
        """Render a regular card face."""
        symbol = card.symbol
        suit = card.suit.value

        # color the suit symbol
        if card.suit in (Suit.HEARTS, Suit.DIAMONDS):
            suit_display = Colors.colorize(suit, Colors.CARD_RED)
        else:
            suit_display = suit

        # pad symbol for alignment
        if len(symbol) == 1:
            left = f" {symbol}       "
            right = f"       {symbol} "
        else:  # "10" or "JKR"
            left = f" {symbol}      "
            right = f"      {symbol} "

        lines = [
            "┌─────────┐",
            f"│{left}│",
            "│         │",
            f"│    {suit_display}    │",
            "│         │",
            f"│{right}│",
            "└─────────┘",
        ]
        if label is not None:
            lines.append(f"    [{label}]    ")
        return lines

    @classmethod
    def render_deck_and_discard(
        cls,
        deck_count: int,
        top_discard: Optional[Card]
    ) -> list[str]:
        """Render the deck and discard pile side by side."""
        # Render deck
        deck_lines = [
            "┌─────────┐",
            f"│░░░{deck_count:>2}░░░░│",
            "│░░░░░░░░░│",
            "│░░DECK░░░│",
            "│░░░░░░░░░│",
            "│░░░░░░░░░│",
            "└─────────┘",
        ]

        # Render discard
        if top_discard:
            discard_lines = cls.render_card(top_discard, show_face=True)
        else:
            discard_lines = [
                "┌─────────┐",
                "│         │",
                "│ DISCARD │",
                "│  EMPTY  │",
                "│         │",
                "│         │",
                "└─────────┘",
            ]

        # Combine side by side
        combined = []
        for i, (disc_line, deck_line) in enumerate(zip(discard_lines, deck_lines)):
            combined.append(f"  {disc_line}    {deck_line}  ")

        return combined

    @classmethod
    def render_grid(
        cls,
        player: Player,
        show_hidden: bool = False,
        show_labels: bool = True
    ) -> list[str]:
        """
        Render a player's 2x2 grid.

        Args:
            player: The player whose grid to render.
            show_hidden: Whether to reveal hidden cards.
            show_labels: Whether to show position labels.

        Returns:
            List of strings representing the grid.
        """
        # Get cards at each position
        cards = [
            player.get_card(GridPosition.TOP_LEFT),
            player.get_card(GridPosition.TOP_RIGHT),
            player.get_card(GridPosition.BOTTOM_LEFT),
            player.get_card(GridPosition.BOTTOM_RIGHT),
        ]

        # Determine which cards to show
        labels = [1, 2, 3, 4] if show_labels else [None, None, None, None]

        # Render top row
        top_left = cls.render_card(
            cards[0],
            show_face=show_hidden or (cards[0] and cards[0].face_up),
            position_label=labels[0]
        )
        top_right = cls.render_card(
            cards[1],
            show_face=show_hidden or (cards[1] and cards[1].face_up),
            position_label=labels[1]
        )

        # Render bottom row
        bottom_left = cls.render_card(
            cards[2],
            show_face=show_hidden or (cards[2] and cards[2].face_up),
            position_label=labels[2]
        )
        bottom_right = cls.render_card(
            cards[3],
            show_face=show_hidden or (cards[3] and cards[3].face_up),
            position_label=labels[3]
        )

        # Combine into grid
        lines = []

        # Top row
        for i in range(len(top_left)):
            lines.append(f"  {top_left[i]} {top_right[i]}")

        # Bottom row
        for i in range(len(bottom_left)):
            lines.append(f"  {bottom_left[i]} {bottom_right[i]}")

        return lines

    @classmethod
    def render_game_board(
        cls,
        human: Player,
        bot: Player,
        deck_count: int,
        top_discard: Optional[Card],
        turn_number: int,
        is_human_turn: bool,
        human_show_known: bool = True
    ) -> str:
        """
        Render the complete game board.

        Args:
            human: Human player.
            bot: Bot player.
            deck_count: Cards remaining in deck.
            top_discard: Top card of discard pile.
            turn_number: Current turn number.
            is_human_turn: Whether it's the human's turn.
            human_show_known: Whether to show human's known cards.

        Returns:
            Complete game board as a string.
        """
        lines = []

        # Header
        lines.append("")
        lines.append("╔" + "═" * 58 + "╗")
        lines.append("║" + "POLISH BLUFF POKER".center(58) + "║")
        lines.append("╠" + "═" * 58 + "╣")

        # Bot's grid (always hidden from human)
        lines.append("║" + "".center(58) + "║")
        lines.append("║  " + f"{bot.name}'s Grid:".ljust(35) +
                    f"Score: ??".rjust(18) + "  ║")

        bot_grid = cls.render_grid(bot, show_hidden=False, show_labels=False)
        for line in bot_grid:
            padded = line.ljust(54)
            lines.append(f"║  {padded}  ║")

        # Separator
        lines.append("║" + "".center(58) + "║")
        lines.append("║" + "─" * 58 + "║")

        # Deck and discard
        deck_discard = cls.render_deck_and_discard(deck_count, top_discard)
        lines.append("║" + "DISCARD".center(25) + "DECK".center(33) + "║")
        for line in deck_discard:
            padded = line.center(58)
            lines.append(f"║{padded}║")

        # Separator
        lines.append("║" + "─" * 58 + "║")
        lines.append("║" + "".center(58) + "║")

        # Human's grid
        penalty_display = f"Penalties: {human.penalty_points}" if human.penalty_points > 0 else ""
        lines.append("║  " + f"YOUR Grid ({human.name}):".ljust(35) +
                    penalty_display.rjust(18) + "  ║")

        human_grid = cls.render_grid(human, show_hidden=human_show_known, show_labels=True)
        for line in human_grid:
            padded = line.ljust(54)
            lines.append(f"║  {padded}  ║")

        # Footer with turn info
        lines.append("║" + "".center(58) + "║")
        lines.append("╠" + "═" * 58 + "╣")

        turn_indicator = "YOUR TURN" if is_human_turn else f"{bot.name}'s Turn"
        turn_info = f"Turn {turn_number} | {turn_indicator}"
        lines.append("║  " + turn_info.ljust(54) + "  ║")
        lines.append("╚" + "═" * 58 + "╝")

        return "\n".join(lines)

    @classmethod
    def render_title(cls) -> str:
        """Render the game title banner."""
        return """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║         ██████╗ ██████╗ ██████╗                              ║
║         ██╔══██╗██╔══██╗██╔══██╗                             ║
║         ██████╔╝██████╔╝██████╔╝                             ║
║         ██╔═══╝ ██╔══██╗██╔═══╝                              ║
║         ██║     ██████╔╝██║                                  ║
║         ╚═╝     ╚═════╝ ╚═╝                                  ║
║                                                              ║
║              POLISH BLUFF POKER                              ║
║           Sports Officiating Edition                         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""

    @classmethod
    def render_var_banner(cls) -> str:
        """Render the VAR challenge banner."""
        return """
┌──────────────────────────────────────────────────┐
│                                                  │
│    ██╗   ██╗ █████╗ ██████╗                     │
│    ██║   ██║██╔══██╗██╔══██╗                    │
│    ██║   ██║███████║██████╔╝                    │
│    ╚██╗ ██╔╝██╔══██║██╔══██╗                    │
│     ╚████╔╝ ██║  ██║██║  ██║                    │
│      ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═╝                    │
│                                                  │
│            VAR CHALLENGE SYSTEM                  │
│                                                  │
└──────────────────────────────────────────────────┘
"""

    @classmethod
    def render_winner_banner(cls, winner_name: str) -> str:
        """Render the winner announcement banner."""
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    ██╗    ██╗██╗███╗   ██╗███╗   ██╗███████╗██████╗ ██╗     ║
║    ██║    ██║██║████╗  ██║████╗  ██║██╔════╝██╔══██╗██║     ║
║    ██║ █╗ ██║██║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝██║     ║
║    ██║███╗██║██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗╚═╝     ║
║    ╚███╔███╔╝██║██║ ╚████║██║ ╚████║███████╗██║  ██║██╗     ║
║     ╚══╝╚══╝ ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝╚═╝     ║
║                                                              ║
║                     {winner_name:^24}                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
