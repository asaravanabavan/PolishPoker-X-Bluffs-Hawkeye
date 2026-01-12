"""Command line interface for user interaction and display."""
import os
import time
from typing import Optional

from ..models import Card, Player, GridPosition, PowerType
from ..engine import GameEngine, GameState, GamePhase
from ..engine.actions import ChallengeContext
from ..ai import BotAI
from .ascii_art import AsciiArt
from .colors import Colors


class CLI:
    """Handles user input and game display."""

    def __init__(self):
        self.engine = GameEngine()
        self.bot_ai = BotAI()
        self.engine.set_bot_ai(self.bot_ai)

    def clear_screen(self) -> None:
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_slow(self, text: str, delay: float = 0.02) -> None:
        for char in text:
            print(char, end='', flush=True)
            time.sleep(delay)
        print()

    def wait_for_enter(self, message: str = "Press Enter to continue...") -> None:
        input(f"\n{message}")

    def get_input(self, prompt: str, valid_options: list[str] = None) -> str:
        """Get validated user input."""
        while True:
            user_input = input(prompt).strip().upper()
            if valid_options is None or user_input in [o.upper() for o in valid_options]:
                return user_input
            print(f"Invalid input. Please enter one of: {', '.join(valid_options)}")

    def get_position(self, prompt: str) -> GridPosition:
        """Get a grid position from user (1-4)."""
        while True:
            try:
                pos = int(input(prompt).strip())
                if 1 <= pos <= 4:
                    return GridPosition(pos - 1)
                print("Please enter a number from 1 to 4.")
            except ValueError:
                print("Please enter a valid number.")

    def show_card_values_reference(self) -> None:
        print("\n" + "=" * 50)
        print("  CARD VALUES QUICK REFERENCE")
        print("=" * 50)
        print("  Joker: -2  |  King: 0  |  Ace: 1")
        print("  2-10: Face Value (2=2, 3=3, etc.)")
        print("  Jack/Queen: 10 points")
        print()
        print("  Your Score = Sum of 4 cards + Penalty Points")
        print("  (You must calculate this yourself!)")
        print("=" * 50)
        self.wait_for_enter()

    def run(self) -> None:
        """Main game loop."""
        self.show_title()
        self.show_rules()

        # Setup game
        self.clear_screen()
        print("\nSetting up the game...")
        human_peeked, bot_peeked = self.engine.setup_game()

        # Initialize bot memory with its peeked cards
        self.bot_ai.initialize_memory(bot_peeked)

        # Show human their starting cards
        self.show_initial_peek(human_peeked)

        # Main game loop
        while not self.engine.state.is_game_over():
            self.clear_screen()
            self.display_game_board()

            if self.engine.state.is_human_turn():
                self.human_turn()
            else:
                self.bot_turn()

            # Check if turn ends the game
            if not self.engine.end_turn():
                break

        # Game over
        self.show_game_over()

    def show_title(self) -> None:
        self.clear_screen()
        print(AsciiArt.render_title())
        self.wait_for_enter()

    def show_rules(self) -> None:
        self.clear_screen()
        rules = """
╔══════════════════════════════════════════════════════════════╗
║                       HOW TO PLAY                            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  OBJECTIVE: Get the LOWEST score possible.                   ║
║                                                              ║
║  CARD VALUES:                                                ║
║    Joker: -2  |  King: 0  |  Ace: 1  |  2-10: Face Value    ║
║    Jack/Queen: 10 points (Bad!)                              ║
║                                                              ║
║  POWER CARDS:                                                ║
║    7 or 8: PEEK - Look at one of YOUR cards                  ║
║    9 or 10: SPY - Look at OPPONENT'S card                    ║
║    J or Q: BLIND SWAP - Swap cards without looking           ║
║                                                              ║
║  THE BLUFF (VAR SYSTEM):                                     ║
║    You can CLAIM any card is a power card (even if lying!)  ║
║    Opponent can CHALLENGE via the VAR system.                ║
║                                                              ║
║    Challenge Outcomes:                                       ║
║    ✓ Truth + No Challenge = Power works, no penalty         ║
║    ✓ Truth + Challenged = Challenger +10, power still works ║
║    ✓ Bluff + No Challenge = FREE POWER! No penalty          ║
║    ✓ Bluff + Challenged = Bluffer +10, power DENIED         ║
║                                                              ║
║  Call "HAWK-EYE" when you think you're winning to end!       ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        print(rules)
        self.wait_for_enter()

    def show_initial_peek(self, peeked_cards: list[tuple[GridPosition, Card]]) -> None:
        self.clear_screen()
        print("\n" + "=" * 50)
        print("   INITIAL PEEK: You see positions [3] and [4]")
        print("   (Bottom row of your 2x2 grid)")
        print("=" * 50 + "\n")
        print("   Grid Layout:")
        print("   [1]  [2]  ← Top row (hidden)")
        print("   [3]  [4]  ← Bottom row (revealed below)")
        print()

        # render both cards side-by-side
        if len(peeked_cards) == 2:
            pos1, card1 = peeked_cards[0]
            pos2, card2 = peeked_cards[1]

            # cards are already face-up from peek_initial()
            card1_art = AsciiArt.render_card(card1, show_face=True, position_label=pos1.display_number)
            card2_art = AsciiArt.render_card(card2, show_face=True, position_label=pos2.display_number)

            # display side-by-side
            for line1, line2 in zip(card1_art, card2_art):
                print(f"    {line1}  {line2}")
            print()

        print("\n  ⚠️  IMPORTANT: Remember these cards AND track your score!")
        print("  The game won't calculate your score for you - that's part")
        print("  of the challenge! Add up card values + penalties mentally.")
        self.wait_for_enter()

    def display_game_board(self) -> None:
        """Display the current game board."""
        state = self.engine.state
        board = AsciiArt.render_game_board(
            human=state.human,
            bot=state.bot,
            deck_count=state.deck.cards_remaining,
            top_discard=state.deck.top_discard,
            turn_number=state.turn_number,
            is_human_turn=state.is_human_turn(),
            human_show_known=True
        )
        print(board)

    def human_turn(self) -> None:
        """Handle human player's turn."""
        state = self.engine.state

        # Draw phase
        print("\n" + "-" * 50)
        print("  DRAW PHASE")
        print("-" * 50)

        drawn_card = self.human_draw_phase()

        # show the drawn card
        print(f"\n  You drew: {Colors.highlight(str(drawn_card))}")
        card_art = AsciiArt.render_card(drawn_card, show_face=True)
        for line in card_art:
            print(f"    {line}")

        # Action phase
        self.human_action_phase(drawn_card)

    def human_draw_phase(self) -> Card:
        """Handle draw phase for human player."""
        top_discard = self.engine.state.deck.top_discard

        print("\n  Choose where to draw from:")
        print(f"  [D] Draw from Deck")
        if top_discard:
            print(f"  [P] Pick from Discard ({top_discard})")
            choice = self.get_input("  Your choice: ", ["D", "P"])
        else:
            print("  (Discard pile is empty)")
            choice = "D"
            self.wait_for_enter()

        if choice == "D":
            return self.engine.draw_from_deck()
        else:
            return self.engine.draw_from_discard()

    def human_action_phase(self, drawn_card: Card) -> None:
        """Handle action phase for human player."""
        print("\n" + "-" * 50)
        print("  ACTION PHASE")
        print("-" * 50)

        can_discard = self.engine.state.can_discard()

        print("\n  What would you like to do?")
        print("  [S] Swap with a card in your grid")
        if can_discard:
            print("  [D] Discard this card")
        print("  [P] Power Play (use or claim a power)")
        print("  [H] Call HAWK-EYE (end the game)")
        print("  [?] Show card values reference")

        valid = ["S", "P", "H", "?"]
        if can_discard:
            valid.append("D")

        choice = self.get_input("  Your choice: ", valid)

        # show reference if requested
        if choice == "?":
            self.show_card_values_reference()
            return self.human_action_phase(drawn_card)  # Re-prompt

        match choice:
            case "S":
                self.human_swap(drawn_card)
            case "D":
                self.human_discard()
            case "P":
                self.human_power_play(drawn_card)
            case "H":
                self.human_call_hawkeye()

    def human_swap(self, drawn_card: Card) -> None:
        """Handle swap action."""
        print("\n  Which position do you want to swap with? (1-4)")
        pos = self.get_position("  Position: ")

        old_card = self.engine.swap_with_grid(pos)
        print(f"\n  Swapped {drawn_card} into position {pos.display_number}")
        print(f"  Discarded: {old_card}")
        self.bot_ai.update_seen_card(old_card)
        self.wait_for_enter()

    def human_discard(self) -> None:
        """Handle discard action."""
        self.engine.discard_drawn()
        print("\n  Card discarded.")
        self.wait_for_enter()

    def human_power_play(self, drawn_card: Card) -> None:
        """Handle power play action."""
        print("\n" + "-" * 50)
        print("  POWER PLAY - Choose what to CLAIM")
        print("  (You can lie! Opponent may challenge you)")
        print("-" * 50)
        print("  [1] PEEK (7/8) - Look at one of your cards")
        print("  [2] SPY (9/10) - Look at opponent's card")
        print("  [3] BLIND SWAP (J/Q) - Swap cards blindly")
        print()
        print("  💡 TIP: You can claim ANY power, even if you're lying!")
        print("       If opponent doesn't challenge, you get a FREE power!")

        choice = self.get_input("\n  Claim power: ", ["1", "2", "3"])

        power_map = {
            "1": PowerType.PEEK,
            "2": PowerType.SPY,
            "3": PowerType.BLIND_SWAP,
        }
        claimed_power = power_map[choice]

        # get target position
        target = None
        opponent_target = None

        if claimed_power == PowerType.PEEK:
            print("\n  Which of YOUR positions to peek? (1-4)")
            target = self.get_position("  Position: ")

        elif claimed_power == PowerType.SPY:
            print("\n  Which of OPPONENT'S positions to spy? (1-4)")
            target = self.get_position("  Position: ")

        elif claimed_power == PowerType.BLIND_SWAP:
            print("\n  Which of YOUR positions to swap? (1-4)")
            target = self.get_position("  Your position: ")
            print("  Which of OPPONENT'S positions to swap with? (1-4)")
            opponent_target = self.get_position("  Opponent position: ")

        # check if this is a bluff
        is_bluff = drawn_card.power_type != claimed_power
        if is_bluff:
            print(f"\n  {Colors.warning('(This is a BLUFF! Your card is actually ' + str(drawn_card) + ')')}")

        # Execute power play with VAR challenge
        print(AsciiArt.render_var_banner())
        print("  The opponent may challenge...")
        time.sleep(1.5)

        result = self.engine.attempt_power_play(
            claimed_power=claimed_power,
            target=target,
            opponent_target=opponent_target
        )

        # show result with explanation
        print("\n" + "=" * 50)
        if result.was_challenged:
            print("  VAR REVIEW: Challenge Issued!")
            print("=" * 50)
            if result.success:
                print(Colors.success(f"  OUTCOME: {result.message}"))
                print("  (The claim was TRUE - challenger penalized)")
            else:
                print(Colors.error(f"  OUTCOME: {result.message}"))
                print("  (The claim was a BLUFF - bluffer penalized)")
        else:
            print("  VAR REVIEW: No Challenge")
            print("=" * 50)
            if result.success:
                print(Colors.success(f"  OUTCOME: {result.message}"))
                if result.was_bluff:
                    print(Colors.info("  (Bluff succeeded! Free power activation!)"))
                else:
                    print("  (Legitimate power - no penalties)")
            else:
                print(f"  OUTCOME: {result.message}")
        print("=" * 50)

        self.wait_for_enter()

    def human_call_hawkeye(self) -> None:
        """Handle calling Hawk-Eye."""
        print("\n  " + Colors.bold("HAWK-EYE!") + " You're calling to end the game!")
        print("  Each player gets one more turn, then scores are revealed.")

        confirm = self.get_input("  Are you sure? [Y/N]: ", ["Y", "N"])
        if confirm == "Y":
            self.engine.call_hawkeye()
            print(Colors.success("\n  HAWK-EYE CALLED! Final round begins."))
        else:
            print("\n  Cancelled. Choose another action.")
            # re-show action phase (simplified - just discard)
            self.engine.discard_drawn()
            print("  Card discarded instead.")

        self.wait_for_enter()

    def bot_turn(self) -> None:
        """Handle bot's turn."""
        state = self.engine.state
        bot = state.bot

        print(f"\n  {bot.name}'s turn...")
        time.sleep(0.8)

        # Draw phase
        top_discard = state.deck.top_discard
        draw_source = self.bot_ai.decide_draw_source(top_discard)

        print(f"  {bot.name} draws from {draw_source}...")
        time.sleep(0.5)

        if draw_source == "deck":
            drawn_card = self.engine.draw_from_deck()
        else:
            drawn_card = self.engine.draw_from_discard()
            self.bot_ai.update_seen_card(drawn_card)

        # Action phase
        decision = self.bot_ai.decide_action(
            drawn_card=drawn_card,
            can_discard=state.can_discard(),
            turn_number=state.turn_number,
            opponent_penalty=state.human.penalty_points
        )

        print(f"  {bot.name} is thinking...")
        time.sleep(1)

        match decision.action:
            case "swap":
                old_card = self.engine.swap_with_grid(decision.target_position)
                print(f"  {bot.name} swaps position {decision.target_position.display_number}")
                self.bot_ai.remember_own_swap(decision.target_position, drawn_card)
                self.bot_ai.update_seen_card(old_card)

            case "discard":
                self.engine.discard_drawn()
                print(f"  {bot.name} discards the drawn card")
                self.bot_ai.update_seen_card(drawn_card)

            case "power":
                self._bot_power_play(decision, drawn_card)

            case "hawkeye":
                self.engine.call_hawkeye()
                print(Colors.warning(f"  {bot.name} calls HAWK-EYE!"))

        self.wait_for_enter()

    def _bot_power_play(self, decision, drawn_card: Card) -> None:
        """Handle bot's power play."""
        bot = self.engine.state.bot

        power_name = decision.claimed_power.value.upper()
        print(f"  {bot.name} claims to play a {power_name}!")

        if decision.is_bluff:
            print(f"  {Colors.bright_black('(This might be a bluff...)')}")

        print(AsciiArt.render_var_banner())
        print("  Will you challenge?")

        choice = self.get_input("  [Y] Challenge (Call VAR) / [N] No challenge: ", ["Y", "N"])

        # create challenge callback
        def human_challenge(context: ChallengeContext) -> bool:
            return choice == "Y"

        result = self.engine.attempt_power_play(
            claimed_power=decision.claimed_power,
            target=decision.target_position,
            opponent_target=decision.opponent_position,
            challenge_callback=human_challenge
        )

        # Show result with explanation
        print("\n" + "=" * 50)
        if result.was_challenged:
            print("  VAR REVIEW: You Challenged!")
            print("=" * 50)
            if result.success:
                print(Colors.error(f"  OUTCOME: {result.message}"))
                print("  (Their claim was TRUE - you get +10 penalty)")
            else:
                print(Colors.success(f"  OUTCOME: {result.message}"))
                print("  (You caught their BLUFF - they get +10 penalty)")
        else:
            print("  VAR REVIEW: You Did Not Challenge")
            print("=" * 50)
            if result.success:
                print(f"  OUTCOME: Their power succeeded.")
                if result.was_bluff:
                    print(Colors.error("  (They bluffed and got away with it!)"))
                else:
                    print("  (It was a legitimate power)")
        print("=" * 50)

    def show_game_over(self) -> None:
        """Display game over screen."""
        self.clear_screen()

        state = self.engine.state
        winner = self.engine.get_winner()

        # Winner banner
        if winner:
            print(AsciiArt.render_winner_banner(winner.name))
        else:
            print("\n  IT'S A TIE!")

        time.sleep(1)

        # Show final grids
        print("\n  FINAL CARDS:")
        print("\n  " + state.human.name + "'s Grid:")
        for line in AsciiArt.render_grid(state.human, show_hidden=True, show_labels=True):
            print(line)

        print("\n  " + state.bot.name + "'s Grid:")
        for line in AsciiArt.render_grid(state.bot, show_hidden=True, show_labels=True):
            print(line)

        self.wait_for_enter("Press Enter to see the Match Report...")

        # Match report
        self.clear_screen()
        report = self.engine.generate_match_report()
        print(report)

        print("\n  Thanks for playing Polish Bluff Poker!")
        print("  A Hawk-Eye Innovations Technical Interview Submission")
        print()
