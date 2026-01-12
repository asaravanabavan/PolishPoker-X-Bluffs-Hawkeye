"""Unit tests for the Card model."""
import unittest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.card import Card, Rank, Suit, PowerType


class TestCardValues(unittest.TestCase):
    """Tests for card scoring values."""

    def test_joker_value_is_negative_two(self):
        """Joker should have value of -2 (best card)."""
        joker = Card(Rank.JOKER, Suit.NONE)
        self.assertEqual(joker.value, -2)

    def test_king_value_is_zero(self):
        """King should have value of 0."""
        king = Card(Rank.KING, Suit.SPADES)
        self.assertEqual(king.value, 0)

    def test_ace_value_is_one(self):
        """Ace should have value of 1."""
        ace = Card(Rank.ACE, Suit.HEARTS)
        self.assertEqual(ace.value, 1)

    def test_number_cards_have_face_value(self):
        """Number cards (2-10) should have face value."""
        self.assertEqual(Card(Rank.TWO, Suit.DIAMONDS).value, 2)
        self.assertEqual(Card(Rank.FIVE, Suit.CLUBS).value, 5)
        self.assertEqual(Card(Rank.TEN, Suit.SPADES).value, 10)

    def test_jack_value_is_ten(self):
        """Jack should have value of 10 (penalty card)."""
        jack = Card(Rank.JACK, Suit.HEARTS)
        self.assertEqual(jack.value, 10)

    def test_queen_value_is_ten(self):
        """Queen should have value of 10 (penalty card)."""
        queen = Card(Rank.QUEEN, Suit.DIAMONDS)
        self.assertEqual(queen.value, 10)


class TestPowerCards(unittest.TestCase):
    """Tests for power card detection."""

    def test_seven_is_power_card(self):
        """7 should be a PEEK power card."""
        card = Card(Rank.SEVEN, Suit.CLUBS)
        self.assertTrue(card.is_power_card)
        self.assertEqual(card.power_type, PowerType.PEEK)

    def test_eight_is_power_card(self):
        """8 should be a PEEK power card."""
        card = Card(Rank.EIGHT, Suit.HEARTS)
        self.assertTrue(card.is_power_card)
        self.assertEqual(card.power_type, PowerType.PEEK)

    def test_nine_is_spy_card(self):
        """9 should be a SPY power card."""
        card = Card(Rank.NINE, Suit.DIAMONDS)
        self.assertTrue(card.is_power_card)
        self.assertEqual(card.power_type, PowerType.SPY)

    def test_ten_is_spy_card(self):
        """10 should be a SPY power card."""
        card = Card(Rank.TEN, Suit.SPADES)
        self.assertTrue(card.is_power_card)
        self.assertEqual(card.power_type, PowerType.SPY)

    def test_jack_is_blind_swap_card(self):
        """Jack should be a BLIND_SWAP power card."""
        card = Card(Rank.JACK, Suit.CLUBS)
        self.assertTrue(card.is_power_card)
        self.assertEqual(card.power_type, PowerType.BLIND_SWAP)

    def test_queen_is_blind_swap_card(self):
        """Queen should be a BLIND_SWAP power card."""
        card = Card(Rank.QUEEN, Suit.HEARTS)
        self.assertTrue(card.is_power_card)
        self.assertEqual(card.power_type, PowerType.BLIND_SWAP)

    def test_king_is_not_power_card(self):
        """King should NOT be a power card."""
        card = Card(Rank.KING, Suit.SPADES)
        self.assertFalse(card.is_power_card)
        self.assertIsNone(card.power_type)

    def test_joker_is_not_power_card(self):
        """Joker should NOT be a power card."""
        card = Card(Rank.JOKER, Suit.NONE)
        self.assertFalse(card.is_power_card)
        self.assertIsNone(card.power_type)

    def test_ace_is_not_power_card(self):
        """Ace should NOT be a power card."""
        card = Card(Rank.ACE, Suit.HEARTS)
        self.assertFalse(card.is_power_card)


class TestCardBehavior(unittest.TestCase):
    """Tests for card behavior."""

    def test_card_starts_face_down(self):
        """Cards should start face down by default."""
        card = Card(Rank.ACE, Suit.HEARTS)
        self.assertFalse(card.face_up)

    def test_card_flip_toggles_face(self):
        """Flip should toggle face_up state."""
        card = Card(Rank.ACE, Suit.HEARTS)
        self.assertFalse(card.face_up)
        card.flip()
        self.assertTrue(card.face_up)
        card.flip()
        self.assertFalse(card.face_up)

    def test_card_equality(self):
        """Cards with same rank and suit should be equal."""
        card1 = Card(Rank.ACE, Suit.HEARTS)
        card2 = Card(Rank.ACE, Suit.HEARTS)
        self.assertEqual(card1, card2)

    def test_card_inequality(self):
        """Cards with different rank or suit should not be equal."""
        card1 = Card(Rank.ACE, Suit.HEARTS)
        card2 = Card(Rank.ACE, Suit.SPADES)
        card3 = Card(Rank.TWO, Suit.HEARTS)
        self.assertNotEqual(card1, card2)
        self.assertNotEqual(card1, card3)

    def test_card_string_representation(self):
        """Test string representation of cards."""
        self.assertEqual(str(Card(Rank.KING, Suit.SPADES)), "K♠")
        self.assertEqual(str(Card(Rank.ACE, Suit.HEARTS)), "A♥")
        self.assertEqual(str(Card(Rank.TEN, Suit.DIAMONDS)), "10♦")
        self.assertEqual(str(Card(Rank.JOKER, Suit.NONE)), "JKR")

    def test_create_joker_factory(self):
        """Test Joker factory method."""
        joker = Card.create_joker()
        self.assertEqual(joker.rank, Rank.JOKER)
        self.assertEqual(joker.suit, Suit.NONE)
        self.assertEqual(joker.value, -2)


class TestCardAsciiArt(unittest.TestCase):
    """Tests for card ASCII art rendering."""

    def test_card_ascii_has_correct_height(self):
        """ASCII art should have 7 lines (plus optional label)."""
        card = Card(Rank.KING, Suit.SPADES, face_up=True)
        art = card.to_ascii()
        self.assertEqual(len(art), 7)

    def test_face_down_card_shows_pattern(self):
        """Face-down cards should show the back pattern."""
        card = Card(Rank.KING, Suit.SPADES, face_up=False)
        art = card.to_ascii()
        # Should contain the pattern character
        self.assertIn("░", art[1])

    def test_face_up_card_shows_rank(self):
        """Face-up cards should show their rank."""
        card = Card(Rank.KING, Suit.SPADES, face_up=True)
        art = card.to_ascii()
        # Should contain K somewhere
        combined = "".join(art)
        self.assertIn("K", combined)


if __name__ == '__main__':
    unittest.main()
