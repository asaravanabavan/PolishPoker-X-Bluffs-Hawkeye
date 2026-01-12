"""Unit tests for the Deck model."""
import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.deck import Deck
from src.models.card import Rank


class TestDeckCreation(unittest.TestCase):
    """Tests for deck creation."""

    def test_deck_has_54_cards(self):
        """Deck should have exactly 54 cards (52 + 2 Jokers)."""
        deck = Deck(auto_shuffle=False)
        self.assertEqual(deck.cards_remaining, 54)

    def test_deck_has_two_jokers(self):
        """Deck should contain exactly 2 Jokers."""
        deck = Deck(auto_shuffle=False)
        jokers = [c for c in deck._cards if c.rank == Rank.JOKER]
        self.assertEqual(len(jokers), 2)

    def test_deck_has_four_of_each_rank(self):
        """Deck should have 4 of each standard rank."""
        deck = Deck(auto_shuffle=False)

        for rank in [Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE,
                     Rank.SIX, Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN,
                     Rank.JACK, Rank.QUEEN, Rank.KING]:
            count = sum(1 for c in deck._cards if c.rank == rank)
            self.assertEqual(count, 4, f"Should have 4 {rank.name}s")

    def test_deck_len_returns_cards_remaining(self):
        """len(deck) should return cards remaining."""
        deck = Deck()
        self.assertEqual(len(deck), deck.cards_remaining)


class TestDeckShuffle(unittest.TestCase):
    """Tests for deck shuffling."""

    def test_shuffle_changes_order(self):
        """Shuffling should change the card order."""
        deck = Deck(auto_shuffle=False)
        original_order = [str(c) for c in deck._cards]

        deck.shuffle()
        shuffled_order = [str(c) for c in deck._cards]

        # Statistically almost impossible to be the same
        self.assertNotEqual(original_order, shuffled_order)

    def test_shuffle_preserves_card_count(self):
        """Shuffling should not change the number of cards."""
        deck = Deck(auto_shuffle=False)
        original_count = len(deck._cards)

        deck.shuffle()

        self.assertEqual(len(deck._cards), original_count)


class TestDeckDraw(unittest.TestCase):
    """Tests for drawing cards."""

    def test_draw_reduces_count(self):
        """Drawing should reduce the card count by 1."""
        deck = Deck()
        initial = deck.cards_remaining

        deck.draw()

        self.assertEqual(deck.cards_remaining, initial - 1)

    def test_draw_returns_card(self):
        """Draw should return a Card object."""
        deck = Deck()
        card = deck.draw()

        from src.models.card import Card
        self.assertIsInstance(card, Card)

    def test_draw_multiple_cards(self):
        """Should be able to draw multiple cards."""
        deck = Deck()

        for i in range(10):
            deck.draw()

        self.assertEqual(deck.cards_remaining, 44)

    def test_deal_returns_correct_count(self):
        """Deal should return the requested number of cards."""
        deck = Deck()
        cards = deck.deal(4)

        self.assertEqual(len(cards), 4)
        self.assertEqual(deck.cards_remaining, 50)


class TestDeckDiscard(unittest.TestCase):
    """Tests for the discard pile."""

    def test_discard_adds_to_pile(self):
        """Discarding should add card to discard pile."""
        deck = Deck()
        card = deck.draw()

        deck.discard(card)

        self.assertEqual(deck.discard_count, 1)
        self.assertEqual(deck.top_discard, card)

    def test_draw_from_discard(self):
        """Should be able to draw from discard pile."""
        deck = Deck()
        card = deck.draw()
        deck.discard(card)

        drawn = deck.draw_from_discard()

        self.assertEqual(drawn, card)
        self.assertEqual(deck.discard_count, 0)

    def test_empty_discard_returns_none_for_top(self):
        """Empty discard pile should return None for top_discard."""
        deck = Deck()
        self.assertIsNone(deck.top_discard)

    def test_draw_from_empty_discard_raises(self):
        """Drawing from empty discard should raise RuntimeError."""
        deck = Deck()

        with self.assertRaises(RuntimeError):
            deck.draw_from_discard()


class TestDeckReshuffle(unittest.TestCase):
    """Tests for reshuffling the discard pile."""

    def test_reshuffle_when_deck_empty(self):
        """When deck is empty, drawing should reshuffle discard."""
        deck = Deck()

        # Draw all cards and discard them
        while deck.cards_remaining > 0:
            card = deck.draw()
            deck.discard(card)

        self.assertEqual(deck.cards_remaining, 0)
        self.assertEqual(deck.discard_count, 54)

        # Drawing should trigger reshuffle
        card = deck.draw()

        self.assertIsNotNone(card)
        self.assertGreater(deck.cards_remaining, 0)

    def test_reshuffle_keeps_top_discard(self):
        """Reshuffle should keep the top discard card visible."""
        deck = Deck()

        # Draw all but a few cards
        for _ in range(50):
            card = deck.draw()
            deck.discard(card)

        # Draw remaining cards
        while deck.cards_remaining > 0:
            deck.draw()

        # Remember top discard before reshuffle
        top_before = deck.top_discard

        # Trigger reshuffle
        deck.draw()

        # Top discard should still be there
        self.assertIsNotNone(deck.top_discard)


class TestDeckProperties(unittest.TestCase):
    """Tests for deck properties."""

    def test_is_empty_property(self):
        """is_empty should return True only when deck is empty."""
        deck = Deck()
        self.assertFalse(deck.is_empty)

        # Empty the deck
        while deck.cards_remaining > 0:
            deck.draw()

        self.assertTrue(deck.is_empty)

    def test_peek_top_returns_without_removing(self):
        """peek_top should return card without removing it."""
        deck = Deck()
        initial_count = deck.cards_remaining

        peeked = deck.peek_top()

        self.assertIsNotNone(peeked)
        self.assertEqual(deck.cards_remaining, initial_count)


if __name__ == '__main__':
    unittest.main()
