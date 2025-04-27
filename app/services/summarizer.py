# app/services/summarization.py
from transformers import pipeline
import torch
from typing import List, Dict, Any, Optional
import numpy as np
from collections import Counter

class CommentSummarizer:
    def __init__(self, model_name: str = "facebook/bart-large-cnn"):
        """
        Initialize the comment summarization service
        
        Args:
            model_name: The name of the Hugging Face model to use for summarization
        """
        # Use GPU if available
        self.device = 0 if torch.cuda.is_available() else -1
        
        print(f"Loading summarization model: {model_name}")
        self.summarizer = pipeline(
            "summarization",
            model=model_name,
            device=self.device
        )
        print("Summarization model loaded successfully")
    
    def summarize_comments(self, comments: List[str], 
                          max_length: int = 150,
                          min_length: int = 30,
                          summary_count: int = 1) -> List[str]:
        """
        Generate summaries from a list of comments
        
        Args:
            comments: List of comment texts
            max_length: Maximum length of the summary in tokens
            min_length: Minimum length of the summary in tokens
            summary_count: Number of summary variants to generate
            
        Returns:
            List of generated summaries
        """
        try:
            if not comments:
                return ["No comments to summarize."]
            
            # Combine comments into a single text
            combined_text = " ".join(comments)
            
            # Handle length constraints - BART models typically have a limit of 1024 tokens
            # Simple truncation strategy - take first ~3000 chars
            max_input_chars = 3000
            if len(combined_text) > max_input_chars:
                combined_text = combined_text[:max_input_chars]
            
            # Generate summary
            summaries = self.summarizer(
                combined_text,
                max_length=max_length,
                min_length=min_length,
                num_return_sequences=summary_count
            )
            
            return [summary['summary_text'] for summary in summaries]
        except Exception as e:
            print(f"Error during summarization: {e}")
            return ["Could not generate summary due to an error."]
    
    def summarize_by_aspect(self, comments: List[Dict[str, Any]], 
                           aspects: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Summarize comments grouped by aspects
        
        Args:
            comments: List of dictionaries containing comments with aspect analysis
            aspects: Optional list of aspects to summarize (all found aspects if None)
            
        Returns:
            Dictionary mapping aspect names to summaries
        """
        try:
            # Group comments by aspect
            aspect_comments = {}
            
            for comment in comments:
                comment_text = comment.get('Comment', '')
                comment_aspects = comment.get('aspects', {})
                
                if not comment_aspects and not aspects:
                    # Add to general bucket if no aspects found
                    aspect_comments.setdefault('general', []).append(comment_text)
                    continue
                
                # Add comment to each aspect's bucket
                for aspect_name in comment_aspects:
                    if aspects and aspect_name not in aspects:
                        continue
                    aspect_comments.setdefault(aspect_name, []).append(comment_text)
            
            # Generate summaries for each aspect
            aspect_summaries = {}
            for aspect, texts in aspect_comments.items():
                if len(texts) < 3:  # Skip if too few comments
                    continue
                summaries = self.summarize_comments(texts)
                if summaries:
                    aspect_summaries[aspect] = summaries[0]
            
            return aspect_summaries
        except Exception as e:
            print(f"Error in aspect-based summarization: {e}")
            return {"error": f"Summarization failed: {str(e)}"}
    
    def generate_insight_summary(self, comments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive insights summary from comments with sentiment data
        
        Args:
            comments: List of comments with sentiment analysis
            
        Returns:
            Dictionary with various insights
        """
        try:
            if not comments:
                return {"overview": "No comments to analyze"}
            
            # Extract comment texts
            texts = [c.get('Comment', '') for c in comments]
            
            # Get sentiment counts
            sentiments = [c.get('Sentiment', 'Neutral') for c in comments]
            sentiment_counts = Counter(sentiments)
            
            # Calculate percentages
            total = len(sentiments)
            sentiment_percentages = {
                k: round(v / total * 100, 1) for k, v in sentiment_counts.items()
            }
            
            # Get top commenters
            usernames = [c.get('Username', 'Anonymous') for c in comments]
            top_commenters = Counter(usernames).most_common(5)
            
            # Generate overall summary
            overall_summary = self.summarize_comments(texts)[0]
            
            # Generate positive and negative summaries
            positive_texts = [c.get('Comment', '') for c in comments 
                             if c.get('Sentiment') == 'Positive']
            negative_texts = [c.get('Comment', '') for c in comments 
                             if c.get('Sentiment') == 'Negative']
            
            positive_summary = ""
            negative_summary = ""
            
            if positive_texts and len(positive_texts) >= 3:
                positive_summary = self.summarize_comments(positive_texts)[0]
            
            if negative_texts and len(negative_texts) >= 3:
                negative_summary = self.summarize_comments(negative_texts)[0]
            
            return {
                "overview": overall_summary,
                "positive_summary": positive_summary,
                "negative_summary": negative_summary,
                "sentiment_distribution": sentiment_percentages,
                "comment_count": total,
                "top_commenters": top_commenters
            }
        except Exception as e:
            print(f"Error generating insight summary: {e}")
            return {"error": f"Could not generate insights: {str(e)}"}

# Create a singleton instance
comment_summarizer = CommentSummarizer()

def summarize_comments(comments: List[str]) -> List[str]:
    """Compatibility function with the API"""
    return comment_summarizer.summarize_comments(comments)

def generate_insights(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compatibility function with the API for generating insights"""
    return comment_summarizer.generate_insight_summary(comments)