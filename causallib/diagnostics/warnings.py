"""
Structured warnings for causal estimators.

Uses Python's standard warnings module to alert users about potential issues:
- Extreme weights
- Low overlap / positivity violations
- Single treatment dominance
- Missing values

All warnings are issued at DEBUG level and can be controlled via Python's
warnings filter (warnings.filterwarnings).
"""

import warnings
from typing import Optional, List, Any, Dict


class CausallibWarning(UserWarning):
    """Base class for causallib warnings."""
    pass


class ExtremeWeightWarning(CausallibWarning):
    """Issued when weight distribution is highly skewed or contains extreme values."""
    pass


class LowOverlapWarning(CausallibWarning):
    """Issued when treatment groups have limited overlap in propensity scores."""
    pass


class PositivityViolationWarning(CausallibWarning):
    """Issued when propensity scores are extreme (< 0.01 or > 0.99)."""
    pass


class SingleTreatmentDominanceWarning(CausallibWarning):
    """Issued when one treatment group is vastly larger than others."""
    pass


class MissingValuesWarning(CausallibWarning):
    """Issued when missing values are detected and handled."""
    pass


class LearnerInterfaceWarning(CausallibWarning):
    """Issued when a learner lacks expected methods (e.g., predict_proba)."""
    pass


def warn_extreme_weights(
    weight_stats: Dict[str, Any],
    stacklevel: int = 3,
) -> None:
    """
    Issue warning for extreme weight distribution.
    
    Args:
        weight_stats: Dictionary with 'min_weight', 'max_weight', 'n_extreme', 'pct_extreme'
        stacklevel: stacklevel for warnings.warn (caller's caller = 3)
    """
    min_w = weight_stats.get('min_weight', 0)
    max_w = weight_stats.get('max_weight', 0)
    n_extreme = weight_stats.get('n_extreme', 0)
    pct_extreme = weight_stats.get('pct_extreme', 0)
    
    msg = (
        f"Extreme weights detected: min={min_w:.6f}, max={max_w:.6f}, "
        f"n_extreme={n_extreme} ({pct_extreme:.1f}% of weights). "
        f"This may indicate positivity violations or unstable estimates. "
        f"Consider overlap weighting or doubly robust methods."
    )
    warnings.warn(msg, ExtremeWeightWarning, stacklevel=stacklevel)


def warn_low_overlap(
    overlap_stats: Dict[str, Any],
    stacklevel: int = 3,
) -> None:
    """
    Issue warning for low overlap between treatment groups.
    
    Args:
        overlap_stats: Dictionary with overlap information
        stacklevel: stacklevel for warnings.warn
    """
    has_overlap = overlap_stats.get('has_overlap', False)
    pct_in_overlap = overlap_stats.get('pct_in_overlap', {})
    
    if not has_overlap:
        msg = (
            f"Severe positivity violation: some treatment groups have no overlap. "
            f"Per-treatment overlap: {pct_in_overlap}. "
            f"Causal estimates may be unreliable or undefined. "
            f"Consider removing non-overlapping treatments or using trimming methods."
        )
        warnings.warn(msg, PositivityViolationWarning, stacklevel=stacklevel)
    else:
        low_coverage_treatments = {
            t: pct for t, pct in pct_in_overlap.items() if pct < 50
        }
        if low_coverage_treatments:
            msg = (
                f"Low overlap warning: treatments with <50% samples in overlap region: "
                f"{low_coverage_treatments}. "
                f"Results for these treatments may be unreliable. "
                f"Consider targeted analysis or sensitivity checks."
            )
            warnings.warn(msg, LowOverlapWarning, stacklevel=stacklevel)


def warn_propensity_extremity(
    propensity_stats: Dict[str, Any],
    stacklevel: int = 3,
) -> None:
    """
    Issue warning for extreme propensity scores.
    
    Args:
        propensity_stats: Dictionary with 'n_extreme_low', 'n_extreme_high', 'pct_extreme'
        stacklevel: stacklevel for warnings.warn
    """
    n_extreme_low = propensity_stats.get('n_extreme_low', 0)
    n_extreme_high = propensity_stats.get('n_extreme_high', 0)
    pct_extreme = propensity_stats.get('pct_extreme', 0)
    
    if n_extreme_low > 0 or n_extreme_high > 0:
        msg = (
            f"Propensity score extremity: {n_extreme_low + n_extreme_high} extreme scores "
            f"({pct_extreme:.1f}% of samples). "
            f"Breakdown: {n_extreme_low} < 0.01, {n_extreme_high} > 0.99. "
            f"This indicates potential positivity violations. "
            f"Consider propensity score trimming (e.g., clip to [0.01, 0.99])."
        )
        warnings.warn(msg, PositivityViolationWarning, stacklevel=stacklevel)


def warn_single_treatment_dominance(
    n_samples_per_treatment: Dict[Any, int],
    stacklevel: int = 3,
) -> None:
    """
    Issue warning when one treatment group dominates sample distribution.
    
    Args:
        n_samples_per_treatment: Dictionary mapping treatment -> count
        stacklevel: stacklevel for warnings.warn
    """
    total = sum(n_samples_per_treatment.values())
    
    for treatment, count in n_samples_per_treatment.items():
        pct = 100 * count / total if total > 0 else 0
        if pct > 80:  # One group is >80% of sample
            msg = (
                f"Single treatment dominance: treatment {treatment} comprises {pct:.1f}% "
                f"of the sample ({count} of {total} observations). "
                f"Causal estimates may be unstable or unreliable. "
                f"Consider stratified analysis or sensitivity checks."
            )
            warnings.warn(msg, SingleTreatmentDominanceWarning, stacklevel=stacklevel)
            break  # Only warn once for the most dominant group


def warn_missing_values(
    n_missing: int,
    n_total: int,
    variable_name: str = "data",
    stacklevel: int = 3,
) -> None:
    """
    Issue warning for missing values detected.
    
    Args:
        n_missing: Number of missing values
        n_total: Total number of observations
        variable_name: Name of variable with missing values (e.g., 'outcome y')
        stacklevel: stacklevel for warnings.warn
    """
    if n_missing > 0:
        pct = 100 * n_missing / n_total if n_total > 0 else 0
        msg = (
            f"Missing values detected in {variable_name}: {n_missing} of {n_total} "
            f"({pct:.1f}% missing). These observations will be excluded from analysis. "
            f"This may introduce bias if missingness is related to treatment or outcome."
        )
        warnings.warn(msg, MissingValuesWarning, stacklevel=stacklevel)


def warn_learner_interface(
    method_name: str,
    learner_type: str,
    stacklevel: int = 3,
) -> None:
    """
    Issue warning for learner lacking required method.
    
    Args:
        method_name: Name of missing method (e.g., 'predict_proba')
        learner_type: Type/class of learner
        stacklevel: stacklevel for warnings.warn
    """
    msg = (
        f"Learner {learner_type} does not have method '{method_name}'. "
        f"This estimator requires learners with {method_name}() for probability estimation. "
        f"Consider using sklearn models (LogisticRegression, RandomForestClassifier, etc.)"
    )
    warnings.warn(msg, LearnerInterfaceWarning, stacklevel=stacklevel)


# Utility to accumulate warnings for summary
_warning_accumulator: List[str] = []


def accumulate_warning(message: str) -> None:
    """Add a warning message to the accumulator for later inclusion in summary()."""
    _warning_accumulator.append(message)


def get_accumulated_warnings() -> List[str]:
    """Get all accumulated warnings."""
    return _warning_accumulator.copy()


def clear_accumulated_warnings() -> None:
    """Clear the warning accumulator."""
    global _warning_accumulator
    _warning_accumulator = []
