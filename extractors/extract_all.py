from flask import Flask, request, jsonify
import re, requests, json
from bs4 import BeautifulSoup
from newspaper import Article
from transformers import AutoTokenizer, AutoModelForTokenClassification, AutoModelForSequenceClassification
from camel_tools.utils.dediac import dediac_ar
from camel_tools.utils.normalize import normalize_alef_ar
import torch
import torch.nn.functional as F

# Initialize the model and tokenizer for NER
tokenizer_ner = AutoTokenizer.from_pretrained("./camel-tool/tokenizer")
model_ner = AutoModelForTokenClassification.from_pretrained("./camel-tool/model")

# Initialize the model and tokenizer for classification
tokenizer_class = AutoTokenizer.from_pretrained("./mbert")
model_class = AutoModelForSequenceClassification.from_pretrained("./mbert")

# Set the maximum length the model can handle
max_length = 512

# Move models to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model_ner.to(device)
model_class.to(device)

class_names = [
    "Finance", "Politics", "Sports", "Technology", "Health", "Entertainment", "Business"
]

def fetch_url_content(url):
    """Fetch the content of a URL and return both the text and soup object."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an error if the request was unsuccessful
        soup = BeautifulSoup(response.text, 'html.parser')
        return response.text, soup
    except requests.RequestException as e:
        raise Exception(f"Request failed: {e}")

def extract_external_links(soup):
    """Extract external links from the soup object."""
    return [link['href'] for link in soup.find_all('a', href=True) if link['href'].startswith('http')]

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

def extract_article_text(url):
    """Extract the main text of an article from the given URL."""
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article.text
    except Exception as e:
        return {"error": str(e)}

def process_text(text):
    """Dediacritize and normalize the text."""
    clean_text = dediac_ar(text)
    clean_text = normalize_alef_ar(clean_text)
    return clean_text

def extract_entities(text):
    """Extract entities from the given text using a pre-trained NER model."""
    clean_text = process_text(text)
    inputs = tokenizer_ner(clean_text, truncation=True, padding='max_length', max_length=max_length, return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items()}

    model_ner.eval()
    with torch.no_grad():
        outputs = model_ner(**inputs)

    predictions = torch.argmax(outputs.logits, dim=2).squeeze().tolist()
    tokens = tokenizer_ner.convert_ids_to_tokens(inputs['input_ids'].squeeze().tolist())
    return aggregate_entities(bio_to_entities(tokens, predictions))

def bio_to_entities(tokens, predictions):
    """Convert BIO tags to entity format."""
    entities, current_entity = [], None
    for token, tag in zip(tokens, predictions):
        if token in tokenizer_ner.all_special_tokens:
            continue
        entity_type = model_ner.config.id2label[tag].split('-')[-1]
        if tag.startswith('B-'):
            if current_entity:
                entities.append(current_entity)
            current_entity = {"text": token.replace('##', ''), "type": entity_type}
        elif tag.startswith('I-') and current_entity:
            current_entity["text"] += token.replace('##', '')
        else:
            if current_entity:
                entities.append(current_entity)
                current_entity = None
    if current_entity:
        entities.append(current_entity)
    return entities

def aggregate_entities(entities):
    """Aggregate entities by type and count."""
    entity_dict = {}
    for entity in entities:
        entity_text = entity['text']
        if entity_text not in entity_dict:
            entity_dict[entity_text] = {"type": entity['type'], "count": 0}
        entity_dict[entity_text]["count"] += 1
    return [{"text": text, "type": details["type"], "count": details["count"]} for text, details in entity_dict.items()]

def text_classification(main_texts):
    """Classify text using a pre-trained model."""
    if not isinstance(main_texts, list):
        main_texts = [main_texts]
        
    inputs = tokenizer_class(main_texts, padding=True, truncation=True, max_length=max_length, return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items()}

    model_class.eval()
    with torch.no_grad():
        outputs = model_class(**inputs)

    logits = outputs.logits
    probabilities = F.softmax(logits, dim=-1)
    predictions = torch.argmax(probabilities, dim=-1)

    predictions_list = predictions.cpu().tolist()
    probabilities_list = probabilities.cpu().tolist()

    results = [
        {
            'label': class_names[prediction],
            'score': prob
        }
        for prediction, prob in zip(predictions_list, probabilities_list[0])
    ]

    return results

def process_url(url):
    """Combine all processing steps for a given URL."""
    try:
        response_text, soup = fetch_url_content(url)
        article_text = extract_article_text(url)
        if article_text:
            entities = extract_entities(response_text)
        else:
            entities = {"error": "Failed to extract text"}

        return {
            "external_links": extract_external_links(soup),
            "datalayer": extract_datalayer_from_soup(soup),
            "article_text": article_text,
            "entities": entities
        }
    except Exception as e:
        return {"error": str(e)}

def update_url(url):
    """Update URL domain if necessary."""
    pattern = r'^(https?://)(www\.)?misbar\.com(/.*)?$'
    if re.match(pattern, url):
        return re.sub(r'^(https?://)(www\.)?misbar\.com', r'\1seo.misbar.com', url)
    return url

app = Flask(__name__)

@app.route('/wams', methods=['POST'])
def wams():
    data = request.get_json()
    url = data.get('url')
    url = update_url(url)

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    response = {}

    try:
        result = process_url(url)
        response['text'] = result
    except Exception as e:
        response['text_error'] = str(e)

    try:
        if 'text' in response:
            entities = extract_entities(response['text'])
            response['entities'] = entities
    except Exception as e:
        response['ner_error'] = str(e)

    try:
        if 'text' in response:
            classification_results = text_classification(response['text'])
            response['classification'] = classification_results
    except Exception as e:
        response['classification_error'] = str(e)

    try:
        datalayer = extract_datalayer_from_soup(fetch_url_content(url)[1])
        response['datalayer'] = datalayer
    except Exception as e:
        response['datalayer_error'] = str(e)

    if any(key in response for key in ['text', 'entities', 'classification', 'datalayer']):
        return jsonify(response)
    else:
        return jsonify({'error': 'Failed to process any data', **response}), 500

@app.route('/ner', methods=['POST'])
def ner():
    data = request.get_json()
    url = data.get('url')
    url = update_url(url)
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    try:
        article_text = extract_article_text(url)
        entities = extract_entities(article_text)
        return jsonify({'entities': entities})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/classification', methods=['POST'])
def classification():
    data = request.get_json()
    url = data.get('url')
    url = update_url(url)
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    try:
        article_text = extract_article_text(url)
        results = text_classification(article_text)
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
    url = update_url(url)
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    try:
        soup = fetch_url_content(url)[1]
        datalayer = extract_datalayer_from_soup(soup)
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
        response_text, soup = fetch_url_content(url)
        links = extract_external_links(soup)
        return jsonify({'external_links': links})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
