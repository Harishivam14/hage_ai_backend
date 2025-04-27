# app/services/comment_analyzer.py
from typing import List, Dict, Any, Optional
import asyncio
import concurrent.futures
from datetime import datetime

from app.services.sentiment import sentiment_analyzer
from app.services.aspect_analysis import absa_analyzer
from app.services.summarizer import comment_summarizer

class CommentAnalyzer:
    """
    Main service that orchestrates the entire comment analysis process
    """
    def __init__(self):
        self.sentiment_analyzer = sentiment_analyzer
        self.absa_analyzer = absa_analyzer
        self.comment_summarizer = comment_summarizer
    
    async def process_comments(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of comments with all analysis services
        
        Args:
            comments: List of comment dictionaries
            
        Returns:
            Dictionary with all analysis results
        """
        if not comments:
            return {
                "error": "No comments to analyze",
                "timestamp": datetime.now().isoformat()
            }
        
        start_time = datetime.now()
        
        # Extract comment texts for processing
        comment_texts = [c.get('Comment', '') for c in comments]
        
        # Run all analyses in parallel using a thread pool
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Run basic sentiment analysis on all comments
            sentiment_future = executor.submit(
                self._batch_analyze_sentiment, comment_texts
            )
            
            # Run aspect-based sentiment analysis
            absa_future = executor.submit(
                self._batch_analyze_aspects, comment_texts
            )
            
            # Wait for all tasks to complete
            sentiment_results = sentiment_future.result()
            absa_results = absa_future.result()
        
        # Combine sentiment and ABSA results with comments
        enriched_comments = []
        for i, comment in enumerate(comments):
            enriched_comment = comment.copy()
            
            # Add basic sentiment analysis
            if i < len(sentiment_results):
                sentiment, score = sentiment_results[i]
                enriched_comment['Sentiment'] = sentiment
                enriched_comment['Sentiment_Score'] = score
            
            # Add aspect-based analysis
            if i < len(absa_results):
                enriched_comment['aspects'] = absa_results[i].get('aspects', {})
            
            enriched_comments.append(enriched_comment)
        
        # Generate summaries and insights
        insights = self.comment_summarizer.generate_insight_summary(enriched_comments)
        
        # Generate aspect-specific summaries if we have enough comments
        aspect_summaries = {}
        if len(comments) >= 10:
            all_aspects = set()
            for result in absa_results:
                all_aspects.update(result.get('aspects', {}).keys())
            
            aspect_summaries = self.comment_summarizer.summarize_by_aspect(
                enriched_comments, list(all_aspects)
            )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return {
            "processed_comments": enriched_comments,
            "insights": insights,
            "aspect_summaries": aspect_summaries,
            "processing_time": processing_time,
            "comment_count": len(comments),
            "timestamp": datetime.now().isoformat()
        }
    
    def _batch_analyze_sentiment(self, texts: List[str]) -> List[Tuple]:
        """Run batch sentiment analysis"""
        return self.sentiment_analyzer.batch_analyze(texts)
    
    def _batch_analyze_aspects(self, texts: List[str]) -> List[Dict]:
        """Run batch aspect-based sentiment analysis"""
        results = []
        for text in texts:
            results.append(self.absa_analyzer.analyze_comment(text))
        return results

# Create a singleton instance
comment_analyzer = CommentAnalyzer()

async def analyze_comments(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Public API function to analyze comments
    
    Args:
        comments: List of comment dictionaries
        
    Returns:
        Analysis results dictionary
    """
    return await comment_analyzer.process_comments(comments)