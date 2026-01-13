"""
Custom exception types for causallib validation and state management.

This module provides production-ready exception classes with clear,
actionable error messages for users and developers.

(C) Copyright 2019 IBM Corp.
Licensed under the Apache License, Version 2.0
"""


class CausallibValidationError(ValueError):
    """
    Base exception for input validation failures in causallib.
    
    Raised when input data violates causal modeling assumptions or
    causallib-specific requirements (e.g., index alignment, treatment values).
    
    Inherits from ValueError to maintain sklearn error hierarchy compatibility.
    """
    pass


class DataAlignmentError(CausallibValidationError):
    """
    Raised when X, a, y, or other inputs have misaligned indices or lengths.
    
    Example:
        >>> X = pd.DataFrame({"feat": [1, 2]}, index=[0, 1])
        >>> a = pd.Series([0, 1], index=[5, 6])  # Different index
        >>> DataAlignmentError: "Indices must align: X has index [0, 1], but a has [5, 6]"
    """
    pass


class TreatmentValueError(CausallibValidationError):
    """
    Raised when treatment values in new data don't match training data.
    
    Example:
        Model trained on a ∈ {0, 1}, but predict() receives a=2.
    """
    pass


class TaskTypeError(CausallibValidationError):
    """
    Raised when learner task type (classification vs regression) is misspecified
    or inconsistent with outcome data.
    
    Example:
        >>> outcome = pd.Series([1.5, 2.3, 3.1])  # Continuous
        >>> learner = LogisticRegression()  # Classification-only learner
        >>> TaskTypeError: "Cannot use classification learner (LogisticRegression) "
        >>>                "with continuous outcome. Use a regression learner."
    """
    pass


class NotFittedError(CausallibValidationError):
    """
    Raised when attempting to call predict/estimate on an unfitted estimator.
    
    Follows sklearn convention (scikit-learn.exceptions.NotFittedError).
    """
    pass


class PositivityViolationError(CausallibValidationError):
    """
    Raised when common support (positivity) assumption is violated.
    
    Example:
        Propensity scores are extremely close to 0 or 1, indicating
        insufficient overlap between treatment and control groups.
    """
    pass


class LearnerInterfaceError(CausallibValidationError):
    """
    Raised when provided learner doesn't conform to sklearn estimator interface.
    
    Example:
        >>> ipw = IPW(my_estimator)
        >>> LearnerInterfaceError: "Learner must have 'predict_proba' method "
        >>>                        "for probability prediction"
    """
    pass
