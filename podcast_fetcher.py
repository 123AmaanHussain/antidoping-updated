import os
import logging
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import traceback

class PodcastFetcher:
    def __init__(self):
        self.spotify_client_id = os.getenv('SPOTIPY_CLIENT_ID')
        self.spotify_client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
        self.itunes_search_url = "https://itunes.apple.com/search"
        self.youtube_api_key = os.getenv('YOUTUBE_API_KEY')
        self.spotify_token = None
        self.spotify_token_expiry = None

    def _get_spotify_token(self) -> Optional[str]:
        """Get or refresh Spotify access token"""
        try:
            # Check if token is still valid
            if self.spotify_token and self.spotify_token_expiry and datetime.now() < self.spotify_token_expiry:
                return self.spotify_token

            if not (self.spotify_client_id and self.spotify_client_secret):
                logging.error("Spotify credentials not found in environment variables")
                return None

            auth_url = "https://accounts.spotify.com/api/token"
            auth_response = requests.post(auth_url, {
                'grant_type': 'client_credentials',
                'client_id': self.spotify_client_id,
                'client_secret': self.spotify_client_secret,
            })

            if auth_response.status_code != 200:
                logging.error(f"Failed to get Spotify token: {auth_response.text}")
                return None

            auth_data = auth_response.json()
            self.spotify_token = auth_data['access_token']
            self.spotify_token_expiry = datetime.now() + timedelta(seconds=auth_data['expires_in'] - 300)
            return self.spotify_token

        except Exception as e:
            logging.error(f"Error getting Spotify token: {str(e)}")
            return None

    def fetch_spotify_podcasts(self) -> List[Dict[str, Any]]:
        """Fetch sports and anti-doping podcasts from Spotify"""
        try:
            token = self._get_spotify_token()
            if not token:
                logging.error("Failed to get Spotify token")
                return []

            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            # Search for sports and anti-doping podcasts
            search_url = "https://api.spotify.com/v1/search"
            queries = ["sports doping", "anti-doping", "clean sport"]
            all_podcasts = []

            for query in queries:
                logging.info(f"Searching Spotify for query: {query}")
                params = {
                    'q': query,
                    'type': 'show',
                    'market': 'US',
                    'limit': 10
                }

                response = requests.get(search_url, headers=headers, params=params)
                logging.info(f"Spotify API response status: {response.status_code}")
                
                if response.status_code != 200:
                    logging.error(f"Spotify API error: {response.text}")
                    continue

                try:
                    data = response.json()
                    logging.debug(f"Spotify API response data: {data}")
                except Exception as json_error:
                    logging.error(f"Failed to parse Spotify response as JSON: {str(json_error)}")
                    continue

                shows = data.get('shows', {}).get('items', [])
                logging.info(f"Found {len(shows)} shows for query: {query}")

                for show in shows:
                    try:
                        podcast = {
                            'title': show.get('name', 'Untitled Show'),
                            'description': show.get('description', 'No description available'),
                            'author': show.get('publisher', 'Unknown Publisher'),
                            'published_date': show.get('updated_at', datetime.now().strftime('%Y-%m-%d'))[:10],
                            'image_url': show.get('images', [{}])[0].get('url') if show.get('images') else None,
                            'audio_url': show.get('external_urls', {}).get('spotify', '#'),
                            'duration': '30 min',  # Default duration as Spotify API doesn't provide episode duration in show search
                            'category': 'Sports & Anti-Doping',
                            'language': show.get('languages', ['en'])[0] if show.get('languages') else 'en',
                            'listens': show.get('total_episodes', 1) * 100  # Estimated listens based on total episodes
                        }
                        all_podcasts.append(podcast)
                        logging.debug(f"Processed show: {podcast['title']}")
                    except Exception as show_error:
                        logging.error(f"Error processing show: {str(show_error)}")
                        continue

            logging.info(f"Successfully fetched {len(all_podcasts)} total podcasts from Spotify")
            return all_podcasts

        except Exception as e:
            logging.error(f"Error fetching Spotify podcasts: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            return []

    def fetch_itunes_podcasts(self) -> List[Dict[str, Any]]:
        """Fetch sports and anti-doping podcasts from iTunes"""
        try:
            queries = ["sports doping", "anti-doping", "clean sport"]
            all_podcasts = []

            for query in queries:
                logging.info(f"Searching iTunes for query: {query}")
                params = {
                    'term': query,
                    'entity': 'podcast',
                    'limit': 10
                }

                response = requests.get(self.itunes_search_url, params=params)
                logging.info(f"iTunes API response status: {response.status_code}")
                
                if response.status_code != 200:
                    logging.error(f"iTunes API error: {response.text}")
                    continue

                try:
                    data = response.json()
                    logging.debug(f"iTunes API response data: {data}")
                except Exception as json_error:
                    logging.error(f"Failed to parse iTunes response as JSON: {str(json_error)}")
                    continue

                results = data.get('results', [])
                logging.info(f"Found {len(results)} podcasts for query: {query}")

                for result in results:
                    try:
                        podcast = {
                            'title': result.get('collectionName', 'Untitled Podcast'),
                            'description': result.get('description', 'No description available'),
                            'author': result.get('artistName', 'Unknown Artist'),
                            'published_date': datetime.now().strftime('%Y-%m-%d'),  # iTunes doesn't provide release date in search
                            'image_url': result.get('artworkUrl600'),
                            'audio_url': result.get('collectionViewUrl', '#'),
                            'duration': '30 min',  # Default duration as iTunes search doesn't provide episode duration
                            'category': result.get('primaryGenreName', 'Sports & Anti-Doping'),
                            'language': 'en',  # iTunes usually returns English content for English queries
                            'listens': 500  # Default listens as iTunes doesn't provide this information
                        }
                        all_podcasts.append(podcast)
                        logging.debug(f"Processed podcast: {podcast['title']}")
                    except Exception as podcast_error:
                        logging.error(f"Error processing podcast: {str(podcast_error)}")
                        continue

            logging.info(f"Successfully fetched {len(all_podcasts)} total podcasts from iTunes")
            return all_podcasts

        except Exception as e:
            logging.error(f"Error fetching iTunes podcasts: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            return []

    def fetch_youtube_videos(self) -> List[Dict[str, Any]]:
        """Fetch sports and anti-doping related videos from YouTube"""
        try:
            if not self.youtube_api_key:
                logging.error("YouTube API key not found in environment variables")
                return []

            base_url = "https://www.googleapis.com/youtube/v3/search"
            queries = ["sports doping", "anti-doping", "clean sport"]
            all_videos = []

            for query in queries:
                logging.info(f"Searching YouTube for query: {query}")
                params = {
                    'part': 'snippet',
                    'q': query,
                    'type': 'video',
                    'maxResults': 10,
                    'key': self.youtube_api_key,
                    'relevanceLanguage': 'en'
                }

                response = requests.get(base_url, params=params)
                logging.info(f"YouTube API response status: {response.status_code}")
                
                if response.status_code != 200:
                    logging.error(f"YouTube API error: {response.text}")
                    continue

                try:
                    data = response.json()
                    logging.debug(f"YouTube API response data: {data}")
                except Exception as json_error:
                    logging.error(f"Failed to parse YouTube response as JSON: {str(json_error)}")
                    continue

                items = data.get('items', [])
                logging.info(f"Found {len(items)} videos for query: {query}")

                for item in items:
                    try:
                        video = {
                            'title': item.get('snippet', {}).get('title', 'Untitled Video'),
                            'description': item.get('snippet', {}).get('description', 'No description available'),
                            'author': item.get('snippet', {}).get('channelTitle', 'Unknown Channel'),
                            'published_date': item.get('snippet', {}).get('publishedAt', datetime.now().strftime('%Y-%m-%d'))[:10],
                            'image_url': item.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url'),
                            'audio_url': f"https://www.youtube.com/watch?v={item.get('id', {}).get('videoId', '')}",
                            'duration': '10 min',  # Default duration as search endpoint doesn't provide video duration
                            'category': 'Video',
                            'language': 'en',
                            'listens': 1000  # Default views as search endpoint doesn't provide view count
                        }
                        all_videos.append(video)
                        logging.debug(f"Processed video: {video['title']}")
                    except Exception as video_error:
                        logging.error(f"Error processing video: {str(video_error)}")
                        continue

            logging.info(f"Successfully fetched {len(all_videos)} total videos from YouTube")
            return all_videos

        except Exception as e:
            logging.error(f"Error fetching YouTube videos: {str(e)}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            return []

    def get_all_podcasts(self) -> List[Dict[str, Any]]:
        """Fetch podcasts from all available sources"""
        all_content = []
        logging.info("Starting to fetch content from all sources")

        # Fetch from Spotify
        try:
            logging.info("Fetching podcasts from Spotify")
            spotify_podcasts = self.fetch_spotify_podcasts()
            logging.info(f"Retrieved {len(spotify_podcasts)} podcasts from Spotify")
            all_content.extend(spotify_podcasts)
        except Exception as e:
            logging.error(f"Failed to fetch Spotify podcasts: {str(e)}")

        # Fetch from iTunes
        try:
            logging.info("Fetching podcasts from iTunes")
            itunes_podcasts = self.fetch_itunes_podcasts()
            logging.info(f"Retrieved {len(itunes_podcasts)} podcasts from iTunes")
            all_content.extend(itunes_podcasts)
        except Exception as e:
            logging.error(f"Failed to fetch iTunes podcasts: {str(e)}")

        # Fetch from YouTube
        try:
            logging.info("Fetching videos from YouTube")
            youtube_videos = self.fetch_youtube_videos()
            logging.info(f"Retrieved {len(youtube_videos)} videos from YouTube")
            all_content.extend(youtube_videos)
        except Exception as e:
            logging.error(f"Failed to fetch YouTube videos: {str(e)}")

        # If no content was fetched, return sample podcasts
        if not all_content:
            logging.warning("No content fetched from any source, returning sample podcasts")
            return self.get_sample_podcasts()

        logging.info(f"Successfully fetched {len(all_content)} total content items")
        return all_content

    def get_sample_podcasts(self) -> List[Dict[str, Any]]:
        """Return sample podcasts as fallback"""
        logging.info("Returning sample podcasts as fallback")
        return [
            {
                'title': 'Clean Sport Insights',
                'description': 'A podcast about maintaining integrity in sports',
                'author': 'Anti-Doping Education Team',
                'published_date': datetime.now().strftime('%Y-%m-%d'),
                'image_url': 'https://example.com/podcast1.jpg',
                'audio_url': 'https://example.com/podcast1.mp3',
                'duration': '45 min',
                'category': 'Sports & Anti-Doping',
                'language': 'en',
                'listens': 1000
            },
            {
                'title': 'The Science of Clean Competition',
                'description': 'Understanding the importance of fair play in sports',
                'author': 'Sports Science Institute',
                'published_date': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),
                'image_url': 'https://example.com/podcast2.jpg',
                'audio_url': 'https://example.com/podcast2.mp3',
                'duration': '30 min',
                'category': 'Sports & Anti-Doping',
                'language': 'en',
                'listens': 800
            }
        ]
