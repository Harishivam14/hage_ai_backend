# app/services/absa.py
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import torch
from typing import List, Dict, Any, Tuple
import re

class AspectBasedSentimentAnalyzer:
    def __init__(self, model_name: str = "yangheng/deberta-v3-base-absa-v1.1"):
        """
        Initialize the Aspect-Based Sentiment Analysis (ABSA) service
        
        Args:
            model_name: The name of the Hugging Face model to use for ABSA
        """
        # Use GPU if available
        self.device = 0 if torch.cuda.is_available() else -1
        
        print(f"Loading ABSA model: {model_name}")
        # For ABSA, we'll need a more specialized pipeline setup
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        
        # Move model to the appropriate device
        if self.device >= 0:
            self.model = self.model.to(self.device)
        
        # Define aspect categories for social media comments
        self.aspects = [
            "content", "quality", "presenter", "visuals", "audio", 
            "length", "editing", "information", "entertainment", "product",
            "service", "responsiveness", "value", "shipping", "usability"
        ]
        print("ABSA model loaded successfully")
    
    def extract_aspects(self, text: str) -> List[str]:
        """
        Extract mentioned aspects from text
        
        Args:
            text: Input comment text
            
        Returns:
            List of aspects found in the text
        """
        # Simple keyword-based aspect extraction
        found_aspects = []
        text_lower = text.lower()
        
        for aspect in self.aspects:
            # Check if aspect or related terms are in the text
            if aspect in text_lower or self._get_aspect_synonyms(aspect, text_lower):
                found_aspects.append(aspect)
        
        return found_aspects
    
    def _get_aspect_synonyms(self, aspect: str, text: str) -> bool:
        """Check for synonyms of aspects in the text"""
        synonyms = {
            "content": ["material", "subject", "topic", "substance"],
            "quality": ["resolution", "hd", "4k", "clarity"],
            "presenter": ["speaker", "host", "creator", "youtuber", "influencer"],
            "visuals": ["graphics", "visual", "picture", "image", "scene"],
            "audio": ["sound", "music", "voice", "volume", "mic"],
            "length": ["duration", "time", "short", "long"],
            "editing": ["cuts", "transitions", "effects", "post-production"],
            "information": ["info", "educational", "informative", "facts"],
            "entertainment": ["funny", "enjoyable", "entertaining", "fun", "humor"],
            "product": ["item", "device", "thing", "stuff", "merchandise"],
            "service": ["customer service", "support", "help", "assistance"],
        }
        
        if aspect in synonyms:
            return any(syn in text for syn in synonyms[aspect])
        return False
    
    def analyze_aspect_sentiment(self, text: str, aspect: str) -> Tuple[str, float]:
        """
        Analyze sentiment for a specific aspect
        
        Args:
            text: The comment text
            aspect: The aspect to analyze
            
        Returns:
            Tuple of (sentiment_label, confidence_score)
        """
        try:
            # Format input for aspect-based sentiment analysis
            input_text = f"{text} [SEP] {aspect}"
            
            # Tokenize input
            inputs = self.tokenizer(input_text, return_tensors="pt", truncation=True, max_length=512)
            if self.device >= 0:
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Get model outputs
            with torch.no_grad():
                outputs = self.model(**inputs)
                predictions = torch.softmax(outputs.logits, dim=1)
                
            # Extract results (most ABSA models use 3 classes: negative, neutral, positive)
            sentiment_score = predictions.detach().cpu().numpy()[0]
            
            # Map to sentiment label
            sentiment_id = sentiment_score.argmax()
            if sentiment_id == 0:
                sentiment = "Negative"
                score = sentiment_score[0]
            elif sentiment_id == 1:
                sentiment = "Neutral"
                score = sentiment_score[1]
            else:
                sentiment = "Positive"
                score = sentiment_score[2]
            
            return sentiment, float(score)
        except Exception as e:
            print(f"Error in aspect sentiment analysis: {e}")
            return "Neutral", 0.5
    
    def analyze_comment(self, text: str) -> Dict[str, Any]:
        """
        Perform full aspect-based sentiment analysis on a comment
        
        Args:
            text: Comment text to analyze
            
        Returns:
            Dictionary with aspects and their sentiments
        """
        results = {
            "overall_sentiment": None,
            "aspects": {}
        }
        
        # Find aspects in the text
        found_aspects = self.extract_aspects(text)
        
        # If no aspects found, add "general" aspect
        if not found_aspects:
            found_aspects = ["general"]
        
        # Analyze sentiment for each aspect
        for aspect in found_aspects:
            sentiment, score = self.analyze_aspect_sentiment(text, aspect)
            results["aspects"][aspect] = {
                "sentiment": sentiment,
                "score": score
            }
        
        # Calculate overall sentiment based on aspect sentiments
        if results["aspects"]:
            positive_count = sum(1 for a in results["aspects"].values() if a["sentiment"] == "Positive")
            negative_count = sum(1 for a in results["aspects"].values() if a["sentiment"] == "Negative")
            
            if positive_count > negative_count:
                results["overall_sentiment"] = "Positive"
            elif negative_count > positive_count:
                results["overall_sentiment"] = "Negative"
            else:
                results["overall_sentiment"] = "Neutral"
        
        return results

# Create a singleton instance
absa_analyzer = AspectBasedSentimentAnalyzer()

def analyze_comment_aspects(text: str) -> Dict[str, Any]:
    """
    Compatibility function with the API
    """
    return absa_analyzer.analyze_comment(text)