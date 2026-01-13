"""
Centralized propensity score computation and utilities.

This module provides shared propensity score functions used across IPW, Matching,
DoublyRobust, and other estimators that require propensity-based weighting.

Design rationale:
- Single source of truth for propensity computation
- Consistent clipping, validation, stabilization logic
- Reusable across weight-based and hybrid estimators
- Clear separation: learner training vs score extraction

(C) Copyright 2019 IBM Corp.
Licensed under the Apache License, Version 2.0
"""

from typing import Optional, Union
import pandas as pd
import numpy as np
import warnings


def extract_propensity_scores(
    learner,
    X: pd.DataFrame,
) -> pd.DataFrame:
    """
    Extract propensity score matrix from fitted learner.
    
    Handles both sklearn-style learners with predict_proba() and
    those with decision_function(). Returns a DataFrame with
    treatment values as columns.
    
    Args:
        learner: Fitted sklearn-like classifier with predict_proba or decision_function
        X: Covariate matrix for prediction
        
    Returns:
        pd.DataFrame: Shape (n_samples, n_treatments) with propensity scores.
                     Columns are treatment class labels.
                     Index matches X.index.
                     
    Raises:
        AttributeError: If learner has neither predict_proba nor decision_function
    """
    if hasattr(learner, "predict_proba"):
        probability_matrix = learner.predict_proba(X)
        classes = getattr(learner, "classes_", None)
    elif hasattr(learner, "decision_function"):
        probability_matrix = learner.decision_function(X)
        classes = None
    else:
        raise AttributeError(
            f"Learner {learner.__class__.__name__} must have 'predict_proba' or "
            "'decision_function' method for propensity score extraction."
        )
    
    # Convert to DataFrame with meaningful column names
    if isinstance(probability_matrix, np.ndarray):
        if len(probability_matrix.shape) == 1:
            # decision_function result: single column
            probability_matrix = probability_matrix.reshape(-1, 1)
            columns = [0] if classes is None else [classes[0]]
        else:
            columns = classes if classes is not None else list(range(probability_matrix.shape[1]))
        
        probability_matrix = pd.DataFrame(
            probability_matrix,
            index=X.index,
            columns=columns
        )
    
    return probability_matrix


def clip_propensity_scores(
    propensity_matrix: pd.DataFrame,
    clip_min: Optional[float] = None,
    clip_max: Optional[float] = None,
    verbose: bool = False,
) -> tuple[pd.DataFrame, dict]:
    """
    Clip propensity score estimates to valid range.
    
    Clipping prevents extreme weights (when p near 0 or 1).
    Returns clipped matrix and statistics about clipping.
    
    Args:
        propensity_matrix: DataFrame of propensity scores in [0, 1]
        clip_min: Lower bound (e.g., 0.05). If None, no lower clipping.
        clip_max: Upper bound (e.g., 0.95). If None, no upper clipping.
        verbose: If True, print clipping statistics
        
    Returns:
        Tuple[clipped_matrix, stats_dict] where stats_dict contains:
        - 'n_clipped_min': Number of values clipped to clip_min
        - 'n_clipped_max': Number of values clipped to clip_max
        - 'pct_clipped': Percentage of all values clipped
        
    Raises:
        ValueError: If clip_min >= clip_max or outside [0, 1]
    """
    _validate_clip_bounds(clip_min, clip_max)
    
    clipped = propensity_matrix.copy()
    n_total = propensity_matrix.size
    
    n_clipped_min = 0
    n_clipped_max = 0
    
    if clip_min is not None:
        clipped_min_mask = clipped < clip_min
        n_clipped_min = clipped_min_mask.sum().sum()
        clipped[clipped_min_mask] = clip_min
    
    if clip_max is not None:
        clipped_max_mask = clipped > clip_max
        n_clipped_max = clipped_max_mask.sum().sum()
        clipped[clipped_max_mask] = clip_max
    
    n_clipped_total = n_clipped_min + n_clipped_max
    pct_clipped = n_clipped_total / n_total * 100
    
    stats = {
        'n_clipped_min': n_clipped_min,
        'n_clipped_max': n_clipped_max,
        'pct_clipped': pct_clipped,
    }
    
    if verbose and n_clipped_total > 0:
        print(
            f"Propensity score clipping: {n_clipped_min} values clipped to {clip_min}, "
            f"{n_clipped_max} values clipped to {clip_max} ({pct_clipped:.2f}% total)"
        )
    
    return clipped, stats


def _validate_clip_bounds(
    clip_min: Optional[float],
    clip_max: Optional[float],
) -> None:
    """Validate clip_min and clip_max parameters."""
    if clip_min is not None:
        if not (0 <= clip_min <= 0.5):
            raise ValueError(
                f"clip_min must be in [0, 0.5], got {clip_min}"
            )
    
    if clip_max is not None:
        if not (0.5 <= clip_max <= 1):
            raise ValueError(
                f"clip_max must be in [0.5, 1], got {clip_max}"
            )
    
    if clip_min is not None and clip_max is not None:
        if clip_min >= clip_max:
            raise ValueError(
                f"clip_min ({clip_min}) must be < clip_max ({clip_max})"
            )


def compute_propensity_weights(
    propensity_matrix: pd.DataFrame,
    treatment_assignment: pd.Series,
    treatment_values: Optional[list] = None,
    use_stabilized: bool = False,
    treatment_prevalence: Optional[pd.Series] = None,
) -> Union[pd.Series, pd.DataFrame]:
    """
    Compute inverse probability weights from propensity scores.
    
    Implements IPW weight formula:
    w_i = 1 / P(A=a_i|X_i)
    
    With optional stabilization:
    w_i_stabilized = [P(A=a_i)] * [1 / P(A=a_i|X_i)]
    
    Args:
        propensity_matrix: (n_samples, n_treatments) DataFrame of P(A=a|X)
        treatment_assignment: (n_samples,) Series of observed treatment values
        treatment_values: Specific treatment value(s) to compute weights for.
                         If None, uses observed assignment.
                         If scalar or list, returns weights for those values.
        use_stabilized: If True, multiply by marginal treatment prevalence
        treatment_prevalence: Pre-computed P(A=a). If None and use_stabilized=True,
                            computed from treatment_assignment.
                            
    Returns:
        pd.Series if treatment_values is None or scalar: individual weights
        pd.DataFrame if treatment_values is list: weight matrix
        
    Raises:
        ValueError: If treatment values not in propensity_matrix columns
    """
    # Inverse probability weights: 1 / P(A|X)
    weights = propensity_matrix.rdiv(1.0)  # Element-wise reciprocal
    
    if use_stabilized:
        if treatment_prevalence is None:
            treatment_prevalence = treatment_assignment.value_counts(normalize=True, sort=False)
        
        # Multiply each row by the prevalence of that unit's treatment
        prevalence_per_sample = treatment_assignment.map(treatment_prevalence)
        weights = weights.multiply(prevalence_per_sample, axis="index")
    
    # Select specific treatment values if requested
    if treatment_values is not None:
        if isinstance(treatment_values, (int, str)):
            treatment_values = [treatment_values]
        weights = weights[treatment_values]
        
        if len(treatment_values) == 1:
            # Return Series if single treatment value
            return weights.iloc[:, 0]
    else:
        # Return weight for observed treatment assignment (lookup operation)
        from ..utils.stat_utils import robust_lookup
        weights = robust_lookup(weights, treatment_assignment)
    
    return weights


def stabilize_weights(
    weights: Union[pd.Series, pd.DataFrame],
    treatment_assignment: pd.Series,
) -> Union[pd.Series, pd.DataFrame]:
    """
    Apply stabilization to IPW weights.
    
    Stabilization reduces variance by multiplying by marginal treatment prevalence:
    w_stabilized = P(A=a) * w
    
    Args:
        weights: Raw inverse probability weights
        treatment_assignment: Observed treatment values
        
    Returns:
        Stabilized weights with same shape as input
    """
    prevalence = treatment_assignment.value_counts(normalize=True, sort=False)
    prevalence_per_sample = treatment_assignment.map(prevalence)
    
    return weights.multiply(prevalence_per_sample, axis="index")
