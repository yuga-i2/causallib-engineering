"""
Diagnostic utilities for causal inference.

Provides:
- reports: Diagnostic report dataclasses for structured observability
- assumptions: Explicit assumption metadata for each estimator
- warnings: Structured warnings for common issues
"""

from .reports import (
    PropensityScoreStats,
    WeightDistribution,
    OverlapDiagnostic,
    EffectEstimationReport,
    compute_propensity_stats,
    compute_weight_distribution,
    compute_overlap_diagnostic,
)
from .assumptions import (
    Assumption,
    AssumptionCategory,
    get_assumptions_for_estimator,
    ESTIMATOR_ASSUMPTIONS,
)
from .warnings import (
    CausallibWarning,
    ExtremeWeightWarning,
    LowOverlapWarning,
    PositivityViolationWarning,
    SingleTreatmentDominanceWarning,
    MissingValuesWarning,
    LearnerInterfaceWarning,
    warn_extreme_weights,
    warn_low_overlap,
    warn_propensity_extremity,
    warn_single_treatment_dominance,
    warn_missing_values,
    warn_learner_interface,
    accumulate_warning,
    get_accumulated_warnings,
    clear_accumulated_warnings,
)

__all__ = [
    # Reports
    'PropensityScoreStats',
    'WeightDistribution',
    'OverlapDiagnostic',
    'EffectEstimationReport',
    'compute_propensity_stats',
    'compute_weight_distribution',
    'compute_overlap_diagnostic',
    # Assumptions
    'Assumption',
    'AssumptionCategory',
    'get_assumptions_for_estimator',
    'ESTIMATOR_ASSUMPTIONS',
    # Warnings
    'CausallibWarning',
    'ExtremeWeightWarning',
    'LowOverlapWarning',
    'PositivityViolationWarning',
    'SingleTreatmentDominanceWarning',
    'MissingValuesWarning',
    'LearnerInterfaceWarning',
    'warn_extreme_weights',
    'warn_low_overlap',
    'warn_propensity_extremity',
    'warn_single_treatment_dominance',
    'warn_missing_values',
    'warn_learner_interface',
    'accumulate_warning',
    'get_accumulated_warnings',
    'clear_accumulated_warnings',
]
