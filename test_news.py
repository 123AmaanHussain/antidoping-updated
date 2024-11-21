from newsapi import NewsApiClient
from datetime import datetime, timedelta

# Initialize News API client
newsapi = NewsApiClient(api_key='c4b74265e83f4568b7f77090527d4204')

def test_news_api():
    print("Testing NewsAPI connection...")
    try:
        # Test sports headlines
        print("\nTesting sports headlines...")
        sports_news = newsapi.get_top_headlines(
            category='sports',
            language='en',
            page_size=5
        )
        print(f"Status: {sports_news.get('status')}")
        print(f"Total Results: {sports_news.get('totalResults')}")
        if sports_news.get('articles'):
            print("\nFirst sports article:")
            article = sports_news['articles'][0]
            print(f"Title: {article.get('title')}")
            print(f"Source: {article.get('source', {}).get('name')}")
        
        # Test doping news
        print("\nTesting doping news search...")
        doping_news = newsapi.get_everything(
            q='doping sports athletics',
            language='en',
            sort_by='publishedAt',
            from_param=(datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'),
            page_size=5
        )
        print(f"Status: {doping_news.get('status')}")
        print(f"Total Results: {doping_news.get('totalResults')}")
        if doping_news.get('articles'):
            print("\nFirst doping article:")
            article = doping_news['articles'][0]
            print(f"Title: {article.get('title')}")
            print(f"Source: {article.get('source', {}).get('name')}")
            
    except Exception as e:
        print(f"Error testing NewsAPI: {str(e)}")
        import traceback
        print(f"Full error traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_news_api()
