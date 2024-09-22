import requests
from bs4 import BeautifulSoup

def extract_external_links(url):
    response = requests.get(url)
    response.raise_for_status()  # Raises an error if the request was unsuccessful
    soup = BeautifulSoup(response.text, 'html.parser')
    links = []

    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('http'):
            links.append(href)

    return links
