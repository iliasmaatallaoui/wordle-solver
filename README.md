# Entropy-Based Wordle Solver

An intelligent Wordle solver that uses information theory and entropy calculations to optimize word guesses. This solver typically solves Wordle puzzles in 3-4 tries, with a theoretical maximum of 6 tries.

## How It Works

### Core Algorithm

The solver uses information theory principles to make optimal guesses:

1. **First Guess**: Always starts with 'SOARE' (pre-computed optimal first word with entropy of 5.89 bits)
2. **Subsequent Guesses**: Uses entropy calculations to maximize information gain
3. **Pattern Matching**: Implements Wordle's green/yellow/black feedback system
4. **Word Filtering**: Progressively narrows down possible solutions

### Entropy-Based Decision Making

The solver calculates the entropy (information gain) for each possible guess using the formula:
```
H = -∑(p * log₂(p))
```
where:
- H is the entropy in bits
- p is the probability of each possible pattern
- The sum is taken over all possible patterns

### Performance

Average performance metrics:
- Expected tries: 3.92
- 95% confidence interval: [3-5] tries
- Distribution:
  - 2 tries: ~2%
  - 3 tries: ~25%
  - 4 tries: ~55%
  - 5 tries: ~16%
  - 6 tries: ~2%

## Technical Implementation

### Key Features

1. **Caching Mechanisms**
   - LRU cache for pattern calculations
   - Word score caching
   - Pre-computed first guess

2. **Optimization Techniques**
   - Smart sampling for large word sets
   - Adaptive strategy based on remaining words
   - Position matching optimization

3. **Flask Web Interface**
   - Interactive web-based solver
   - Real-time feedback processing
   - Suggestion system

## Setup and Installation

1. Clone the repository:
```bash
git clone https://github.com/iliasmaatallaoui/wordle-solver.git
```

2. Install requirements:
```bash
pip install -r requirements.txt
```

3. Run the Flask application:
```bash
python wordle-solver-flask.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. The solver will suggest 'SOARE' as the first guess
2. Enter the feedback from Wordle using:
   - 'g' for green (correct letter, correct position)
   - 'y' for yellow (correct letter, wrong position)
   - 'b' for black (letter not in word)
3. Get the next optimal guess
4. Repeat until solved

## Dependencies

- Flask
- Pandas
- Python 3.7+

## Credits

- Dictionary data modified from [English Dictionary Database](https://github.com/benjihillard/English-Dictionary-Database) by Benji Hillard
- Entropy calculation methodology inspired by information theory principles

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
