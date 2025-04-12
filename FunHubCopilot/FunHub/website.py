from app.my_packages import list_to_markov, generate_sentence
from app.my_packages import url_generator, link_decorator

pages=url_generator("http://funhub.lol", 50)

for url in pages:
    print(link_decorator("Link", url))


markov=list_to_markov(pages, state_size=2)

for range in range(10):
    print(generate_sentence(markov, state_size=2, max_length=50))