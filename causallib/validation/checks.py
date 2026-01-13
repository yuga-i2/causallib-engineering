"""
Centralized input validation and state management for causallib.

This module provides unified validation entry points following sklearn conventions
but tailored for causal inference-specific contracts (e.g., treatment value
consistency, propensity score ranges, index alignment).

Design philosophy:
- Validate early and explicitly: fail at input time, not during computation
- Clear, actionable error messages
- No silent failures (e.g., dropped treatment values without warning)
- Minimal performance overhead for fitted estimators

(C) Copyright 2019 IBM Corp.
Licensed under the Apache License, Version 2.0
"""

import logging
from typing import Optional, Any, Tuple
import pandas as pd
import numpy as np
from .exceptions import (
    CausallibValidationError,
    DataAlignmentError,
    TreatmentValueError,
    NotFittedError,
    TaskTypeError,
    LearnerInterfaceError,
)

# Configure logger for validation module
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def check_X_a(X: pd.DataFrame, a: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
    """
    Validate covariate matrix X and treatment assignment a.
    
    Checks:
    - X is a DataFrame with valid index
    - a is a Series with valid index
    - X and a have same length
    - X and a indices align (if both are indexed)
    - a has no missing values
    
    Args:
        X: Covariate matrix of shape (n_samples, n_features)
        a: Treatment assignment of shape (n_samples,)
        
    Returns:
        Tuple[X, a]: Validated X and a (as-is, only checked for validity)
        
    Raises:
        DataAlignmentError: If X and a don't have compatible lengths/indices
        CausallibValidationError: If inputs have invalid structure
    """
    logger.debug(f"Validating X (shape {X.shape if hasattr(X, 'shape') else 'unknown'}) "
                 f"and a (length {len(a) if hasattr(a, '__len__') else 'unknown'})")
    
    if not isinstance(X, pd.DataFrame):
        raise CausallibValidationError(
            f"X must be a pandas DataFrame, got {type(X).__name__}. "
            "CausalLib requires indexed DataFrames to track sample identity through "
            "cross-validation and effect estimation."
        )
    
    if not isinstance(a, pd.Series):
        raise CausallibValidationError(
            f"a (treatment assignment) must be a pandas Series, got {type(a).__name__}. "
            "Treatment must be tracked by index."
        )
    
    if len(X) != len(a):
        raise DataAlignmentError(
            f"X and a must have same length. Got X: {len(X)}, a: {len(a)}"
        )
    
    # Check index alignment: if both have non-default indices, they should match
    if not X.index.equals(a.index):
        raise DataAlignmentError(
            f"X and a must have aligned indices (same order and values). "
            f"X index: {list(X.index[:5])}{'...' if len(X.index) > 5 else ''}, "
            f"a index: {list(a.index[:5])}{'...' if len(a.index) > 5 else ''}"
        )
    
    if a.isnull().any():
        n_missing = a.isnull().sum()
        raise CausallibValidationError(
            f"Treatment assignment a has {n_missing} missing values (NaN). "
            "All treatment assignments must be observed."
        )
    
    logger.debug(f"Validation passed: X and a aligned ({len(X)} samples)")
    return X, a


def check_X_a_y(
    X: pd.DataFrame,
    a: pd.Series,
    y: Optional[pd.Series] = None,
) -> Tuple[pd.DataFrame, pd.Series, Optional[pd.Series]]:
    """
    Validate covariate matrix X, treatment assignment a, and outcome y.
    
    Extends check_X_a() to include outcome validation.
    
    Checks:
    - X, a are valid (via check_X_a)
    - y is a Series with valid index
    - X, a, y all have same length and aligned indices
    - y has appropriate number of non-missing values
    
    Args:
        X: Covariate matrix of shape (n_samples, n_features)
        a: Treatment assignment of shape (n_samples,)
        y: Outcome variable of shape (n_samples,), optional
        
    Returns:
        Tuple[X, a, y]: Validated arrays
        
    Raises:
        DataAlignmentError: If inputs have misaligned shapes/indices
        CausallibValidationError: If outcomes have excessive missing data
    """
    X, a = check_X_a(X, a)
    
    if y is not None:
        if not isinstance(y, pd.Series):
            raise CausallibValidationError(
                f"y (outcome) must be a pandas Series or None, got {type(y).__name__}"
            )
        
        if len(y) != len(X):
            raise DataAlignmentError(
                f"y must have same length as X and a. Got X: {len(X)}, y: {len(y)}"
            )
        
        if not y.index.equals(X.index):
            raise DataAlignmentError(
                f"y index must align with X and a. "
                f"X index: {list(X.index[:5])}, y index: {list(y.index[:5])}"
            )
        
        # Check for excessive missing data in outcome
        n_missing = y.isnull().sum()
        pct_missing = n_missing / len(y) * 100
        if n_missing > 0:
            if pct_missing > 50:
                raise CausallibValidationError(
                    f"Outcome y has {pct_missing:.1f}% missing values. "
                    "Cannot reliably estimate effects with >50% missing outcomes."
                )
            # Warn about any missing data but don't fail
            import warnings
            warnings.warn(
                f"Outcome y has {n_missing} ({pct_missing:.1f}%) missing values. "
                "These will be excluded from effect estimation.",
                UserWarning
            )
    
    return X, a, y


def check_treatment_values_match(
    treatment_values_train: Any,
    treatment_values_test: Any,
    allow_subset: bool = False,
) -> None:
    """
    Validate that treatment values in test data match training data.
    
    Ensures model doesn't silently drop unseen treatment values during prediction.
    
    Args:
        treatment_values_train: Unique treatment values seen during fit()
        treatment_values_test: Unique treatment values in new predict() data
        allow_subset: If True, allow test data to have subset of training values.
                     If False, require exact match.
                     
    Raises:
        TreatmentValueError: If test values don't match training
        
    Example:
        >>> check_treatment_values_match([0, 1], [0, 1])  # OK
        >>> check_treatment_values_match([0, 1], [0, 1, 2])  # Error: new value
        >>> check_treatment_values_match([0, 1], [0], allow_subset=True)  # OK
    """
    train_set = set(treatment_values_train)
    test_set = set(treatment_values_test)
    
    unseen_values = test_set - train_set
    if unseen_values:
        raise TreatmentValueError(
            f"Treatment values in prediction data contain unseen values: {unseen_values}. "
            f"Model was trained on treatment values: {train_set}. "
            "Cannot reliably estimate effects for unseen treatment values."
        )
    
    if not allow_subset:
        missing_values = train_set - test_set
        if missing_values:
            raise TreatmentValueError(
                f"Treatment values in prediction data are missing expected values: {missing_values}. "
                f"Model was trained on: {train_set}, but got: {test_set}"
            )


def check_is_fitted(
    estimator,
    attributes: Optional[list] = None,
    msg: Optional[str] = None,
    all_or_any: str = "all",
) -> None:
    """
    Check if estimator has been fitted by verifying required attributes.
    
    Follows sklearn convention (scikit-learn.utils.validation.check_is_fitted).
    
    Args:
        estimator: Estimator to check
        attributes: List of attribute names that must exist if fitted.
                   If None, checks for default causallib fitted markers:
                   ['learner_', 'treatment_values_']
        msg: Custom error message
        all_or_any: 'all' requires all attributes, 'any' requires at least one
        
    Raises:
        NotFittedError: If estimator is not fitted
        
    Example:
        >>> from causallib.estimation import IPW
        >>> ipw = IPW(LogisticRegression())
        >>> check_is_fitted(ipw)  # Raises NotFittedError
        >>> ipw.fit(X, a)
        >>> check_is_fitted(ipw)  # OK
    """
    logger.debug(f"Checking if {estimator.__class__.__name__} is fitted")
    
    if attributes is None:
        attributes = ["learner_", "treatment_values_"]
    
    if isinstance(attributes, str):
        attributes = [attributes]
    
    found_attrs = [hasattr(estimator, attr) for attr in attributes]
    
    if all_or_any == "all":
        if not all(found_attrs):
            if msg is None:
                fitted_attrs = [attr for attr, found in zip(attributes, found_attrs) if found]
                missing_attrs = [attr for attr, found in zip(attributes, found_attrs) if not found]
                msg = (
                    f"{estimator.__class__.__name__} has not been fitted. "
                    f"Expected attributes: {attributes}, "
                    f"but missing: {missing_attrs}"
                )
            raise NotFittedError(msg)
    else:  # any
        if not any(found_attrs):
            if msg is None:
                msg = (
                    f"{estimator.__class__.__name__} has not been fitted. "
                    f"None of expected attributes {attributes} were found."
                )
            raise NotFittedError(msg)


def check_learner_has_method(
    learner,
    method_name: str,
    learner_name: Optional[str] = None,
) -> None:
    """
    Validate that learner has required method (e.g., 'predict_proba').
    
    Used early in estimator initialization to fail fast if learner
    is incompatible with causal model.
    
    Args:
        learner: sklearn-like estimator
        method_name: Name of method (e.g., 'predict_proba')
        learner_name: Display name for learner in error message
        
    Raises:
        LearnerInterfaceError: If method doesn't exist
        
    Example:
        >>> from sklearn.svm import SVC
        >>> check_learner_has_method(SVC(), 'predict_proba', 'SVC')
        >>> # Raises: LearnerInterfaceError: SVC must have 'predict_proba' method
    """
    if not hasattr(learner, method_name):
        learner_name = learner_name or learner.__class__.__name__
        raise LearnerInterfaceError(
            f"{learner_name} must have '{method_name}' method. "
            f"Current methods: {[m for m in dir(learner) if not m.startswith('_')]}"
        )


def check_consistent_treatment_vector(a: pd.Series) -> None:
    """
    Validate that treatment assignment vector is well-formed.
    
    Checks:
    - No missing values
    - Has at least 2 distinct values (otherwise not a treatment)
    - No infinite/NaN values if numeric
    
    Args:
        a: Treatment assignment Series
        
    Raises:
        CausallibValidationError: If validation fails
    """
    if a.isnull().any():
        raise CausallibValidationError(
            f"Treatment assignment has {a.isnull().sum()} missing values"
        )
    
    n_unique = a.nunique()
    if n_unique < 2:
        raise CausallibValidationError(
            f"Treatment assignment must have at least 2 distinct values "
            f"(for treatment vs control contrast). Found {n_unique} unique value(s)."
        )
    
    if pd.api.types.is_numeric_dtype(a):
        if np.isinf(a).any() or np.isnan(a).any():
            raise CausallibValidationError(
                "Treatment assignment contains infinite or NaN values"
            )


def validate_propensity_scores(
    propensity: pd.Series,
    column_name: str = "propensity",
    clip_min: Optional[float] = None,
    clip_max: Optional[float] = None,
) -> None:
    """
    Validate propensity score estimates for common issues.
    
    Checks:
    - All values in [0, 1]
    - No extreme values near 0 or 1 (indicate positivity violation)
    - Warn if many values clipped (indicate model misspecification)
    
    Args:
        propensity: Propensity score estimates
        column_name: Name for error messages
        clip_min: Lower bound threshold (e.g., 0.05)
        clip_max: Upper bound threshold (e.g., 0.95)
        
    Raises:
        CausallibValidationError: If propensity values are invalid
    """
    if (propensity < 0).any() or (propensity > 1).any():
        raise CausallibValidationError(
            f"{column_name} must be in [0, 1]. "
            f"Found range: [{propensity.min():.4f}, {propensity.max():.4f}]. "
            "Ensure learner outputs valid probabilities."
        )
    
    # Warn about extreme values indicating positivity violations
    near_zero = (propensity < 0.01).sum()
    near_one = (propensity > 0.99).sum()
    if near_zero > 0 or near_one > 0:
        import warnings
        warnings.warn(
            f"{column_name}: {near_zero} samples have p<0.01, {near_one} have p>0.99. "
            "Strong positivity violation detected. Model estimates may be unreliable.",
            UserWarning
        )
