from collections import defaultdict

def markovify(text, state_size=2):
    """
    Generate a Markov chain model from the input text.

    :param text: Input text to build the Markov model from.
    :param state_size: The size of the state (number of words) to consider for the Markov chain.
    :return: A dictionary representing the Markov model.
    """
    import random
    from collections import defaultdict

    words = text.split()
    markov_model = defaultdict(list)

    for i in range(len(words) - state_size):
        state = tuple(words[i:i + state_size])
        next_word = words[i + state_size]
        markov_model[state].append(next_word)

    return markov_model
def generate_sentence(markov_model, state_size=2, max_length=50):
    """
    Generate a random sentence from the Markov model.

    :param markov_model: The Markov model to use for sentence generation.
    :param state_size: The size of the state (number of words) to consider for the Markov chain.
    :param max_length: The maximum length of the generated sentence.
    :return: A randomly generated sentence as a string.
    """
    import random

    # Start with a random state
    current_state = random.choice(list(markov_model.keys()))
    sentence = list(current_state)

    for _ in range(max_length - state_size):
        next_words = markov_model.get(current_state)
        if not next_words:
            break
        next_word = random.choice(next_words)
        sentence.append(next_word)
        current_state = tuple(sentence[-state_size:])

    return ' '.join(sentence)

def sentence_tokenizer(text):
    """
    Tokenize the input text into sentences.

    :param text: Input text to tokenize.
    :return: A list of sentences.
    """
    import re

    # Simple regex to split sentences based on punctuation
    sentences = re.split(r'(?<=[.!?]) +', text)
    return [sentence.strip() for sentence in sentences if sentence.strip()]

def list_to_markov(text_list, state_size=2):
    """
    Generate a Markov chain model from a list of text strings.

    :param text_list: List of text strings to build the Markov model from.
    :param state_size: The size of the state (number of words) to consider for the Markov chain.
    :return: A dictionary representing the Markov model.
    """
    markov_model = defaultdict(list)

    for text in text_list:
        model = markovify(text, state_size)
        for state, next_words in model.items():
            markov_model[state].extend(next_words)

    return markov_model

