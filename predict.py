"""
StockScope AI - Prediction Generation Module
Generates directional predictions and probabilities for the next trading session
using the trained Scikit-Learn Pipeline and the latest available feature vector.
"""

from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline

from src.features import FEATURE_DOCUMENTATION


def predict_next_day(
    pipeline: Pipeline,
    latest_feature_row: pd.DataFrame,
    model_name: str,
    feature_importance_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    Generate next-trading-day directional prediction and movement probabilities.

    Returns:
        Dict containing predicted direction, probabilities, dates, confidence,
        and contributing feature context.
    """
    if latest_feature_row.empty:
        raise ValueError("Cannot predict on an empty feature row.")

    # 1. Generate prediction and probabilities
    pred_class = int(pipeline.predict(latest_feature_row)[0])
    
    if hasattr(pipeline, "predict_proba"):
        probs = pipeline.predict_proba(latest_feature_row)[0]
        prob_down = float(probs[0])
        prob_up = float(probs[1])
    else:
        # Fallback if probability is not supported
        prob_up = 1.0 if pred_class == 1 else 0.0
        prob_down = 1.0 - prob_up

    # 2. Format direction label
    if pred_class == 1:
        direction_label = "Upward Movement (Bullish)"
        direction_short = "UP"
    else:
        direction_label = "Downward or Unchanged (Bearish/Neutral)"
        direction_short = "DOWN"

    # 3. Assess probabilistic confidence level
    # Proximity to 0.5 implies low confidence; farther implies higher confidence
    max_prob = max(prob_up, prob_down)
    if max_prob >= 0.65:
        confidence = "High Confidence"
    elif max_prob >= 0.55:
        confidence = "Moderate Confidence"
    else:
        confidence = "Low Confidence (Near 50/50 Chance)"

    # 4. Top features context
    top_contributors = []
    if feature_importance_df is not None and not feature_importance_df.empty:
        top_k = feature_importance_df.head(5)
        for _, row in top_k.iterrows():
            feat_name = row["feature"]
            feat_val = latest_feature_row[feat_name].values[0] if feat_name in latest_feature_row else np.nan
            doc_desc = FEATURE_DOCUMENTATION.get(feat_name, "Technical indicator feature.")
            top_contributors.append({
                "feature": feat_name,
                "importance": float(row["importance"]),
                "current_value": float(feat_val) if not pd.isna(feat_val) else None,
                "description": doc_desc,
            })

    feature_date_str = latest_feature_row.index[0].strftime("%Y-%m-%d") if hasattr(latest_feature_row.index[0], "strftime") else str(latest_feature_row.index[0])[:10]

    return {
        "model_name": model_name,
        "feature_date": feature_date_str,
        "prediction_target": "Next Available Trading Session",
        "predicted_class": pred_class,
        "predicted_direction": direction_label,
        "direction_short": direction_short,
        "prob_up": prob_up,
        "prob_down": prob_down,
        "prob_up_pct": prob_up * 100.0,
        "prob_down_pct": prob_down * 100.0,
        "confidence": confidence,
        "top_contributors": top_contributors,
        "disclaimer": (
            "Probabilities are model-generated statistical estimates based on historical features. "
            "They do not guarantee market movement."
        )
    }
