"""Deck with shuffle, draw, and discard functionality."""
import random
from typing import Optional

from .card import Card, Rank, Suit


class Deck:
    """54-card deck with draw and discard piles."""

    def __init__(self, auto_shuffle: bool = True):
        self._cards: list[Card] = []
        self._discard: list[Card] = []
        self._build_deck()
        if auto_shuffle:
            self.shuffle()

    def _build_deck(self) -> None:
        self._cards = []

        # Add standard cards (4 suits x 13 ranks = 52 cards)
        standard_ranks = [
            Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE,
            Rank.SIX, Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN,
            Rank.JACK, Rank.QUEEN, Rank.KING
        ]
        standard_suits = [Suit.HEARTS, Suit.DIAMONDS, Suit.CLUBS, Suit.SPADES]

        for suit in standard_suits:
            for rank in standard_ranks:
                self._cards.append(Card(rank, suit))

        # add 2 Jokers
        self._cards.append(Card.create_joker())
        self._cards.append(Card.create_joker())

    @property
    def cards_remaining(self) -> int:
        return len(self._cards)

    @property
    def discard_count(self) -> int:
        return len(self._discard)

    @property
    def top_discard(self) -> Optional[Card]:
        if self._discard:
            return self._discard[-1]
        return None

    @property
    def is_empty(self) -> bool:
        return len(self._cards) == 0

    def shuffle(self) -> None:
        """Shuffle the draw pile."""
        random.shuffle(self._cards)

    def draw(self) -> Card:
        """Draw a card from deck (reshuffle discard if needed)."""
        if self.is_empty:
            self._reshuffle_discard()

        if self.is_empty:
            raise RuntimeError("Cannot draw: both deck and discard are empty")

        return self._cards.pop()

    def draw_from_discard(self) -> Card:
        """Draw the top card from the discard pile."""
        if not self._discard:
            raise RuntimeError("Cannot draw: discard pile is empty")

        return self._discard.pop()

    def discard(self, card: Card) -> None:
        """Add a card to the top of the discard pile."""
        self._discard.append(card)

    def peek_top(self) -> Optional[Card]:
        """Peek at the top card of the draw pile without removing it."""
        if self._cards:
            return self._cards[-1]
        return None

    def _reshuffle_discard(self) -> None:
        """Reshuffle discard pile back into deck (keep top card visible)."""
        if not self._discard:
            return

        # keep the top discard card visible
        if len(self._discard) > 1:
            top_card = self._discard.pop()
            self._cards = self._discard.copy()
            self._discard = [top_card]
            self.shuffle()

    def deal(self, count: int) -> list[Card]:
        """Deal multiple cards from the deck."""
        cards = []
        for _ in range(count):
            cards.append(self.draw())
        return cards

    def __len__(self) -> int:
        """Return total cards remaining in draw pile."""
        return self.cards_remaining

    def __repr__(self) -> str:
        """Return string representation of deck state."""
        return f"Deck(draw={self.cards_remaining}, discard={self.discard_count})"
