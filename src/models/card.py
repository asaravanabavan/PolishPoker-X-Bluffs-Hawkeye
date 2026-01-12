"""Card model with Rank, Suit, and PowerType enums."""
from enum import Enum, auto
from typing import Optional


class Rank(Enum):
    """Card ranks from Joker to King."""
    JOKER = auto()
    ACE = auto()
    TWO = auto()
    THREE = auto()
    FOUR = auto()
    FIVE = auto()
    SIX = auto()
    SEVEN = auto()
    EIGHT = auto()
    NINE = auto()
    TEN = auto()
    JACK = auto()
    QUEEN = auto()
    KING = auto()


class Suit(Enum):
    """Card suits including NONE for Jokers."""
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"
    NONE = ""  # For Jokers


class PowerType(Enum):
    """Power card abilities."""
    PEEK = "peek"           # 7, 8 - Look at one of your own hidden cards
    SPY = "spy"             # 9, 10 - Look at opponent's hidden card
    BLIND_SWAP = "blind_swap"  # J, Q - Swap cards blindly with opponent


class Card:
    """Playing card with rank, suit, and face state."""

    # value mapping for scoring
    VALUE_MAP: dict[Rank, int] = {
        Rank.JOKER: -2,
        Rank.KING: 0,
        Rank.ACE: 1,
        Rank.TWO: 2,
        Rank.THREE: 3,
        Rank.FOUR: 4,
        Rank.FIVE: 5,
        Rank.SIX: 6,
        Rank.SEVEN: 7,
        Rank.EIGHT: 8,
        Rank.NINE: 9,
        Rank.TEN: 10,
        Rank.JACK: 10,
        Rank.QUEEN: 10,
    }

    # Power card mapping
    POWER_MAP: dict[Rank, PowerType] = {
        Rank.SEVEN: PowerType.PEEK,
        Rank.EIGHT: PowerType.PEEK,
        Rank.NINE: PowerType.SPY,
        Rank.TEN: PowerType.SPY,
        Rank.JACK: PowerType.BLIND_SWAP,
        Rank.QUEEN: PowerType.BLIND_SWAP,
    }

    # Display symbols for ranks
    RANK_SYMBOLS: dict[Rank, str] = {
        Rank.JOKER: "JKR",
        Rank.ACE: "A",
        Rank.TWO: "2",
        Rank.THREE: "3",
        Rank.FOUR: "4",
        Rank.FIVE: "5",
        Rank.SIX: "6",
        Rank.SEVEN: "7",
        Rank.EIGHT: "8",
        Rank.NINE: "9",
        Rank.TEN: "10",
        Rank.JACK: "J",
        Rank.QUEEN: "Q",
        Rank.KING: "K",
    }

    def __init__(self, rank: Rank, suit: Suit, face_up: bool = False):
        self.rank = rank
        self.suit = suit
        self.face_up = face_up

    @property
    def value(self) -> int:
        """Get the scoring value of this card."""
        return self.VALUE_MAP[self.rank]

    @property
    def is_power_card(self) -> bool:
        """Check if this card has a power ability."""
        return self.rank in self.POWER_MAP

    @property
    def power_type(self) -> Optional[PowerType]:
        """Get the power type if this is a power card, else None."""
        return self.POWER_MAP.get(self.rank)

    @property
    def symbol(self) -> str:
        """Get the display symbol for the rank."""
        return self.RANK_SYMBOLS[self.rank]

    def flip(self) -> None:
        """Toggle the face-up state of the card."""
        self.face_up = not self.face_up

    def __str__(self) -> str:
        """Return string representation like 'K♠' or 'JKR'."""
        if self.rank == Rank.JOKER:
            return "JKR"
        return f"{self.symbol}{self.suit.value}"

    def __repr__(self) -> str:
        """Return detailed representation."""
        state = "up" if self.face_up else "down"
        return f"Card({self.rank.name}, {self.suit.name}, {state})"

    def __eq__(self, other: object) -> bool:
        """Check equality based on rank and suit."""
        if not isinstance(other, Card):
            return NotImplemented
        return self.rank == other.rank and self.suit == other.suit

    def __hash__(self) -> int:
        """Make card hashable for use in sets."""
        return hash((self.rank, self.suit))

    @classmethod
    def value_for_rank(cls, rank: Rank) -> int:
        """Class method to get value for a rank without instantiating."""
        return cls.VALUE_MAP[rank]

    @classmethod
    def create_joker(cls, face_up: bool = False) -> 'Card':
        """Factory method to create a Joker card."""
        return cls(Rank.JOKER, Suit.NONE, face_up)

    def to_ascii(self, show_face: bool = True) -> list[str]:
        """Generate ASCII art representation of the card."""
        if not show_face or not self.face_up:
            # face-down card
            return [
                "┌─────────┐",
                "│░░░░░░░░░│",
                "│░░░░░░░░░│",
                "│░░░░░░░░░│",
                "│░░░░░░░░░│",
                "│░░░░░░░░░│",
                "└─────────┘",
            ]

        if self.rank == Rank.JOKER:
            # special Joker display
            return [
                "┌─────────┐",
                "│ ★       │",
                "│  JOKER  │",
                "│    *    │",
                "│         │",
                "│       ★ │",
                "└─────────┘",
            ]

        # regular card display
        symbol = self.symbol
        suit = self.suit.value

        # Pad symbol for alignment (handle "10" being 2 chars)
        left_symbol = f"{symbol:<2}"
        right_symbol = f"{symbol:>2}"

        return [
            "┌─────────┐",
            f"│ {left_symbol}      │",
            "│         │",
            f"│    {suit}    │",
            "│         │",
            f"│      {right_symbol} │",
            "└─────────┘",
        ]
