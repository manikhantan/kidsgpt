"""
YouTube service for fetching kid-safe educational videos.
"""
import logging
from typing import Optional, Dict, Any
import httpx

logger = logging.getLogger(__name__)


class YouTubeVideo:
    """Represents a YouTube video suggestion."""

    def __init__(self, video_id: str, title: str, thumbnail_url: str, channel_title: str):
        self.video_id = video_id
        self.title = title
        self.thumbnail_url = thumbnail_url
        self.channel_title = channel_title
        self.url = f"https://www.youtube.com/watch?v={video_id}"

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary format for API responses."""
        return {
            "video_id": self.video_id,
            "title": self.title,
            "url": self.url,
            "thumbnail_url": self.thumbnail_url,
            "channel_title": self.channel_title
        }


class YouTubeService:
    """Service for fetching kid-safe educational videos from YouTube."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube service.

        Args:
            api_key: YouTube Data API v3 key
        """
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    async def search_video(self, query: str, max_results: int = 1) -> Optional[YouTubeVideo]:
        """
        Search for a kid-safe educational video.

        Args:
            query: Search query based on the conversation topic
            max_results: Number of videos to return (default: 1)

        Returns:
            YouTubeVideo object or None if no video found or API not configured
        """
        if not self.api_key:
            logger.warning("YouTube API key not configured, skipping video search")
            return None

        try:
            # Build search parameters
            params = {
                "part": "snippet",
                "q": f"{query} educational for kids",
                "type": "video",
                "maxResults": max_results,
                "safeSearch": "strict",  # Enable strict safe search
                "videoEmbeddable": "true",  # Only embeddable videos
                "videoCategoryId": "27",  # Education category
                "relevanceLanguage": "en",
                "key": self.api_key
            }

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/search",
                    params=params,
                    timeout=10.0
                )

                if response.status_code != 200:
                    logger.error(f"YouTube API error: {response.status_code} - {response.text}")
                    return None

                data = response.json()

                if not data.get("items"):
                    logger.info(f"No videos found for query: {query}")
                    return None

                # Get the first video
                video_item = data["items"][0]
                video_id = video_item["id"]["videoId"]
                snippet = video_item["snippet"]

                # Get the best quality thumbnail available
                thumbnails = snippet["thumbnails"]
                thumbnail_url = (
                    thumbnails.get("high", {}).get("url") or
                    thumbnails.get("medium", {}).get("url") or
                    thumbnails.get("default", {}).get("url", "")
                )

                video = YouTubeVideo(
                    video_id=video_id,
                    title=snippet["title"],
                    thumbnail_url=thumbnail_url,
                    channel_title=snippet["channelTitle"]
                )

                logger.info(f"Found video: {video.title} ({video.url})")
                return video

        except httpx.TimeoutException:
            logger.error("YouTube API request timed out")
            return None
        except Exception as e:
            logger.error(f"Error fetching YouTube video: {str(e)}")
            return None

    def search_video_sync(self, query: str, max_results: int = 1) -> Optional[YouTubeVideo]:
        """
        Search for a kid-safe educational video (synchronous version).

        Args:
            query: Search query based on the conversation topic
            max_results: Number of videos to return (default: 1)

        Returns:
            YouTubeVideo object or None if no video found or API not configured
        """
        if not self.api_key:
            logger.warning("YouTube API key not configured, skipping video search")
            return None

        try:
            # Build search parameters
            params = {
                "part": "snippet",
                "q": f"{query} educational for kids",
                "type": "video",
                "maxResults": max_results,
                "safeSearch": "strict",  # Enable strict safe search
                "videoEmbeddable": "true",  # Only embeddable videos
                "videoCategoryId": "27",  # Education category
                "relevanceLanguage": "en",
                "key": self.api_key
            }

            with httpx.Client() as client:
                response = client.get(
                    f"{self.base_url}/search",
                    params=params,
                    timeout=10.0
                )

                if response.status_code != 200:
                    logger.error(f"YouTube API error: {response.status_code} - {response.text}")
                    return None

                data = response.json()

                if not data.get("items"):
                    logger.info(f"No videos found for query: {query}")
                    return None

                # Get the first video
                video_item = data["items"][0]
                video_id = video_item["id"]["videoId"]
                snippet = video_item["snippet"]

                # Get the best quality thumbnail available
                thumbnails = snippet["thumbnails"]
                thumbnail_url = (
                    thumbnails.get("high", {}).get("url") or
                    thumbnails.get("medium", {}).get("url") or
                    thumbnails.get("default", {}).get("url", "")
                )

                video = YouTubeVideo(
                    video_id=video_id,
                    title=snippet["title"],
                    thumbnail_url=thumbnail_url,
                    channel_title=snippet["channelTitle"]
                )

                logger.info(f"Found video: {video.title} ({video.url})")
                return video

        except httpx.TimeoutException:
            logger.error("YouTube API request timed out")
            return None
        except Exception as e:
            logger.error(f"Error fetching YouTube video: {str(e)}")
            return None

    def extract_search_query(self, message: str, ai_response: str) -> str:
        """
        Extract a search query from the conversation.

        Args:
            message: User's message
            ai_response: AI's response

        Returns:
            Search query string
        """
        # Use the user's message as the primary search term
        # This is a simple extraction - could be enhanced with NLP
        query = message.strip()

        # Limit query length
        if len(query) > 100:
            query = query[:100]

        return query


# Global YouTube service instance
youtube_service: Optional[YouTubeService] = None


def get_youtube_service() -> YouTubeService:
    """Get the global YouTube service instance."""
    global youtube_service
    if youtube_service is None:
        from app.config import get_settings
        settings = get_settings()
        youtube_service = YouTubeService(api_key=settings.YOUTUBE_API_KEY)
    return youtube_service


async def get_video_suggestion(message: str, ai_response: str) -> Optional[Dict[str, str]]:
    """
    Get a video suggestion for the conversation.

    Args:
        message: User's message
        ai_response: AI's response

    Returns:
        Video dictionary or None
    """
    service = get_youtube_service()
    query = service.extract_search_query(message, ai_response)
    video = await service.search_video(query)
    return video.to_dict() if video else None


def get_video_suggestion_sync(message: str, ai_response: str) -> Optional[Dict[str, str]]:
    """
    Get a video suggestion for the conversation (synchronous).

    Args:
        message: User's message
        ai_response: AI's response

    Returns:
        Video dictionary or None
    """
    service = get_youtube_service()
    query = service.extract_search_query(message, ai_response)
    video = service.search_video_sync(query)
    return video.to_dict() if video else None
