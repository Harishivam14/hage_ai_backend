import requests
import os
from typing import List, Dict, Any, Tuple

from app.utils.url_parser import extract_youtube_video_id

# Get API key from environment variable or use default
API_KEY = os.environ.get('YOUTUBE_API_KEY', 'YOUR_YOUTUBE_API_KEY')

async def extract_data(video_url: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Extract comments and metadata from YouTube video"""
    video_id = extract_youtube_video_id(video_url)
    
    if not video_id:
        return [], {'Platform': 'YouTube', 'Error': 'Invalid YouTube URL format'}
    
    # Get video metadata
    video_info_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&id={video_id}&key={API_KEY}"
    try:
        video_response = requests.get(video_info_url)
        video_data = video_response.json()
        
        if 'items' in video_data and len(video_data['items']) > 0:
            snippet = video_data['items'][0]['snippet']
            statistics = video_data['items'][0]['statistics']
            
            video_metadata = {
                'Platform': 'YouTube',
                'Video ID': video_id,
                'Title': snippet['title'],
                'Description': snippet['description'],
                'Published At': snippet['publishedAt'],
                'Channel': snippet['channelTitle'],
                'View Count': statistics.get('viewCount', 'N/A'),
                'Like Count': statistics.get('likeCount', 'N/A'),
                'Comment Count': statistics.get('commentCount', 'N/A'),
                'Tags': ', '.join(snippet.get('tags', [])) if 'tags' in snippet else 'No tags'
            }
        else:
            video_metadata = {
                'Platform': 'YouTube',
                'Video ID': video_id,
                'Error': 'Could not retrieve video metadata'
            }
        
        comments = []
        next_page_token = None

        while True:
            url = f"https://www.googleapis.com/youtube/v3/commentThreads?part=snippet,replies&videoId={video_id}&key={API_KEY}&maxResults=100"
            if next_page_token:
                url += f"&pageToken={next_page_token}"

            response = requests.get(url)
            data = response.json()

            if 'items' not in data:
                if 'error' in data:
                    print(f"API Error: {data['error']['message']}")
                break

            for item in data['items']:
                # Process top-level comment
                comment_snippet = item['snippet']['topLevelComment']['snippet']
                text = ' '.join(comment_snippet['textDisplay'].splitlines())
                comment_id = item['snippet']['topLevelComment']['id']

                comments.append({
                    'Username': comment_snippet['authorDisplayName'],
                    'Comment': text,
                    'Platform': 'YouTube',
                    'Likes': comment_snippet['likeCount'],
                    'CommentId': comment_id,
                    'IsReply': False,
                    'Timestamp': comment_snippet['publishedAt']
                })
                
                # Process replies if any
                if 'replies' in item and 'comments' in item['replies']:
                    for reply in item['replies']['comments']:
                        reply_snippet = reply['snippet']
                        reply_text = ' '.join(reply_snippet['textDisplay'].splitlines())
                        
                        comments.append({
                            'Username': reply_snippet['authorDisplayName'],
                            'Comment': reply_text,
                            'Platform': 'YouTube',
                            'Likes': reply_snippet['likeCount'],
                            'CommentId': reply['id'],
                            'ParentId': comment_id,
                            'IsReply': True,
                            'Timestamp': reply_snippet['publishedAt']
                        })

            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break

        return comments, video_metadata
        
    except Exception as e:
        return [], {'Platform': 'YouTube', 'Video ID': video_id, 'Error': str(e)}