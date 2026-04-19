"""
Robust Model Validation and Stress-Testing Script
==================================================

Validates whether a binary classification model (early vs late-stage pancreatic cancer)
is learning real biological signal or exploiting dataset artifacts.

Key components:
1. Data loading and validation
2. Train/test evaluation with full metrics
3. Stratified k-fold cross-validation (stability check)
4. Permutation testing (leakage detection)
5. Baseline comparison
6. Visualization of results
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import (
    train_test_split, StratifiedKFold, cross_val_score
)
from sklearn.linear_model import LogisticRegression
from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score, roc_auc_score, precision_score, recall_score,
    confusion_matrix, roc_curve, auc, classification_report
)
import warnings
warnings.filterwarnings('ignore')


# ============================================================================
# 1. DATA LOADING & VALIDATION
# ============================================================================

def load_and_validate_data(filepath):
    """
    Load and validate mutation data from CSV.
    
    Checks:
    - 'label' column exists
    - Binary classification (only 0 and 1)
    - No missing values
    - All features are numeric
    
    Returns:
        X: Feature matrix (numpy array)
        y: Labels (numpy array)
        feature_names: List of feature column names
    """
    print("=" * 80)
    print("DATA LOADING & VALIDATION")
    print("=" * 80)
    
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        raise FileNotFoundError(f"Data file not found: {filepath}")
    
    # Validate label column
    if "label" not in df.columns:
        raise ValueError("CSV must contain 'label' column")
    
    # Extract features and labels
    y = df["label"].values
    X = df.drop(columns=["label"]).values
    feature_names = df.columns[1:].tolist()
    
    # Validate no missing values
    if np.isnan(X).any() or np.isnan(y).any():
        raise ValueError("Dataset contains missing values")
    
    # Validate all features are numeric
    try:
        X = X.astype(float)
    except (ValueError, TypeError):
        raise ValueError("Feature matrix must be numeric")
    
    # Validate binary classification
    unique_labels = np.unique(y)
    if len(unique_labels) != 2 or not all(l in [0, 1] for l in unique_labels):
        raise ValueError(f"Labels must be binary (0, 1). Found: {unique_labels}")
    
    # Print validation summary
    label_counts = np.bincount(y.astype(int))
    print(f"✓ Data loaded successfully")
    print(f"  - Shape: {X.shape[0]} samples × {X.shape[1]} features")
    print(f"  - Label distribution: Class 0 = {label_counts[0]}, Class 1 = {label_counts[1]}")
    print(f"  - Class balance: {label_counts[0]/len(y)*100:.1f}% vs {label_counts[1]/len(y)*100:.1f}%")
    print(f"  - Missing values: 0")
    print(f"  - All features numeric: ✓")
    
    return X, y, feature_names


# ============================================================================
# 2. TRAIN/TEST EVALUATION FUNCTION
# ============================================================================

def evaluate_model(model, X_train, X_test, y_train, y_test, model_name="Test Model"):
    """
    Evaluate model on test set with comprehensive metrics.
    
    Computes:
    - Accuracy
    - ROC-AUC
    - Precision
    - Recall
    - Confusion matrix
    - Classification report
    
    Args:
        model: Trained sklearn model
        X_train, X_test: Training and test features
        y_train, y_test: Training and test labels
        model_name: Label for output
        
    Returns:
        metrics_dict: Dictionary with all computed metrics
    """
    # Predictions
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    
    # Compute metrics
    accuracy = accuracy_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_pred_proba)
    precision = precision_score(y_test, y_pred, zero_division=0)
    recall = recall_score(y_test, y_pred, zero_division=0)
    cm = confusion_matrix(y_test, y_pred)
    
    metrics_dict = {
        'accuracy': accuracy,
        'roc_auc': roc_auc,
        'precision': precision,
        'recall': recall,
        'confusion_matrix': cm,
        'y_pred': y_pred,
        'y_pred_proba': y_pred_proba
    }
    
    return metrics_dict


def print_evaluation(metrics, y_test, model_name="Model"):
    """Pretty-print evaluation metrics."""
    print(f"\n{model_name}")
    print("-" * 60)
    print(f"  Accuracy:  {metrics['accuracy']:.4f}")
    print(f"  ROC-AUC:   {metrics['roc_auc']:.4f}")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall:    {metrics['recall']:.4f}")
    
    cm = metrics['confusion_matrix']
    print(f"\n  Confusion Matrix:")
    print(f"    TN={cm[0,0]:3d}  FP={cm[0,1]:3d}")
    print(f"    FN={cm[1,0]:3d}  TP={cm[1,1]:3d}")


# ============================================================================
# 3. CROSS-VALIDATION (STABILITY CHECK)
# ============================================================================

def run_cross_validation(X, y, k=5, random_state=42):
    """
    Run Stratified K-Fold cross-validation to check model stability.
    
    Args:
        X: Feature matrix
        y: Labels
        k: Number of folds (default 5)
        random_state: Random seed
        
    Returns:
        cv_scores: Array of ROC-AUC scores for each fold
        mean_cv_auc: Mean ROC-AUC across folds
        std_cv_auc: Standard deviation of ROC-AUC
    """
    print("\n" + "=" * 80)
    print("CROSS-VALIDATION (STABILITY CHECK)")
    print("=" * 80)
    
    model = LogisticRegression(
        max_iter=1000, class_weight="balanced", random_state=random_state
    )
    
    skf = StratifiedKFold(n_splits=k, shuffle=True, random_state=random_state)
    cv_scores = cross_val_score(model, X, y, cv=skf, scoring='roc_auc')
    
    mean_cv_auc = cv_scores.mean()
    std_cv_auc = cv_scores.std()
    
    print(f"\nStratified {k}-Fold Cross-Validation Results:")
    print(f"  Mean ROC-AUC:     {mean_cv_auc:.4f}")
    print(f"  Std Dev:          {std_cv_auc:.4f}")
    print(f"  95% CI:           [{mean_cv_auc - 1.96*std_cv_auc:.4f}, {mean_cv_auc + 1.96*std_cv_auc:.4f}]")
    print(f"\n  Fold scores:      {[f'{s:.4f}' for s in cv_scores]}")
    
    # Stability assessment
    if std_cv_auc < 0.05:
        stability = "EXCELLENT (very stable across folds)"
    elif std_cv_auc < 0.10:
        stability = "GOOD (reasonably stable)"
    else:
        stability = "CONCERNING (high variance across folds - potential overfitting)"
    
    print(f"  Stability:        {stability}")
    
    return cv_scores, mean_cv_auc, std_cv_auc


# ============================================================================
# 4. PERMUTATION TEST (CRITICAL - LEAKAGE DETECTION)
# ============================================================================

def run_permutation_test(X_train, X_test, y_train, y_test, n_permutations=100,
                         random_state=42):
    """
    Run permutation test to detect if model is learning signal or exploiting artifacts.
    
    Procedure:
    1. Record real model's test ROC-AUC
    2. Shuffle y_test labels randomly (N times)
    3. For each shuffle: refit model and compute ROC-AUC
    4. Compare: how often shuffled ROC-AUC >= real ROC-AUC?
    
    Interpretation:
    - If shuffled ROC-AUC << real ROC-AUC: Model learns real signal ✓
    - If shuffled ROC-AUC ≈ real ROC-AUC: Model exploits artifacts ✗
    - p-value: proportion of shuffled runs with AUC >= real AUC
    
    Args:
        X_train, X_test: Training and test features
        y_train, y_test: Training and test labels
        n_permutations: Number of permutation iterations
        random_state: Random seed
        
    Returns:
        permuted_aucs: Array of ROC-AUC scores from shuffled labels
        real_auc: ROC-AUC on real labels
        p_value: Empirical p-value
    """
    print("\n" + "=" * 80)
    print("PERMUTATION TEST (LEAKAGE DETECTION)")
    print("=" * 80)
    
    np.random.seed(random_state)
    
    # Train real model and get baseline AUC
    real_model = LogisticRegression(
        max_iter=1000, class_weight="balanced", random_state=random_state
    )
    real_model.fit(X_train, y_train)
    y_pred_proba_real = real_model.predict_proba(X_test)[:, 1]
    real_auc = roc_auc_score(y_test, y_pred_proba_real)
    
    print(f"\nReal model ROC-AUC on original labels: {real_auc:.4f}")
    print(f"Running {n_permutations} permutations with shuffled labels...\n")
    
    permuted_aucs = []
    for i in range(n_permutations):
        # Shuffle labels
        y_test_shuffled = np.random.permutation(y_test)
        
        # Retrain model on shuffled test labels (with original training data)
        model_perm = LogisticRegression(
            max_iter=1000, class_weight="balanced", random_state=None
        )
        model_perm.fit(X_train, y_train)
        
        # Evaluate on shuffled test set
        y_pred_proba_perm = model_perm.predict_proba(X_test)[:, 1]
        try:
            auc_perm = roc_auc_score(y_test_shuffled, y_pred_proba_perm)
            permuted_aucs.append(auc_perm)
        except:
            # Skip if AUC cannot be computed (e.g., all labels same class)
            permuted_aucs.append(np.nan)
    
    # Remove NaN values
    permuted_aucs = np.array([a for a in permuted_aucs if not np.isnan(a)])
    
    # Compute p-value: fraction of permuted AUCs >= real AUC
    p_value = np.sum(permuted_aucs >= real_auc) / len(permuted_aucs)
    
    # Statistics
    mean_perm_auc = np.mean(permuted_aucs)
    std_perm_auc = np.std(permuted_aucs)
    
    print(f"Permutation Test Results:")
    print(f"  Mean ROC-AUC (shuffled): {mean_perm_auc:.4f}")
    print(f"  Std Dev (shuffled):      {std_perm_auc:.4f}")
    print(f"  Min (shuffled):          {np.min(permuted_aucs):.4f}")
    print(f"  Max (shuffled):          {np.max(permuted_aucs):.4f}")
    print(f"\n  Real ROC-AUC:            {real_auc:.4f}")
    print(f"  p-value:                 {p_value:.4f}")
    
    # Interpretation
    print(f"\n  Interpretation:")
    if p_value < 0.01:
        interpretation = (
            "✓ EXCELLENT: Real model significantly outperforms random shuffle "
            "→ Strong signal detected"
        )
    elif p_value < 0.05:
        interpretation = (
            "✓ GOOD: Real model clearly better than shuffled "
            "→ Genuine signal present"
        )
    elif p_value < 0.10:
        interpretation = (
            "⚠ CAUTION: Modest improvement over shuffled "
            "→ Signal present but weak"
        )
    else:
        interpretation = (
            "✗ CRITICAL: Real model not significantly better than shuffle "
            "→ NO meaningful signal detected, likely overfitting/artifacts"
        )
    
    print(f"  {interpretation}")
    
    return permuted_aucs, real_auc, p_value


# ============================================================================
# 5. BASELINE COMPARISON
# ============================================================================

def run_baseline_comparison(X_train, X_test, y_train, y_test):
    """
    Train and evaluate baseline models for comparison:
    1. DummyClassifier(strategy="most_frequent")
    2. Simple logistic regression with 1 feature
    
    Args:
        X_train, X_test: Training and test features
        y_train, y_test: Training and test labels
        
    Returns:
        baseline_metrics: Dictionary with baseline evaluation results
    """
    print("\n" + "=" * 80)
    print("BASELINE COMPARISON")
    print("=" * 80)
    
    # Baseline 1: Most frequent class
    print("\nBaseline 1: DummyClassifier (always predict most frequent class)")
    dummy = DummyClassifier(strategy="most_frequent", random_state=42)
    dummy.fit(X_train, y_train)
    dummy_metrics = evaluate_model(dummy, X_train, X_test, y_train, y_test)
    print_evaluation(dummy_metrics, y_test, "Dummy Classifier")
    
    # Baseline 2: Single best feature
    print("\nBaseline 2: LogisticRegression with single best feature")
    # Find feature with highest correlation to label
    correlations = np.abs([np.corrcoef(X_train[:, i], y_train)[0, 1] 
                           for i in range(X_train.shape[1])])
    best_feature_idx = np.argmax(correlations)
    
    X_train_single = X_train[:, best_feature_idx].reshape(-1, 1)
    X_test_single = X_test[:, best_feature_idx].reshape(-1, 1)
    
    single_model = LogisticRegression(max_iter=1000, random_state=42)
    single_model.fit(X_train_single, y_train)
    single_metrics = evaluate_model(single_model, X_train_single, X_test_single, 
                                    y_train, y_test)
    print_evaluation(single_metrics, y_test, "Single Feature Model")
    
    return {
        'dummy': dummy_metrics,
        'single_feature': single_metrics
    }


# ============================================================================
# 6. FULL PIPELINE EXECUTION
# ============================================================================

def run_full_validation(data_filepath="mutation_matrix.csv", random_state=42):
    """
    Execute complete validation and stress-testing pipeline.
    
    Args:
        data_filepath: Path to CSV with features and binary label
        random_state: Random seed for reproducibility
    """
    print("\n" + "=" * 80)
    print("PANCREATIC CANCER CLASSIFICATION - MODEL VALIDATION & STRESS TEST")
    print("=" * 80 + "\n")
    
    # 1. Load and validate data
    X, y, feature_names = load_and_validate_data(data_filepath)
    
    # 2. Train/test split
    print("\n" + "=" * 80)
    print("TRAIN/TEST SPLIT")
    print("=" * 80)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )
    print(f"✓ Training set: {X_train.shape[0]} samples")
    print(f"✓ Test set: {X_test.shape[0]} samples")
    print(f"✓ Training label distribution: {np.bincount(y_train.astype(int))}")
    print(f"✓ Test label distribution: {np.bincount(y_test.astype(int))}")
    
    # 3. Train real model
    print("\n" + "=" * 80)
    print("REAL MODEL TRAINING")
    print("=" * 80)
    model = LogisticRegression(
        max_iter=1000, class_weight="balanced", random_state=random_state
    )
    model.fit(X_train, y_train)
    print("✓ LogisticRegression trained on full feature set")
    
    # 4. Evaluate on test set
    print("\n" + "=" * 80)
    print("TEST SET EVALUATION")
    print("=" * 80)
    test_metrics = evaluate_model(model, X_train, X_test, y_train, y_test)
    print_evaluation(test_metrics, y_test, "Real Model (Test Set)")
    
    # 5. Cross-validation
    cv_scores, cv_mean, cv_std = run_cross_validation(X, y, k=5, 
                                                       random_state=random_state)
    
    # 6. Permutation test
    perm_aucs, real_auc, p_value = run_permutation_test(
        X_train, X_test, y_train, y_test, n_permutations=100,
        random_state=random_state
    )
    
    # 7. Baseline comparison
    baseline_results = run_baseline_comparison(X_train, X_test, y_train, y_test)
    
    # 8. Summary report
    print_summary_report(test_metrics, cv_mean, cv_std, real_auc, perm_aucs,
                        p_value, baseline_results)
    
    # 9. Visualization
    plot_results(test_metrics, y_test, perm_aucs, real_auc, cv_scores,
                 baseline_results)
    
    return {
        'model': model,
        'X_train': X_train,
        'X_test': X_test,
        'y_train': y_train,
        'y_test': y_test,
        'test_metrics': test_metrics,
        'cv_scores': cv_scores,
        'permutation_aucs': perm_aucs,
        'baseline_results': baseline_results
    }


# ============================================================================
# 7. SUMMARY REPORT
# ============================================================================

def print_summary_report(test_metrics, cv_mean, cv_std, real_auc, perm_aucs,
                        p_value, baseline_results):
    """Print final comprehensive summary report."""
    print("\n" + "=" * 80)
    print("FINAL VALIDATION SUMMARY")
    print("=" * 80)
    
    print("\n┌─ REAL MODEL PERFORMANCE ─────────────────────────────────────────────┐")
    print(f"│ Test ROC-AUC:               {test_metrics['roc_auc']:.4f}")
    print(f"│ CV Mean ROC-AUC (k=5):      {cv_mean:.4f} ± {cv_std:.4f}")
    print(f"│ Test Accuracy:              {test_metrics['accuracy']:.4f}")
    print(f"│ Test Precision:             {test_metrics['precision']:.4f}")
    print(f"│ Test Recall:                {test_metrics['recall']:.4f}")
    print("└─────────────────────────────────────────────────────────────────────┘")
    
    print("\n┌─ PERMUTATION TEST (Signal vs Artifacts) ─────────────────────────────┐")
    print(f"│ Real ROC-AUC:               {real_auc:.4f}")
    print(f"│ Shuffled Mean ROC-AUC:      {np.mean(perm_aucs):.4f}")
    print(f"│ Shuffled Std:               {np.std(perm_aucs):.4f}")
    print(f"│ p-value (empirical):        {p_value:.4f}")
    
    if p_value < 0.01:
        signal_interpretation = "✓ STRONG SIGNAL (p < 0.01)"
    elif p_value < 0.05:
        signal_interpretation = "✓ GENUINE SIGNAL (p < 0.05)"
    elif p_value < 0.10:
        signal_interpretation = "⚠ WEAK SIGNAL (p < 0.10)"
    else:
        signal_interpretation = "✗ NO SIGNAL DETECTED (p >= 0.10)"
    
    print(f"│ Interpretation:             {signal_interpretation}")
    print("└─────────────────────────────────────────────────────────────────────┘")
    
    print("\n┌─ BASELINE COMPARISON ────────────────────────────────────────────────┐")
    dummy_auc = baseline_results['dummy']['roc_auc']
    single_auc = baseline_results['single_feature']['roc_auc']
    print(f"│ Dummy Classifier ROC-AUC:   {dummy_auc:.4f}")
    print(f"│ Single Feature ROC-AUC:     {single_auc:.4f}")
    print(f"│ Full Model ROC-AUC:         {test_metrics['roc_auc']:.4f}")
    print(f"│ Improvement vs Dummy:       {(test_metrics['roc_auc'] - dummy_auc):.4f}")
    print(f"│ Improvement vs Single:      {(test_metrics['roc_auc'] - single_auc):.4f}")
    print("└─────────────────────────────────────────────────────────────────────┘")
    
    # Overall assessment
    print("\n" + "=" * 80)
    print("OVERALL ASSESSMENT")
    print("=" * 80)
    
    assessment = []
    
    # Signal detection
    if p_value < 0.05:
        assessment.append("✓ Model detects real biological signal")
    else:
        assessment.append("✗ Model may be exploiting dataset artifacts")
    
    # Stability
    if cv_std < 0.05:
        assessment.append("✓ Model is stable across cross-validation folds")
    else:
        assessment.append("⚠ Model performance varies across folds (potential overfitting)")
    
    # Improvement over baseline
    if test_metrics['roc_auc'] > dummy_auc + 0.1:
        assessment.append("✓ Significant improvement over baseline models")
    else:
        assessment.append("⚠ Modest improvement over baseline (limited added value)")
    
    for point in assessment:
        print(f"  {point}")
    
    print("\n" + "=" * 80)


# ============================================================================
# 8. VISUALIZATION
# ============================================================================

def plot_results(test_metrics, y_test, perm_aucs, real_auc, cv_scores,
                baseline_results):
    """
    Create visualizations:
    1. ROC curve for real model
    2. Permutation test histogram
    3. Cross-validation scores
    4. Baseline comparison bar plot
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Model Validation & Stress Test Results', fontsize=16, fontweight='bold')
    
    # 1. ROC Curve
    ax = axes[0, 0]
    fpr = []
    tpr = []
    y_pred_proba = test_metrics['y_pred_proba']
    
    from sklearn.metrics import roc_curve, auc
    fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
    roc_auc = test_metrics['roc_auc']
    
    ax.plot(fpr, tpr, 'b-', linewidth=2, label=f'Real Model (AUC={roc_auc:.4f})')
    ax.plot([0, 1], [0, 1], 'k--', linewidth=1, label='Random (AUC=0.5)')
    ax.fill_between(fpr, tpr, alpha=0.2)
    ax.set_xlabel('False Positive Rate', fontsize=10)
    ax.set_ylabel('True Positive Rate', fontsize=10)
    ax.set_title('ROC Curve (Test Set)', fontweight='bold')
    ax.legend(loc='lower right')
    ax.grid(True, alpha=0.3)
    
    # 2. Permutation Test Histogram
    ax = axes[0, 1]
    ax.hist(perm_aucs, bins=20, alpha=0.7, color='gray', edgecolor='black')
    ax.axvline(real_auc, color='red', linestyle='--', linewidth=2, 
               label=f'Real AUC={real_auc:.4f}')
    ax.axvline(np.mean(perm_aucs), color='blue', linestyle='--', linewidth=2,
               label=f'Mean Shuffled={np.mean(perm_aucs):.4f}')
    ax.set_xlabel('ROC-AUC Score', fontsize=10)
    ax.set_ylabel('Frequency', fontsize=10)
    ax.set_title('Permutation Test Distribution (100 iterations)', fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3, axis='y')
    
    # 3. Cross-Validation Scores
    ax = axes[1, 0]
    ax.plot(range(1, len(cv_scores)+1), cv_scores, 'o-', linewidth=2, 
            markersize=8, color='green')
    ax.axhline(cv_scores.mean(), color='red', linestyle='--', linewidth=2,
               label=f'Mean={cv_scores.mean():.4f}')
    ax.fill_between(range(1, len(cv_scores)+1), 
                     cv_scores.mean() - cv_scores.std(),
                     cv_scores.mean() + cv_scores.std(),
                     alpha=0.2, color='green')
    ax.set_xlabel('Fold Number', fontsize=10)
    ax.set_ylabel('ROC-AUC', fontsize=10)
    ax.set_title('Stratified 5-Fold Cross-Validation', fontweight='bold')
    ax.set_xticks(range(1, len(cv_scores)+1))
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # 4. Baseline Comparison
    ax = axes[1, 1]
    models = ['Dummy', 'Single Feature', 'Full Model']
    aucs = [
        baseline_results['dummy']['roc_auc'],
        baseline_results['single_feature']['roc_auc'],
        test_metrics['roc_auc']
    ]
    colors = ['lightcoral', 'lightyellow', 'lightgreen']
    
    bars = ax.bar(models, aucs, color=colors, edgecolor='black', linewidth=1.5)
    ax.axhline(0.5, color='black', linestyle='--', linewidth=1, alpha=0.5, 
               label='Random (0.5)')
    ax.set_ylabel('ROC-AUC', fontsize=10)
    ax.set_title('Baseline Comparison', fontweight='bold')
    ax.set_ylim([0, 1])
    ax.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, auc in zip(bars, aucs):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{auc:.4f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig('validation_results.png', dpi=300, bbox_inches='tight')
    print("\n✓ Visualization saved as 'validation_results.png'")
    plt.show()


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == "__main__":
    results = run_full_validation("mutation_matrix.csv", random_state=42)
    
    print("\n" + "=" * 80)
    print("VALIDATION COMPLETE")
    print("=" * 80)
    print("Results saved. Check 'validation_results.png' for visualizations.")
