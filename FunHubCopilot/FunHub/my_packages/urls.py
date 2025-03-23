def random_string(length=10):
    """
    Generate a random string of fixed length.

    :param length: Length of the random string to generate.
    :return: A random string of the specified length.
    """
    import random
    import string

    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(length))

def url_generator(base_url, num_urls=5):
    """
    Generate a list of random URLs based on a base URL.

    :param base_url: The base URL to append random strings to.
    :param num_urls: The number of random URLs to generate.
    :return: A list of generated random URLs.
    """
    urls = []
    for _ in range(num_urls):
        random_part = random_string(10)
        urls.append(f"{base_url}/{random_part}")
    return urls

def link_decorator(text, url):
    """
    Wrap a given text in an HTML anchor tag with the specified URL.

    :param text: The text to be wrapped.
    :param url: The URL to link to.
    :return: An HTML anchor tag as a string.
    """
    return f'<a href="{url}">{text}</a>'

def link_detector(text):
    """
    Detect and extract URLs from the given text.

    :param text: The input text to search for URLs.
    :return: A list of detected URLs.
    """
    import re

    # Simple regex to find URLs in the text
    url_pattern = r'(https?://[^\s]+)'
    urls = re.findall(url_pattern, text)
    return urls

def url_shortener(url, length=10):
    """
    Shorten a given URL to a specified length by generating a random string.

    :param url: The original URL to shorten.
    :param length: The length of the random string to append to the base URL.
    :return: A shortened URL with the random string appended.
    """
    base_url = "http://short.url"
    random_part = random_string(length)
    return f"{base_url}/{random_part}"