"""Unit tests for the Player model."""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.player import Player, GridPosition
from src.models.card import Card, Rank, Suit


class TestPlayerCreation(unittest.TestCase):
    """Tests for player creation."""

    def test_player_has_name(self):
        """Player should have the provided name."""
        player = Player("TestPlayer")
        self.assertEqual(player.name, "TestPlayer")

    def test_player_starts_with_zero_penalty(self):
        """Player should start with 0 penalty points."""
        player = Player("Test")
        self.assertEqual(player.penalty_points, 0)

    def test_player_is_human_flag(self):
        """Player should correctly store is_human flag."""
        human = Player("Human", is_human=True)
        bot = Player("Bot", is_human=False)

        self.assertTrue(human.is_human)
        self.assertFalse(bot.is_human)


class TestGridPosition(unittest.TestCase):
    """Tests for GridPosition enum."""

    def test_grid_position_values(self):
        """GridPosition should have values 0-3."""
        self.assertEqual(GridPosition.TOP_LEFT.value, 0)
        self.assertEqual(GridPosition.TOP_RIGHT.value, 1)
        self.assertEqual(GridPosition.BOTTOM_LEFT.value, 2)
        self.assertEqual(GridPosition.BOTTOM_RIGHT.value, 3)

    def test_display_number_is_one_indexed(self):
        """display_number should be 1-indexed."""
        self.assertEqual(GridPosition.TOP_LEFT.display_number, 1)
        self.assertEqual(GridPosition.TOP_RIGHT.display_number, 2)
        self.assertEqual(GridPosition.BOTTOM_LEFT.display_number, 3)
        self.assertEqual(GridPosition.BOTTOM_RIGHT.display_number, 4)

    def test_top_row(self):
        """top_row should return TOP_LEFT and TOP_RIGHT."""
        top = GridPosition.top_row()
        self.assertEqual(top, [GridPosition.TOP_LEFT, GridPosition.TOP_RIGHT])

    def test_bottom_row(self):
        """bottom_row should return BOTTOM_LEFT and BOTTOM_RIGHT."""
        bottom = GridPosition.bottom_row()
        self.assertEqual(bottom, [GridPosition.BOTTOM_LEFT, GridPosition.BOTTOM_RIGHT])


class TestPlayerGrid(unittest.TestCase):
    """Tests for player grid management."""

    def setUp(self):
        """Create test cards and player."""
        self.cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.TWO, Suit.DIAMONDS),
            Card(Rank.THREE, Suit.CLUBS),
            Card(Rank.FOUR, Suit.SPADES),
        ]
        self.player = Player("Test")

    def test_setup_grid_requires_four_cards(self):
        """setup_grid should require exactly 4 cards."""
        with self.assertRaises(ValueError):
            self.player.setup_grid([self.cards[0]])

        with self.assertRaises(ValueError):
            self.player.setup_grid(self.cards + [Card(Rank.FIVE, Suit.HEARTS)])

    def test_setup_grid_places_cards(self):
        """setup_grid should place cards at correct positions."""
        self.player.setup_grid(self.cards)

        self.assertEqual(self.player.get_card(GridPosition.TOP_LEFT), self.cards[0])
        self.assertEqual(self.player.get_card(GridPosition.TOP_RIGHT), self.cards[1])
        self.assertEqual(self.player.get_card(GridPosition.BOTTOM_LEFT), self.cards[2])
        self.assertEqual(self.player.get_card(GridPosition.BOTTOM_RIGHT), self.cards[3])

    def test_setup_grid_cards_are_face_down(self):
        """All cards should start face down after setup."""
        self.player.setup_grid(self.cards)

        for pos in GridPosition.all_positions():
            card = self.player.get_card(pos)
            self.assertFalse(card.face_up)

    def test_peek_initial_returns_bottom_cards(self):
        """peek_initial should return bottom row cards."""
        self.player.setup_grid(self.cards)
        peeked = self.player.peek_initial()

        self.assertEqual(len(peeked), 2)
        positions = [p for p, c in peeked]
        self.assertIn(GridPosition.BOTTOM_LEFT, positions)
        self.assertIn(GridPosition.BOTTOM_RIGHT, positions)

    def test_peek_initial_marks_positions_known(self):
        """peek_initial should mark bottom positions as known."""
        self.player.setup_grid(self.cards)
        self.player.peek_initial()

        known = self.player.known_positions
        self.assertIn(GridPosition.BOTTOM_LEFT, known)
        self.assertIn(GridPosition.BOTTOM_RIGHT, known)
        self.assertNotIn(GridPosition.TOP_LEFT, known)


class TestPlayerSwap(unittest.TestCase):
    """Tests for card swapping."""

    def setUp(self):
        """Create test player with grid."""
        self.cards = [
            Card(Rank.QUEEN, Suit.HEARTS),  # 10 pts
            Card(Rank.JACK, Suit.DIAMONDS),  # 10 pts
            Card(Rank.ACE, Suit.CLUBS),      # 1 pt
            Card(Rank.TWO, Suit.SPADES),     # 2 pts
        ]
        self.player = Player("Test")
        self.player.setup_grid(self.cards)

    def test_swap_returns_old_card(self):
        """swap_card should return the old card."""
        new_card = Card(Rank.KING, Suit.HEARTS)
        old_card = self.player.swap_card(GridPosition.TOP_LEFT, new_card)

        self.assertEqual(old_card, self.cards[0])

    def test_swap_places_new_card(self):
        """swap_card should place the new card in the grid."""
        new_card = Card(Rank.KING, Suit.HEARTS)
        self.player.swap_card(GridPosition.TOP_LEFT, new_card)

        self.assertEqual(self.player.get_card(GridPosition.TOP_LEFT), new_card)

    def test_swap_makes_new_card_face_up(self):
        """Swapped-in card should be face up."""
        new_card = Card(Rank.KING, Suit.HEARTS)
        self.player.swap_card(GridPosition.TOP_LEFT, new_card)

        self.assertTrue(self.player.get_card(GridPosition.TOP_LEFT).face_up)

    def test_swap_marks_position_known(self):
        """swap_card should mark position as known."""
        new_card = Card(Rank.KING, Suit.HEARTS)
        self.player.swap_card(GridPosition.TOP_LEFT, new_card)

        self.assertIn(GridPosition.TOP_LEFT, self.player.known_positions)


class TestPlayerScoring(unittest.TestCase):
    """Tests for score calculation."""

    def test_calculate_grid_score(self):
        """Should correctly sum all card values."""
        cards = [
            Card(Rank.JOKER, Suit.NONE),  # -2
            Card(Rank.KING, Suit.HEARTS),  # 0
            Card(Rank.ACE, Suit.CLUBS),    # 1
            Card(Rank.FIVE, Suit.SPADES),  # 5
        ]
        player = Player("Test")
        player.setup_grid(cards)

        # -2 + 0 + 1 + 5 = 4
        self.assertEqual(player.calculate_grid_score(), 4)

    def test_total_score_includes_penalty(self):
        """total_score should include penalty points."""
        cards = [
            Card(Rank.ACE, Suit.HEARTS),
            Card(Rank.TWO, Suit.DIAMONDS),
            Card(Rank.THREE, Suit.CLUBS),
            Card(Rank.FOUR, Suit.SPADES),
        ]
        player = Player("Test")
        player.setup_grid(cards)
        player.add_penalty(10)

        # 1 + 2 + 3 + 4 = 10 grid + 10 penalty = 20
        self.assertEqual(player.total_score, 20)


class TestPlayerPenalty(unittest.TestCase):
    """Tests for penalty points."""

    def test_add_penalty(self):
        """add_penalty should increase penalty_points."""
        player = Player("Test")
        player.add_penalty(10)

        self.assertEqual(player.penalty_points, 10)

    def test_add_multiple_penalties(self):
        """Multiple penalties should accumulate."""
        player = Player("Test")
        player.add_penalty(10)
        player.add_penalty(10)

        self.assertEqual(player.penalty_points, 20)


if __name__ == '__main__':
    unittest.main()
