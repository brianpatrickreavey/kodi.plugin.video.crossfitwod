import re
import xbmcaddon # type: ignore

def extract_video_id(url):
    """
    Extract the YouTube video ID from a URL.
    """
    patterns = [
        r'(?:v=|\/embed\/|\/v\/|youtu\.be\/|\/shorts\/)([A-Za-z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return url  # fallback: return the original URL if not matched

def is_youtube_plugin_installed():
    try:
        xbmcaddon.Addon('plugin.video.youtube')
        return True
    except Exception:
        return False