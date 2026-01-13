"""
Validation module initialization - public API.

This module provides centralized input validation and state checking for causallib,
ensuring production-ready error handling and early failure detection.

(C) Copyright 2019 IBM Corp.
Licensed under the Apache License, Version 2.0
"""

from .exceptions import (
    CausallibValidationError,
    DataAlignmentError,
    TreatmentValueError,
    NotFittedError,
    TaskTypeError,
    LearnerInterfaceError,
    PositivityViolationError,
)

from .checks import (
    check_X_a,
    check_X_a_y,
    check_treatment_values_match,
    check_is_fitted,
    check_learner_has_method,
    check_consistent_treatment_vector,
    validate_propensity_scores,
)

__all__ = [
    # Exceptions
    "CausallibValidationError",
    "DataAlignmentError",
    "TreatmentValueError",
    "NotFittedError",
    "TaskTypeError",
    "LearnerInterfaceError",
    "PositivityViolationError",
    # Validation functions
    "check_X_a",
    "check_X_a_y",
    "check_treatment_values_match",
    "check_is_fitted",
    "check_learner_has_method",
    "check_consistent_treatment_vector",
    "validate_propensity_scores",
]
