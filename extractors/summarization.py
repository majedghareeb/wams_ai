from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import os

# Set the model name and local directory
model_name = "./arabartsummarization"

# Download and save the model and tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

max_length = 512
def summarize_arabic(text):
    inputs = tokenizer(text, return_tensors="pt", max_length=max_length, truncation=True)
    summary_ids = model.generate(inputs.input_ids, max_length=max_length, min_length=60, length_penalty=2.0, num_beams=4, early_stopping=True)

     # Convert the decoded output to an integer
    summary = []  
    try:
        summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    except ValueError:
        summary = 'N/A'

    return summary

