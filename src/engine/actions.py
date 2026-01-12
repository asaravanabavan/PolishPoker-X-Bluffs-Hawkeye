"""Action types and result structures."""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class ActionType(Enum):
    """Player action types."""
    DRAW_DECK = auto()      # Draw from the deck
    DRAW_DISCARD = auto()   # Draw from discard pile
    SWAP = auto()           # Swap drawn card with grid card
    DISCARD = auto()        # Discard the drawn card
    POWER_PLAY = auto()     # Use (or claim to use) a power card
    CALL_HAWKEYE = auto()   # End the game (call Hawk-Eye)
    CHALLENGE = auto()      # Challenge a claimed power play


@dataclass
class Action:
    """Represents a player action with optional parameters."""
    action_type: ActionType
    target_position: Optional['GridPosition'] = None
    claimed_power: Optional['PowerType'] = None
    opponent_position: Optional['GridPosition'] = None  # For blind swap

    def __str__(self) -> str:
        match self.action_type:
            case ActionType.DRAW_DECK:
                return "Draw from deck"
            case ActionType.DRAW_DISCARD:
                return "Draw from discard pile"
            case ActionType.SWAP:
                pos = self.target_position.display_number if self.target_position else "?"
                return f"Swap with position {pos}"
            case ActionType.DISCARD:
                return "Discard drawn card"
            case ActionType.POWER_PLAY:
                power = self.claimed_power.value if self.claimed_power else "?"
                return f"Power Play: {power}"
            case ActionType.CALL_HAWKEYE:
                return "Call Hawk-Eye! (End game)"
            case ActionType.CHALLENGE:
                return "Challenge (Call VAR)"
            case _:
                return f"Unknown action: {self.action_type}"


@dataclass
class PowerPlayResult:
    """Result of a power play attempt."""
    success: bool
    message: str
    revealed_card: Optional['Card'] = None
    was_bluff: bool = False
    was_challenged: bool = False
    penalty_applied_to: Optional['Player'] = None

    def __str__(self) -> str:
        return self.message


@dataclass
class ChallengeContext:
    """Context information for making a challenge decision."""
    claimed_power: 'PowerType'
    claimant_name: str
    turn_number: int
    claimant_penalty_points: int
    challenger_penalty_points: int
    claimant_known_score: Optional[int] = None
    cards_in_discard: int = 0
    power_cards_seen: dict = field(default_factory=dict)


@dataclass
class SwapTarget:
    """Target positions for a blind swap action."""
    own_position: 'GridPosition'
    opponent_position: 'GridPosition'


@dataclass
class TurnResult:
    """Summary of a completed turn."""
    player_name: str
    turn_number: int
    draw_source: str  # "deck" or "discard"
    action_taken: ActionType
    action_details: str
    var_incident: Optional[str] = None  # Description of any VAR challenge

    def __str__(self) -> str:
        result = f"Turn {self.turn_number} ({self.player_name}): {self.action_details}"
        if self.var_incident:
            result += f" | VAR: {self.var_incident}"
        return result


class DrawSource(Enum):
    """Where a card was drawn from."""
    DECK = "deck"
    DISCARD = "discard"
