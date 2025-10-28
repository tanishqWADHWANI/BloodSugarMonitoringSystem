import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import logging
import os
from dotenv import load_dotenv

print("="*60)
print("BLOOD SUGAR ML MODEL TRAINING")
print("="*60)

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BloodSugarMLTrainer:
    def __init__(self, use_database=True):
        """Initialize the ML trainer"""
        self.use_database = use_database
        self.model = None
        self.scaler = None
        self.feature_columns = None
    
    def load_and_prepare_data(self):
        """Load and prepare training data from database"""
        logger.info("Loading data from database...")
        
        if not self.use_database:
            logger.warning("Generating synthetic data...")
            return self._generate_synthetic_data(5000)
        
        try:
            from models import Database
            db = Database()
            
            # Get blood sugar readings from main table
            logger.info("Loading blood sugar readings from bloodsugarreadings table...")
            readings = db.get_all_readings_for_training()
            logger.info(f"Loaded {len(readings)} readings from bloodsugarreadings")
            
            # Get diabetes dataset
            logger.info("Loading diabetes data from diabetesdataanslysis...")
            diabetes_data = db.get_diabetes_dataset()
            logger.info(f"Loaded {len(diabetes_data)} records from diabetes dataset")
            
            # Get heart disease dataset
            logger.info("Loading heart disease data...")
            heart_data = db.get_heart_disease_dataset()
            logger.info(f"Loaded {len(heart_data)} records from heart disease dataset")
            
            db.close()
            
            # Combine all data
            combined_df = self._combine_datasets(readings, diabetes_data, heart_data)
            logger.info(f"Combined dataset: {len(combined_df)} total records")
            
            return combined_df
            
        except Exception as e:
            logger.error(f"Error loading from database: {e}")
            logger.warning("Falling back to synthetic data...")
            return self._generate_synthetic_data(5000)
    
    def _combine_datasets(self, readings, diabetes_data, heart_data):
        """Combine multiple datasets into unified training data"""
        all_data = []
        
        # Process blood sugar readings
        for reading in readings:
            row = {
                'value': float(reading.get('value', 0)),
                'fasting': 1 if reading.get('fasting') else 0,
                'hour': 12,
                'food_intake': reading.get('food_intake', 'none'),
                'activity': reading.get('activity', 'none'),
                'status': self._map_status(reading.get('status', 'normal'))
            }
            all_data.append(row)
        
        # Process diabetes dataset
        for record in diabetes_data:
            if record.get('Glucose') and record['Glucose'] > 0:
                row = {
                    'value': float(record['Glucose']),
                    'fasting': 1,
                    'hour': 8,
                    'food_intake': 'none',
                    'activity': 'none',
                    'status': self._classify_glucose(float(record['Glucose']))
                }
                all_data.append(row)
        
        # Process heart disease dataset
        for record in heart_data:
            fasting_sugar = record.get('Fasting Blood Sugar', '')
            if fasting_sugar and fasting_sugar != 'Fasting Bl':
                try:
                    glucose = float(fasting_sugar)
                    if glucose > 0:
                        row = {
                            'value': glucose,
                            'fasting': 1,
                            'hour': 8,
                            'food_intake': 'none',
                            'activity': record.get('Exercise Habits', 'none'),
                            'status': self._classify_glucose(glucose)
                        }
                        all_data.append(row)
                except (ValueError, TypeError):
                    continue
        
        df = pd.DataFrame(all_data)
        logger.info(f"Created dataframe with {len(df)} records")
        logger.info(f"Status distribution:\n{df['status'].value_counts()}")
        
        return df
    
    def _map_status(self, db_status):
        """Map database status to training labels"""
        status_map = {
            'normal': 'normal',
            'borderline': 'prediabetic',
            'abnormal': 'high'
        }
        return status_map.get(db_status, 'normal')
    
    def _classify_glucose(self, value):
        """Classify glucose value into status"""
        if value < 70:
            return 'low'
        elif value <= 140:
            return 'normal'
        elif value <= 199:
            return 'prediabetic'
        else:
            return 'high'
    
    def _generate_synthetic_data(self, n_samples=5000):
        """Generate synthetic blood sugar data for training"""
        np.random.seed(42)
        
        data = {
            'value': [],
            'fasting': [],
            'hour': [],
            'food_intake': [],
            'activity': [],
            'status': []
        }
        
        for _ in range(n_samples):
            fasting = np.random.choice([0, 1])
            hour = np.random.randint(0, 24)
            
            # Base value depends on fasting state
            if fasting:
                base_value = np.random.normal(95, 15)
            else:
                base_value = np.random.normal(120, 25)
            
            # Add noise based on food intake
            food_intake = np.random.choice(['none', 'light', 'moderate', 'heavy'])
            if food_intake == 'heavy':
                base_value += np.random.normal(30, 10)
            elif food_intake == 'moderate':
                base_value += np.random.normal(15, 5)
            elif food_intake == 'light':
                base_value += np.random.normal(5, 3)
            
            # Activity reduces blood sugar
            activity = np.random.choice(['none', 'light', 'moderate', 'intense'])
            if activity == 'intense':
                base_value -= np.random.normal(20, 5)
            elif activity == 'moderate':
                base_value -= np.random.normal(10, 3)
            elif activity == 'light':
                base_value -= np.random.normal(5, 2)
            
            value = max(40, min(400, base_value))
            
            # Determine status
            if fasting:
                if value < 70:
                    status = 'low'
                elif value <= 100:
                    status = 'normal'
                elif value <= 125:
                    status = 'prediabetic'
                else:
                    status = 'high'
            else:
                if value < 70:
                    status = 'low'
                elif value <= 140:
                    status = 'normal'
                elif value <= 199:
                    status = 'prediabetic'
                else:
                    status = 'high'
            
            data['value'].append(value)
            data['fasting'].append(fasting)
            data['hour'].append(hour)
            data['food_intake'].append(food_intake)
            data['activity'].append(activity)
            data['status'].append(status)
        
        return pd.DataFrame(data)
    
    def preprocess_data(self, df):
        """Preprocess the data for training"""
        logger.info("Preprocessing data...")
        
        df = df.copy()
        df = pd.get_dummies(df, columns=['food_intake', 'activity'], prefix=['food', 'activity'])
        
        X = df.drop('status', axis=1)
        y = df['status']
        
        self.feature_columns = X.columns.tolist()
        
        logger.info(f"Features: {len(self.feature_columns)} columns")
        logger.info(f"Classes: {y.unique().tolist()}")
        logger.info(f"Class distribution:\n{y.value_counts()}")
        
        return X, y
    
    def train_model(self, X, y):
        """Train the machine learning model"""
        logger.info("Training model...")
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"Training set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train Random Forest
        logger.info("Training Random Forest...")
        rf_model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1
        )
        rf_model.fit(X_train_scaled, y_train)
        rf_score = rf_model.score(X_test_scaled, y_test)
        logger.info(f"Random Forest Accuracy: {rf_score:.4f}")
        
        # Train Gradient Boosting
        logger.info("Training Gradient Boosting...")
        gb_model = GradientBoostingClassifier(
            n_estimators=100,
            learning_rate=0.1,
            max_depth=5,
            random_state=42
        )
        gb_model.fit(X_train_scaled, y_train)
        gb_score = gb_model.score(X_test_scaled, y_test)
        logger.info(f"Gradient Boosting Accuracy: {gb_score:.4f}")
        
        # Choose best model
        if rf_score > gb_score:
            self.model = rf_model
            logger.info("Selected Random Forest as final model")
        else:
            self.model = gb_model
            logger.info("Selected Gradient Boosting as final model")
        
        # Evaluate
        self.evaluate_model(X_test_scaled, y_test)
        
        return X_test_scaled, y_test
    
    def evaluate_model(self, X_test, y_test):
        """Evaluate the trained model"""
        logger.info("\n" + "="*60)
        logger.info("MODEL EVALUATION")
        logger.info("="*60)
        
        y_pred = self.model.predict(X_test)
        
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"\nOverall Accuracy: {accuracy:.4f}")
        
        logger.info("\nClassification Report:")
        logger.info("\n" + classification_report(y_test, y_pred))
        
        logger.info("\nConfusion Matrix:")
        logger.info(f"\n{confusion_matrix(y_test, y_pred)}")
        
        if hasattr(self.model, 'feature_importances_'):
            feature_importance = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            logger.info("\nTop 10 Important Features:")
            logger.info(f"\n{feature_importance.head(10).to_string()}")
        
        logger.info("\n" + "="*60)
    
    def save_model(self, model_dir='models'):
        """Save the trained model and scaler"""
        # Create directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, 'blood_sugar_model.joblib')
        scaler_path = os.path.join(model_dir, 'scaler.joblib')
        features_path = os.path.join(model_dir, 'feature_columns.joblib')
        
        # Save files
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        joblib.dump(self.feature_columns, features_path)
        
        # Verify files were created
        if os.path.exists(model_path):
            logger.info(f"\nModel saved to {os.path.abspath(model_path)}")
        else:
            logger.error(f"\nFailed to save model to {model_path}")
        
        if os.path.exists(scaler_path):
            logger.info(f"Scaler saved to {os.path.abspath(scaler_path)}")
        else:
            logger.error(f"Failed to save scaler to {scaler_path}")
        
        if os.path.exists(features_path):
            logger.info(f"Features saved to {os.path.abspath(features_path)}")
        else:
            logger.error(f"Failed to save features to {features_path}")
    
    def run_full_pipeline(self):
        """Run the complete training pipeline"""
        logger.info("="*60)
        logger.info("Starting ML training pipeline...")
        logger.info("="*60 + "\n")
        
        # Step 1: Load data
        df = self.load_and_prepare_data()
        
        if df is None or len(df) == 0:
            logger.error("No data loaded! Cannot train model.")
            return False
        
        # Step 2: Preprocess
        X, y = self.preprocess_data(df)
        
        # Step 3: Train
        self.train_model(X, y)
        
        # Step 4: Save
        self.save_model()
        
        logger.info("\n" + "="*60)
        logger.info("TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        
        return True

# MAIN EXECUTION - THIS IS WHAT ACTUALLY RUNS THE TRAINING!
if __name__ == '__main__':
    print("\nInitializing trainer...")
    trainer = BloodSugarMLTrainer(use_database=True)
    
    print("Starting training process...")
    success = trainer.run_full_pipeline()
    
    if success:
        print("\n" + "="*60)
        print("SUCCESS! Model training complete.")
        print("="*60)
        print("\nNext steps:")
        print("1. Check the 'models/' folder for saved files")
        print("2. Run 'python app.py' to start the server")
        print("="*60 + "\n")
    else:
        print("\n" + "="*60)
        print("TRAINING FAILED! Check the error messages above.")
        print("="*60 + "\n")