from urllib.parse import urlparse, parse_qs
from typing import Optional

def get_platform_from_url(url: str) -> str:
    """Determine platform from URL"""
    if 'instagram.com' in url:
        return "Instagram"
    elif 'youtube.com' in url or 'youtu.be' in url:
        return "YouTube"
    else:
        return "Unknown"

def extract_youtube_video_id(url: str) -> Optional[str]:
    """Extract video ID from various YouTube URL formats"""
    # Handle standard youtube.com URLs
    if 'youtube.com/watch' in url:
        parsed_url = urlparse(url)
        return parse_qs(parsed_url.query).get('v', [None])[0]
    
    # Handle youtu.be shortened URLs
    elif 'youtu.be' in url:
        parsed_url = urlparse(url)
        path = parsed_url.path
        # Remove leading slash if present
        video_id = path[1:] if path.startswith('/') else path
        # Handle query parameters
        return video_id.split('?')[0]
    
    return None

def extract_instagram_shortcode(url: str) -> Optional[str]:
    """Extract shortcode from Instagram URL"""
    try:
        if '/p/' in url:
            shortcode = url.split('/p/')[-1].split('/')[0]
        elif '/reel/' in url:
            shortcode = url.split('/reel/')[-1].split('/')[0]
        else:
            shortcode = url.split('/')[-2] if url[-1] != '/' else url.split('/')[-3]
        
        # Clean up any query parameters
        return shortcode.split('?')[0]
    except Exception:
        return None