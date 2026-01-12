"""Bot memory for tracking known cards."""
from typing import Optional
from collections import defaultdict

from ..models import Card, Rank, GridPosition


class BotMemory:
    """Tracks known cards in play."""

    # initial deck composition
    INITIAL_COUNTS = {
        Rank.JOKER: 2,
        Rank.ACE: 4, Rank.TWO: 4, Rank.THREE: 4, Rank.FOUR: 4,
        Rank.FIVE: 4, Rank.SIX: 4, Rank.SEVEN: 4, Rank.EIGHT: 4,
        Rank.NINE: 4, Rank.TEN: 4, Rank.JACK: 4, Rank.QUEEN: 4,
        Rank.KING: 4,
    }

    def __init__(self):
        """Initialize empty memory."""
        # known cards in bot's grid
        self._own_cards: dict[GridPosition, Optional[Card]] = {
            pos: None for pos in GridPosition.all_positions()
        }

        # known cards in opponent's grid
        self._opponent_cards: dict[GridPosition, Optional[Card]] = {
            pos: None for pos in GridPosition.all_positions()
        }

        # cards seen (in discard or revealed)
        self._seen_cards: list[Card] = []

        # Remaining card counts (for probability)
        self._remaining: dict[Rank, int] = dict(self.INITIAL_COUNTS)

    def remember_own_card(self, pos: GridPosition, card: Card) -> None:
        self._own_cards[pos] = card

    def remember_opponent_card(self, pos: GridPosition, card: Card) -> None:
        self._opponent_cards[pos] = card

    def forget_own_position(self, pos: GridPosition) -> None:
        self._own_cards[pos] = None

    def forget_opponent_position(self, pos: GridPosition) -> None:
        self._opponent_cards[pos] = None

    def update_seen(self, card: Card) -> None:
        """Record card was seen - reduces probability estimates."""
        self._seen_cards.append(card)
        if self._remaining[card.rank] > 0:
            self._remaining[card.rank] -= 1

    def get_own_known(self) -> dict[GridPosition, Card]:
        return {pos: card for pos, card in self._own_cards.items() if card}

    def get_opponent_known(self) -> dict[GridPosition, Card]:
        return {pos: card for pos, card in self._opponent_cards.items() if card}

    def get_own_unknown_positions(self) -> list[GridPosition]:
        return [pos for pos, card in self._own_cards.items() if card is None]

    def get_opponent_unknown_positions(self) -> list[GridPosition]:
        return [pos for pos, card in self._opponent_cards.items() if card is None]

    def count_own_known(self) -> int:
        """Count how many of bot's own cards are known."""
        return sum(1 for card in self._own_cards.values() if card is not None)

    def probability_of_rank(self, rank: Rank) -> float:
        """
        Calculate probability of drawing a specific rank.

        Args:
            rank: The rank to calculate probability for.

        Returns:
            Probability from 0.0 to 1.0.
        """
        total_remaining = sum(self._remaining.values())
        if total_remaining == 0:
            return 0.0
        return self._remaining[rank] / total_remaining

    def count_power_cards_seen(self, power_ranks: list[Rank]) -> int:
        """Count how many of specific power card ranks have been seen."""
        count = 0
        for card in self._seen_cards:
            if card.rank in power_ranks:
                count += 1
        return count

    def expected_unknown_value(self) -> float:
        """
        Calculate expected value of an unknown card.

        E[X] = Σ(value × probability) for all unseen ranks

        Returns:
            Expected point value.
        """
        total_remaining = sum(self._remaining.values())
        if total_remaining == 0:
            return 5.0  # Fallback average

        expected = sum(
            Card.value_for_rank(rank) * (count / total_remaining)
            for rank, count in self._remaining.items()
            if count > 0
        )
        return expected

    def estimate_own_score(self) -> float:
        """
        Estimate bot's grid score.

        Known cards: exact value
        Unknown cards: expected value

        Returns:
            Estimated total score.
        """
        total = 0.0
        expected = self.expected_unknown_value()

        for pos in GridPosition.all_positions():
            known_card = self._own_cards.get(pos)
            if known_card:
                total += known_card.value
            else:
                total += expected

        return total

    def estimate_opponent_score(self) -> float:
        """Estimate opponent's grid score."""
        total = 0.0
        expected = self.expected_unknown_value()

        for pos in GridPosition.all_positions():
            known_card = self._opponent_cards.get(pos)
            if known_card:
                total += known_card.value
            else:
                total += expected

        return total

    def find_worst_own_known(self) -> Optional[tuple[GridPosition, Card]]:
        """Find the worst (highest value) known card in bot's grid."""
        worst_pos = None
        worst_card = None
        worst_value = -10  # Lower than Joker's -2

        for pos, card in self._own_cards.items():
            if card and card.value > worst_value:
                worst_value = card.value
                worst_pos = pos
                worst_card = card

        if worst_pos is not None and worst_card is not None:
            return (worst_pos, worst_card)
        return None

    def find_best_own_known(self) -> Optional[tuple[GridPosition, Card]]:
        """Find the best (lowest value) known card in bot's grid."""
        best_pos = None
        best_card = None
        best_value = 100

        for pos, card in self._own_cards.items():
            if card and card.value < best_value:
                best_value = card.value
                best_pos = pos
                best_card = card

        if best_pos is not None and best_card is not None:
            return (best_pos, best_card)
        return None

    def get_cards_remaining(self) -> dict[Rank, int]:
        """Get remaining card counts by rank."""
        return dict(self._remaining)

    def reset(self) -> None:
        """Reset memory for a new game."""
        self._own_cards = {pos: None for pos in GridPosition.all_positions()}
        self._opponent_cards = {pos: None for pos in GridPosition.all_positions()}
        self._seen_cards = []
        self._remaining = dict(self.INITIAL_COUNTS)
