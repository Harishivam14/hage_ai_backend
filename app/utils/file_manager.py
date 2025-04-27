import os
import csv
from datetime import datetime
from typing import List, Dict, Any
from collections import Counter

from app.services.sentiment import analyze_sentiment

# Output directory
OUTPUT_DIR = "output"

def save_output_files(request_id: str, comments: List[Dict[str, Any]], 
                     metadata: Dict[str, Any], platform: str) -> Dict[str, str]:
    """Save comments and metadata to files and return file URLs"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    short_platform = 'insta' if platform == 'Instagram' else 'yt'
    
    # Create unique folder for this response
    response_folder = f"{short_platform}_{request_id}_{timestamp}"
    response_dir = os.path.join(OUTPUT_DIR, response_folder)
    os.makedirs(response_dir, exist_ok=True)
    
    comments_csv = "comments.csv"
    sentiment_csv = "sentiment.csv"
    metadata_txt = "metadata.txt"
    
    comments_path = os.path.join(response_dir, comments_csv)
    sentiment_path = os.path.join(response_dir, sentiment_csv)
    metadata_path = os.path.join(response_dir, metadata_txt)
    
    # Calculate sentiment metrics
    sentiments = []
    for comment in comments:
        sentiment, score = analyze_sentiment(comment['Comment'])
        sentiments.append(sentiment)
        comment['Sentiment'] = sentiment
        comment['Sentiment_Score'] = score
    
    # Get sentiment report
    sentiment_counts = Counter(sentiments)
    total_comments = len(comments)
    sentiment_report = {
        'Total Comments': total_comments,
        'Positive': f"{sentiment_counts.get('Positive', 0)} ({sentiment_counts.get('Positive', 0)/total_comments*100:.1f}%)" if total_comments > 0 else "0 (0%)",
        'Neutral': f"{sentiment_counts.get('Neutral', 0)} ({sentiment_counts.get('Neutral', 0)/total_comments*100:.1f}%)" if total_comments > 0 else "0 (0%)",
        'Negative': f"{sentiment_counts.get('Negative', 0)} ({sentiment_counts.get('Negative', 0)/total_comments*100:.1f}%)" if total_comments > 0 else "0 (0%)"
    }
    
    # Get top commenters
    if comments:
        commenters = Counter([comment.get('Username', 'Anonymous') for comment in comments])
        top_commenters = commenters.most_common(5)
        top_commenters_list = [f"{username} ({count})" for username, count in top_commenters]
    else:
        top_commenters_list = []

    # First CSV: comments with specified columns in the requested order
    with open(comments_path, 'w', newline='', encoding='utf-8') as file:
        fieldnames = ['Username', 'Comment', 'Comment ID', 'Platform', 'Likes', 'Is Reply', 'Parent Comment ID']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        for comment in comments:
            writer.writerow({
                'Username': comment.get('Username', 'Anonymous'),
                'Comment': comment['Comment'],
                'Comment ID': comment.get('CommentId', ''),
                'Platform': comment['Platform'],
                'Likes': comment.get('Likes', 0),
                'Is Reply': 'Yes' if comment.get('IsReply', False) else 'No',
                'Parent Comment ID': comment.get('ParentId', '') if comment.get('IsReply', False) else 'Null'
            })

    # Second CSV: sentiment analysis data
    with open(sentiment_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=['Comment', 'Sentiment', 'Sentiment Score'])
        writer.writeheader()
        for comment in comments:
            writer.writerow({
                'Comment': comment['Comment'],
                'Sentiment': comment.get('Sentiment', 'Neutral'),
                'Sentiment Score': comment.get('Sentiment_Score', 0.0)
            })

    # Text file with metadata, sentiment report and top commenters
    with open(metadata_path, 'w', encoding='utf-8') as file:
        file.write(f"Metadata for {platform} content:\n")
        file.write('='*50 + '\n')
        for key, value in metadata.items():
            file.write(f"{key}: {value}\n")
        
        file.write('\nSentiment Analysis Report:\n')
        file.write('='*50 + '\n')
        for key, value in sentiment_report.items():
            file.write(f"{key}: {value}\n")
        
        if top_commenters_list:
            file.write('\nTop Commenters:\n')
            file.write('='*50 + '\n')
            for i, commenter in enumerate(top_commenters_list, 1):
                file.write(f"{i}. {commenter}\n")
    
    # Create URLs for the files
    base_url = f"/api/files/{response_folder}"
    return {
        "comments_csv": f"{base_url}/{comments_csv}",
        "sentiment_csv": f"{base_url}/{sentiment_csv}",
        "metadata_txt": f"{base_url}/{metadata_txt}",
        "folder": response_folder
    }