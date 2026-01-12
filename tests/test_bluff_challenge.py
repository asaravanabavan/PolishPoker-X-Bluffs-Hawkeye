"""Unit tests for the VAR Bluff/Challenge system."""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.game_engine import GameEngine
from src.models import Card, Rank, Suit, GridPosition, PowerType


class TestBluffChallengeSystem(unittest.TestCase):
    """Tests for the VAR challenge system."""

    def setUp(self):
        """Set up a game engine."""
        self.engine = GameEngine()
        self.engine.setup_game()

    def test_caught_bluff_adds_penalty(self):
        """When bluff is caught, bluffer receives 10 penalty points."""
        # Draw a non-power card
        self.engine.draw_from_deck()

        # Force the drawn card to be a 5 (non-power card)
        self.engine.state.drawn_card = Card(Rank.FIVE, Suit.HEARTS)

        # Attempt to claim it's a PEEK (7/8)
        # Challenge callback always challenges
        result = self.engine.attempt_power_play(
            claimed_power=PowerType.PEEK,
            target=GridPosition.TOP_LEFT,
            challenge_callback=lambda ctx: True  # Always challenge
        )

        # Bluffer should have 10 penalty points
        self.assertEqual(self.engine.state.human.penalty_points, 10)
        self.assertFalse(result.success)
        self.assertTrue(result.was_bluff)
        self.assertTrue(result.was_challenged)

    def test_wrong_challenge_penalizes_challenger(self):
        """When challenge is wrong, challenger receives 10 penalty points."""
        self.engine.draw_from_deck()

        # Force the drawn card to be a 7 (actual PEEK card)
        self.engine.state.drawn_card = Card(Rank.SEVEN, Suit.HEARTS)

        # Claim PEEK and get challenged (wrongly)
        result = self.engine.attempt_power_play(
            claimed_power=PowerType.PEEK,
            target=GridPosition.TOP_LEFT,
            challenge_callback=lambda ctx: True  # Always challenge
        )

        # Challenger (bot) should have 10 penalty points
        self.assertEqual(self.engine.state.bot.penalty_points, 10)
        self.assertTrue(result.success)
        self.assertFalse(result.was_bluff)
        self.assertTrue(result.was_challenged)

    def test_unchallenged_bluff_succeeds(self):
        """When bluff is not challenged, it succeeds."""
        self.engine.draw_from_deck()

        # Force a non-power card
        self.engine.state.drawn_card = Card(Rank.FIVE, Suit.HEARTS)

        # Claim PEEK but don't get challenged
        result = self.engine.attempt_power_play(
            claimed_power=PowerType.PEEK,
            target=GridPosition.TOP_LEFT,
            challenge_callback=lambda ctx: False  # Never challenge
        )

        # Should succeed with no penalties
        self.assertTrue(result.success)
        self.assertEqual(self.engine.state.human.penalty_points, 0)
        self.assertEqual(self.engine.state.bot.penalty_points, 0)

    def test_unchallenged_truth_succeeds(self):
        """When truth is not challenged, it succeeds."""
        self.engine.draw_from_deck()

        # Force an actual power card
        self.engine.state.drawn_card = Card(Rank.NINE, Suit.HEARTS)

        # Claim SPY (matching power)
        result = self.engine.attempt_power_play(
            claimed_power=PowerType.SPY,
            target=GridPosition.TOP_LEFT,  # Spy on opponent
            challenge_callback=lambda ctx: False
        )

        self.assertTrue(result.success)
        self.assertEqual(self.engine.state.human.penalty_points, 0)


class TestPowerExecution(unittest.TestCase):
    """Tests for power card execution."""

    def setUp(self):
        """Set up a game engine."""
        self.engine = GameEngine()
        self.engine.setup_game()

    def test_peek_reveals_own_card(self):
        """PEEK should reveal one of player's own cards."""
        self.engine.draw_from_deck()
        self.engine.state.drawn_card = Card(Rank.SEVEN, Suit.HEARTS)

        result = self.engine.attempt_power_play(
            claimed_power=PowerType.PEEK,
            target=GridPosition.TOP_LEFT,
            challenge_callback=lambda ctx: False
        )

        self.assertTrue(result.success)
        self.assertIsNotNone(result.revealed_card)
        self.assertIn("PEEK", result.message)

    def test_spy_reveals_opponent_card(self):
        """SPY should reveal one of opponent's cards."""
        self.engine.draw_from_deck()
        self.engine.state.drawn_card = Card(Rank.NINE, Suit.HEARTS)

        result = self.engine.attempt_power_play(
            claimed_power=PowerType.SPY,
            target=GridPosition.TOP_LEFT,
            challenge_callback=lambda ctx: False
        )

        self.assertTrue(result.success)
        self.assertIsNotNone(result.revealed_card)
        self.assertIn("SPY", result.message)

    def test_blind_swap_exchanges_cards(self):
        """BLIND_SWAP should exchange cards between players."""
        self.engine.draw_from_deck()
        self.engine.state.drawn_card = Card(Rank.JACK, Suit.HEARTS)

        # Remember original cards
        human_card = self.engine.state.human.get_card(GridPosition.TOP_LEFT)
        bot_card = self.engine.state.bot.get_card(GridPosition.BOTTOM_RIGHT)

        result = self.engine.attempt_power_play(
            claimed_power=PowerType.BLIND_SWAP,
            target=GridPosition.TOP_LEFT,
            opponent_target=GridPosition.BOTTOM_RIGHT,
            challenge_callback=lambda ctx: False
        )

        self.assertTrue(result.success)

        # Cards should be swapped
        new_human_card = self.engine.state.human.get_card(GridPosition.TOP_LEFT)
        new_bot_card = self.engine.state.bot.get_card(GridPosition.BOTTOM_RIGHT)

        self.assertEqual(new_human_card, bot_card)
        self.assertEqual(new_bot_card, human_card)


class TestChallengeContext(unittest.TestCase):
    """Tests for challenge context information."""

    def test_challenge_callback_receives_context(self):
        """Challenge callback should receive proper context."""
        self.engine = GameEngine()
        self.engine.setup_game()
        self.engine.draw_from_deck()

        received_context = None

        def capture_context(ctx):
            nonlocal received_context
            received_context = ctx
            return False

        self.engine.attempt_power_play(
            claimed_power=PowerType.PEEK,
            target=GridPosition.TOP_LEFT,
            challenge_callback=capture_context
        )

        self.assertIsNotNone(received_context)
        self.assertEqual(received_context.claimed_power, PowerType.PEEK)
        self.assertEqual(received_context.claimant_name, "Player")


class TestVARTruthTable(unittest.TestCase):
    """
    Tests for the complete VAR truth table:

    | Was Bluff | Challenged |        Result               |
    |-----------|------------|------------------------------|
    |   False   |   False    | Power executes normally      |
    |   False   |   True     | Challenger +10, power OK     |
    |   True    |   False    | Power executes (free bluff!) |
    |   True    |   True     | Bluffer +10, power DENIED    |
    """

    def setUp(self):
        """Set up a game engine."""
        self.engine = GameEngine()
        self.engine.setup_game()

    def test_truth_no_challenge_succeeds(self):
        """Truth + No Challenge = Power executes, no penalties."""
        self.engine.draw_from_deck()
        self.engine.state.drawn_card = Card(Rank.SEVEN, Suit.HEARTS)

        result = self.engine.attempt_power_play(
            claimed_power=PowerType.PEEK,
            target=GridPosition.TOP_LEFT,
            challenge_callback=lambda ctx: False
        )

        self.assertTrue(result.success)
        self.assertEqual(self.engine.state.human.penalty_points, 0)
        self.assertEqual(self.engine.state.bot.penalty_points, 0)

    def test_truth_challenged_penalizes_challenger(self):
        """Truth + Challenge = Challenger +10, power executes."""
        self.engine.draw_from_deck()
        self.engine.state.drawn_card = Card(Rank.SEVEN, Suit.HEARTS)

        result = self.engine.attempt_power_play(
            claimed_power=PowerType.PEEK,
            target=GridPosition.TOP_LEFT,
            challenge_callback=lambda ctx: True
        )

        self.assertTrue(result.success)
        self.assertEqual(self.engine.state.human.penalty_points, 0)
        self.assertEqual(self.engine.state.bot.penalty_points, 10)

    def test_bluff_no_challenge_free_bluff(self):
        """Bluff + No Challenge = Free bluff! Power executes."""
        self.engine.draw_from_deck()
        self.engine.state.drawn_card = Card(Rank.FIVE, Suit.HEARTS)

        result = self.engine.attempt_power_play(
            claimed_power=PowerType.PEEK,
            target=GridPosition.TOP_LEFT,
            challenge_callback=lambda ctx: False
        )

        self.assertTrue(result.success)
        self.assertEqual(self.engine.state.human.penalty_points, 0)
        self.assertEqual(self.engine.state.bot.penalty_points, 0)

    def test_bluff_caught_penalizes_bluffer(self):
        """Bluff + Challenge = Bluffer +10, power denied."""
        self.engine.draw_from_deck()
        self.engine.state.drawn_card = Card(Rank.FIVE, Suit.HEARTS)

        result = self.engine.attempt_power_play(
            claimed_power=PowerType.PEEK,
            target=GridPosition.TOP_LEFT,
            challenge_callback=lambda ctx: True
        )

        self.assertFalse(result.success)
        self.assertEqual(self.engine.state.human.penalty_points, 10)
        self.assertEqual(self.engine.state.bot.penalty_points, 0)


if __name__ == '__main__':
    unittest.main()
