"""Game state management."""
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class GamePhase(Enum):
    """Game turn cycle phases."""
    SETUP = auto()
    DRAW = auto()
    ACTION = auto()
    CHALLENGE = auto()
    END_TURN = auto()
    GAME_OVER = auto()


@dataclass
class GameState:
    """Current game state snapshot."""
    deck: 'Deck'
    human: 'Player'
    bot: 'Player'
    current_player: 'Player'
    phase: GamePhase = GamePhase.SETUP
    drawn_card: Optional['Card'] = None
    drew_from_discard: bool = False
    turn_number: int = 0
    final_round: bool = False
    who_called_hawkeye: Optional['Player'] = None
    pending_power_claim: Optional[str] = None

    def get_opponent(self, player: 'Player') -> 'Player':
        return self.bot if player == self.human else self.human

    def is_human_turn(self) -> bool:
        return self.current_player == self.human

    def is_game_over(self) -> bool:
        """Check if the game has ended."""
        return self.phase == GamePhase.GAME_OVER

    def can_draw_from_discard(self) -> bool:
        """Check if drawing from discard is allowed."""
        return self.deck.top_discard is not None

    def can_discard(self) -> bool:
        """Check if discarding the drawn card is allowed."""
        # Can only discard if drew from deck (not discard pile)
        return self.drawn_card is not None and not self.drew_from_discard

    def snapshot(self) -> dict:
        """
        Create a dictionary snapshot for logging.

        Returns:
            Dict with current game state information.
        """
        return {
            "turn": self.turn_number,
            "phase": self.phase.name,
            "current_player": self.current_player.name,
            "deck_remaining": self.deck.cards_remaining,
            "human_score": self.human.total_score,
            "human_penalty": self.human.penalty_points,
            "bot_score": self.bot.total_score,
            "bot_penalty": self.bot.penalty_points,
            "final_round": self.final_round,
            "drawn_card": str(self.drawn_card) if self.drawn_card else None,
        }

    def get_winner(self) -> Optional['Player']:
        """
        Determine the winner (lowest score wins).

        Returns:
            The winning player, or None if game not over.
        """
        if not self.is_game_over():
            return None

        if self.human.total_score < self.bot.total_score:
            return self.human
        elif self.bot.total_score < self.human.total_score:
            return self.bot
        else:
            # Tie goes to the player who called Hawk-Eye
            return self.who_called_hawkeye

    def __repr__(self) -> str:
        """Return string representation."""
        return (f"GameState(turn={self.turn_number}, phase={self.phase.name}, "
                f"current={self.current_player.name})")
