from newspaper import Article
from requests.exceptions import RequestException
from newspaper.article import ArticleException

def extract_article_text(url):
    try:
        # Create an Article object
        article = Article(url)
        
        # Attempt to download the article
        article.download()
        
        # Attempt to parse the article
        article.parse()
        
        # Return the main text of the article
        return article.text,article.top_image
    
    except RequestException as e:
        # Handle exceptions related to network issues or invalid URL
        return {"error": f"Request error: {str(e)}"}
    
    except ArticleException as e:
        # Handle exceptions related to parsing or processing the article
        return {"error": f"Article parsing error: {str(e)}"}
    
    except Exception as e:
        # Handle any other unexpected exceptions
        return {"error": f"An unexpected error occurred: {str(e)}"}
