from flask import Flask, request, jsonify
import re
import requests
import json
from bs4 import BeautifulSoup
from requests.exceptions import RequestException
from newspaper import Article
from newspaper.article import ArticleException
from extractors.ner import extract_enitites
from extractors.classifications import text_classification
from extractors.summarization import summarize_arabic
from functools import lru_cache  # For caching
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

# Create a session for connection pooling
session = requests.Session()

app = Flask(__name__)

@lru_cache(maxsize=128)  # Cache results of frequently accessed URLs
def fetch_url_content(url):
    """Fetch the content of a URL and return both the text and soup object."""
    try:
        response = session.get(url)
        response.raise_for_status()  # Raises an error if the request was unsuccessful
        return response.text
    except RequestException as e:
        logging.error(f"Request failed: {e}")
        return {"error": f"Request failed: {e}"}

def extract_article_text(url):
    """Extract the main text of an article from the given URL."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except ArticleException as e:
        logging.error(f"Article extraction failed: {e}")
        return {"error": str(e)}

def extract_external_links(soup):
    """Extract the links from the soup object."""
    links = []
    for link in soup.find_all('a', href=True):
        href = link['href']
        if href.startswith('http'):
            links.append(href)

    return links

def extract_datalayer_from_soup(soup):
    """Extract the dataLayer from the soup object."""
    script_tag = soup.find("script", string=lambda string: string and "dataLayer" in string)
    if script_tag:
        script_text = script_tag.string.strip().replace("\n", "")
        match = re.search(r'(?<=dataLayer.push\().*?(?=\);)', script_text)
        if match:
            json_data = re.sub(r',\s*}', '}', match.group(0).strip().replace("'", '"'))
            try:
                return json.loads(json_data)
            except json.JSONDecodeError as e:
                return {"error": f"JSON decoding error: {e}"}
    return {"error": "No dataLayer found"}

@app.route('/wams', methods=['POST'])
def wams():
    data = request.get_json()
    url = data.get('url')
    if not url:
        return jsonify({'error': 'URL is required'}), 400

    response = {}
    article_text = extract_article_text(url)

    if 'error' in article_text:
        return jsonify(article_text), 500

    entities = extract_enitites(article_text)
    response['entities'] = entities

    return jsonify(response)

@app.route('/ner', methods=['POST'])
def ner():
    data = request.get_json()
    url = data.get('url')
    update_url(url)
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    try:
        article_text = extract_article_text(url)
        entities = extract_enitites(article_text)
        return jsonify({'entities': entities})
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/classification', methods=['POST'])
def classification():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        # Placeholder functions for extracting article text and updating URL
        article_text = extract_article_text(url)
        results = text_classification([article_text])
        
        return jsonify(results)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/extract_text', methods=['POST'])
def extract_text():
    data = request.json
    url = data.get('url')
    url = update_url(url)
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    try:
        text = extract_article_text(url)
        if text:
            return jsonify({'text': text})
        else:
            return jsonify({'error': 'Text not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/extract_datalayer', methods=['POST'])
def extract_datalayer():
    data = request.json
    url = data.get('url')
    update_url(url)
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    try:
        datalayer = extract_datalayer_from_url(url)
        if datalayer:
            return jsonify({'datalayer': datalayer})
        else:
            return jsonify({'error': 'dataLayer not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    

@app.route('/extract_links', methods=['POST'])
def extract_links():
    data = request.json
    url = data.get('url')
    url = update_url(url)

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        links = extract_external_links(url)
        return jsonify({'external_links': links})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)  # Set debug to False for production
