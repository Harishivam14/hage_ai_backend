import instaloader
import requests
from typing import List, Dict, Any, Tuple
import os
import time

from app.utils.url_parser import extract_instagram_shortcode

# Get access token from environment variables
ACCESS_TOKEN = os.environ.get('INSTAGRAM_ACCESS_TOKEN', 'YOUR_INSTAGRAM_ACCESS_TOKEN')
APP_ID = os.environ.get('INSTAGRAM_APP_ID', 'YOUR_INSTAGRAM_APP_ID')

# Get Instagram username and password from environment variables
INSTAGRAM_USERNAME = os.environ.get('INSTAGRAM_USERNAME', '')
INSTAGRAM_PASSWORD = os.environ.get('INSTAGRAM_PASSWORD', '')

async def extract_metadata(post_url: str) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Extract metadata and comments from Instagram post"""
    try:
        shortcode = extract_instagram_shortcode(post_url)
        if not shortcode:
            return [], {"error": "Could not extract Instagram shortcode from URL"}
        
        # First use instaloader to get basic post metadata
        L = instaloader.Instaloader()
        post = instaloader.Post.from_shortcode(L.context, shortcode)
        
        # Extract post metadata
        post_metadata = {
            'Platform': 'Instagram',
            'Post ID': post.shortcode,
            'Media ID': post.mediaid,
            'Caption': post.caption if post.caption else 'No caption',
            'Posted Date': post.date_local.strftime('%Y-%m-%d %H:%M:%S'),
            'Likes': post.likes,
            'Owner': post.owner_username,
            'Owner ID': post.owner_id,
            'Is Video': post.is_video,
            'View Count': post.video_view_count if post.is_video else 'N/A',
            'Location': post.location.name if post.location and post.location.name else 'No location',
            'Hashtags': ', '.join(post.caption_hashtags) if post.caption_hashtags else 'No hashtags'
        }
        
        # First try using access token
        comments = await fetch_comments_with_token(post.mediaid)
        
        # If no comments or error, try with username and password
        if not comments and INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD:
            comments = await fetch_comments_with_login(L, post)
            post_metadata['Auth Method'] = 'Username/Password Login'
        else:
            post_metadata['Auth Method'] = 'Access Token'
        
        return comments, post_metadata
        
    except Exception as e:
        return [], {'Platform': 'Instagram', 'Error': str(e)}

async def fetch_comments_with_token(media_id: str) -> List[Dict[str, Any]]:
    """Fetch comments using Instagram Graph API with access token"""
    comments = []
    
    try:
        # Use Instagram Graph API to get comments
        url = f"https://graph.facebook.com/v19.0/{media_id}/comments"
        params = {
            "access_token": ACCESS_TOKEN,
            "fields": "text,username,timestamp,like_count,id,replies{text,username,timestamp,like_count,id}"
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'data' in data:
            for comment in data['data']:
                # Add main comment
                comment_data = {
                    'Comment': comment.get('text', ''),
                    'Username': comment.get('username', 'Anonymous'),
                    'Platform': 'Instagram',
                    'Likes': comment.get('like_count', 0),
                    'CommentId': comment.get('id', ''),
                    'Timestamp': comment.get('timestamp', ''),
                    'IsReply': False
                }
                comments.append(comment_data)
                
                # Add replies if any
                if 'replies' in comment and 'data' in comment['replies']:
                    for reply in comment['replies']['data']:
                        reply_data = {
                            'Comment': reply.get('text', ''),
                            'Username': reply.get('username', 'Anonymous'),
                            'Platform': 'Instagram',
                            'Likes': reply.get('like_count', 0),
                            'CommentId': reply.get('id', ''),
                            'ParentId': comment.get('id', ''),
                            'Timestamp': reply.get('timestamp', ''),
                            'IsReply': True
                        }
                        comments.append(reply_data)
                
        return comments
    except Exception as e:
        print(f"Error fetching Instagram comments with token: {e}")
        return []

async def fetch_comments_with_login(L: instaloader.Instaloader, post: instaloader.Post) -> List[Dict[str, Any]]:
    """Fetch comments using username and password login"""
    comments = []
    
    try:
        # Login to Instagram
        print(f"Trying to login with username {INSTAGRAM_USERNAME}")
        L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        print("Login successful")
        
        # Sleep to avoid rate limiting after login
        time.sleep(2)
        
        # Fetch comments
        for comment in post.get_comments():
            comment_data = {
                'Comment': comment.text,
                'Username': comment.owner.username,
                'Platform': 'Instagram',
                'Likes': 0,  # Instaloader doesn't provide like count for comments
                'CommentId': str(comment.id),
                'Timestamp': comment.created_at_utc.strftime('%Y-%m-%d %H:%M:%S'),
                'IsReply': False
            }
            comments.append(comment_data)
            
            # Fetch replies
            try:
                for answer in comment.answers:
                    reply_data = {
                        'Comment': answer.text,
                        'Username': answer.owner.username,
                        'Platform': 'Instagram',
                        'Likes': 0,  # Instaloader doesn't provide like count for replies
                        'CommentId': str(answer.id),
                        'ParentId': str(comment.id),
                        'Timestamp': answer.created_at_utc.strftime('%Y-%m-%d %H:%M:%S'),
                        'IsReply': True
                    }
                    comments.append(reply_data)
            except Exception as e:
                print(f"Error fetching replies for comment {comment.id}: {e}")
                
            # Throttle to avoid rate limits
            time.sleep(0.5)
                
        return comments
    except Exception as e:
        print(f"Error fetching Instagram comments with login: {e}")
        return []