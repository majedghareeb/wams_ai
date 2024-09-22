from transformers import T5ForConditionalGeneration, T5Tokenizer

model_name="./arabartClassification"
model = T5ForConditionalGeneration.from_pretrained(model_name)
tokenizer = T5Tokenizer.from_pretrained(model_name)

category_mapping = { 'Politics':1, 'Finance':2, 'Medical':3, 'Sports':4, 'Culture':5, 'Tech':6, 'Religion':7 }


# Define the maximum length for tokenization
max_length = 512


def text_classification(main_texts):
    # Tokenize the input texts with padding and truncation
    tokens=tokenizer(main_texts, max_length=max_length,
                    truncation=True,
                    padding="max_length",
                    return_tensors="pt"
                )

    output= model.generate(tokens['input_ids'],
                        max_length=3,
                        #length_penalty=10
                        )

    decoded_output = tokenizer.decode(output[0], skip_special_tokens=True, clean_up_tokenization_spaces=True)

    results = []


    # Convert the decoded output to an integer
    try:
        category_number = int(decoded_output)
        # Reverse the category mapping to get the label
        reverse_mapping = {v: k for k, v in category_mapping.items()}
        category_label = reverse_mapping.get(category_number, "Unknown")
        results = [
            {
                'label': category_label,
                'number': category_number
            }
        ]
    except ValueError:
        results = [
            {
                'label': 'N/A',
                'number': category_number
            }
        ]

    return results
