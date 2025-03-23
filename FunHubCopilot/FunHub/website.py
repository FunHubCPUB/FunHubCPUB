import my_packages
from my_packages.markov import list_to_markov, sentence_tokenizer, generate_sentence
from my_packages.urls import random_string, url_generator, link_decorator

pages=url_generator("http://funhub.lol", 50)

for url in pages:
    print(link_decorator("Link", url))


markov=list_to_markov(pages, state_size=2)

for range in range(10):
    print(generate_sentence(markov, state_size=2, max_length=50))