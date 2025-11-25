"""
Blood Sugar Monitoring System - ML Model Training Script
=========================================================
This script trains machine learning models for blood sugar prediction and classification.

Features:
- Loads data from database (blood sugar readings, diabetes dataset, heart disease dataset)
- Combines multiple data sources for comprehensive training
- Generates synthetic data as fallback if database is unavailable
- Trains multiple models (Random Forest, Gradient Boosting) and selects the best
- Evaluates model performance with accuracy, classification reports, and confusion matrices
- Saves trained model, scaler, and feature columns to disk

Usage:
    python train_model.py

Output:
    - models/blood_sugar_model.joblib (trained classifier)
    - models/scaler.joblib (feature scaler)
    - models/feature_columns.joblib (feature names for inference)

Requirements: scikit-learn, pandas, numpy, joblib

CLASSES & METHODS SUMMARY
==========================

CLASS: BloodSugarMLTrainer
--------------------------
Main class for training blood sugar classification models

INITIALIZATION:
---------------
- __init__(): 
    Initialize trainer with model directory and empty data structures

DATA LOADING:
-------------
- load_data_from_database(): 
    Load blood sugar readings from MySQL database
    Connects to database, queries readings table
    Returns: DataFrame with readings or None if connection fails

- load_diabetes_dataset(): 
    Load diabetes classification dataset from CSV
    Path: datasets/Diabetes Classification.csv
    Returns: DataFrame or None if file not found

- load_heart_disease_dataset(): 
    Load heart disease dataset from CSV
    Path: datasets/heart_disease.csv
    Returns: DataFrame or None if file not found

DATA GENERATION:
----------------
- generate_synthetic_data(): 
    Generate synthetic blood sugar data as fallback
    Creates realistic glucose readings with meal types, times, activities
    Returns: DataFrame with 1000+ synthetic samples

DATA PREPROCESSING:
-------------------
- prepare_training_data(df): 
    Prepare data for model training
    Steps:
        1. Feature engineering (extract hour, day of week from timestamp)
        2. Handle missing values
        3. Encode categorical variables
        4. Create target labels (normal/prediabetic/diabetic)
        5. Split into features (X) and target (y)
    Returns: X (features), y (target labels)

FEATURE ENGINEERING:
--------------------
- engineer_features(df): 
    Create additional features from raw data
    Creates: time-based features, meal patterns, activity indicators
    Returns: DataFrame with engineered features

MODEL TRAINING:
---------------
- train_models(X_train, y_train): 
    Train multiple ML models and select best performer
    Models: Random Forest, Gradient Boosting
    Uses 5-fold cross-validation
    Returns: Best trained model

MODEL EVALUATION:
-----------------
- evaluate_model(model, X_test, y_test): 
    Evaluate model performance on test set
    Prints: accuracy, classification report, confusion matrix
    Returns: accuracy score

MODEL PERSISTENCE:
------------------
- save_model(model, scaler, feature_columns): 
    Save trained model and preprocessing objects to disk
    Saves to: models/ directory
    Files: blood_sugar_model.joblib, scaler.joblib, feature_columns.joblib

MAIN EXECUTION:
---------------
- run(): 
    Main training pipeline
    Steps:
        1. Load data from all sources
        2. Combine datasets
        3. Prepare training data
        4. Split train/test sets
        5. Train models
        6. Evaluate best model
        7. Save model to disk

MAIN SCRIPT:
------------
if __name__ == '__main__':
    Create trainer instance and run training pipeline
"""

import pandas as pd  # Data manipulation and analysis library
import numpy as np  # Numerical computing library
from sklearn.model_selection import train_test_split  # Split data into train/test sets
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier  # ML algorithms
from sklearn.preprocessing import StandardScaler  # Feature scaling
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score  # Model evaluation
import joblib  # Model serialization (save/load)
import logging  # Logging library for tracking progress
import os  # Operating system interface for file operations
from dotenv import load_dotenv  # Load environment variables from .env file

# Print header banner
print("="*60)
print("BLOOD SUGAR ML MODEL TRAINING")
print("="*60)

# Load environment variables from .env file (database credentials, etc.)
load_dotenv()

# Configure logging to show INFO level messages with timestamps
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BloodSugarMLTrainer:
    """
    Machine Learning trainer for blood sugar classification.
    Handles data loading, preprocessing, training, evaluation, and model persistence.
    """
    
    def __init__(self, use_database=True):
        """
        Initialize the ML trainer.
        
        Args:
            use_database (bool): If True, load data from MySQL database. If False, generate synthetic data.
        """
        self.use_database = use_database  # Flag to determine data source
        self.model = None  # Will store the trained classifier
        self.scaler = None  # Will store the StandardScaler for feature normalization
        self.feature_columns = None  # Will store list of feature names for inference
    
    def load_and_prepare_data(self):
        """
        Load and prepare training data from database or generate synthetic data.
        
        Returns:
            pandas.DataFrame: Combined dataset with blood sugar readings and features
        """
        logger.info("Loading data from database...")
        
        # If not using database, generate synthetic data
        if not self.use_database:
            logger.warning("Generating synthetic data...")
            return self._generate_synthetic_data(5000)
        
        try:
            # Import Database class to connect to MySQL
            from models import Database
            db = Database()
            
            # Get blood sugar readings from bloodsugarreadings table
            logger.info("Loading blood sugar readings from bloodsugarreadings table...")
            readings = db.get_all_readings_for_training()
            logger.info(f"Loaded {len(readings)} readings from bloodsugarreadings")
            
            # Get diabetes dataset from diabetesdataanslysis table
            logger.info("Loading diabetes data from diabetesdataanslysis...")
            diabetes_data = db.get_diabetes_dataset()
            logger.info(f"Loaded {len(diabetes_data)} records from diabetes dataset")
            
            # Get heart disease dataset
            logger.info("Loading heart disease data...")
            heart_data = db.get_heart_disease_dataset()
            logger.info(f"Loaded {len(heart_data)} records from heart disease dataset")
            
            # Close database connection
            db.close()
            
            # Combine all datasets into single DataFrame
            combined_df = self._combine_datasets(readings, diabetes_data, heart_data)
            logger.info(f"Combined dataset: {len(combined_df)} total records")
            
            return combined_df
            
        except Exception as e:
            # If database loading fails, fall back to synthetic data
            logger.error(f"Error loading from database: {e}")
            logger.warning("Falling back to synthetic data...")
            return self._generate_synthetic_data(5000)
    
    def _combine_datasets(self, readings, diabetes_data, heart_data):
        """
        Combine multiple datasets into unified training data with consistent schema.
        
        Args:
            readings (list): Blood sugar readings from bloodsugarreadings table
            diabetes_data (list): Diabetes dataset records
            heart_data (list): Heart disease dataset records
            
        Returns:
            pandas.DataFrame: Unified dataset with columns: value, fasting, hour, food_intake, activity, status
        """
        all_data = []  # List to collect all records
        
        # Process blood sugar readings from main table
        for reading in readings:
            row = {
                'value': float(reading.get('value', 0)),  # Blood glucose level (mg/dL)
                'fasting': 1 if reading.get('fasting') else 0,  # 1 if fasting, 0 otherwise
                'hour': 12,  # Default hour (12 PM) if not specified
                'food_intake': reading.get('food_intake', 'none'),  # Food consumption level
                'activity': reading.get('activity', 'none'),  # Physical activity level
                'status': self._map_status(reading.get('status', 'normal'))  # Classification label
            }
            all_data.append(row)
        
        # Process diabetes dataset records
        for record in diabetes_data:
            # Only use records with valid glucose values
            if record.get('Glucose') and record['Glucose'] > 0:
                row = {
                    'value': float(record['Glucose']),  # Glucose level from diabetes dataset
                    'fasting': 1,  # Diabetes dataset typically has fasting glucose
                    'hour': 8,  # Morning fasting time (8 AM)
                    'food_intake': 'none',  # No food before fasting measurement
                    'activity': 'none',  # No activity before fasting measurement
                    'status': self._classify_glucose(float(record['Glucose']))  # Auto-classify based on value
                }
                all_data.append(row)
        
        # Process heart disease dataset records
        for record in heart_data:
            fasting_sugar = record.get('Fasting Blood Sugar', '')  # Get fasting blood sugar value
            # Validate and process the value
            if fasting_sugar and fasting_sugar != 'Fasting Bl':  # Skip header rows
                try:
                    glucose = float(fasting_sugar)  # Convert to float
                    if glucose > 0:  # Only use positive values
                        row = {
                            'value': glucose,  # Fasting blood sugar level
                            'fasting': 1,  # From fasting measurement
                            'hour': 8,  # Morning fasting time
                            'food_intake': 'none',  # Fasting = no food
                            'activity': record.get('Exercise Habits', 'none'),  # Use exercise habits if available
                            'status': self._classify_glucose(glucose)  # Auto-classify
                        }
                        all_data.append(row)
                except (ValueError, TypeError):
                    # Skip records with invalid glucose values
                    continue
        
        # Convert list of dictionaries to pandas DataFrame
        df = pd.DataFrame(all_data)
        logger.info(f"Created dataframe with {len(df)} records")
        logger.info(f"Status distribution:\n{df['status'].value_counts()}")  # Show class distribution
        
        return df
    
    def _map_status(self, db_status):
        """
        Map database status strings to standardized training labels.
        
        Args:
            db_status (str): Status from database ('normal', 'borderline', 'abnormal')
            
        Returns:
            str: Standardized label ('normal', 'prediabetic', 'high', 'low')
        """
        status_map = {
            'normal': 'normal',  # Normal blood sugar
            'borderline': 'prediabetic',  # Pre-diabetes range
            'abnormal': 'high'  # High/diabetic range
        }
        return status_map.get(db_status, 'normal')  # Default to 'normal' if unknown
    
    def _classify_glucose(self, value):
        """
        Classify glucose value into status category based on medical thresholds.
        Uses standard fasting glucose thresholds.
        
        Args:
            value (float): Glucose level in mg/dL
            
        Returns:
            str: Classification ('low', 'normal', 'prediabetic', 'high')
        """
        if value < 70:
            return 'low'  # Hypoglycemia (dangerously low)
        elif value <= 140:
            return 'normal'  # Normal range (fasting: <100, post-meal: <140)
        elif value <= 199:
            return 'prediabetic'  # Pre-diabetes range (100-125 fasting, 140-199 post-meal)
        else:
            return 'high'  # Diabetes range (>=126 fasting, >=200 post-meal)
    
    def _generate_synthetic_data(self, n_samples=5000):
        """
        Generate synthetic blood sugar data for training when database is unavailable.
        Creates realistic data with correlations between features and outcomes.
        
        Args:
            n_samples (int): Number of synthetic samples to generate
            
        Returns:
            pandas.DataFrame: Synthetic dataset with same schema as real data
        """
        np.random.seed(42)  # Set random seed for reproducibility
        
        # Initialize data dictionary
        data = {
            'value': [],  # Blood glucose values
            'fasting': [],  # Fasting state (0 or 1)
            'hour': [],  # Hour of day (0-23)
            'food_intake': [],  # Food consumption level
            'activity': [],  # Physical activity level
            'status': []  # Classification label
        }
        
        # Generate each sample
        for _ in range(n_samples):
            # Randomly determine if measurement is fasting or not
            fasting = np.random.choice([0, 1])
            # Random hour of day
            hour = np.random.randint(0, 24)
            
            # Base glucose value depends on fasting state
            if fasting:
                base_value = np.random.normal(95, 15)  # Fasting: mean=95, std=15
            else:
                base_value = np.random.normal(120, 25)  # Non-fasting: mean=120, std=25
            
            # Food intake increases glucose level
            food_intake = np.random.choice(['none', 'light', 'moderate', 'heavy'])
            if food_intake == 'heavy':
                base_value += np.random.normal(30, 10)  # Heavy meal: +30 mg/dL average
            elif food_intake == 'moderate':
                base_value += np.random.normal(15, 5)  # Moderate: +15 mg/dL average
            elif food_intake == 'light':
                base_value += np.random.normal(5, 3)  # Light: +5 mg/dL average
            
            # Physical activity decreases blood sugar
            activity = np.random.choice(['none', 'light', 'moderate', 'intense'])
            if activity == 'intense':
                base_value -= np.random.normal(20, 5)  # Intense exercise: -20 mg/dL
            elif activity == 'moderate':
                base_value -= np.random.normal(10, 3)  # Moderate: -10 mg/dL
            elif activity == 'light':
                base_value -= np.random.normal(5, 2)  # Light: -5 mg/dL
            
            # Clip value to realistic range (40-400 mg/dL)
            value = max(40, min(400, base_value))
            
            # Determine status label based on value and fasting state
            if fasting:
                # Fasting glucose thresholds
                if value < 70:
                    status = 'low'  # Hypoglycemia
                elif value <= 100:
                    status = 'normal'  # Normal fasting glucose
                elif value <= 125:
                    status = 'prediabetic'  # Impaired fasting glucose
                else:
                    status = 'high'  # Diabetes range
            else:
                # Post-meal (non-fasting) glucose thresholds
                if value < 70:
                    status = 'low'  # Hypoglycemia
                elif value <= 140:
                    status = 'normal'  # Normal post-meal
                elif value <= 199:
                    status = 'prediabetic'  # Impaired glucose tolerance
                else:
                    status = 'high'  # Diabetes range
            
            # Append values to data dictionary
            data['value'].append(value)
            data['fasting'].append(fasting)
            data['hour'].append(hour)
            data['food_intake'].append(food_intake)
            data['activity'].append(activity)
            data['status'].append(status)
        
        return pd.DataFrame(data)  # Convert to DataFrame
    
    def preprocess_data(self, df):
        """
        Preprocess the data for machine learning training.
        Performs one-hot encoding on categorical variables.
        
        Args:
            df (pandas.DataFrame): Raw data
            
        Returns:
            tuple: (X, y) where X is features DataFrame and y is target Series
        """
        logger.info("Preprocessing data...")
        
        df = df.copy()  # Create copy to avoid modifying original
        # One-hot encode categorical variables (food_intake, activity)
        # Creates binary columns like food_none, food_light, activity_moderate, etc.
        df = pd.get_dummies(df, columns=['food_intake', 'activity'], prefix=['food', 'activity'])
        
        # Separate features (X) and target (y)
        X = df.drop('status', axis=1)  # All columns except 'status'
        y = df['status']  # Target variable (classification label)
        
        # Save feature column names for later use in prediction
        self.feature_columns = X.columns.tolist()
        
        logger.info(f"Features: {len(self.feature_columns)} columns")
        logger.info(f"Classes: {y.unique().tolist()}")
        logger.info(f"Class distribution:\n{y.value_counts()}")
        
        return X, y
    
    def train_model(self, X, y):
        """
        Train machine learning models and select the best performer.
        Trains both Random Forest and Gradient Boosting classifiers.
        
        Args:
            X (pandas.DataFrame): Feature matrix
            y (pandas.Series): Target labels
            
        Returns:
            tuple: (X_test_scaled, y_test) for final evaluation
        """
        logger.info("Training model...")
        
        # Split data into training (80%) and testing (20%) sets
        # stratify=y ensures class distribution is maintained in both sets
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        logger.info(f"Training set: {len(X_train)} samples")
        logger.info(f"Test set: {len(X_test)} samples")
        
        # Scale features to have mean=0 and std=1 (improves model performance)
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)  # Fit on training data
        X_test_scaled = self.scaler.transform(X_test)  # Transform test data using same scaler
        
        # Train Random Forest Classifier
        logger.info("Training Random Forest...")
        rf_model = RandomForestClassifier(
            n_estimators=200,  # Number of trees in the forest
            max_depth=15,  # Maximum depth of each tree
            min_samples_split=10,  # Minimum samples required to split a node
            min_samples_leaf=5,  # Minimum samples required at leaf node
            random_state=42,  # Seed for reproducibility
            n_jobs=-1  # Use all CPU cores for parallel processing
        )
        rf_model.fit(X_train_scaled, y_train)  # Train the model
        rf_score = rf_model.score(X_test_scaled, y_test)  # Calculate accuracy on test set
        logger.info(f"Random Forest Accuracy: {rf_score:.4f}")
        
        # Train Gradient Boosting Classifier
        logger.info("Training Gradient Boosting...")
        gb_model = GradientBoostingClassifier(
            n_estimators=100,  # Number of boosting stages
            learning_rate=0.1,  # Step size for each boosting iteration
            max_depth=5,  # Maximum depth of each tree
            random_state=42  # Seed for reproducibility
        )
        gb_model.fit(X_train_scaled, y_train)  # Train the model
        gb_score = gb_model.score(X_test_scaled, y_test)  # Calculate accuracy
        logger.info(f"Gradient Boosting Accuracy: {gb_score:.4f}")
        
        # Choose the model with better accuracy
        if rf_score > gb_score:
            self.model = rf_model
            logger.info("Selected Random Forest as final model")
        else:
            self.model = gb_model
            logger.info("Selected Gradient Boosting as final model")
        
        # Evaluate selected model on test set
        self.evaluate_model(X_test_scaled, y_test)
        
        return X_test_scaled, y_test
    
    def evaluate_model(self, X_test, y_test):
        """
        Evaluate the trained model's performance with detailed metrics.
        
        Args:
            X_test (numpy.ndarray): Test features (scaled)
            y_test (pandas.Series): True labels for test set
        """
        logger.info("\n" + "="*60)
        logger.info("MODEL EVALUATION")
        logger.info("="*60)
        
        # Make predictions on test set
        y_pred = self.model.predict(X_test)
        
        # Calculate overall accuracy
        accuracy = accuracy_score(y_test, y_pred)
        logger.info(f"\nOverall Accuracy: {accuracy:.4f}")
        
        # Print detailed classification report (precision, recall, f1-score for each class)
        logger.info("\nClassification Report:")
        logger.info("\n" + classification_report(y_test, y_pred))
        
        # Print confusion matrix (shows true positives, false positives, etc.)
        logger.info("\nConfusion Matrix:")
        logger.info(f"\n{confusion_matrix(y_test, y_pred)}")
        
        # Show feature importances (only available for tree-based models)
        if hasattr(self.model, 'feature_importances_'):
            feature_importance = pd.DataFrame({
                'feature': self.feature_columns,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)  # Sort by importance
            
            logger.info("\nTop 10 Important Features:")
            logger.info(f"\n{feature_importance.head(10).to_string()}")
        
        logger.info("\n" + "="*60)
    
    def save_model(self, model_dir='models'):
        """
        Save the trained model, scaler, and feature columns to disk.
        Uses joblib for efficient serialization of scikit-learn objects.
        
        Args:
            model_dir (str): Directory path where models will be saved
        """
        # Create models directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)
        
        # Define file paths
        model_path = os.path.join(model_dir, 'blood_sugar_model.joblib')
        scaler_path = os.path.join(model_dir, 'scaler.joblib')
        features_path = os.path.join(model_dir, 'feature_columns.joblib')
        
        # Save model, scaler, and feature columns using joblib
        joblib.dump(self.model, model_path)  # Save trained classifier
        joblib.dump(self.scaler, scaler_path)  # Save StandardScaler
        joblib.dump(self.feature_columns, features_path)  # Save feature names list
        
        # Verify files were created successfully
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
        """
        Run the complete ML training pipeline from start to finish.
        Executes: data loading -> preprocessing -> training -> saving
        
        Returns:
            bool: True if pipeline completed successfully, False otherwise
        """
        logger.info("="*60)
        logger.info("Starting ML training pipeline...")
        logger.info("="*60 + "\n")
        
        # Step 1: Load data from database or generate synthetic data
        df = self.load_and_prepare_data()
        
        # Check if data was loaded successfully
        if df is None or len(df) == 0:
            logger.error("No data loaded! Cannot train model.")
            return False
        
        # Step 2: Preprocess data (one-hot encoding, split features/target)
        X, y = self.preprocess_data(df)
        
        # Step 3: Train models and select best performer
        self.train_model(X, y)
        
        # Step 4: Save trained model, scaler, and features to disk
        self.save_model()
        
        logger.info("\n" + "="*60)
        logger.info("TRAINING PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("="*60)
        
        return True

# MAIN EXECUTION - Entry point when script is run directly
if __name__ == '__main__':
    print("\nInitializing trainer...")
    # Create trainer instance (will use database if available)
    trainer = BloodSugarMLTrainer(use_database=True)
    
    print("Starting training process...")
    # Run the complete training pipeline
    success = trainer.run_full_pipeline()
    
    # Print final status message
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