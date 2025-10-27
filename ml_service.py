import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self):
        """Initialize ML service"""
        try:
            if os.path.exists('models/blood_sugar_model.joblib'):
                self.model = joblib.load('models/blood_sugar_model.joblib')
                self.scaler = joblib.load('models/scaler.joblib')
                logger.info("ML models loaded")
            else:
                self.model = None
                self.scaler = None
                logger.warning("ML models not found, using rules")
        except Exception as e:
            logger.error(f"Error loading models: {e}")
            self.model = None
            self.scaler = None
    
    def predict_status(self, value, fasting=False, food_intake='', activity='', time_of_day=12):
        """Predict blood sugar status"""
        # Rule-based classification
        if fasting:
            if value < 70:
                status, severity = 'low', 'high'
            elif value <= 100:
                status, severity = 'normal', 'low'
            elif value <= 125:
                status, severity = 'prediabetic', 'medium'
            else:
                status, severity = 'high', 'high'
        else:
            if value < 70:
                status, severity = 'low', 'high'
            elif value <= 140:
                status, severity = 'normal', 'low'
            elif value <= 199:
                status, severity = 'prediabetic', 'medium'
            else:
                status, severity = 'high', 'high'
        
        # Generate insights
        insights = []
        if status == 'low':
            insights.append({
                'type': 'alert',
                'message': f'Blood sugar is low ({value} mg/dL). Consume 15-20g of carbs.',
                'priority': 'high'
            })
        elif status == 'high':
            insights.append({
                'type': 'alert',
                'message': f'Blood sugar is elevated ({value} mg/dL). Monitor and consult doctor.',
                'priority': 'high'
            })
        elif status == 'prediabetic':
            insights.append({
                'type': 'warning',
                'message': f'Reading is in prediabetic range ({value} mg/dL). Lifestyle changes may help.',
                'priority': 'medium'
            })
        else:
            insights.append({
                'type': 'success',
                'message': f'Blood sugar is normal ({value} mg/dL). Keep it up!',
                'priority': 'low'
            })
        
        return {
            'status': status,
            'severity': severity,
            'confidence': 0.90,
            'insights': insights
        }
    
    def generate_insights(self, readings):
        """Generate insights from readings"""
        if not readings:
            return {}
        
        df = pd.DataFrame(readings)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        avg = df['value'].mean()
        abnormal = 0
        if 'status' in df.columns:
            abnormal = len(df[df['status'].isin(['abnormal', 'borderline', 'high', 'low'])]) / len(df) * 100
        
        return {
            'summary': {
                'total_readings': len(df),
                'average_value': float(avg),
                'abnormal_percentage': float(abnormal)
            },
            'recommendations': [
                {'message': 'Test regularly', 'priority': 'medium'}
            ] if len(df) < 20 else []
        }
    
    def analyze_trends(self, readings):
        """Analyze trends"""
        if not readings or len(readings) < 2:
            return {'trend': 'insufficient_data', 'message': 'Need more data'}
        
        df = pd.DataFrame(readings)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        recent = df.tail(7)['value'].mean()
        older = df.head(7)['value'].mean()
        
        if recent > older + 5:
            return {'trend': 'increasing', 'message': 'Blood sugar trending up'}
        elif recent < older - 5:
            return {'trend': 'decreasing', 'message': 'Blood sugar trending down'}
        else:
            return {'trend': 'stable', 'message': 'Blood sugar is stable'}
    
    def identify_patterns(self, readings):
        """Identify patterns"""
        if not readings:
            return {}
        
        df = pd.DataFrame(readings)
        return {'message': 'Pattern analysis available with more data'}
    
    def generate_report(self, user_id, readings):
        """Generate report"""
        return {
            'userId': user_id,
            'generated_at': datetime.now().isoformat(),
            'insights': self.generate_insights(readings),
            'trends': self.analyze_trends(readings)
        }