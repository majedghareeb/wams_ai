# WAMS AI Application

This project is a web application for extracting and processing data from URLs using various NLP techniques.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation Steps

1. **Clone the Repository**

   Open your terminal and clone the repository:

   ```bash
   git clone <repository-url>
   cd wams_ai
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   Create a virtual environment to manage dependencies:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install Required Packages**

   Install the necessary packages using the `requirements.txt` file:

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application Locally**

   Start the Flask application:

   ```bash
   python app.py
   ```

   The application will run on `http://0.0.0.0:5000`.

5. **Deploy the Application Using Gunicorn**

   To deploy the application in a production environment, use `gunicorn`:

   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

   - `-w 4` specifies the number of worker processes (adjust based on your server's CPU cores).
   - `-b 0.0.0.0:5000` binds the application to all available IP addresses on port 5000.

6. **Access the API**

   You can now access the API endpoints using tools like `curl` or Postman. For example, to use the `/wams` endpoint:

   ```bash
   curl -X POST http://localhost:5000/wams -H "Content-Type: application/json" -d '{"url": "http://example.com"}'
   ```

## Usage

- **/wams**: Main endpoint for processing URLs.
- **/ner**: Extract entities from a given URL.
- **/classification**: Classify text from a given URL.
- **/extract_text**: Extract main text from a given URL.
- **/extract_datalayer**: Extract dataLayer from a given URL.
- **/extract_links**: Extract external links from a given URL.

## License

This project is licensed under the MIT License.
