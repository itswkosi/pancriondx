"""
Evaluation script for binary classification model predicting early vs late stage pancreatic cancer.

Loads a pre-trained model, evaluates it on test data, and reports key metrics:
- Accuracy, ROC-AUC, Precision, Recall, Confusion Matrix
"""

import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    precision_score,
    recall_score,
    confusion_matrix
)


def load_data(file_path):
    """
    Load data from a CSV file.
    
    Args:
        file_path: Path to CSV file with 'label' column as target
        
    Returns:
        X: Features as numpy array (n_samples, n_features)
        y: Labels as numpy array (n_samples,)
        
    Raises:
        ValueError: If 'label' column is missing
        FileNotFoundError: If file does not exist
    """
    df = pd.read_csv(file_path)
    
    if 'label' not in df.columns:
        raise ValueError("CSV must contain a 'label' column")
    
    y = df['label'].values
    X = df.drop('label', axis=1).values
    
    return X, y


def load_model(model_path):
    """
    Load a pre-trained sklearn model from a pickle file.
    
    Args:
        model_path: Path to model.pkl file
        
    Returns:
        model: Loaded sklearn model
        
    Raises:
        ValueError: If model lacks predict() or predict_proba() methods
        FileNotFoundError: If model file does not exist
    """
    model = joblib.load(model_path)
    
    # Validate model has required methods
    if not hasattr(model, 'predict'):
        raise ValueError("Model must support predict() method")
    if not hasattr(model, 'predict_proba'):
        raise ValueError("Model must support predict_proba() method")
    
    return model


def evaluate_model(model, X, y, test_size=0.2, random_state=42):
    """
    Evaluate model on provided data using an 80/20 train-test split.
    
    Args:
        model: Trained sklearn model
        X: Feature array (n_samples, n_features) - numpy array or DataFrame
        y: Label array (n_samples,) - binary values (0 or 1)
        test_size: Proportion of data for testing (default: 0.2)
        random_state: Random seed for reproducibility (default: 42)
        
    Returns:
        metrics: Dictionary containing computed metrics:
            - accuracy: Classification accuracy
            - roc_auc: ROC-AUC score
            - precision: Precision score
            - recall: Recall score
            - confusion_matrix: 2D array with shape (2, 2)
        y_test: Test labels
        y_pred: Predicted labels for test set
        
    Raises:
        ValueError: If X and y have mismatched lengths
    """
    # Convert to numpy if needed
    if isinstance(X, pd.DataFrame):
        X = X.values
    if isinstance(y, pd.Series):
        y = y.values
    
    # Validate input shapes
    if len(X) != len(y):
        raise ValueError(f"X and y must have same length: {len(X)} != {len(y)}")
    
    # Split data into train/test
    X_test, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
    
    # Generate predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]  # Probabilities for class 1
    
    # Compute metrics
    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    conf_matrix = confusion_matrix(y_test, y_pred)
    
    # Compile results
    metrics = {
        'accuracy': accuracy,
        'roc_auc': roc_auc,
        'precision': precision,
        'recall': recall,
        'confusion_matrix': conf_matrix
    }
    
    return metrics, y_test, y_pred


def print_metrics(metrics, y_test, y_pred):
    """
    Print metrics in a readable, formatted output.
    
    Args:
        metrics: Dictionary of computed metrics
        y_test: Test labels
        y_pred: Predicted labels
    """
    print("\n" + "=" * 60)
    print("MODEL EVALUATION RESULTS - Pancreatic Cancer Classification")
    print("=" * 60)
    
    print(f"\nAccuracy:  {metrics['accuracy']:.4f}")
    print(f"ROC-AUC:   {metrics['roc_auc']:.4f}")
    print(f"Precision: {metrics['precision']:.4f}")
    print(f"Recall:    {metrics['recall']:.4f}")
    
    print("\n" + "-" * 60)
    print("Confusion Matrix:")
    print("-" * 60)
    cm = metrics['confusion_matrix']
    print(f"                 Predicted")
    print(f"                 Negative   Positive")
    print(f"Actual Negative     {cm[0, 0]:3d}        {cm[0, 1]:3d}")
    print(f"Actual Positive     {cm[1, 0]:3d}        {cm[1, 1]:3d}")
    
    print("\nInterpretation:")
    print(f"  True Negatives (Early stage correctly identified):   {cm[0, 0]}")
    print(f"  False Positives (Early stage misclassified):         {cm[0, 1]}")
    print(f"  False Negatives (Late stage missed):                 {cm[1, 0]}")
    print(f"  True Positives (Late stage correctly identified):    {cm[1, 1]}")
    
    print("\n" + "=" * 60)


def main(data_path='data.csv', model_path='model.pkl'):
    """
    Main evaluation pipeline.
    
    Args:
        data_path: Path to CSV file with features and 'label' column
        model_path: Path to pickled sklearn model
        
    Returns:
        metrics: Dictionary of computed metrics, or None if evaluation failed
    """
    try:
        # Load data and model
        print("Loading data...")
        X, y = load_data(data_path)
        print(f"✓ Loaded {len(X)} samples with {X.shape[1]} features")
        
        print("Loading model...")
        model = load_model(model_path)
        print("✓ Model loaded successfully")
        
        # Evaluate
        print("Evaluating model (80/20 train-test split)...")
        metrics, y_test, y_pred = evaluate_model(model, X, y)
        print(f"✓ Evaluation complete on {len(y_test)} test samples")
        
        # Print results
        print_metrics(metrics, y_test, y_pred)
        
        return metrics
        
    except FileNotFoundError as e:
        print(f"\n✗ Error: File not found - {e}")
        print("Make sure both data.csv and model.pkl exist in the current directory")
        return None
    except ValueError as e:
        print(f"\n✗ Error: Invalid data or model - {e}")
        return None
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return None


if __name__ == "__main__":
    main()
