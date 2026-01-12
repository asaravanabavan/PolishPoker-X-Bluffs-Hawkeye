"""Player model with 2x2 grid management."""
from enum import IntEnum
from typing import Optional

from .card import Card


class GridPosition(IntEnum):
    """2x2 grid positions for player cards."""
    TOP_LEFT = 0
    TOP_RIGHT = 1
    BOTTOM_LEFT = 2
    BOTTOM_RIGHT = 3

    @classmethod
    def top_row(cls) -> list['GridPosition']:
        """Return positions in the top row."""
        return [cls.TOP_LEFT, cls.TOP_RIGHT]

    @classmethod
    def bottom_row(cls) -> list['GridPosition']:
        """Return positions in the bottom row."""
        return [cls.BOTTOM_LEFT, cls.BOTTOM_RIGHT]

    @classmethod
    def all_positions(cls) -> list['GridPosition']:
        """Return all positions in order."""
        return [cls.TOP_LEFT, cls.TOP_RIGHT, cls.BOTTOM_LEFT, cls.BOTTOM_RIGHT]

    @property
    def display_number(self) -> int:
        """Return 1-indexed display number for UI."""
        return self.value + 1


class Player:
    """A player with a 2x2 grid of cards and penalty tracking."""

    def __init__(self, name: str, is_human: bool = True):
        self.name = name
        self.is_human = is_human
        self._grid: list[Optional[Card]] = [None, None, None, None]
        self.penalty_points: int = 0
        # track which positions we've seen
        self._known_positions: set[GridPosition] = set()

    @property
    def grid(self) -> list[Optional[Card]]:
        """Return the card grid."""
        return self._grid

    @property
    def total_score(self) -> int:
        """Calculate total score (grid values + penalties). Lower is better."""
        grid_score = self.calculate_grid_score()
        return grid_score + self.penalty_points

    @property
    def visible_cards(self) -> list[tuple[GridPosition, Card]]:
        """Return list of (position, card) for all face-up cards."""
        result = []
        for pos in GridPosition.all_positions():
            card = self._grid[pos]
            if card and card.face_up:
                result.append((pos, card))
        return result

    @property
    def hidden_cards(self) -> list[tuple[GridPosition, Card]]:
        """Return list of (position, card) for all face-down cards."""
        result = []
        for pos in GridPosition.all_positions():
            card = self._grid[pos]
            if card and not card.face_up:
                result.append((pos, card))
        return result

    @property
    def known_positions(self) -> set[GridPosition]:
        """Return positions the player knows the value of."""
        return self._known_positions.copy()

    def setup_grid(self, cards: list[Card]) -> None:
        """Initialize grid with 4 cards (all face-down initially)."""
        if len(cards) != 4:
            raise ValueError(f"Grid requires exactly 4 cards, got {len(cards)}")

        for i, card in enumerate(cards):
            card.face_up = False  # All start face-down
            self._grid[i] = card

        self._known_positions.clear()

    def peek_initial(self) -> list[tuple[GridPosition, Card]]:
        """Peek at bottom two cards at game start."""
        result = []
        for pos in GridPosition.bottom_row():
            card = self._grid[pos]
            if card:
                card.face_up = True  # Mark as revealed/known
                self._known_positions.add(pos)
                result.append((pos, card))
        return result

    def get_card(self, pos: GridPosition) -> Optional[Card]:
        """Get the card at a specific grid position."""
        return self._grid[pos]

    def swap_card(self, pos: GridPosition, new_card: Card) -> Card:
        """
        Swap a card at a position with a new card.

        The new card becomes face-up.
        The old card is returned (typically goes to discard).

        Args:
            pos: The grid position to swap.
            new_card: The new card to place.

        Returns:
            The old card that was removed.

        Raises:
            ValueError: If no card exists at that position.
        """
        old_card = self._grid[pos]
        if old_card is None:
            raise ValueError(f"No card at position {pos}")

        new_card.face_up = True
        self._grid[pos] = new_card
        self._known_positions.add(pos)

        return old_card

    def reveal_card(self, pos: GridPosition) -> Optional[Card]:
        """
        Reveal (flip face-up) the card at a position.

        Also marks this position as known.

        Args:
            pos: The grid position to reveal.

        Returns:
            The revealed card, or None if position is empty.
        """
        card = self._grid[pos]
        if card:
            card.face_up = True
            self._known_positions.add(pos)
        return card

    def mark_known(self, pos: GridPosition) -> None:
        """Mark position as known (player has seen the card)."""
        self._known_positions.add(pos)

    def mark_unknown(self, pos: GridPosition) -> None:
        """Mark position as unknown (e.g., after blind swap)."""
        self._known_positions.discard(pos)

    def add_penalty(self, points: int) -> None:
        """Add penalty points from failed bluffs or wrong challenges."""
        self.penalty_points += points

    def calculate_grid_score(self) -> int:
        """Calculate total score of all cards in the grid."""
        total = 0
        for card in self._grid:
            if card:
                total += card.value
        return total

    def reveal_all(self) -> None:
        """Reveal all cards in the grid (end of game)."""
        for card in self._grid:
            if card:
                card.face_up = True
        self._known_positions = set(GridPosition.all_positions())

    def get_unknown_positions(self) -> list[GridPosition]:
        """Return list of positions the player hasn't seen."""
        return [pos for pos in GridPosition.all_positions()
                if pos not in self._known_positions]

    def get_known_cards(self) -> dict[GridPosition, Card]:
        """Return dict of known position -> card."""
        result = {}
        for pos in self._known_positions:
            card = self._grid[pos]
            if card:
                result[pos] = card
        return result

    def __repr__(self) -> str:
        """Return string representation of player state."""
        return (f"Player(name='{self.name}', is_human={self.is_human}, "
                f"penalty={self.penalty_points})")
