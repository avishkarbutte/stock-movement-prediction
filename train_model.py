"""
StockScope AI - Machine Learning Model Training Module
Implements chronological train-test splitting, scikit-learn Pipelines,
hyperparameter configurations, and feature importance extraction.
"""

from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd

from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.model_selection import TimeSeriesSplit

from config import ML_CONFIG


def chronological_train_test_split(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.20
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split time-series data chronologically.
    Never shuffles observations, preserving the temporal arrow of time.
    """
    n_samples = len(X)
    split_idx = int(n_samples * (1.0 - test_size))
    
    # Ensure at least 10 samples in test set and 20 in train set
    if split_idx < 20 or (n_samples - split_idx) < 10:
        split_idx = max(20, n_samples - 10)

    X_train = X.iloc[:split_idx]
    X_test = X.iloc[split_idx:]
    y_train = y.iloc[:split_idx]
    y_test = y.iloc[split_idx:]

    return X_train, X_test, y_train, y_test


def get_model_pipeline(model_name: str, random_state: int = 42) -> Pipeline:
    """
    Factory function to initialize Scikit-Learn Pipelines with appropriate
    scalers and robust classification algorithms.
    """
    if model_name == "Logistic Regression":
        # Logistic regression requires scaled features
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(
                C=1.0,
                max_iter=1000,
                class_weight="balanced",
                random_state=random_state,
                solver="lbfgs"
            ))
        ])
    elif model_name == "Random Forest Classifier":
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", RandomForestClassifier(
                n_estimators=100,
                max_depth=6,
                min_samples_split=10,
                min_samples_leaf=5,
                class_weight="balanced_subsample",
                random_state=random_state,
                n_jobs=-1
            ))
        ])
    elif model_name == "Gradient Boosting Classifier":
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", HistGradientBoostingClassifier(
                max_iter=100,
                max_depth=4,
                min_samples_leaf=10,
                learning_rate=0.05,
                class_weight="balanced",
                random_state=random_state
            ))
        ])
    else:
        raise ValueError(f"Unknown model name '{model_name}'.")

    return pipeline


def extract_feature_importance(
    pipeline: Pipeline,
    feature_names: List[str],
    X_test: Optional[pd.DataFrame] = None,
    y_test: Optional[pd.Series] = None
) -> pd.DataFrame:
    """
    Extract interpretable feature importance or coefficients from the trained model.
    Returns a sorted DataFrame: [feature, importance, absolute_importance].
    """
    classifier = pipeline.named_steps["classifier"]
    importance_scores = None

    if hasattr(classifier, "feature_importances_"):
        # Tree-based feature importances (e.g. Random Forest)
        importance_scores = classifier.feature_importances_
    elif hasattr(classifier, "coef_"):
        # Linear model coefficients (Logistic Regression)
        importance_scores = classifier.coef_[0]
    elif X_test is not None and y_test is not None:
        # Fallback to permutation importance on test set (e.g. HistGradientBoosting)
        try:
            r = permutation_importance(
                pipeline, X_test, y_test, n_repeats=5, random_state=42, n_jobs=-1
            )
            importance_scores = r.importances_mean
        except Exception:
            importance_scores = np.ones(len(feature_names)) / len(feature_names)
    else:
        importance_scores = np.ones(len(feature_names)) / len(feature_names)

    df_importance = pd.DataFrame({
        "feature": feature_names,
        "importance": importance_scores,
        "abs_importance": np.abs(importance_scores)
    }).sort_values(by="abs_importance", ascending=False).reset_index(drop=True)

    return df_importance


def train_single_model(
    model_name: str,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    random_state: int = 42
) -> Tuple[Pipeline, pd.DataFrame]:
    """
    Fit a single pipeline on chronological train data and extract feature importance.
    """
    pipeline = get_model_pipeline(model_name, random_state=random_state)
    pipeline.fit(X_train, y_train)

    feature_importance_df = extract_feature_importance(
        pipeline, list(X_train.columns), X_test, y_test
    )

    return pipeline, feature_importance_df


def train_all_models(
    X: pd.DataFrame,
    y: pd.Series,
    test_size: float = 0.20,
    random_state: int = 42
) -> Dict[str, Any]:
    """
    Train and compare all three models on the same chronological split.
    Returns dictionary with models, datasets, and feature importances.
    """
    X_train, X_test, y_train, y_test = chronological_train_test_split(
        X, y, test_size=test_size
    )

    models_dict = {}
    feature_importances_dict = {}

    for model_name in ML_CONFIG["models"].keys():
        pipeline, feat_imp = train_single_model(
            model_name, X_train, y_train, X_test, y_test, random_state=random_state
        )
        models_dict[model_name] = pipeline
        feature_importances_dict[model_name] = feat_imp

    return {
        "models": models_dict,
        "feature_importances": feature_importances_dict,
        "X_train": X_train,
        "X_test": X_test,
        "y_train": y_train,
        "y_test": y_test,
        "train_dates": (X_train.index[0].strftime("%Y-%m-%d"), X_train.index[-1].strftime("%Y-%m-%d")),
        "test_dates": (X_test.index[0].strftime("%Y-%m-%d"), X_test.index[-1].strftime("%Y-%m-%d")),
    }
