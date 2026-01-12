"""Unit tests for the Bot AI."""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai.bot_ai import BotAI
from src.ai.memory import BotMemory
from src.ai.heuristics import ChallengeHeuristics, SwapHeuristics
from src.models import Card, Rank, Suit, GridPosition, PowerType


class TestBotMemory(unittest.TestCase):
    """Tests for bot memory system."""

    def test_memory_starts_empty(self):
        """Memory should start with no known cards."""
        memory = BotMemory()
        self.assertEqual(len(memory.get_own_known()), 0)
        self.assertEqual(len(memory.get_opponent_known()), 0)

    def test_remember_own_card(self):
        """Should remember cards in bot's grid."""
        memory = BotMemory()
        card = Card(Rank.ACE, Suit.HEARTS)

        memory.remember_own_card(GridPosition.TOP_LEFT, card)

        known = memory.get_own_known()
        self.assertEqual(len(known), 1)
        self.assertEqual(known[GridPosition.TOP_LEFT], card)

    def test_remember_opponent_card(self):
        """Should remember cards in opponent's grid."""
        memory = BotMemory()
        card = Card(Rank.KING, Suit.SPADES)

        memory.remember_opponent_card(GridPosition.BOTTOM_RIGHT, card)

        known = memory.get_opponent_known()
        self.assertEqual(len(known), 1)
        self.assertEqual(known[GridPosition.BOTTOM_RIGHT], card)

    def test_forget_own_position(self):
        """Should be able to forget a position (after blind swap)."""
        memory = BotMemory()
        card = Card(Rank.ACE, Suit.HEARTS)
        memory.remember_own_card(GridPosition.TOP_LEFT, card)

        memory.forget_own_position(GridPosition.TOP_LEFT)

        self.assertEqual(len(memory.get_own_known()), 0)

    def test_update_seen_reduces_probability(self):
        """Seeing a card should reduce its probability."""
        memory = BotMemory()
        initial_prob = memory.probability_of_rank(Rank.ACE)

        # There are 4 Aces initially
        memory.update_seen(Card(Rank.ACE, Suit.HEARTS))

        new_prob = memory.probability_of_rank(Rank.ACE)
        self.assertLess(new_prob, initial_prob)

    def test_find_worst_own_known(self):
        """Should find the highest value known card."""
        memory = BotMemory()
        memory.remember_own_card(GridPosition.TOP_LEFT, Card(Rank.ACE, Suit.HEARTS))  # 1
        memory.remember_own_card(GridPosition.TOP_RIGHT, Card(Rank.QUEEN, Suit.SPADES))  # 10

        worst = memory.find_worst_own_known()

        self.assertIsNotNone(worst)
        pos, card = worst
        self.assertEqual(pos, GridPosition.TOP_RIGHT)
        self.assertEqual(card.value, 10)

    def test_find_best_own_known(self):
        """Should find the lowest value known card."""
        memory = BotMemory()
        memory.remember_own_card(GridPosition.TOP_LEFT, Card(Rank.ACE, Suit.HEARTS))  # 1
        memory.remember_own_card(GridPosition.TOP_RIGHT, Card(Rank.QUEEN, Suit.SPADES))  # 10

        best = memory.find_best_own_known()

        self.assertIsNotNone(best)
        pos, card = best
        self.assertEqual(pos, GridPosition.TOP_LEFT)
        self.assertEqual(card.value, 1)


class TestChallengeHeuristics(unittest.TestCase):
    """Tests for challenge probability calculations."""

    def test_peek_has_low_base_probability(self):
        """PEEK claims should have low challenge probability."""
        memory = BotMemory()
        prob = ChallengeHeuristics.calculate_challenge_probability(
            PowerType.PEEK, memory, turn_number=1,
            claimant_penalty=0, challenger_penalty=0
        )
        self.assertLess(prob, 0.3)

    def test_blind_swap_has_higher_probability(self):
        """BLIND_SWAP claims should have higher challenge probability."""
        memory = BotMemory()
        peek_prob = ChallengeHeuristics.calculate_challenge_probability(
            PowerType.PEEK, memory, turn_number=1,
            claimant_penalty=0, challenger_penalty=0
        )
        swap_prob = ChallengeHeuristics.calculate_challenge_probability(
            PowerType.BLIND_SWAP, memory, turn_number=1,
            claimant_penalty=0, challenger_penalty=0
        )
        self.assertGreater(swap_prob, peek_prob)

    def test_late_game_increases_probability(self):
        """Challenge probability should increase late game."""
        memory = BotMemory()
        early_prob = ChallengeHeuristics.calculate_challenge_probability(
            PowerType.PEEK, memory, turn_number=3,
            claimant_penalty=0, challenger_penalty=0
        )
        late_prob = ChallengeHeuristics.calculate_challenge_probability(
            PowerType.PEEK, memory, turn_number=15,
            claimant_penalty=0, challenger_penalty=0
        )
        self.assertGreater(late_prob, early_prob)

    def test_prior_penalty_increases_probability(self):
        """If claimant has prior penalties, challenge more."""
        memory = BotMemory()
        no_penalty = ChallengeHeuristics.calculate_challenge_probability(
            PowerType.PEEK, memory, turn_number=5,
            claimant_penalty=0, challenger_penalty=0
        )
        with_penalty = ChallengeHeuristics.calculate_challenge_probability(
            PowerType.PEEK, memory, turn_number=5,
            claimant_penalty=10, challenger_penalty=0
        )
        self.assertGreater(with_penalty, no_penalty)


class TestSwapHeuristics(unittest.TestCase):
    """Tests for swap decision heuristics."""

    def test_should_swap_excellent_cards(self):
        """Should always swap excellent cards (Joker, King, Ace)."""
        self.assertTrue(SwapHeuristics.should_swap(
            drawn_value=-2, known_worst_value=None, has_unknown_positions=True
        ))
        self.assertTrue(SwapHeuristics.should_swap(
            drawn_value=0, known_worst_value=None, has_unknown_positions=True
        ))
        self.assertTrue(SwapHeuristics.should_swap(
            drawn_value=1, known_worst_value=None, has_unknown_positions=True
        ))

    def test_should_swap_improvement(self):
        """Should swap if drawn card is better than known card."""
        self.assertTrue(SwapHeuristics.should_swap(
            drawn_value=3, known_worst_value=10, has_unknown_positions=False
        ))

    def test_should_not_swap_worse_card(self):
        """Should not swap if drawn card is worse."""
        self.assertFalse(SwapHeuristics.should_swap(
            drawn_value=8, known_worst_value=3, has_unknown_positions=False
        ))


class TestBotAI(unittest.TestCase):
    """Tests for the main Bot AI."""

    def test_initialize_memory(self):
        """Should initialize memory with peeked cards."""
        bot = BotAI()
        peeked = [
            (GridPosition.BOTTOM_LEFT, Card(Rank.ACE, Suit.HEARTS)),
            (GridPosition.BOTTOM_RIGHT, Card(Rank.TWO, Suit.SPADES)),
        ]

        bot.initialize_memory(peeked)

        known = bot.memory.get_own_known()
        self.assertEqual(len(known), 2)

    def test_decide_draw_takes_joker_from_discard(self):
        """Should always take Joker from discard."""
        bot = BotAI()
        joker = Card(Rank.JOKER, Suit.NONE)

        decision = bot.decide_draw_source(joker)

        self.assertEqual(decision, "discard")

    def test_decide_draw_takes_king_from_discard(self):
        """Should always take King from discard."""
        bot = BotAI()
        king = Card(Rank.KING, Suit.HEARTS)

        decision = bot.decide_draw_source(king)

        self.assertEqual(decision, "discard")

    def test_decide_draw_declines_bad_discard(self):
        """Should draw from deck if discard is bad."""
        bot = BotAI()
        queen = Card(Rank.QUEEN, Suit.HEARTS)  # 10 points

        decision = bot.decide_draw_source(queen)

        self.assertEqual(decision, "deck")

    def test_decide_action_swaps_excellent_card(self):
        """Should swap excellent cards into grid."""
        bot = BotAI()
        bot.initialize_memory([
            (GridPosition.BOTTOM_LEFT, Card(Rank.FIVE, Suit.HEARTS)),
            (GridPosition.BOTTOM_RIGHT, Card(Rank.SIX, Suit.SPADES)),
        ])

        joker = Card(Rank.JOKER, Suit.NONE)
        decision = bot.decide_action(joker, can_discard=True, turn_number=5, opponent_penalty=0)

        self.assertEqual(decision.action, "swap")

    def test_decide_action_improves_known_position(self):
        """Should swap to improve a known bad position."""
        bot = BotAI()
        bot.initialize_memory([
            (GridPosition.BOTTOM_LEFT, Card(Rank.QUEEN, Suit.HEARTS)),  # 10
            (GridPosition.BOTTOM_RIGHT, Card(Rank.TWO, Suit.SPADES)),   # 2
        ])

        ace = Card(Rank.ACE, Suit.CLUBS)  # 1
        decision = bot.decide_action(ace, can_discard=True, turn_number=5, opponent_penalty=0)

        self.assertEqual(decision.action, "swap")
        self.assertEqual(decision.target_position, GridPosition.BOTTOM_LEFT)


class TestBotHawkeyeDecision(unittest.TestCase):
    """Tests for Hawk-Eye calling decision."""

    def test_should_not_call_early(self):
        """Should not call Hawk-Eye early in the game."""
        bot = BotAI()
        bot.initialize_memory([
            (GridPosition.TOP_LEFT, Card(Rank.JOKER, Suit.NONE)),
            (GridPosition.TOP_RIGHT, Card(Rank.KING, Suit.HEARTS)),
            (GridPosition.BOTTOM_LEFT, Card(Rank.ACE, Suit.CLUBS)),
            (GridPosition.BOTTOM_RIGHT, Card(Rank.TWO, Suit.SPADES)),
        ])

        # Even with excellent cards, don't call on turn 2
        self.assertFalse(bot.should_call_hawkeye(turn_number=2))

    def test_should_not_call_without_knowledge(self):
        """Should not call if don't know enough cards."""
        bot = BotAI()
        bot.initialize_memory([
            (GridPosition.BOTTOM_LEFT, Card(Rank.ACE, Suit.HEARTS)),
            (GridPosition.BOTTOM_RIGHT, Card(Rank.TWO, Suit.SPADES)),
        ])

        # Only knows 2 cards - not enough
        self.assertFalse(bot.should_call_hawkeye(turn_number=10))


if __name__ == '__main__':
    unittest.main()
