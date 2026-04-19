import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score, recall_score,
    confusion_matrix, classification_report
)
import joblib


def load_data(filepath):
    """Load and validate mutation data from CSV."""
    df = pd.read_csv(filepath)
    
    # Validate label column exists
    if "label" not in df.columns:
        raise ValueError("CSV must contain 'label' column")
    
    # Separate features and labels
    y = df["label"].values
    X = df.drop(columns=["label"]).values
    
    # Validate: no missing values
    if np.isnan(X).any() or np.isnan(y).any():
        raise ValueError("Dataset contains missing values")
    
    # Validate: features are numeric
    try:
        X = X.astype(float)
    except (ValueError, TypeError):
        raise ValueError("Feature matrix must be numeric")
    
    # Validate: binary classification
    unique_labels = np.unique(y)
    if len(unique_labels) != 2:
        raise ValueError(f"Label must be binary. Found {len(unique_labels)} classes")
    
    print(f"✓ Loaded {X.shape[0]} samples with {X.shape[1]} features")
    print(f"✓ Label distribution: {np.bincount(y.astype(int))}")
    
    return X, y, df.columns[1:]  # Return feature names


def train_model(X, y):
    """Train logistic regression model with stratified train/test split."""
    # Stratified split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\n✓ Train set: {X_train.shape[0]} samples")
    print(f"✓ Test set: {X_test.shape[0]} samples")
    
    # Train model
    model = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    model.fit(X_train, y_train)
    
    print(f"✓ Model training complete")
    
    return model, X_train, X_test, y_train, y_test


def evaluate_model(model, X_train, X_test, y_train, y_test, feature_names):
    """Evaluate model performance on test set."""
    print("\n" + "="*60)
    print("MODEL EVALUATION METRICS")
    print("="*60)
    
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]  # Probability of late-stage
    
    # Metrics
    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    
    print(f"\nAccuracy:  {accuracy:.4f}")
    print(f"ROC-AUC:   {roc_auc:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall:    {recall:.4f}")
    
    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred)
    print(f"\nConfusion Matrix:")
    print(f"  Early (0) | Late (1)")
    print(f"  {cm[0,0]:7d} | {cm[0,1]:7d}  (Actual Early)")
    print(f"  {cm[1,0]:7d} | {cm[1,1]:7d}  (Actual Late)")
    
    # Classification report
    print(f"\nClassification Report:")
    print(classification_report(y_test, y_pred, target_names=["Early-Stage", "Late-Stage"]))
    
    # Feature importance (coefficients)
    print(f"\nTop Feature Coefficients (learned weights):")
    coef_df = pd.DataFrame({
        "Feature": feature_names,
        "Coefficient": model.coef_[0]
    }).sort_values("Coefficient", key=abs, ascending=False)
    print(coef_df.head(10).to_string(index=False))
    
    # Probabilistic output example
    print(f"\nProbabilistic Predictions (first 5 test samples):")
    for i in range(min(5, len(y_test))):
        p_late = y_pred_proba[i]
        p_early = 1 - p_late
        true_label = "Late-Stage" if y_test[i] == 1 else "Early-Stage"
        print(f"  Sample {i+1}: P(Late)={p_late:.4f}, P(Early)={p_early:.4f} | True: {true_label}")
    
    print("\n" + "="*60)
    
    return {
        "accuracy": accuracy,
        "roc_auc": roc_auc,
        "precision": precision,
        "recall": recall,
        "confusion_matrix": cm
    }


def save_model(model, filepath="logreg_model.pkl"):
    """Save trained model to disk."""
    joblib.dump(model, filepath)
    print(f"✓ Model saved to {filepath}")


def main():
    """Main pipeline execution."""
    try:
        # Load data
        print("Loading mutation data...")
        X, y, feature_names = load_data("mutation_matrix.csv")
        
        # Train model
        print("\nTraining probabilistic classifier...")
        model, X_train, X_test, y_train, y_test = train_model(X, y)
        
        # Evaluate
        results = evaluate_model(model, X_train, X_test, y_train, y_test, feature_names)
        
        # Save model
        print("\nSaving model...")
        save_model(model)
        
        print("\n✓ Pipeline complete. Heuristic system replaced with probabilistic ML model.")
        
    except FileNotFoundError:
        print("Error: mutation_matrix.csv not found in current directory")
    except ValueError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
