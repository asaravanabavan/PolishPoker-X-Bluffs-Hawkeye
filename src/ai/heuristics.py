"""Heuristics for bot decision making."""
from ..models import PowerType, Rank
from .memory import BotMemory


class ChallengeHeuristics:
    """Calculate challenge probabilities based on game state."""

    # base challenge probabilities by power type
    BASE_PROBABILITIES = {
        PowerType.PEEK: 0.05,       # 7/8 are common, rarely bluffed
        PowerType.SPY: 0.15,        # 9/10 somewhat valuable
        PowerType.BLIND_SWAP: 0.30, # J/Q are high-value to discard
    }

    # Power card ranks for counting
    PEEK_RANKS = [Rank.SEVEN, Rank.EIGHT]
    SPY_RANKS = [Rank.NINE, Rank.TEN]
    SWAP_RANKS = [Rank.JACK, Rank.QUEEN]

    @classmethod
    def calculate_challenge_probability(
        cls,
        claimed_power: PowerType,
        memory: BotMemory,
        turn_number: int,
        claimant_penalty: int,
        challenger_penalty: int,
        claimant_is_winning: bool = False
    ) -> float:
        """Calculate probability bot should challenge a claim.
        
        Returns:
            Probability from 0.0 to 1.0.
        """
        # Start with base probability
        prob = cls.BASE_PROBABILITIES.get(claimed_power, 0.2)

        # adjust for cards seen
        prob += cls._adjust_for_cards_seen(claimed_power, memory)

        # adjust for game phase (more suspicious late game)
        if turn_number > 10:
            prob += 0.10

        # adjust for claimant's desperation
        if claimant_penalty > 0:
            prob += 0.15  # Already caught bluffing once, might do it again

        # Adjust if we're behind (more willing to take risks)
        if challenger_penalty > claimant_penalty:
            prob += 0.10

        # Adjust if claimant is winning (less reason to bluff)
        if claimant_is_winning:
            prob -= 0.10

        # clamp to valid range
        return max(0.0, min(1.0, prob))

    @classmethod
    def _adjust_for_cards_seen(
        cls,
        claimed_power: PowerType,
        memory: BotMemory
    ) -> float:
        """
        Adjust probability based on how many power cards have been seen.

        If many of a power card type are already seen, less likely
        opponent has one, so more likely they're bluffing.
        """
        adjustment = 0.0

        match claimed_power:
            case PowerType.PEEK:
                seen = memory.count_power_cards_seen(cls.PEEK_RANKS)
                # 8 total peek cards (4 sevens + 4 eights)
                if seen >= 6:
                    adjustment = 0.40  # Only 2 left, very suspicious
                elif seen >= 4:
                    adjustment = 0.20
                elif seen >= 2:
                    adjustment = 0.10

            case PowerType.SPY:
                seen = memory.count_power_cards_seen(cls.SPY_RANKS)
                if seen >= 6:
                    adjustment = 0.40
                elif seen >= 4:
                    adjustment = 0.20
                elif seen >= 2:
                    adjustment = 0.10

            case PowerType.BLIND_SWAP:
                seen = memory.count_power_cards_seen(cls.SWAP_RANKS)
                if seen >= 6:
                    adjustment = 0.40
                elif seen >= 4:
                    adjustment = 0.20
                elif seen >= 2:
                    adjustment = 0.10

        return adjustment


class SwapHeuristics:
    """Heuristics for evaluating swap decisions."""

    # Thresholds for card quality
    EXCELLENT_THRESHOLD = 1   # Joker (-2), King (0), Ace (1)
    GOOD_THRESHOLD = 4        # 2, 3, 4
    BAD_THRESHOLD = 8         # 8, 9, 10, J, Q

    @classmethod
    def should_swap(
        cls,
        drawn_value: int,
        known_worst_value: int | None,
        has_unknown_positions: bool
    ) -> bool:
        """
        Determine if bot should swap the drawn card.

        Args:
            drawn_value: Value of the drawn card.
            known_worst_value: Value of worst known card (None if none known).
            has_unknown_positions: Whether there are unknown positions.

        Returns:
            True if swap is recommended.
        """
        # Excellent cards (Joker, King, Ace) - always swap somewhere
        if drawn_value <= cls.EXCELLENT_THRESHOLD:
            return True

        # good cards - swap if we have worse known cards
        if drawn_value <= cls.GOOD_THRESHOLD:
            if known_worst_value and known_worst_value > drawn_value:
                return True
            # also swap if we have unknowns and card is good
            if has_unknown_positions:
                return True

        # medium cards - only swap if definitely improving
        if known_worst_value and known_worst_value > drawn_value + 2:
            return True

        return False

    @classmethod
    def evaluate_swap_value(
        cls,
        drawn_value: int,
        target_known_value: int | None,
        expected_unknown: float
    ) -> float:
        """
        Calculate the expected improvement from a swap.

        Args:
            drawn_value: Value of drawn card.
            target_known_value: Value at target position (None if unknown).
            expected_unknown: Expected value of unknown cards.

        Returns:
            Expected point improvement (positive = good swap).
        """
        if target_known_value is not None:
            # known target: exact calculation
            return target_known_value - drawn_value
        else:
            # unknown target: probabilistic
            return expected_unknown - drawn_value


class BluffHeuristics:
    """Heuristics for when to attempt bluffs."""

    # Base bluff frequency (how often bot considers bluffing)
    BASE_BLUFF_FREQUENCY = 0.15

    @classmethod
    def should_bluff(
        cls,
        card_value: int,
        desired_power: PowerType,
        own_score: float,
        opponent_score: float,
        turn_number: int,
        own_penalty: int
    ) -> bool:
        """
        Determine if bot should attempt a bluff.

        Args:
            card_value: Value of the card to bluff with.
            desired_power: Power type to claim.
            own_score: Bot's estimated score.
            opponent_score: Opponent's estimated score.
            turn_number: Current turn.
            own_penalty: Bot's current penalty points.

        Returns:
            True if bluff is recommended.
        """
        import random

        # never bluff if already have penalties (too risky)
        if own_penalty >= 10:
            return False

        # Only bluff with high-value cards (J, Q) - want to discard them
        if card_value < 10:
            return False

        # more likely to bluff if losing
        if own_score > opponent_score + 5:
            if random.random() < cls.BASE_BLUFF_FREQUENCY * 2:
                return True

        # Standard bluff frequency
        return random.random() < cls.BASE_BLUFF_FREQUENCY

    @classmethod
    def choose_bluff_power(cls, card_value: int) -> PowerType:
        """
        Choose which power to claim when bluffing.

        Lower-value powers are safer to claim (less likely challenged).
        """
        import random

        # PEEK is safest (least challenged)
        # SPY is medium
        # BLIND_SWAP is risky but high reward

        weights = {
            PowerType.PEEK: 0.60,      # Most common claim
            PowerType.SPY: 0.30,
            PowerType.BLIND_SWAP: 0.10,
        }

        # if card is J/Q, more likely to claim BLIND_SWAP (matching power)
        if card_value == 10:
            weights[PowerType.BLIND_SWAP] = 0.40
            weights[PowerType.PEEK] = 0.40
            weights[PowerType.SPY] = 0.20

        # Weighted random choice
        r = random.random()
        cumulative = 0.0
        for power, weight in weights.items():
            cumulative += weight
            if r < cumulative:
                return power

        return PowerType.PEEK  # Fallback
