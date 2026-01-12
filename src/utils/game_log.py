"""Game logging for replay and analysis."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class GameEvent:
    """Single game event."""
    turn: int
    player: str
    action: str
    details: dict = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def __str__(self) -> str:
        return f"Turn {self.turn} | {self.player}: {self.action}"


@dataclass
class BluffRecord:
    """Bluff attempt record."""
    turn: int
    player: str
    claimed_power: str
    actual_card: str
    was_challenged: bool
    bluff_succeeded: bool
    penalty_to: Optional[str] = None


@dataclass
class ChallengeRecord:
    """VAR challenge record."""
    turn: int
    challenger: str
    challenged_player: str
    claimed_power: str
    was_bluff: bool
    revealed_card: str
    penalty_to: str


class GameLog:
    """Tracks game events for replay analysis."""

    def __init__(self):
        self.events: list[GameEvent] = []
        self.bluff_attempts: list[BluffRecord] = []
        self.challenges: list[ChallengeRecord] = []
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None
        self.total_turns: int = 0

    def record_game_start(self) -> None:
        self.start_time = datetime.now()
        self.events.append(GameEvent(
            turn=0,
            player="System",
            action="Game Started",
            details={"timestamp": self.start_time.isoformat()}
        ))

    def record_game_end(self, winner: str, human_score: int, bot_score: int) -> None:
        self.end_time = datetime.now()
        self.events.append(GameEvent(
            turn=self.total_turns,
            player="System",
            action="Game Ended",
            details={
                "winner": winner,
                "human_score": human_score,
                "bot_score": bot_score,
                "timestamp": self.end_time.isoformat()
            }
        ))

    def record_draw(self, turn: int, player: str, source: str,
                    card: Optional['Card'] = None) -> None:
        """Record a draw action."""
        self.total_turns = max(self.total_turns, turn)
        self.events.append(GameEvent(
            turn=turn,
            player=player,
            action=f"Drew from {source}",
            details={"source": source, "card": str(card) if card else "hidden"}
        ))

    def record_swap(self, turn: int, player: str, position: 'GridPosition',
                    old_card: 'Card', new_card: 'Card') -> None:
        """Record a swap action."""
        self.events.append(GameEvent(
            turn=turn,
            player=player,
            action=f"Swapped position {position.display_number}",
            details={
                "position": position.name,
                "old_card": str(old_card),
                "new_card": str(new_card)
            }
        ))

    def record_discard(self, turn: int, player: str, card: 'Card') -> None:
        """Record a discard action."""
        self.events.append(GameEvent(
            turn=turn,
            player=player,
            action=f"Discarded {card}",
            details={"card": str(card)}
        ))

    def record_power_attempt(self, turn: int, player: str,
                             claimed_power: 'PowerType',
                             actual_card: 'Card',
                             is_bluff: bool) -> None:
        """Record a power play attempt."""
        self.events.append(GameEvent(
            turn=turn,
            player=player,
            action=f"Claimed {claimed_power.value.upper()} power",
            details={
                "claimed": claimed_power.value,
                "actual_card": str(actual_card),
                "is_bluff": is_bluff
            }
        ))

    def record_var_result(self, turn: int, challenger: str,
                          challenged_player: str, claimed_power: str,
                          was_challenged: bool, was_bluff: bool,
                          revealed_card: Optional['Card'] = None,
                          penalty_to: Optional[str] = None) -> None:
        """Record the result of a VAR challenge."""
        if was_challenged:
            self.challenges.append(ChallengeRecord(
                turn=turn,
                challenger=challenger,
                challenged_player=challenged_player,
                claimed_power=claimed_power,
                was_bluff=was_bluff,
                revealed_card=str(revealed_card) if revealed_card else "N/A",
                penalty_to=penalty_to or "None"
            ))

            result = "FOUL! Bluff detected" if was_bluff else "Decision stands"
            self.events.append(GameEvent(
                turn=turn,
                player="VAR",
                action=f"REVIEW: {result}",
                details={
                    "challenger": challenger,
                    "was_bluff": was_bluff,
                    "penalty_to": penalty_to
                }
            ))
        else:
            # no challenge - record if it was a successful bluff
            self.events.append(GameEvent(
                turn=turn,
                player="VAR",
                action="No challenge" + (" (Bluff succeeded!)" if was_bluff else ""),
                details={"was_bluff": was_bluff}
            ))

        # record bluff attempt if applicable
        if was_bluff or was_challenged:
            self.bluff_attempts.append(BluffRecord(
                turn=turn,
                player=challenged_player,
                claimed_power=claimed_power,
                actual_card=str(revealed_card) if revealed_card else "hidden",
                was_challenged=was_challenged,
                bluff_succeeded=was_bluff and not was_challenged,
                penalty_to=penalty_to
            ))

    def record_power_execute(self, turn: int, player: str,
                             power_type: str, target: str,
                             result: str) -> None:
        """Record execution of a power card ability."""
        self.events.append(GameEvent(
            turn=turn,
            player=player,
            action=f"Executed {power_type}",
            details={"power": power_type, "target": target, "result": result}
        ))

    def record_hawkeye_call(self, turn: int, player: str) -> None:
        """Record when a player calls Hawk-Eye to end the game."""
        self.events.append(GameEvent(
            turn=turn,
            player=player,
            action="Called HAWK-EYE! Final round begins.",
            details={}
        ))

    def get_duration(self) -> str:
        """Get formatted game duration."""
        if not self.end_time:
            self.end_time = datetime.now()

        duration = self.end_time - self.start_time
        minutes = int(duration.total_seconds() // 60)
        seconds = int(duration.total_seconds() % 60)
        return f"{minutes}m {seconds}s"

    def generate_report(self, human_name: str, human_grid_score: int,
                       human_penalty: int, bot_name: str,
                       bot_grid_score: int, bot_penalty: int,
                       winner_name: str) -> str:
        """
        Generate the end-of-game Match Report.

        Returns:
            Formatted ASCII match report string.
        """
        human_total = human_grid_score + human_penalty
        bot_total = bot_grid_score + bot_penalty

        lines = [
            "",
            "=" * 66,
            "                        MATCH REPORT                              ",
            "                      Polish Bluff Poker                          ",
            "=" * 66,
            f"  Date: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"  Total Turns: {self.total_turns}",
            f"  Duration: {self.get_duration()}",
            "=" * 66,
            "                       FINAL SCORES                               ",
            "-" * 66,
            f"  {'':^20} | {'':^20} | {'':^10}",
            f"  {human_name:^20} | {bot_name:^20} | {'Winner':^10}",
            "-" * 66,
            f"  Grid:  {human_grid_score:>3} pts       | Grid:  {bot_grid_score:>3} pts       |",
            f"  Penalty: {human_penalty:>2} pts      | Penalty: {bot_penalty:>2} pts      | {winner_name:^10}",
            f"  {'─' * 15}      | {'─' * 15}      |",
            f"  TOTAL: {human_total:>3} pts      | TOTAL: {bot_total:>3} pts      |",
            "=" * 66,
        ]

        # var incidents section
        if self.challenges or any(b.bluff_succeeded for b in self.bluff_attempts):
            lines.append("                       VAR INCIDENTS                               ")
            lines.append("-" * 66)

            # show all bluff attempts and challenges
            for bluff in self.bluff_attempts:
                lines.append(f"  Turn {bluff.turn}: {bluff.player} claimed "
                           f"{bluff.claimed_power.upper()}")
                if bluff.was_challenged:
                    if bluff.bluff_succeeded is False and bluff.penalty_to:
                        lines.append(f"           -> CHALLENGED")
                        lines.append(f"           -> VAR REVIEW: FOUL! +10 penalty to {bluff.penalty_to}")
                    else:
                        lines.append(f"           -> CHALLENGED (wrongly)")
                        lines.append(f"           -> VAR REVIEW: Decision stands. +10 penalty to {bluff.penalty_to}")
                else:
                    if bluff.bluff_succeeded:
                        lines.append(f"           -> NO CHALLENGE - Bluff succeeded!")
                    else:
                        lines.append(f"           -> NO CHALLENGE - Action proceeded")
                lines.append("")
        else:
            lines.append("                       VAR INCIDENTS                               ")
            lines.append("-" * 66)
            lines.append("  No VAR incidents this match.")
            lines.append("")

        lines.append("=" * 66)

        return "\n".join(lines)

    def get_turn_summary(self, turn: int) -> list[GameEvent]:
        """Get all events for a specific turn."""
        return [e for e in self.events if e.turn == turn]

    def __len__(self) -> int:
        """Return total number of logged events."""
        return len(self.events)
