from flask import Flask, render_template, request, jsonify
import pandas as pd
from collections import Counter, defaultdict
import os
import math
from functools import lru_cache

app = Flask(__name__)

# --- Core Functions ---

@lru_cache(maxsize=10000)
def calculate_pattern_cached(guess, target):
    """Cached version of pattern calculation"""
    pattern = ['b'] * 5
    letter_counts = defaultdict(int)
    
    # First pass: mark green matches
    for i in range(5):
        if guess[i] == target[i]:
            pattern[i] = 'g'
        else:
            letter_counts[target[i]] += 1
    
    # Second pass: mark yellow matches
    for i in range(5):
        if pattern[i] != 'g' and guess[i] in letter_counts and letter_counts[guess[i]] > 0:
            pattern[i] = 'y'
            letter_counts[guess[i]] -= 1
            
    return ''.join(pattern)

def calculate_entropy(word, possible_words):
    """Calculate the entropy (information gain) for a word given the possible words."""
    pattern_counts = defaultdict(int)
    total = len(possible_words)
    
    # Count how many words would result in each pattern
    for target in possible_words:
        pattern = calculate_pattern_cached(word, target)
        pattern_counts[pattern] += 1
    
    # Calculate entropy using the formula: -sum(p * log2(p))
    entropy = 0
    for count in pattern_counts.values():
        prob = count / total
        entropy -= prob * math.log2(prob)
        
    return entropy

# Cache for word scores
word_score_cache = {}

def score_words_with_entropy(word_list, possible_words=None):
    """Score words based on their entropy and return sorted list of (word, score) tuples."""
    if possible_words is None:
        possible_words = word_list

    # If this is the first guess, return the pre-computed best starter word
    if len(possible_words) == len(word_list):
        return [('soare', 5.89)]  # Pre-computed best starter word
    
    cache_key = (len(possible_words), hash(tuple(sorted(possible_words[:10]))))
    if cache_key in word_score_cache:
        return word_score_cache[cache_key]
    
    # For small sets, use all possible words
    if len(possible_words) <= 500:
        possible_words_sample = possible_words
    else:
        # For larger sets, use sampling
        sample_size = min(len(possible_words), 500)
        import random
        possible_words_sample = random.sample(possible_words, sample_size)
        
        # Only check for matching positions if we have a moderate number of words
        if len(possible_words) <= 1000:
            def count_matching_positions(word, possible_words):
                return sum(sum(1 for w in possible_words if w[pos] == word[pos]) for pos in range(5))
            
            # If we find a word with many matching positions, switch to full analysis
            for word in possible_words_sample:
                if count_matching_positions(word, possible_words_sample) >= 3:
                    possible_words_sample = possible_words
                    break
    
    # Smart word selection strategy:
    # 1. If we have very few words, only try those words
    # 2. Otherwise, try words from both possible words and word list
    words_to_score = possible_words if len(possible_words) <= 10 else word_list
    
    word_scores = {}
    for word in words_to_score:
        word_scores[word] = calculate_entropy(word, possible_words_sample)
    
    result = sorted(word_scores.items(), key=lambda x: (-x[1], x[0]))
    word_score_cache[cache_key] = result
    return result

def get_words_by_length(file_path, word_length):
#    df = pd.read_csv(file_path)
#    df["word"] = df["word"].str.lower()
#    return df[df["word"].str.len() == word_length]["word"].tolist()
    # Load the CSV into a DataFrame
    df = pd.read_csv(file_path)    
    df["word"] = df["word"].str.lower()    
    # Filter for words that are alphabetic and have the desired length
    df_filtered = df[df["word"].str.isalpha() & (df["word"].str.len() == word_length)]    
    # Return the list of words
    return df_filtered["word"].tolist()


def score_words(word_list):
    letter_counts = Counter("".join(word_list))
    word_scores = {}
    for word in word_list:
        score = 0
        used = set()
        for letter in word:
            if letter not in used:
                score += letter_counts[letter]
                used.add(letter)
        word_scores[word] = score
    return sorted(word_scores.items(), key=lambda x: -x[1])

def filter_words(possible_words, guess, feedback):
    new_list = []
    for word in possible_words:
        match = True
        for i in range(len(guess)):
            if feedback[i] == 'g':
                if word[i] != guess[i]:
                    match = False
                    break
            elif feedback[i] == 'y':
                if guess[i] not in word or word[i] == guess[i]:
                    match = False
                    break
            elif feedback[i] == 'b':
                if guess[i] in word:
                    if not any((guess[j] == guess[i] and feedback[j] in 'gy') for j in range(len(guess)) if j != i):
                        match = False
                        break
        if match:
            new_list.append(word)
    return new_list

# Global variables to store state
word_list = []
possible_words = []
current_guess_index = 0
guess_history = []
used_suggestions = set()  # Track used suggestions

# Load words on startup
# Initialize words using app context
def load_words():
    global word_list, possible_words
    word_list = get_words_by_length('ENGDICT.csv', 5)
    possible_words = word_list[:]

# Call load_words on startup
load_words()

@app.route('/')
def index():
    # Clear the cache when starting a new game
    word_score_cache.clear()
    calculate_pattern_cached.cache_clear()
    return render_template('index.html')

@app.route('/api/reset', methods=['POST'])
def reset():
    global possible_words, current_guess_index, guess_history, used_suggestions
    possible_words = word_list[:]
    current_guess_index = 0
    guess_history = []
    used_suggestions = set()  # Clear used suggestions
    # Clear the cache when resetting
    word_score_cache.clear()
    calculate_pattern_cached.cache_clear()
    
    scored_words = score_words_with_entropy(word_list, possible_words)
    next_guess = scored_words[current_guess_index][0] if scored_words else ""
    
    return jsonify({
        'success': True,
        'remaining_count': len(possible_words),
        'remaining_words': possible_words[:20],
        'next_guess': next_guess
    })

@app.route('/api/get_suggestion', methods=['GET'])
def get_suggestion():
    global current_guess_index
    
    scored_words = score_words_with_entropy(word_list, possible_words)
    
    if not scored_words:
        return jsonify({
            'success': False,
            'message': 'No possible words remaining'
        })
    
    next_guess = scored_words[current_guess_index][0]
    
    # Get the entropy score for display
    entropy = next((score for word, score in scored_words if word == next_guess), None)
    
    return jsonify({
        'success': True,
        'next_guess': next_guess,
        'entropy': entropy,
        'remaining_count': len(possible_words),
        'remaining_words': possible_words[:20]
    })

@app.route('/api/next_suggestion', methods=['POST'])
def next_suggestion():
    global current_guess_index, used_suggestions
    
    scored_words = score_words_with_entropy(word_list, possible_words)
    
    if not scored_words:
        return jsonify({
            'success': False,
            'message': 'No possible words remaining'
        })
    
    # Find next unused suggestion
    for _ in range(len(scored_words)):
        current_guess_index = (current_guess_index + 1) % len(scored_words)
        next_guess = scored_words[current_guess_index][0]
        if next_guess not in used_suggestions:
            break
    else:
        # If all words have been used, clear the used suggestions and start over
        used_suggestions.clear()
    
    next_guess = scored_words[current_guess_index][0]
    entropy = scored_words[current_guess_index][1]
    used_suggestions.add(next_guess)
    
    return jsonify({
        'success': True,
        'next_guess': next_guess,
        'entropy': entropy
    })

@app.route('/api/submit_feedback', methods=['POST'])
def submit_feedback():
    global possible_words, current_guess_index, guess_history, used_suggestions
    
    data = request.get_json()
    print("Received feedback data:", data)
    # Clear used suggestions when submitting feedback for a new guess
    used_suggestions.clear()
    
    guess = data.get('guess', '')
    feedback = data.get('feedback', '')
    
    print(f"Processing guess: '{guess}' with feedback: '{feedback}'")
    
    if not guess or not feedback or len(guess) != 5 or len(feedback) != 5:
        print("Invalid guess or feedback detected")
        return jsonify({
            'success': False,
            'message': 'Invalid guess or feedback'
        })
    
    if not all(c in 'gyb' for c in feedback):
        print("Feedback contains invalid characters")
        return jsonify({
            'success': False,
            'message': 'Feedback must only contain g, y, or b'
        })
    
    # Add to history
    guess_history.append({
        'guess': guess,
        'feedback': feedback
    })
    
    # Filter words based on feedback
    possible_words = filter_words(possible_words, guess, feedback)
    current_guess_index = 0
    
    scored_words = score_words_with_entropy(word_list, possible_words)
    next_guess = scored_words[current_guess_index][0] if scored_words else ""
    
    if scored_words:
        entropy = scored_words[current_guess_index][1]
        print(f"Filtered to {len(possible_words)} possible words. Next guess: {next_guess} (entropy: {entropy:.2f})")
    
    return jsonify({
        'success': True,
        'remaining_count': len(possible_words),
        'remaining_words': possible_words[:20],
        'next_guess': next_guess,
        'history': guess_history
    })

# Create templates directory if it doesn't exist
if not os.path.exists('templates'):
    os.makedirs('templates')

if __name__ == '__main__':
    app.run(debug=True)