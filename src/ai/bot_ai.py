
import random
from dataclasses import dataclass
from typing import Optional, TYPE_CHECKING

from ..models import Card, GridPosition, PowerType, Rank
from .memory import BotMemory
from .heuristics import ChallengeHeuristics, SwapHeuristics, BluffHeuristics

if TYPE_CHECKING:
    from ..engine.actions import ChallengeContext


@dataclass
class BotDecision:
    """Container for bot's action decision."""
    action: str  # "swap", "discard", "power", "hawkeye"
    target_position: Optional[GridPosition] = None
    opponent_position: Optional[GridPosition] = None
    claimed_power: Optional[PowerType] = None
    is_bluff: bool = False
    reasoning: str = ""


class BotAI:
    """
    The Polish Bluff Poker AI decision engine.

    Decision Priority Order:
    1. Draw Decision:
       - Take discard if value <= worst known card
       - Take discard if King (0) or Joker (-2)
       - Otherwise draw from deck

    2. Action Decision:
       - SWAP if drawn card improves a known position
       - SWAP with unknown if drawn is excellent (Joker/King/Ace)
       - USE POWER if beneficial
       - Consider BLUFF if card is high-value
       - DISCARD as fallback

    3. Challenge Decision:
       - Calculate probability from heuristics
       - Apply situational factors
       - Random threshold check
    """

    def __init__(self):
        """Initialize the bot AI."""
        self.memory = BotMemory()
        self.risk_tolerance = 0.3
        self.bluff_frequency = 0.15

    def initialize_memory(self, bottom_cards: list[tuple[GridPosition, Card]]) -> None:
        """
        Initialize memory with the bottom two cards (peeked at start).
        """
        for pos, card in bottom_cards:
            self.memory.remember_own_card(pos, card)

    def update_seen_card(self, card: Card) -> None:
        """Record a card that was seen (in discard or revealed)."""
        self.memory.update_seen(card)

    def remember_own_swap(self, pos: GridPosition, card: Card) -> None:
        """Remember a card swapped into bot's grid."""
        self.memory.remember_own_card(pos, card)

    def remember_opponent_card(self, pos: GridPosition, card: Card) -> None:
        """Remember a card seen in opponent's grid."""
        self.memory.remember_opponent_card(pos, card)

    def forget_after_blind_swap(
        self,
        own_pos: GridPosition,
        opponent_pos: GridPosition
    ) -> None:
        """Forget positions after a blind swap."""
        self.memory.forget_own_position(own_pos)
        self.memory.forget_opponent_position(opponent_pos)

    # draw decision


    def decide_draw_source(self, top_discard: Optional[Card]) -> str:
        """
        Decide whether to draw from deck or discard pile.

        Args:
            top_discard: The top card of the discard pile (None if empty).

        Returns:
            "deck" or "discard"
        """
        if top_discard is None:
            return "deck"

        discard_value = top_discard.value

        # always take Joker or King from discard
        if discard_value <= 0:
            return "discard"

        # Take if better than our worst known card
        worst = self.memory.find_worst_own_known()
        if worst:
            worst_pos, worst_card = worst
            if discard_value < worst_card.value:
                return "discard"

        # Take if good card (Ace, 2, 3) and we have unknown positions
        if discard_value <= 3 and self.memory.get_own_unknown_positions():
            return "discard"

        return "deck"

    def decide_action(
        self,
        drawn_card: Card,
        can_discard: bool,
        turn_number: int,
        opponent_penalty: int
    ) -> BotDecision:
        """Decide what to do with drawn card."""
        drawn_value = drawn_card.value

        # Priority 1: Swap if card improves a known position
        worst = self.memory.find_worst_own_known()
        if worst:
            worst_pos, worst_card = worst
            if drawn_value < worst_card.value:
                return BotDecision(
                    action="swap",
                    target_position=worst_pos,
                    reasoning=f"Swapping {drawn_card} for {worst_card} at position {worst_pos.display_number}"
                )

        # priority 2: swap with unknown if drawn is excellent
        unknown_positions = self.memory.get_own_unknown_positions()
        if drawn_value <= 1 and unknown_positions:  # Joker, King, or Ace
            target = random.choice(unknown_positions)
            return BotDecision(
                action="swap",
                target_position=target,
                reasoning=f"Excellent card {drawn_card}, swapping with unknown position {target.display_number}"
            )

        # Priority 3: Use actual power if card is a power card
        if drawn_card.is_power_card:
            power = drawn_card.power_type
            power_decision = self._decide_power_use(power, drawn_card)
            if power_decision:
                return power_decision

        # priority 4: consider bluffing with high-value cards
        if drawn_value >= 10:  # J or Q
            own_score = self.memory.estimate_own_score()
            opponent_score = self.memory.estimate_opponent_score()

            if BluffHeuristics.should_bluff(
                drawn_value, PowerType.PEEK, own_score, opponent_score,
                turn_number, 0  # Bot's own penalty
            ):
                bluff_power = BluffHeuristics.choose_bluff_power(drawn_value)
                bluff_decision = self._create_bluff_decision(bluff_power, drawn_card)
                if bluff_decision:
                    return bluff_decision

        # Priority 5: Swap with unknown position for medium cards
        if unknown_positions and drawn_value <= 6:
            target = random.choice(unknown_positions)
            return BotDecision(
                action="swap",
                target_position=target,
                reasoning=f"Medium card {drawn_card}, trying unknown position {target.display_number}"
            )

        # priority 6: discard if possible
        if can_discard:
            return BotDecision(
                action="discard",
                reasoning=f"Discarding {drawn_card} (no good swap available)"
            )

        # Fallback: Swap with random position
        all_positions = list(GridPosition.all_positions())
        target = random.choice(all_positions)
        return BotDecision(
            action="swap",
            target_position=target,
            reasoning=f"Forced swap of {drawn_card} to position {target.display_number}"
        )

    def _decide_power_use(
        self,
        power: PowerType,
        card: Card
    ) -> Optional[BotDecision]:
        match power:
            case PowerType.PEEK:
                # use if we have unknown cards
                unknown = self.memory.get_own_unknown_positions()
                if unknown:
                    target = random.choice(unknown)
                    return BotDecision(
                        action="power",
                        claimed_power=PowerType.PEEK,
                        target_position=target,
                        is_bluff=False,
                        reasoning=f"Using PEEK on position {target.display_number}"
                    )

            case PowerType.SPY:
                # use if opponent has unknown cards
                opp_unknown = self.memory.get_opponent_unknown_positions()
                if opp_unknown:
                    target = random.choice(opp_unknown)
                    return BotDecision(
                        action="power",
                        claimed_power=PowerType.SPY,
                        target_position=target,
                        is_bluff=False,
                        reasoning=f"Using SPY on opponent's position {target.display_number}"
                    )

            case PowerType.BLIND_SWAP:
                # Use if we have a bad known card and opponent might have better
                worst = self.memory.find_worst_own_known()
                if worst:
                    worst_pos, worst_card = worst
                    if worst_card.value >= 8:  # Our card is bad
                        opp_unknown = self.memory.get_opponent_unknown_positions()
                        if opp_unknown:
                            opp_target = random.choice(opp_unknown)
                            return BotDecision(
                                action="power",
                                claimed_power=PowerType.BLIND_SWAP,
                                target_position=worst_pos,
                                opponent_position=opp_target,
                                is_bluff=False,
                                reasoning=f"BLIND SWAP: our bad card at {worst_pos.display_number}"
                            )

        return None

    def _create_bluff_decision(
        self,
        claimed_power: PowerType,
        actual_card: Card
    ) -> Optional[BotDecision]:
        match claimed_power:
            case PowerType.PEEK:
                unknown = self.memory.get_own_unknown_positions()
                if unknown:
                    return BotDecision(
                        action="power",
                        claimed_power=claimed_power,
                        target_position=random.choice(unknown),
                        is_bluff=True,
                        reasoning=f"BLUFF: Claiming PEEK with {actual_card}"
                    )

            case PowerType.SPY:
                opp_unknown = self.memory.get_opponent_unknown_positions()
                if opp_unknown:
                    return BotDecision(
                        action="power",
                        claimed_power=claimed_power,
                        target_position=random.choice(opp_unknown),
                        is_bluff=True,
                        reasoning=f"BLUFF: Claiming SPY with {actual_card}"
                    )

            case PowerType.BLIND_SWAP:
                own_positions = list(GridPosition.all_positions())
                opp_unknown = self.memory.get_opponent_unknown_positions()
                if opp_unknown:
                    return BotDecision(
                        action="power",
                        claimed_power=claimed_power,
                        target_position=random.choice(own_positions),
                        opponent_position=random.choice(opp_unknown),
                        is_bluff=True,
                        reasoning=f"BLUFF: Claiming BLIND SWAP with {actual_card}"
                    )

        return None

    def decide_challenge(self, context: 'ChallengeContext') -> bool:
        """Decide whether to challenge a power claim."""
        # calculate challenge probability
        own_score = self.memory.estimate_own_score()
        opponent_score = self.memory.estimate_opponent_score()
        claimant_winning = opponent_score < own_score

        probability = ChallengeHeuristics.calculate_challenge_probability(
            claimed_power=context.claimed_power,
            memory=self.memory,
            turn_number=context.turn_number,
            claimant_penalty=context.claimant_penalty_points,
            challenger_penalty=context.challenger_penalty_points,
            claimant_is_winning=claimant_winning
        )

        # add some randomness based on risk tolerance
        adjusted_prob = probability * (1 + self.risk_tolerance)

        # make the decision
        return random.random() < adjusted_prob

    def should_call_hawkeye(self, turn_number: int) -> bool:
        """Decide whether to call Hawk-Eye to end game."""
        # don't end too early
        if turn_number < 6:
            return False

        # Need to know most of our cards
        if self.memory.count_own_known() < 3:
            return False

        own_score = self.memory.estimate_own_score()
        opponent_score = self.memory.estimate_opponent_score()

        # Only call if we have a good score
        if own_score > 4:
            return False

        # Only call if we're winning by significant margin
        if own_score < opponent_score - 5:
            return True

        return False

    def get_status(self) -> str:
        own_known = self.memory.count_own_known()
        own_score = self.memory.estimate_own_score()
        return f"Known: {own_known}/4, Est. Score: {own_score:.1f}"
