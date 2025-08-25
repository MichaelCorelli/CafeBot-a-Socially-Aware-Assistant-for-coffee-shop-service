# simulation/emotion_analyzer.py
import numpy as np
from collections import deque
import time
import logging
import json
from enum import Enum
from typing import Dict, List, Tuple, Optional
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

class EmotionState(Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral" 
    NEGATIVE = "negative"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    SATISFIED = "satisfied"

class EmotionAnalyzer:
    
    def __init__(self, history_size: int = 10):
        self.emotion_history = deque(maxlen=history_size)
        self.interaction_timestamps = deque(maxlen=history_size)
        self.query_history = deque(maxlen=history_size)
        self.vader = SentimentIntensityAnalyzer()
        
        #Keywords for emotion detection
        self.emotion_keywords = {
            'frustrated': ['annoying', 'frustrated', 'stupid', 'broken', 'doesn\'t work', 
                          'not working', 'useless', 'terrible', 'awful'],
            'confused': ['don\'t understand', 'confused', 'what', 'how', 'where', 
                        'lost', 'help', '?', 'explain'],
            'satisfied': ['perfect', 'great', 'thanks', 'excellent', 'good', 
                         'nice', 'wonderful', 'amazing'],
            'urgent': ['quickly', 'hurry', 'fast', 'now', 'immediately', 'urgent']
        }

        self.repetition_counter = {}
        self.topic_switches = 0
        self.last_topic = None
        self.clarification_requests = 0
        self.last_query_time = None
        self.response_times = deque(maxlen=5)

        self.current_state = {
            'primary_emotion': EmotionState.NEUTRAL,
            'secondary_emotions': [],
            'intensity': 0.5,
            'stability': 1.0,
            'engagement': 0.5
        }
        
        logging.basicConfig(level=logging.INFO)
        
    def analyze_sentiment(self, text: str) -> Tuple[str, float, float]:
        try:
            blob = TextBlob(text)
            tb_polarity = blob.sentiment.polarity
            tb_subjectivity = blob.sentiment.subjectivity
            vader_scores = self.vader.polarity_scores(text)
            vader_compound = vader_scores['compound']
            combined_polarity = 0.6 * tb_polarity + 0.4 * vader_compound
            primary_emotion = self._detect_primary_emotion(
                text, combined_polarity, tb_subjectivity
            )
            analyzer_agreement = 1 - abs(tb_polarity - vader_compound)
            confidence = min(analyzer_agreement * (1 + tb_subjectivity), 1.0)
            self._update_emotion_history(
                primary_emotion, combined_polarity, confidence, text
            )
            engagement = self._calculate_engagement(text)
            self.current_state['primary_emotion'] = primary_emotion
            self.current_state['intensity'] = abs(combined_polarity)
            self.current_state['engagement'] = engagement
            
            return primary_emotion.value, confidence, combined_polarity
            
        except Exception as e:
            logging.error(f"Sentiment analysis error: {e}")
            return EmotionState.NEUTRAL.value, 0.5, 0.0
    
    def _detect_primary_emotion(self, text: str, polarity: float, subjectivity: float) -> EmotionState:

        text_lower = text.lower()
        frustration_score = sum(
            1 for word in self.emotion_keywords['frustrated'] 
            if word in text_lower
        )
        if frustration_score >= 2 or (polarity < -0.3 and self._check_repetition(text)):
            return EmotionState.FRUSTRATED
        confusion_score = sum(
            1 for word in self.emotion_keywords['confused'] 
            if word in text_lower
        )
        if confusion_score >= 2 or text_lower.count('?') > 2:
            return EmotionState.CONFUSED
        satisfaction_score = sum(
            1 for word in self.emotion_keywords['satisfied'] 
            if word in text_lower
        )
        if satisfaction_score >= 2 and polarity > 0.5:
            return EmotionState.SATISFIED
        if polarity > 0.3:
            return EmotionState.POSITIVE
        elif polarity < -0.3:
            return EmotionState.NEGATIVE
        else:
            return EmotionState.NEUTRAL
    
    def _check_repetition(self, text: str) -> bool:
        text_normalized = text.lower().strip()
        if text_normalized in self.repetition_counter:
            self.repetition_counter[text_normalized] += 1
            return self.repetition_counter[text_normalized] > 1
        for past_query in list(self.query_history)[-3:]:
            if self._calculate_similarity(text_normalized, past_query) > 0.7:
                return True
        
        self.repetition_counter[text_normalized] = 1
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        set1 = set(text1.split())
        set2 = set(text2.split())
        
        if not set1 or not set2:
            return 0.0
        
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        return len(intersection) / len(union)
    
    def _calculate_engagement(self, text: str) -> float:
        engagement_score = 0.5
        word_count = len(text.split())
        if word_count > 10:
            engagement_score += 0.2
        elif word_count < 3:
            engagement_score -= 0.2
        
        if '?' in text:
            engagement_score += 0.1
        
        if self.last_query_time:
            time_diff = time.time() - self.last_query_time
            if time_diff < 5:
                engagement_score += 0.2
            elif time_diff > 30:
                engagement_score -= 0.1
        
        return max(0.0, min(1.0, engagement_score))
    
    def _update_emotion_history(self, emotion: EmotionState, polarity: float, confidence: float, text: str):
        current_time = time.time()
        
        self.emotion_history.append({
            'emotion': emotion,
            'polarity': polarity,
            'confidence': confidence,
            'timestamp': current_time,
            'text_sample': text[:50]
        })
        
        self.query_history.append(text.lower().strip())
        self.interaction_timestamps.append(current_time)
        if len(self.emotion_history) >= 3:
            recent_emotions = [h['emotion'] for h in list(self.emotion_history)[-3:]]
            unique_emotions = len(set(recent_emotions))
            self.current_state['stability'] = 1.0 / unique_emotions
        
        self.last_query_time = current_time
    
    def detect_frustration_patterns(self, text: str) -> float:
        frustration_score = 0.0
        current_time = time.time()
        if self.last_query_time:
            time_diff = current_time - self.last_query_time
            if time_diff < 3:
                frustration_score += 0.3
            self.response_times.append(time_diff)

        if self._check_repetition(text):
            frustration_score += 0.3
        if self.current_state['stability'] < 0.5:
            frustration_score += 0.2
        if len(self.emotion_history) >= 3:
            recent = list(self.emotion_history)[-3:]
            negative_trend = all(
                h['polarity'] < 0 and h['polarity'] < prev['polarity']
                for h, prev in zip(recent[1:], recent[:-1])
            )
            if negative_trend:
                frustration_score += 0.4
        text_lower = text.lower()
        keyword_count = sum(
            1 for word in self.emotion_keywords['frustrated']
            if word in text_lower
        )
        frustration_score += keyword_count * 0.1
        current_topic = self._extract_topic(text)
        if self.last_topic and current_topic != self.last_topic:
            self.topic_switches += 1
            if self.topic_switches > 3:
                frustration_score += 0.2
        self.last_topic = current_topic
        
        return min(frustration_score, 1.0)
    
    def _extract_topic(self, text: str) -> str:
        menu_items = ['cappuccino', 'espresso', 'tea', 'cornetto', 
                     'muffin', 'sandwich', 'water', 'juice']
        actions = ['price', 'location', 'allergen', 'order', 'menu']
        
        text_lower = text.lower()
        
        for item in menu_items:
            if item in text_lower:
                return f"menu_{item}"
        
        for action in actions:
            if action in text_lower:
                return f"action_{action}"
        
        return "general"
    
    def get_emotional_context(self) -> Dict:
        if not self.emotion_history:
            return {
                'current_emotion': EmotionState.NEUTRAL.value,
                'intensity': 0.5,
                'trend': 'stable',
                'frustration_level': 0.0,
                'confusion_level': 0.0,
                'engagement': 0.5,
                'stability': 1.0,
                'recommendations': []
            }
        
        current = self.emotion_history[-1]
        frustration_level = self.detect_frustration_patterns("")
        confusion_level = 0.0
        if self.current_state['primary_emotion'] == EmotionState.CONFUSED:
            confusion_level = 0.5
        if self.clarification_requests > 2:
            confusion_level += 0.3
        trend = self._calculate_emotional_trend()
        recommendations = self._generate_interaction_recommendations(
            frustration_level, confusion_level
        )
        
        return {
            'current_emotion': self.current_state['primary_emotion'].value,
            'intensity': self.current_state['intensity'],
            'trend': trend,
            'frustration_level': frustration_level,
            'confusion_level': min(confusion_level, 1.0),
            'engagement': self.current_state['engagement'],
            'stability': self.current_state['stability'],
            'recommendations': recommendations,
            'response_time_avg': np.mean(self.response_times) if self.response_times else 10.0
        }
    
    def _calculate_emotional_trend(self) -> str:
        if len(self.emotion_history) < 2:
            return 'stable'
        
        recent = list(self.emotion_history)[-5:]
        polarities = [h['polarity'] for h in recent]
        x = np.arange(len(polarities))
        slope = np.polyfit(x, polarities, 1)[0]
        
        if slope > 0.1:
            return 'improving'
        elif slope < -0.1:
            return 'declining'
        else:
            return 'stable'
    
    def _generate_interaction_recommendations(self, frustration: float, confusion: float) -> List[str]:

        recommendations = []
        
        if frustration > 0.7:
            recommendations.extend([
                'use_simple_language',
                'offer_human_assistance',
                'acknowledge_difficulty',
                'provide_step_by_step'
            ])
        elif frustration > 0.4:
            recommendations.extend([
                'increase_clarity',
                'check_understanding',
                'offer_alternatives'
            ])
        
        if confusion > 0.5:
            recommendations.extend([
                'provide_examples',
                'use_visual_aids',
                'break_down_complex_info'
            ])
        
        if self.current_state['engagement'] < 0.3:
            recommendations.append('increase_engagement')
        elif self.current_state['engagement'] > 0.7:
            recommendations.append('match_enthusiasm')
        
        if self.current_state['stability'] < 0.5:
            recommendations.append('maintain_consistency')
        
        return list(set(recommendations))
    
    def reset_conversation(self):
        self.emotion_history.clear()
        self.interaction_timestamps.clear()
        self.query_history.clear()
        self.repetition_counter.clear()
        self.topic_switches = 0
        self.last_topic = None
        self.clarification_requests = 0
        self.response_times.clear()
        self.current_state = {
            'primary_emotion': EmotionState.NEUTRAL,
            'secondary_emotions': [],
            'intensity': 0.5,
            'stability': 1.0,
            'engagement': 0.5
        }
        logging.info("Emotion analyzer reset for new conversation")