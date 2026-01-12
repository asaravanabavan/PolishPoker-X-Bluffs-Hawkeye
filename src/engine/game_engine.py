
from typing import Optional, Callable, TYPE_CHECKING

from ..models import Card, Deck, Player, GridPosition, PowerType
from ..utils import GameLog
from .game_state import GameState, GamePhase
from .actions import (
    Action, ActionType, PowerPlayResult, ChallengeContext,
    SwapTarget, TurnResult, DrawSource
)

if TYPE_CHECKING:
    from ..ai.bot_ai import BotAI


class GameEngine:
    """
    The core game logic engine.

    Manages:
    - Game setup and state transitions
    - Turn flow (draw -> action -> challenge -> end)
    - VAR challenge resolution
    - Win condition checking
    """

    PENALTY_POINTS = 10  # Points for failed bluff/wrong challenge

    def __init__(self):
        """Initialize a new game engine."""
        self._deck = Deck()
        self._human = Player("Player", is_human=True)
        self._bot = Player("PBP AI", is_human=False)
        self._game_log = GameLog()

        self._state = GameState(
            deck=self._deck,
            human=self._human,
            bot=self._bot,
            current_player=self._human,
            phase=GamePhase.SETUP
        )

        # callback for bot AI decisions (set by CLI)
        self._bot_ai: Optional['BotAI'] = None

    @property
    def state(self):
        return self._state

    @property
    def game_log(self):
        return self._game_log

    def set_bot_ai(self, bot_ai: 'BotAI') -> None:
        self._bot_ai = bot_ai

    def setup_game(self) -> tuple[list[tuple[GridPosition, Card]],
                                   list[tuple[GridPosition, Card]]]:
        """Deal cards and peek bottom rows."""
        self._game_log.record_game_start()

        # Deal 4 cards to each player
        human_cards = self._deck.deal(4)
        bot_cards = self._deck.deal(4)

        self._human.setup_grid(human_cards)
        self._bot.setup_grid(bot_cards)

        # Each player peeks at their bottom 2 cards
        human_peeked = self._human.peek_initial()
        bot_peeked = self._bot.peek_initial()

        # Place first card in discard pile
        first_discard = self._deck.draw()
        first_discard.face_up = True
        self._deck.discard(first_discard)

        # Set initial state
        self._state.phase = GamePhase.DRAW
        self._state.turn_number = 1
        self._state.current_player = self._human

        return human_peeked, bot_peeked

    def get_valid_actions(self) -> list[Action]:
        actions = []

        match self._state.phase:
            case GamePhase.DRAW:
                actions.append(Action(ActionType.DRAW_DECK))
                if self._state.can_draw_from_discard():
                    actions.append(Action(ActionType.DRAW_DISCARD))

            case GamePhase.ACTION:
                # Swap with any grid position
                for pos in GridPosition.all_positions():
                    actions.append(Action(ActionType.SWAP, target_position=pos))

                # Discard (only if drew from deck)
                if self._state.can_discard():
                    actions.append(Action(ActionType.DISCARD))

                # Power plays (can claim any power, even if bluffing)
                for power in PowerType:
                    actions.append(Action(ActionType.POWER_PLAY, claimed_power=power))

                # Call Hawk-Eye (end game)
                actions.append(Action(ActionType.CALL_HAWKEYE))

            case GamePhase.CHALLENGE:
                actions.append(Action(ActionType.CHALLENGE))
                # Not challenging is implicit (any other action)

        return actions

    def draw_from_deck(self) -> Card:
        """Draw from deck."""
        card = self._deck.draw()
        self._state.drawn_card = card
        self._state.drew_from_discard = False
        self._state.phase = GamePhase.ACTION

        self._game_log.record_draw(
            self._state.turn_number,
            self._state.current_player.name,
            "deck"
        )

        return card

    def draw_from_discard(self) -> Card:
        """Draw from discard pile."""
        card = self._deck.draw_from_discard()
        card.face_up = True
        self._state.drawn_card = card
        self._state.drew_from_discard = True
        self._state.phase = GamePhase.ACTION

        self._game_log.record_draw(
            self._state.turn_number,
            self._state.current_player.name,
            "discard",
            card
        )

        return card

    def swap_with_grid(self, pos: GridPosition) -> Card:
        """Swap drawn card with grid card at position."""
        if not self._state.drawn_card:
            raise RuntimeError("No drawn card to swap")

        new_card = self._state.drawn_card
        new_card.face_up = True
        old_card = self._state.current_player.swap_card(pos, new_card)

        # old card goes to discard
        old_card.face_up = True
        self._deck.discard(old_card)

        self._game_log.record_swap(
            self._state.turn_number,
            self._state.current_player.name,
            pos, old_card, new_card
        )

        self._state.drawn_card = None
        self._end_action_phase()

        return old_card

    def discard_drawn(self) -> None:
        """Discard the drawn card without using it."""
        if not self._state.drawn_card:
            raise RuntimeError("No drawn card to discard")

        if not self._state.can_discard():
            raise RuntimeError("Cannot discard: drew from discard pile")

        card = self._state.drawn_card
        card.face_up = True
        self._deck.discard(card)

        self._game_log.record_discard(
            self._state.turn_number,
            self._state.current_player.name,
            card
        )

        self._state.drawn_card = None
        self._end_action_phase()

    def attempt_power_play(
        self,
        claimed_power: PowerType,
        target: Optional[GridPosition] = None,
        opponent_target: Optional[GridPosition] = None,
        challenge_callback: Optional[Callable[[ChallengeContext], bool]] = None
    ) -> PowerPlayResult:
        """Attempt a power play (may be a bluff). Opponent can challenge."""
        if not self._state.drawn_card:
            raise RuntimeError("No drawn card to play")

        drawn_card = self._state.drawn_card
        actual_power = drawn_card.power_type
        is_bluff = (actual_power != claimed_power)

        # Log the attempt
        self._game_log.record_power_attempt(
            self._state.turn_number,
            self._state.current_player.name,
            claimed_power,
            drawn_card,
            is_bluff
        )

        # Card goes face-down to discard
        drawn_card.face_up = False
        self._deck.discard(drawn_card)
        self._state.drawn_card = None

        # create challenge context
        opponent = self._get_opponent()
        context = ChallengeContext(
            claimed_power=claimed_power,
            claimant_name=self._state.current_player.name,
            turn_number=self._state.turn_number,
            claimant_penalty_points=self._state.current_player.penalty_points,
            challenger_penalty_points=opponent.penalty_points,
            cards_in_discard=self._deck.discard_count
        )

        # determine if opponent challenges
        challenges = False
        if challenge_callback:
            challenges = challenge_callback(context)
        elif self._bot_ai and opponent == self._bot:
            challenges = self._bot_ai.decide_challenge(context)

        # Resolve the challenge
        result = self._resolve_var_challenge(
            is_bluff=is_bluff,
            challenger_challenges=challenges,
            claimed_power=claimed_power,
            target=target,
            opponent_target=opponent_target,
            drawn_card=drawn_card
        )

        self._end_action_phase()
        return result

    def _resolve_var_challenge(
        self,
        is_bluff: bool,
        challenger_challenges: bool,
        claimed_power: PowerType,
        target: Optional[GridPosition],
        opponent_target: Optional[GridPosition],
        drawn_card: Card
    ) -> PowerPlayResult:
        """
        Resolve a VAR challenge.

        Truth Table:
        | Was Bluff | Challenged |        Result               |
        |-----------|------------|------------------------------|
        |   False   |   False    | Power executes normally      |
        |   False   |   True     | Challenger +10, power OK     |
        |   True    |   False    | Power executes (free bluff!) |
        |   True    |   True     | Bluffer +10, power DENIED    |
        """
        current = self._state.current_player
        opponent = self._get_opponent()

        if not challenger_challenges:
            # NO CHALLENGE: Action proceeds regardless of truth
            self._game_log.record_var_result(
                turn=self._state.turn_number,
                challenger=opponent.name,
                challenged_player=current.name,
                claimed_power=claimed_power.value,
                was_challenged=False,
                was_bluff=is_bluff,
                revealed_card=None,
                penalty_to=None
            )
            return self._execute_power(claimed_power, target, opponent_target)

        else:
            # CHALLENGED: Reveal the card
            drawn_card.face_up = True

            if is_bluff:
                # CAUGHT! Bluffer penalized, action cancelled
                current.add_penalty(self.PENALTY_POINTS)
                self._game_log.record_var_result(
                    turn=self._state.turn_number,
                    challenger=opponent.name,
                    challenged_player=current.name,
                    claimed_power=claimed_power.value,
                    was_challenged=True,
                    was_bluff=True,
                    revealed_card=drawn_card,
                    penalty_to=current.name
                )
                return PowerPlayResult(
                    success=False,
                    message=f"VAR REVIEW: FOUL! Bluff detected with {drawn_card}. +10 penalty.",
                    revealed_card=drawn_card,
                    was_bluff=True,
                    was_challenged=True,
                    penalty_applied_to=current
                )

            else:
                # WRONGFUL CHALLENGE: Challenger penalized, action proceeds
                opponent.add_penalty(self.PENALTY_POINTS)
                self._game_log.record_var_result(
                    turn=self._state.turn_number,
                    challenger=opponent.name,
                    challenged_player=current.name,
                    claimed_power=claimed_power.value,
                    was_challenged=True,
                    was_bluff=False,
                    revealed_card=drawn_card,
                    penalty_to=opponent.name
                )
                result = self._execute_power(claimed_power, target, opponent_target)
                result.message = (f"VAR REVIEW: Decision stands! Card was {drawn_card}. "
                                f"Challenger +10. {result.message}")
                result.was_challenged = True
                result.penalty_applied_to = opponent
                return result

    def _execute_power(
        self,
        power_type: PowerType,
        target: Optional[GridPosition],
        opponent_target: Optional[GridPosition]
    ) -> PowerPlayResult:
        """Execute the actual power card ability."""
        current = self._state.current_player
        opponent = self._get_opponent()

        match power_type:
            case PowerType.PEEK:
                if target is None:
                    return PowerPlayResult(False, "No target specified for PEEK")
                card = current.get_card(target)
                if card:
                    current.mark_known(target)
                    self._game_log.record_power_execute(
                        self._state.turn_number,
                        current.name,
                        "PEEK",
                        f"position {target.display_number}",
                        str(card)
                    )
                    return PowerPlayResult(
                        success=True,
                        message=f"PEEK: Your position {target.display_number} is {card}",
                        revealed_card=card
                    )
                return PowerPlayResult(False, "No card at that position")

            case PowerType.SPY:
                if target is None:
                    return PowerPlayResult(False, "No target specified for SPY")
                card = opponent.get_card(target)
                if card:
                    self._game_log.record_power_execute(
                        self._state.turn_number,
                        current.name,
                        "SPY",
                        f"opponent position {target.display_number}",
                        str(card)
                    )
                    return PowerPlayResult(
                        success=True,
                        message=f"SPY: Opponent's position {target.display_number} is {card}",
                        revealed_card=card
                    )
                return PowerPlayResult(False, "No card at that position")

            case PowerType.BLIND_SWAP:
                if target is None or opponent_target is None:
                    return PowerPlayResult(False, "Need both positions for BLIND SWAP")

                # perform the swap
                my_card = current.get_card(target)
                opp_card = opponent.get_card(opponent_target)

                if my_card and opp_card:
                    current.swap_card(target, opp_card)
                    opponent.swap_card(opponent_target, my_card)

                    # neither player knows what they now have
                    current.mark_unknown(target)
                    opponent.mark_unknown(opponent_target)

                    # Make cards face-down since neither knows
                    current.get_card(target).face_up = False
                    opponent.get_card(opponent_target).face_up = False

                    self._game_log.record_power_execute(
                        self._state.turn_number,
                        current.name,
                        "BLIND SWAP",
                        f"pos {target.display_number} <-> opp pos {opponent_target.display_number}",
                        "Cards exchanged blindly"
                    )
                    return PowerPlayResult(
                        success=True,
                        message=(f"BLIND SWAP: Exchanged your position {target.display_number} "
                                f"with opponent's position {opponent_target.display_number}")
                    )
                return PowerPlayResult(False, "Invalid positions for swap")

            case _:
                return PowerPlayResult(False, f"Unknown power type: {power_type}")

    def call_hawkeye(self) -> None:
        """Call Hawk-Eye to trigger final round."""
        self._state.final_round = True
        self._state.who_called_hawkeye = self._state.current_player

        self._game_log.record_hawkeye_call(
            self._state.turn_number,
            self._state.current_player.name
        )

        # discard the drawn card
        if self._state.drawn_card:
            self._state.drawn_card.face_up = True
            self._deck.discard(self._state.drawn_card)
            self._state.drawn_card = None

        self._end_action_phase()

    def _end_action_phase(self) -> None:
        """Transition from action phase to end turn."""
        self._state.phase = GamePhase.END_TURN

    def end_turn(self) -> bool:
        """
        End the current turn and prepare for the next.

        Returns:
            True if game continues, False if game is over.
        """
        # check if game should end
        if self._check_game_over():
            self._finalize_game()
            return False

        # switch players
        if self._state.current_player == self._human:
            self._state.current_player = self._bot
        else:
            self._state.current_player = self._human
            self._state.turn_number += 1

        # reset for next turn
        self._state.phase = GamePhase.DRAW
        self._state.drawn_card = None
        self._state.drew_from_discard = False

        return True

    def _check_game_over(self) -> bool:
        """Check if the game should end."""
        if not self._state.final_round:
            return False

        # Game ends when we return to the player who called Hawk-Eye
        # (everyone has had one more turn)
        next_player = (self._bot if self._state.current_player == self._human
                      else self._human)
        return next_player == self._state.who_called_hawkeye

    def _finalize_game(self) -> None:
        """Finalize the game - reveal all cards, determine winner."""
        self._state.phase = GamePhase.GAME_OVER

        # reveal all cards
        self._human.reveal_all()
        self._bot.reveal_all()

        # Determine winner
        winner = self._state.get_winner()

        self._game_log.record_game_end(
            winner.name if winner else "Tie",
            self._human.total_score,
            self._bot.total_score
        )

    def get_winner(self) -> Optional[Player]:
        """Get the winner (only valid after game over)."""
        return self._state.get_winner()

    def generate_match_report(self) -> str:
        """Generate the end-of-game match report."""
        winner = self.get_winner()
        return self._game_log.generate_report(
            human_name=self._human.name,
            human_grid_score=self._human.calculate_grid_score(),
            human_penalty=self._human.penalty_points,
            bot_name=self._bot.name,
            bot_grid_score=self._bot.calculate_grid_score(),
            bot_penalty=self._bot.penalty_points,
            winner_name=winner.name if winner else "Tie"
        )

    def _get_opponent(self) -> Player:
        """Get the opponent of the current player."""
        return self._state.get_opponent(self._state.current_player)
