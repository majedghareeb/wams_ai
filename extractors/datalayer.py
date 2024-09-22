import requests
from bs4 import BeautifulSoup
import json
import re

def extract_datalayer_from_url(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Step 2: Find the script tag containing the dataLayer
        script_tag = soup.find("script", string=lambda string: string and "dataLayer" in string)

        # Step 3: Extract and parse the JSON data
        if script_tag:
            script_text = script_tag.string
            if script_text:
                # Step 1: Clean the script string
                cleaned_script = script_text.strip()
                # Step 2: Replace multiple spaces with a single space
                cleaned_script = re.sub(r'\s+', ' ', cleaned_script)
                cleaned_script = cleaned_script.replace("\n", "")
                # Use regex to find the JSON object within the script
                match = re.search(r'(?<=dataLayer.push\().*?(?=\);)', cleaned_script)
                
                if match:
                    json_data = match.group(0)  # Extract the matched JSON string
                    json_data = json_data.strip()  # Remove any leading/trailing whitespace
                    
                    # Step 2: Replace single quotes with double quotes for valid JSON
                    json_data = json_data.replace("'", '"')
                    
                    # Step 3: Remove any trailing commas
                    json_data = re.sub(r',\s*}', '}', json_data)  # Remove trailing comma before closing brace
                    
                    # Step 4: Convert to JSON
                    try:
                        data = json.loads(json_data)  # Load the JSON data
                        return data  # Print the extracted data
                    except json.JSONDecodeError as e:
                        return {f"JSON decoding error: {e}"}
                else:
                    return {"No JSON data found in the script."}
            else:
                return {"No script tag containing dataLayer found."}
    
    except requests.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}