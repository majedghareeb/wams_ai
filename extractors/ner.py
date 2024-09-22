from transformers import AutoTokenizer, AutoModelForTokenClassification
from camel_tools.utils.normalize import normalize_unicode , normalize_alef_ar, normalize_alef_maksura_bw, normalize_alef_maksura_safebw
from camel_tools.utils.dediac import dediac_ar
import torch

# Initialize the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained("./camel-tool/tokenizer")
model = AutoModelForTokenClassification.from_pretrained("./camel-tool/model")

# Set the maximum length the model can handle
max_length = 512


def extract_enitites(main_text):
    # Dediacritize and normalize the text
    clean_text = process_text(main_text)

    # Tokenize the text with truncation and padding
    inputs = tokenizer(clean_text, truncation=True, padding='max_length', max_length=max_length, return_tensors="pt")

    # Perform NER using the model
    with torch.no_grad():
        outputs = model(**inputs)
    
    # Decode the outputs to get results
    logits = outputs.logits
    predictions = torch.argmax(logits, dim=2).squeeze().tolist()
    tokens = tokenizer.convert_ids_to_tokens(inputs['input_ids'].squeeze().tolist())
    
    # Convert predictions to entity tags
    ner_results = []
    word_start = 0  # Track the start position of each word in the text
    for token, tag in zip(tokens, predictions):
        if token not in tokenizer.all_special_tokens:  # Ignore special tokensc
            word_len = len(token.replace('##', ''))  # Adjust word length without ##
            ner_results.append({'word': token, 'entity': model.config.id2label[tag], 'start': word_start, 'end': word_start + word_len})
            word_start += word_len
    
    # Convert the results into a structured format
    entities = bio_to_entities(ner_results)
        
    # Aggregate entities to show only one instance with counts
    aggregated_entities = aggregate_entities(entities)
    
    return aggregated_entities

def bio_to_entities(results):
    entities = []
    current_entity = None
    
    for result in results:
        word = result['word']
        tag = result['entity']
        start = result['start']
        end = result['end']
        
        # Remove the prefix (B- or I-) from the tag
        entity_type = tag.split('-')[-1]
        # Handle subword tokens (tokens starting with ##)
        if word.startswith("##"):
            if current_entity:
                current_entity['text'] += word[2:]  # Append the subword without the ##
                current_entity['end'] += len(word[2:])  # Adjust the end index
        elif tag.startswith("B-"):
            if current_entity:
                entities.append(current_entity)
            current_entity = {"text": word, "start": start, "end": end, "type": entity_type}
        elif tag.startswith("I-"):
            if current_entity:
                current_entity["text"] += " " + word
                current_entity["end"] = end
        else:  # O or any other tag
            if current_entity:
                entities.append(current_entity)
                current_entity = None
    
    if current_entity:
        entities.append(current_entity)
    
    return entities
def process_text(text):
    # Dediacritize and normalize the text
    clean_text = dediac_ar(text)
    clean_text = normalize_alef_ar(clean_text)
    return clean_text


def aggregate_entities(entities):
    entity_dict = {}

    for entity in entities:
        entity_text = entity['text']
        if entity_text not in entity_dict:
            entity_dict[entity_text] = {"type": entity['type'], "count": 0}
        entity_dict[entity_text]["count"] += 1

    # Convert the aggregated dictionary to a list of entities
    aggregated_entities = [
        {"text": text, "type": details["type"], "count": details["count"]}
        for text, details in entity_dict.items()
    ]
    
    return aggregated_entities