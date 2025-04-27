# app/services/enhanced_sentiment.py
from transformers import pipeline
import torch
from typing import Tuple, Dict, Any, List
import os

class SentimentAnalyzer:
    def __init__(self, model_name: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"):
        """
        Initialize the sentiment analyzer with the specified model
        
        Args:
            model_name: The name of the Hugging Face model to use for sentiment analysis
        """
        # Use GPU if available
        self.device = 0 if torch.cuda.is_available() else -1
        
        # Initialize the sentiment analysis pipeline
        print(f"Loading sentiment analysis model: {model_name}")
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model=model_name,
            device=self.device
        )
        print("Sentiment analysis model loaded successfully")
    
    def analyze(self, text: str) -> Tuple[str, float]:
        """
        Analyze sentiment of a text
        
        Args:
            text: The text to analyze
            
        Returns:
            Tuple of (sentiment_label, sentiment_score)
        """
        try:
            # Skip empty or very short texts
            if not text or len(text) < 3:
                return "Neutral", 0.5
            
            # Get sentiment prediction
            result = self.sentiment_analyzer(text)[0]
            
            # Extract label and score
            label = result['label']
            score = result['score']
            
            # Map model-specific labels to standard Positive/Negative/Neutral
            if 'POSITIVE' in label or 'POS' in label:
                sentiment = "Positive"
            elif 'NEGATIVE' in label or 'NEG' in label:
                sentiment = "Negative"
            else:
                sentiment = "Neutral"
                
            return sentiment, score
        except Exception as e:
            print(f"Error analyzing sentiment: {e}")
            return "Neutral", 0.5
    
    def batch_analyze(self, texts: List[str]) -> List[Tuple[str, float]]:
        """
        Analyze sentiment for a batch of texts
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of tuples (sentiment_label, sentiment_score)
        """
        try:
            # Filter out empty texts
            valid_texts = [t for t in texts if t and len(t) >= 3]
            if not valid_texts:
                return [("Neutral", 0.5) for _ in texts]
            
            # Get batch predictions
            results = self.sentiment_analyzer(valid_texts)
            
            # Map results
            sentiments = []
            result_index = 0
            
            for text in texts:
                if not text or len(text) < 3:
                    sentiments.append(("Neutral", 0.5))
                else:
                    result = results[result_index]
                    result_index += 1
                    
                    label = result['label']
                    score = result['score']
                    
                    if 'POSITIVE' in label or 'POS' in label:
                        sentiment = "Positive"
                    elif 'NEGATIVE' in label or 'NEG' in label:
                        sentiment = "Negative"
                    else:
                        sentiment = "Neutral"
                    
                    sentiments.append((sentiment, score))
            
            return sentiments
        except Exception as e:
            print(f"Error in batch sentiment analysis: {e}")
            return [("Neutral", 0.5) for _ in texts]

# Create a singleton instance
sentiment_analyzer = SentimentAnalyzer()

def analyze_sentiment(text: str) -> Tuple[str, float]:
    """
    Compatibility function with the original API
    """
    return sentiment_analyzer.analyze(text)