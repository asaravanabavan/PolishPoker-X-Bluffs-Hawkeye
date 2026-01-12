"""Unit tests for the GameEngine."""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.engine.game_engine import GameEngine
from src.engine.game_state import GamePhase
from src.models import GridPosition


class TestGameEngineSetup(unittest.TestCase):
    """Tests for game setup."""

    def test_setup_game_deals_cards(self):
        """setup_game should deal 4 cards to each player."""
        engine = GameEngine()
        engine.setup_game()

        for pos in GridPosition.all_positions():
            self.assertIsNotNone(engine.state.human.get_card(pos))
            self.assertIsNotNone(engine.state.bot.get_card(pos))

    def test_setup_game_returns_peeked_cards(self):
        """setup_game should return peeked cards for both players."""
        engine = GameEngine()
        human_peeked, bot_peeked = engine.setup_game()

        self.assertEqual(len(human_peeked), 2)
        self.assertEqual(len(bot_peeked), 2)

    def test_setup_game_places_initial_discard(self):
        """setup_game should place one card in discard pile."""
        engine = GameEngine()
        engine.setup_game()

        self.assertIsNotNone(engine.state.deck.top_discard)

    def test_setup_game_sets_draw_phase(self):
        """setup_game should set phase to DRAW."""
        engine = GameEngine()
        engine.setup_game()

        self.assertEqual(engine.state.phase, GamePhase.DRAW)

    def test_setup_game_human_goes_first(self):
        """Human should be current player after setup."""
        engine = GameEngine()
        engine.setup_game()

        self.assertEqual(engine.state.current_player, engine.state.human)


class TestGameEngineDraw(unittest.TestCase):
    """Tests for draw phase."""

    def setUp(self):
        """Set up a game in draw phase."""
        self.engine = GameEngine()
        self.engine.setup_game()

    def test_draw_from_deck_returns_card(self):
        """draw_from_deck should return a card."""
        card = self.engine.draw_from_deck()
        self.assertIsNotNone(card)

    def test_draw_from_deck_sets_drawn_card(self):
        """draw_from_deck should set state.drawn_card."""
        card = self.engine.draw_from_deck()
        self.assertEqual(self.engine.state.drawn_card, card)

    def test_draw_from_deck_transitions_to_action(self):
        """draw_from_deck should transition to ACTION phase."""
        self.engine.draw_from_deck()
        self.assertEqual(self.engine.state.phase, GamePhase.ACTION)

    def test_draw_from_deck_marks_source(self):
        """draw_from_deck should mark drew_from_discard as False."""
        self.engine.draw_from_deck()
        self.assertFalse(self.engine.state.drew_from_discard)

    def test_draw_from_discard_returns_top_card(self):
        """draw_from_discard should return the top discard card."""
        top = self.engine.state.deck.top_discard
        card = self.engine.draw_from_discard()
        self.assertEqual(card, top)

    def test_draw_from_discard_marks_source(self):
        """draw_from_discard should mark drew_from_discard as True."""
        self.engine.draw_from_discard()
        self.assertTrue(self.engine.state.drew_from_discard)


class TestGameEngineAction(unittest.TestCase):
    """Tests for action phase."""

    def setUp(self):
        """Set up a game in action phase."""
        self.engine = GameEngine()
        self.engine.setup_game()
        self.drawn_card = self.engine.draw_from_deck()

    def test_swap_with_grid_returns_old_card(self):
        """swap_with_grid should return the old card."""
        old_card = self.engine.swap_with_grid(GridPosition.TOP_LEFT)
        self.assertIsNotNone(old_card)

    def test_swap_with_grid_places_drawn_card(self):
        """swap_with_grid should place drawn card in grid."""
        self.engine.swap_with_grid(GridPosition.TOP_LEFT)

        # The card at TOP_LEFT should now be the drawn card
        placed = self.engine.state.human.get_card(GridPosition.TOP_LEFT)
        self.assertEqual(placed, self.drawn_card)

    def test_swap_with_grid_discards_old_card(self):
        """swap_with_grid should discard the old card."""
        old_card = self.engine.swap_with_grid(GridPosition.TOP_LEFT)
        self.assertEqual(self.engine.state.deck.top_discard, old_card)

    def test_discard_drawn_puts_card_in_discard(self):
        """discard_drawn should put drawn card in discard pile."""
        self.engine.discard_drawn()
        self.assertEqual(self.engine.state.deck.top_discard, self.drawn_card)

    def test_cannot_discard_if_drew_from_discard(self):
        """Should not be able to discard if drew from discard pile."""
        engine = GameEngine()
        engine.setup_game()
        engine.draw_from_discard()

        self.assertFalse(engine.state.can_discard())


class TestGameEngineTurns(unittest.TestCase):
    """Tests for turn management."""

    def setUp(self):
        """Set up a game."""
        self.engine = GameEngine()
        self.engine.setup_game()

    def test_end_turn_switches_player(self):
        """end_turn should switch current player."""
        # Human's turn
        self.engine.draw_from_deck()
        self.engine.discard_drawn()
        self.engine.end_turn()

        # Should now be bot's turn
        self.assertEqual(self.engine.state.current_player, self.engine.state.bot)

    def test_end_turn_increments_turn_number(self):
        """Turn number should increment after full round."""
        # Human's turn
        self.engine.draw_from_deck()
        self.engine.discard_drawn()
        self.engine.end_turn()

        # Bot's turn - turn number same
        self.assertEqual(self.engine.state.turn_number, 1)

        self.engine.draw_from_deck()
        self.engine.discard_drawn()
        self.engine.end_turn()

        # Now turn number should be 2
        self.assertEqual(self.engine.state.turn_number, 2)


class TestGameEngineHawkeye(unittest.TestCase):
    """Tests for Hawk-Eye (end game) mechanic."""

    def setUp(self):
        """Set up a game."""
        self.engine = GameEngine()
        self.engine.setup_game()

    def test_call_hawkeye_sets_final_round(self):
        """call_hawkeye should set final_round flag."""
        self.engine.draw_from_deck()
        self.engine.call_hawkeye()

        self.assertTrue(self.engine.state.final_round)

    def test_call_hawkeye_records_caller(self):
        """call_hawkeye should record who called it."""
        self.engine.draw_from_deck()
        self.engine.call_hawkeye()

        self.assertEqual(
            self.engine.state.who_called_hawkeye,
            self.engine.state.human
        )

    def test_game_ends_after_final_round(self):
        """Game should end when returning to Hawk-Eye caller."""
        # Human calls Hawk-Eye
        self.engine.draw_from_deck()
        self.engine.call_hawkeye()
        self.engine.end_turn()

        # Bot's turn
        self.engine.draw_from_deck()
        self.engine.discard_drawn()
        continues = self.engine.end_turn()

        # Game should be over
        self.assertFalse(continues)
        self.assertEqual(self.engine.state.phase, GamePhase.GAME_OVER)


if __name__ == '__main__':
    unittest.main()
