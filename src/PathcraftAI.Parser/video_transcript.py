"""
Video Content Extraction Module with 3-Stage Fallback
Priority: 1 (YouTube Transcript API) -> 2 (Description) -> 3 (Whisper)

GGG always provides English subtitles, so success rate is ~99%
"""

import os
import re
from typing import Optional, Dict, Any
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
from googleapiclient.discovery import build
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from URL

    Args:
        url: YouTube video URL

    Returns:
        Video ID or None if invalid

    Examples:
        https://www.youtube.com/watch?v=VIDEO_ID -> VIDEO_ID
        https://youtu.be/VIDEO_ID -> VIDEO_ID
    """
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})',
        r'(?:youtu\.be\/)([a-zA-Z0-9_-]{11})',
        r'(?:youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None


def get_transcript_stage1(video_id: str) -> Optional[str]:
    """
    Stage 1: YouTube Transcript API (99% success rate for GGG videos)

    Args:
        video_id: YouTube video ID

    Returns:
        Transcript text or None if failed
    """
    try:
        logger.info(f"[Stage 1] Attempting YouTube Transcript API for video {video_id}")

        # Try English first (GGG always provides English subtitles)
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)

        try:
            transcript = transcript_list.find_transcript(['en'])
            transcript_data = transcript.fetch()

            # Combine all text segments
            full_text = ' '.join([entry['text'] for entry in transcript_data])

            logger.info(f"[Stage 1] ✅ SUCCESS - Transcript length: {len(full_text)} chars")
            return full_text

        except NoTranscriptFound:
            logger.warning(f"[Stage 1] ❌ No English transcript found")
            return None

    except TranscriptsDisabled:
        logger.warning(f"[Stage 1] ❌ Transcripts disabled for video {video_id}")
        return None
    except Exception as e:
        logger.error(f"[Stage 1] ❌ Error: {str(e)}")
        return None


def get_description_stage2(video_id: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Stage 2: Video Description Fallback

    Args:
        video_id: YouTube video ID
        api_key: YouTube Data API v3 key (optional, uses env var if not provided)

    Returns:
        Description text or None if failed
    """
    try:
        logger.info(f"[Stage 2] Attempting video description extraction for {video_id}")

        if not api_key:
            api_key = os.environ.get('YOUTUBE_API_KEY')

        if not api_key:
            logger.warning("[Stage 2] ❌ No YouTube API key provided")
            return None

        youtube = build('youtube', 'v3', developerKey=api_key)

        request = youtube.videos().list(
            part='snippet',
            id=video_id
        )
        response = request.execute()

        if not response.get('items'):
            logger.warning(f"[Stage 2] ❌ No video found for ID {video_id}")
            return None

        description = response['items'][0]['snippet']['description']

        logger.info(f"[Stage 2] ✅ SUCCESS - Description length: {len(description)} chars")
        return description

    except Exception as e:
        logger.error(f"[Stage 2] ❌ Error: {str(e)}")
        return None


def get_whisper_stage3(video_id: str, api_key: Optional[str] = None) -> Optional[str]:
    """
    Stage 3: OpenAI Whisper Fallback (최후의 수단, 비용 발생)

    NOTE: This requires downloading the video audio and costs ~$0.006/minute
    Only use if Stage 1 and 2 fail (extremely rare for GGG videos)

    Args:
        video_id: YouTube video ID
        api_key: OpenAI API key (optional, uses env var if not provided)

    Returns:
        Transcription text or None if failed
    """
    try:
        logger.warning(f"[Stage 3] ⚠️ EXPENSIVE FALLBACK - Whisper transcription for {video_id}")

        # TODO: Implement Whisper fallback if needed
        # Requirements:
        # 1. Download audio using yt-dlp or pytube
        # 2. Call OpenAI Whisper API
        # 3. Clean up temp files
        # 4. Cost: ~$0.006/minute (~$0.12 for 20min patch video)

        logger.warning("[Stage 3] ❌ Whisper fallback not implemented yet (rarely needed)")
        return None

    except Exception as e:
        logger.error(f"[Stage 3] ❌ Error: {str(e)}")
        return None


def extract_video_content(
    video_url: str,
    youtube_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Extract video content with 3-stage fallback strategy

    Args:
        video_url: YouTube video URL
        youtube_api_key: YouTube Data API v3 key (optional)
        openai_api_key: OpenAI API key for Whisper (optional)

    Returns:
        Dict with:
            - success: bool
            - content: str (transcript or description text)
            - method: str (stage1_transcript | stage2_description | stage3_whisper)
            - video_id: str
            - error: str (if failed)
    """
    video_id = extract_video_id(video_url)

    if not video_id:
        return {
            'success': False,
            'content': None,
            'method': None,
            'video_id': None,
            'error': 'Invalid YouTube URL'
        }

    logger.info(f"Extracting content for video: {video_id}")

    # Stage 1: YouTube Transcript API (99% success for GGG)
    content = get_transcript_stage1(video_id)
    if content:
        return {
            'success': True,
            'content': content,
            'method': 'stage1_transcript',
            'video_id': video_id,
            'error': None
        }

    # Stage 2: Video Description Fallback
    content = get_description_stage2(video_id, youtube_api_key)
    if content:
        return {
            'success': True,
            'content': content,
            'method': 'stage2_description',
            'video_id': video_id,
            'error': None
        }

    # Stage 3: Whisper Fallback (최후의 수단)
    content = get_whisper_stage3(video_id, openai_api_key)
    if content:
        return {
            'success': True,
            'content': content,
            'method': 'stage3_whisper',
            'video_id': video_id,
            'error': None
        }

    # All stages failed (extremely rare)
    logger.error(f"❌ ALL STAGES FAILED for video {video_id}")
    return {
        'success': False,
        'content': None,
        'method': None,
        'video_id': video_id,
        'error': 'All extraction methods failed'
    }


def main():
    """Test video content extraction"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python video_transcript.py <youtube_url>")
        print("Example: python video_transcript.py https://www.youtube.com/watch?v=VIDEO_ID")
        sys.exit(1)

    video_url = sys.argv[1]

    result = extract_video_content(video_url)

    print("\n" + "="*60)
    print("Video Content Extraction Result")
    print("="*60)
    print(f"Success: {result['success']}")
    print(f"Video ID: {result['video_id']}")
    print(f"Method: {result['method']}")

    if result['success']:
        content_preview = result['content'][:500] + "..." if len(result['content']) > 500 else result['content']
        print(f"\nContent Preview ({len(result['content'])} chars):")
        print(content_preview)
    else:
        print(f"Error: {result['error']}")

    print("="*60)


if __name__ == '__main__':
    main()
