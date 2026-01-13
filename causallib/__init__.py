"""
CausalLib: A Python package for inferring causal effects from observational data.

CausalLib provides a suite of production-ready causal inference methods under a
unified scikit-learn-inspired API. It supports flexible causal modeling through
pluggable machine learning estimators.

Architecture:
    - estimation/    : Causal inference algorithms (IPW, Standardization, DR, etc.)
    - validation/    : Centralized input validation and state management
    - effects/       : Treatment effect computation (single source of truth)
    - propensity/    : Propensity score utilities
    - evaluation/    : Cross-validation and metrics
    - diagnostics/   : Model diagnostics and observability (Phase 2)
    
Quick Start:
    >>> from sklearn.linear_model import LogisticRegression
    >>> from causallib.estimation import IPW
    >>> from causallib.datasets import load_nhefs
    >>> 
    >>> data = load_nhefs()
    >>> ipw = IPW(LogisticRegression())
    >>> ipw.fit(data.X, data.a, data.y)
    >>> outcomes = ipw.estimate_population_outcome(data.X, data.a)
    >>> effect = ipw.estimate_effect(outcomes[1], outcomes[0])
    >>> summary = ipw.summary()  # Phase 2: Introspection

Production Hardening (Phase 1 & 2):
    Phase 1 (Stability & Validation):
    - Centralized validation layer (causallib.validation)
    - Unified effect calculation (causallib.effects)
    - Centralized propensity computation (causallib.propensity)
    - Type hints on public APIs
    - Enhanced docstrings explaining design intent
    
    Phase 2 (Observability & Debuggability):
    - Diagnostic reports with lazy computation
    - Explicit assumption metadata for each estimator
    - Structured warnings (not silent failures)
    - Optional DEBUG-level logging
    - Estimator introspection via summary()
    - Weight distribution & overlap diagnostics
    
    Full backward compatibility maintained throughout.
"""

__version__ = "0.10.0"

# Import new modules for public API
from . import validation
from . import effects
from . import propensity
from . import diagnostics

# Make commonly-used validation exports available at package level
from .validation import (
    CausallibValidationError,
    DataAlignmentError,
    TreatmentValueError,
    NotFittedError,
    check_X_a,
    check_X_a_y,
    check_is_fitted,
)

# Make commonly-used diagnostics exports available at package level
from .diagnostics import (
    PropensityScoreStats,
    WeightDistribution,
    OverlapDiagnostic,
    EffectEstimationReport,
    Assumption,
    AssumptionCategory,
    get_assumptions_for_estimator,
    ExtremeWeightWarning,
    LowOverlapWarning,
    PositivityViolationWarning,
)

__all__ = [
    "validation",
    "effects",
    "propensity",
    "diagnostics",
    # Commonly-used validation functions
    "CausallibValidationError",
    "DataAlignmentError",
    "TreatmentValueError",
    "NotFittedError",
    "check_X_a",
    "check_X_a_y",
    "check_is_fitted",
    # Commonly-used diagnostics functions
    "PropensityScoreStats",
    "WeightDistribution",
    "OverlapDiagnostic",
    "EffectEstimationReport",
    "Assumption",
    "AssumptionCategory",
    "get_assumptions_for_estimator",
    "ExtremeWeightWarning",
    "LowOverlapWarning",
    "PositivityViolationWarning",
]
