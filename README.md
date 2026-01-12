# Polish Bluff Poker

A CLI card game combining Golf, Cambio, and Bluffing mechanics.

Technical Interview Submission for Hawk-Eye Innovations

## Quick Start

```bash
# Python 3.10+ required (Standard Library only)
python main.py
```

---

## How to Play

### Goal
Get the **lowest score** possible. Your 2x2 grid of cards is totaled at game end.

### Card Values
- **Joker**: -2 (best card!)
- **King**: 0
- **Ace**: 1
- **2-10**: Face value
- **Jack/Queen**: 10 (penalty cards)

### Power Cards
When you draw these cards, you can use their special abilities:
- **7 or 8**: Peek at one of YOUR hidden cards
- **9 or 10**: Spy on OPPONENT's hidden card
- **Jack or Queen**: Blind swap with opponent (no peeking)

### The Bluff System
Here's where it gets interesting: **you can lie** about having a power card!

Claim any card is a power card, even if it's not. Your opponent can:
- **Challenge you** (call VAR): If you lied, you get +10 penalty. If you told the truth, they get +10.
- **Let it slide**: Your action proceeds (even if you lied!)

### Ending the Game
Call **"HAWK-EYE!"** when you think you're winning. Each player gets one final turn, then all cards are revealed.

---

## Project Structure

```
submission_hawk_eye_abishaan/
├── main.py              # Entry point
├── requirements.txt     # Empty (stdlib only)
├── README.md
│
├── src/
│   ├── models/          # Card, Deck, Player
│   ├── engine/          # Game logic & VAR system
│   ├── ai/              # Bot decision engine
│   ├── ui/              # CLI interface & ASCII art
│   └── utils/           # Game logging
│
└── tests/               # 117 unit tests
```

## Technical Details

- Python 3.10+ with type hints
- State machine pattern for game flow
- Standard library only (no external dependencies)
- Probability-based AI
- 117 unit tests
- VAR challenge system with bluff detection

## Running Tests

```bash
# Run all tests
python -m unittest discover -s tests

```

## Architecture

Separation of concerns:

- **Models**: Data structures (Card, Deck, Player)
- **Engine**: Game logic
- **AI**: Decision making
- **UI**: Display layer

## Design Notes

The bot uses probability calculations and card tracking for decisions. Game state machine has clear phases (DRAW → ACTION → CHALLENGE → END_TURN) to prevent invalid states. GameLog records actions for post-game analysis.

---

Technical Interview Submission for Hawk-Eye Innovations
