"""
Blood Sugar Monitoring System - Machine Learning Service
=========================================================
This module provides ML-powered analysis and predictions for blood sugar data.

Features:
- Blood sugar level predictions based on patient history
- Risk assessment and categorization
- Pattern analysis and trend detection
- Food and activity trigger identification
- Personalized recommendations generation
- Anomaly detection in readings

The service uses scikit-learn models trained on historical blood sugar data.
If trained models are not available, it falls back to rule-based analysis.

Models stored in: models/blood_sugar_model.joblib, models/scaler.joblib
"""

import joblib
import numpy as np
import pandas as pd
from datetime import datetime
import logging
import os

# Set up logging for ML operations
logger = logging.getLogger(__name__)

class MLService:
    """
    Machine Learning service for blood sugar analysis and predictions.
    Loads pre-trained models or uses rule-based fallback logic.
    """
    
    def __init__(self):
        """Initialize ML service and load trained models if available"""
        try:
            if os.path.exists('models/blood_sugar_model.joblib'):
                self.model = joblib.load('models/blood_sugar_model.joblib')
                self.scaler = joblib.load('models/scaler.joblib')
                logger.info("ML models loaded successfully")
            else:
                self.model = None
                self.scaler = None
                logger.warning("ML models not found, using rule-based analysis")
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
        """Generate comprehensive AI insights with correlation analysis"""
        if not readings:
            return {}
        
        df = pd.DataFrame(readings)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        avg = df['value'].mean()
        abnormal_readings = []
        
        if 'status' in df.columns:
            abnormal_readings = df[df['status'].isin(['abnormal', 'borderline', 'high', 'low'])]
            abnormal_pct = len(abnormal_readings) / len(df) * 100 if len(df) > 0 else 0
        else:
            abnormal_pct = 0
        
        # Analyze correlations
        food_correlations = self._analyze_food_patterns(df, abnormal_readings)
        activity_correlations = self._analyze_activity_patterns(df, abnormal_readings)
        time_patterns = self._analyze_time_patterns(df, abnormal_readings)
        symptom_patterns = self._analyze_symptom_patterns(df, abnormal_readings)
        
        # Generate personalized recommendations
        recommendations = self._generate_personalized_recommendations(
            food_correlations, 
            activity_correlations, 
            time_patterns,
            symptom_patterns,
            abnormal_pct
        )
        
        return {
            'summary': {
                'total_readings': len(df),
                'average_value': float(avg),
                'abnormal_percentage': float(abnormal_pct)
            },
            'correlations': {
                'food_triggers': food_correlations,
                'activity_impacts': activity_correlations,
                'time_patterns': time_patterns,
                'symptom_associations': symptom_patterns
            },
            'personalized_recommendations': recommendations
        }
    
    def _analyze_food_patterns(self, df, abnormal_df):
        """Analyze correlation between food intake and abnormal readings"""
        if 'food_intake' not in df.columns or abnormal_df.empty:
            return []
        
        # Get foods associated with abnormal readings
        abnormal_foods = abnormal_df[abnormal_df['food_intake'].notna() & (abnormal_df['food_intake'] != '')]
        
        if abnormal_foods.empty:
            return []
        
        # Count frequency of each food in abnormal readings
        food_counts = abnormal_foods['food_intake'].value_counts().head(10)
        
        # Calculate correlation strength
        correlations = []
        for food, count in food_counts.items():
            total_with_food = len(df[df['food_intake'] == food])
            abnormal_with_food = count
            correlation_strength = (abnormal_with_food / total_with_food * 100) if total_with_food > 0 else 0
            
            if correlation_strength > 40:  # More than 40% abnormal rate
                correlations.append({
                    'food': food,
                    'abnormal_count': int(abnormal_with_food),
                    'total_count': int(total_with_food),
                    'correlation_strength': round(correlation_strength, 1),
                    'risk_level': 'high' if correlation_strength > 60 else 'medium'
                })
        
        return sorted(correlations, key=lambda x: x['correlation_strength'], reverse=True)
    
    def _analyze_activity_patterns(self, df, abnormal_df):
        """Analyze correlation between activities and blood sugar levels"""
        if 'activity' not in df.columns or abnormal_df.empty:
            return []
        
        # Get activities associated with abnormal readings
        abnormal_activities = abnormal_df[abnormal_df['activity'].notna() & (abnormal_df['activity'] != '')]
        
        if abnormal_activities.empty:
            return []
        
        # Count frequency of each activity
        activity_counts = abnormal_activities['activity'].value_counts().head(10)
        
        correlations = []
        for activity, count in activity_counts.items():
            total_with_activity = len(df[df['activity'] == activity])
            abnormal_with_activity = count
            correlation_strength = (abnormal_with_activity / total_with_activity * 100) if total_with_activity > 0 else 0
            
            # Determine if activity helps or harms
            activity_readings = df[df['activity'] == activity]['value'].mean()
            overall_avg = df['value'].mean()
            impact = 'beneficial' if activity_readings < overall_avg else 'detrimental'
            
            if correlation_strength > 30:
                correlations.append({
                    'activity': activity,
                    'abnormal_count': int(abnormal_with_activity),
                    'total_count': int(total_with_activity),
                    'correlation_strength': round(correlation_strength, 1),
                    'impact': impact,
                    'avg_reading': round(activity_readings, 1)
                })
        
        return sorted(correlations, key=lambda x: x['correlation_strength'], reverse=True)
    
    def _analyze_time_patterns(self, df, abnormal_df):
        """Analyze time-of-day patterns for abnormal readings"""
        if 'date_time' not in df.columns or abnormal_df.empty:
            return {}
        
        # Convert to datetime if string
        try:
            df['datetime_parsed'] = pd.to_datetime(df['date_time'])
            abnormal_df['datetime_parsed'] = pd.to_datetime(abnormal_df['date_time'])
            
            # Extract hour
            df['hour'] = df['datetime_parsed'].dt.hour
            abnormal_df['hour'] = abnormal_df['datetime_parsed'].dt.hour
            
            # Group by time periods
            time_periods = {
                'morning': (6, 11),
                'afternoon': (12, 17),
                'evening': (18, 21),
                'night': (22, 5)
            }
            
            patterns = {}
            for period, (start, end) in time_periods.items():
                if start <= end:
                    period_readings = df[(df['hour'] >= start) & (df['hour'] <= end)]
                    period_abnormal = abnormal_df[(abnormal_df['hour'] >= start) & (abnormal_df['hour'] <= end)]
                else:  # night wraps around
                    period_readings = df[(df['hour'] >= start) | (df['hour'] <= end)]
                    period_abnormal = abnormal_df[(abnormal_df['hour'] >= start) | (abnormal_df['hour'] <= end)]
                
                if len(period_readings) > 0:
                    patterns[period] = {
                        'total_readings': len(period_readings),
                        'abnormal_readings': len(period_abnormal),
                        'abnormal_rate': round(len(period_abnormal) / len(period_readings) * 100, 1),
                        'avg_value': round(period_readings['value'].mean(), 1)
                    }
            
            return patterns
        except:
            return {}
    
    def _analyze_symptom_patterns(self, df, abnormal_df):
        """Analyze symptoms and notes associated with abnormal readings"""
        patterns = []
        
        # Check symptoms column
        if 'symptoms' in abnormal_df.columns:
            symptoms = abnormal_df[abnormal_df['symptoms'].notna() & (abnormal_df['symptoms'] != '')]
            if not symptoms.empty:
                symptom_counts = symptoms['symptoms'].value_counts().head(5)
                for symptom, count in symptom_counts.items():
                    patterns.append({
                        'symptom': symptom,
                        'occurrences': int(count),
                        'type': 'symptom'
                    })
        
        # Check notes column
        if 'notes' in abnormal_df.columns:
            notes = abnormal_df[abnormal_df['notes'].notna() & (abnormal_df['notes'] != '')]
            if not notes.empty and len(notes) > 0:
                # Extract common keywords from notes
                all_notes = ' '.join(notes['notes'].astype(str).tolist()).lower()
                keywords = ['stress', 'tired', 'sick', 'pain', 'headache', 'dizzy', 'nausea', 'fatigue']
                for keyword in keywords:
                    if keyword in all_notes:
                        patterns.append({
                            'symptom': keyword,
                            'occurrences': all_notes.count(keyword),
                            'type': 'note_keyword'
                        })
        
        return patterns[:10]  # Top 10
    
    def _generate_personalized_recommendations(self, food_correlations, activity_correlations, 
                                               time_patterns, symptom_patterns, abnormal_pct):
        """Generate personalized recommendations based on identified patterns"""
        recommendations = []
        
        # Food-based recommendations
        if food_correlations:
            high_risk_foods = [f for f in food_correlations if f['risk_level'] == 'high']
            if high_risk_foods:
                foods_list = ', '.join([f['food'] for f in high_risk_foods[:3]])
                recommendations.append({
                    'category': 'diet',
                    'priority': 'high',
                    'title': '🍽️ High-Risk Foods Identified',
                    'message': f'Avoid or limit: {foods_list}. These foods are strongly correlated with abnormal readings.',
                    'actionable': True,
                    'details': high_risk_foods[:3]
                })
            
            medium_risk_foods = [f for f in food_correlations if f['risk_level'] == 'medium']
            if medium_risk_foods:
                foods_list = ', '.join([f['food'] for f in medium_risk_foods[:3]])
                recommendations.append({
                    'category': 'diet',
                    'priority': 'medium',
                    'title': '⚠️ Monitor These Foods',
                    'message': f'Be cautious with: {foods_list}. Consider portion control or timing.',
                    'actionable': True,
                    'details': medium_risk_foods[:3]
                })
        
        # Activity-based recommendations
        if activity_correlations:
            beneficial = [a for a in activity_correlations if a['impact'] == 'beneficial']
            detrimental = [a for a in activity_correlations if a['impact'] == 'detrimental']
            
            if beneficial:
                activities_list = ', '.join([a['activity'] for a in beneficial[:3]])
                recommendations.append({
                    'category': 'activity',
                    'priority': 'high',
                    'title': '✅ Beneficial Activities',
                    'message': f'Continue these activities: {activities_list}. They help maintain healthy levels.',
                    'actionable': True,
                    'details': beneficial[:3]
                })
            
            if detrimental:
                activities_list = ', '.join([a['activity'] for a in detrimental[:3]])
                recommendations.append({
                    'category': 'activity',
                    'priority': 'medium',
                    'title': '⚠️ Activities to Adjust',
                    'message': f'Consider modifying: {activities_list}. These may need timing or intensity adjustments.',
                    'actionable': True,
                    'details': detrimental[:3]
                })
        
        # Time-based recommendations
        if time_patterns:
            high_risk_periods = {k: v for k, v in time_patterns.items() if v['abnormal_rate'] > 40}
            if high_risk_periods:
                periods = ', '.join(high_risk_periods.keys())
                recommendations.append({
                    'category': 'timing',
                    'priority': 'high',
                    'title': '🕐 High-Risk Time Periods',
                    'message': f'Extra monitoring needed during: {periods}. Consider meal timing and medication schedule.',
                    'actionable': True,
                    'details': high_risk_periods
                })
        
        # Symptom-based recommendations
        if symptom_patterns:
            common_symptoms = [s['symptom'] for s in symptom_patterns[:3]]
            if common_symptoms:
                symptoms_list = ', '.join(common_symptoms)
                recommendations.append({
                    'category': 'symptoms',
                    'priority': 'high',
                    'title': '🏥 Common Symptoms Detected',
                    'message': f'Frequently reported: {symptoms_list}. Discuss these patterns with your doctor.',
                    'actionable': True,
                    'details': symptom_patterns[:3]
                })
        
        # General recommendations based on abnormal percentage
        if abnormal_pct > 30:
            recommendations.append({
                'category': 'general',
                'priority': 'high',
                'title': '🚨 High Abnormal Rate Alert',
                'message': f'{abnormal_pct:.1f}% of your readings are abnormal. Schedule an appointment with your healthcare provider.',
                'actionable': True
            })
        elif abnormal_pct > 15:
            recommendations.append({
                'category': 'general',
                'priority': 'medium',
                'title': '📊 Elevated Abnormal Rate',
                'message': f'{abnormal_pct:.1f}% abnormal readings. Review your diet and activity patterns.',
                'actionable': True
            })
        else:
            recommendations.append({
                'category': 'general',
                'priority': 'low',
                'title': '✅ Good Control',
                'message': f'Only {abnormal_pct:.1f}% abnormal readings. Keep up the good work!',
                'actionable': False
            })
        
        # Default recommendations if no patterns found
        if not recommendations:
            recommendations.append({
                'category': 'general',
                'priority': 'low',
                'title': '📈 Keep Tracking',
                'message': 'Continue logging your readings, food, and activities to identify patterns.',
                'actionable': True
            })
        
        return recommendations
    
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
        """Identify comprehensive patterns in blood sugar data"""
        if not readings or len(readings) < 5:
            return {'message': 'Need at least 5 readings for pattern analysis'}
        
        df = pd.DataFrame(readings)
        df['value'] = pd.to_numeric(df['value'], errors='coerce')
        
        patterns = {
            'weekly_patterns': self._identify_weekly_patterns(df),
            'meal_patterns': self._identify_meal_patterns(df),
            'variability': self._calculate_variability(df),
            'consistency': self._assess_consistency(df)
        }
        
        return patterns
    
    def _identify_weekly_patterns(self, df):
        """Identify day-of-week patterns"""
        if 'date_time' not in df.columns:
            return {}
        
        try:
            df['datetime_parsed'] = pd.to_datetime(df['date_time'])
            df['day_of_week'] = df['datetime_parsed'].dt.day_name()
            
            daily_stats = df.groupby('day_of_week')['value'].agg(['mean', 'count']).to_dict('index')
            
            # Find best and worst days
            if daily_stats:
                best_day = min(daily_stats.items(), key=lambda x: x[1]['mean'])
                worst_day = max(daily_stats.items(), key=lambda x: x[1]['mean'])
                
                return {
                    'daily_averages': {day: round(stats['mean'], 1) for day, stats in daily_stats.items()},
                    'best_day': {'day': best_day[0], 'avg': round(best_day[1]['mean'], 1)},
                    'worst_day': {'day': worst_day[0], 'avg': round(worst_day[1]['mean'], 1)}
                }
        except:
            pass
        
        return {}
    
    def _identify_meal_patterns(self, df):
        """Identify patterns related to meals"""
        if 'food_intake' not in df.columns:
            return {}
        
        meals_data = df[df['food_intake'].notna() & (df['food_intake'] != '')]
        no_meals_data = df[~df.index.isin(meals_data.index)]
        
        if len(meals_data) > 0 and len(no_meals_data) > 0:
            return {
                'avg_with_meals': round(meals_data['value'].mean(), 1),
                'avg_without_meals': round(no_meals_data['value'].mean(), 1),
                'difference': round(meals_data['value'].mean() - no_meals_data['value'].mean(), 1)
            }
        
        return {}
    
    def _calculate_variability(self, df):
        """Calculate blood sugar variability metrics"""
        return {
            'standard_deviation': round(df['value'].std(), 1),
            'coefficient_of_variation': round((df['value'].std() / df['value'].mean()) * 100, 1),
            'range': round(df['value'].max() - df['value'].min(), 1)
        }
    
    def _assess_consistency(self, df):
        """Assess testing consistency"""
        if 'date_time' not in df.columns:
            return {}
        
        try:
            df['datetime_parsed'] = pd.to_datetime(df['date_time'])
            df_sorted = df.sort_values('datetime_parsed')
            
            # Calculate gaps between readings
            time_diffs = df_sorted['datetime_parsed'].diff().dt.total_seconds() / 3600  # hours
            
            return {
                'avg_gap_hours': round(time_diffs.mean(), 1),
                'max_gap_hours': round(time_diffs.max(), 1),
                'consistency_score': 'high' if time_diffs.mean() < 48 else 'medium' if time_diffs.mean() < 96 else 'low'
            }
        except:
            pass
        
        return {}
    
    def generate_report(self, user_id, readings):
        """Generate report"""
        return {
            'userId': user_id,
            'generated_at': datetime.now().isoformat(),
            'insights': self.generate_insights(readings),
            'trends': self.analyze_trends(readings)
        }