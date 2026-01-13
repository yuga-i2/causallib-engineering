"""
Diagnostic report dataclasses for structured observability.

This module provides lightweight, pure-Python diagnostic reports using dataclasses.
All reports are computed lazily (on demand) and return structured data suitable for
inspection, logging, and programmatic analysis.

No side effects: reports do not print, log, or modify estimator state.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Dict, List, Any, Tuple
import numpy as np
import pandas as pd


@dataclass
class PropensityScoreStats:
    """Statistics about propensity scores in a fitted estimator."""
    
    min_score: float
    max_score: float
    mean_score: float
    median_score: float
    std_score: float
    n_clipped: int = 0
    pct_clipped: float = 0.0
    n_extreme_low: int = 0  # < 0.01
    n_extreme_high: int = 0  # > 0.99
    pct_extreme: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def __repr__(self) -> str:
        return (
            f"PropensityScoreStats("
            f"min={self.min_score:.4f}, max={self.max_score:.4f}, "
            f"mean={self.mean_score:.4f}, std={self.std_score:.4f}, "
            f"n_extreme={self.n_extreme_low + self.n_extreme_high})"
        )


@dataclass
class WeightDistribution:
    """Statistics about weight distribution in a fitted estimator."""
    
    min_weight: float
    max_weight: float
    mean_weight: float
    median_weight: float
    std_weight: float
    n_weights: int
    n_extreme: int = 0  # Weights > mean + 3*std or < mean - 3*std
    pct_extreme: float = 0.0
    effective_sample_size: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def __repr__(self) -> str:
        return (
            f"WeightDistribution("
            f"min={self.min_weight:.4f}, max={self.max_weight:.4f}, "
            f"mean={self.mean_weight:.4f}, n_extreme={self.n_extreme})"
        )


@dataclass
class OverlapDiagnostic:
    """Overlap / positivity assessment between treatment groups."""
    
    treatment_values: List[Any]
    n_samples_per_treatment: Dict[Any, int]
    has_overlap: bool
    overlap_range: Tuple[float, float]  # (min_propensity, max_propensity) in overlap
    n_samples_in_overlap: Dict[Any, int]  # Samples within overlap range per treatment
    pct_in_overlap: Dict[Any, float]  # Percentage of samples in overlap per treatment
    propensity_min: float
    propensity_max: float
    propensity_mean: float
    propensity_q1: float
    propensity_q3: float
    notes: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        d = asdict(self)
        # Convert tuples to lists for JSON serialization
        d['overlap_range'] = list(d['overlap_range'])
        return d
    
    def __repr__(self) -> str:
        overlap_str = f"[{self.overlap_range[0]:.4f}, {self.overlap_range[1]:.4f}]"
        return (
            f"OverlapDiagnostic("
            f"has_overlap={self.has_overlap}, "
            f"overlap_range={overlap_str}, "
            f"n_treatments={len(self.treatment_values)})"
        )


@dataclass
class EffectEstimationReport:
    """Complete diagnostic report for effect estimation."""
    
    estimator_name: str
    estimator_class: str
    treatment_values: List[Any]
    n_samples: int
    outcome_type: str  # 'classification', 'regression', 'unknown'
    propensity_stats: Optional[PropensityScoreStats] = None
    weight_distribution: Optional[WeightDistribution] = None
    overlap_diagnostic: Optional[OverlapDiagnostic] = None
    warnings: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization (JSON-compatible)."""
        d = {
            'estimator_name': self.estimator_name,
            'estimator_class': self.estimator_class,
            'treatment_values': self.treatment_values,
            'n_samples': self.n_samples,
            'outcome_type': self.outcome_type,
            'propensity_stats': self.propensity_stats.to_dict() if self.propensity_stats else None,
            'weight_distribution': self.weight_distribution.to_dict() if self.weight_distribution else None,
            'overlap_diagnostic': self.overlap_diagnostic.to_dict() if self.overlap_diagnostic else None,
            'warnings': self.warnings,
            'assumptions': self.assumptions,
        }
        return d
    
    def __repr__(self) -> str:
        return (
            f"EffectEstimationReport("
            f"estimator={self.estimator_name}, "
            f"n_samples={self.n_samples}, "
            f"treatments={len(self.treatment_values)}, "
            f"warnings={len(self.warnings)})"
        )


def compute_propensity_stats(propensity_scores: pd.Series) -> PropensityScoreStats:
    """
    Compute propensity score statistics from a series.
    
    Args:
        propensity_scores: Series of propensity scores, assumed to be in [0, 1]
        
    Returns:
        PropensityScoreStats with min, max, mean, std, and extremity counts
    """
    scores = propensity_scores.dropna().values
    
    if len(scores) == 0:
        raise ValueError("No valid propensity scores provided")
    
    min_score = float(np.min(scores))
    max_score = float(np.max(scores))
    mean_score = float(np.mean(scores))
    median_score = float(np.median(scores))
    std_score = float(np.std(scores))
    
    # Count extreme propensity scores (< 0.01 or > 0.99)
    n_extreme_low = int(np.sum(scores < 0.01))
    n_extreme_high = int(np.sum(scores > 0.99))
    n_extreme = n_extreme_low + n_extreme_high
    pct_extreme = 100.0 * n_extreme / len(scores) if len(scores) > 0 else 0.0
    
    return PropensityScoreStats(
        min_score=min_score,
        max_score=max_score,
        mean_score=mean_score,
        median_score=median_score,
        std_score=std_score,
        n_extreme_low=n_extreme_low,
        n_extreme_high=n_extreme_high,
        pct_extreme=pct_extreme,
    )


def compute_weight_distribution(
    weights: pd.Series,
    treatment_values: Optional[List[Any]] = None,
) -> WeightDistribution:
    """
    Compute weight distribution statistics.
    
    Args:
        weights: Series of weights
        treatment_values: Optional list of treatment values (for effective sample size calc)
        
    Returns:
        WeightDistribution with min, max, mean, std, extremity, and ESS
    """
    w = weights.dropna().values
    
    if len(w) == 0:
        raise ValueError("No valid weights provided")
    
    min_weight = float(np.min(w))
    max_weight = float(np.max(w))
    mean_weight = float(np.mean(w))
    median_weight = float(np.median(w))
    std_weight = float(np.std(w))
    n_weights = len(w)
    
    # Count extreme weights (mean ± 3*std)
    lower_bound = mean_weight - 3 * std_weight
    upper_bound = mean_weight + 3 * std_weight
    n_extreme = int(np.sum((w < lower_bound) | (w > upper_bound)))
    pct_extreme = 100.0 * n_extreme / n_weights if n_weights > 0 else 0.0
    
    # Compute effective sample size (Kish's formula)
    # ESS = (sum(w))^2 / sum(w^2)
    sum_w = np.sum(w)
    sum_w2 = np.sum(w ** 2)
    ess = float((sum_w ** 2) / sum_w2) if sum_w2 > 0 else None
    
    return WeightDistribution(
        min_weight=min_weight,
        max_weight=max_weight,
        mean_weight=mean_weight,
        median_weight=median_weight,
        std_weight=std_weight,
        n_weights=n_weights,
        n_extreme=n_extreme,
        pct_extreme=pct_extreme,
        effective_sample_size=ess,
    )


def compute_overlap_diagnostic(
    propensity_scores: pd.Series,
    treatment_assignment: pd.Series,
    treatment_values: List[Any],
) -> OverlapDiagnostic:
    """
    Assess overlap / positivity between treatment groups.
    
    Args:
        propensity_scores: Series of propensity scores
        treatment_assignment: Series of treatment assignments
        treatment_values: List of possible treatment values
        
    Returns:
        OverlapDiagnostic with overlap assessment and statistics
    """
    # Remove missing values
    valid_idx = propensity_scores.notna() & treatment_assignment.notna()
    scores = propensity_scores[valid_idx].values
    treatments = treatment_assignment[valid_idx].values
    
    if len(scores) == 0:
        raise ValueError("No valid propensity scores or treatments")
    
    # Per-treatment statistics
    n_per_treatment = {}
    n_in_overlap = {}
    
    for t in treatment_values:
        mask = treatments == t
        n_per_treatment[t] = int(np.sum(mask))
    
    # Define overlap region as [Q1, Q3] of propensity scores
    # This is conservative: ensures substantial overlap
    q1 = float(np.percentile(scores, 25))
    q3 = float(np.percentile(scores, 75))
    overlap_range = (q1, q3)
    
    # Check if each treatment group has samples in overlap region
    has_overlap = True
    for t in treatment_values:
        mask = (treatments == t) & (scores >= q1) & (scores <= q3)
        n_in_overlap[t] = int(np.sum(mask))
        if n_in_overlap[t] == 0:
            has_overlap = False
    
    # Compute percentage in overlap
    pct_in_overlap = {
        t: 100.0 * n_in_overlap[t] / n_per_treatment[t] if n_per_treatment[t] > 0 else 0.0
        for t in treatment_values
    }
    
    # Generate notes
    notes = []
    if not has_overlap:
        notes.append("WARNING: Some treatment groups have no samples in overlap region")
    
    low_overlap_treatments = [t for t in treatment_values if pct_in_overlap[t] < 50]
    if low_overlap_treatments:
        notes.append(f"WARNING: Low overlap for treatments {low_overlap_treatments}: <50% in overlap")
    
    return OverlapDiagnostic(
        treatment_values=treatment_values,
        n_samples_per_treatment=n_per_treatment,
        has_overlap=has_overlap,
        overlap_range=overlap_range,
        n_samples_in_overlap=n_in_overlap,
        pct_in_overlap=pct_in_overlap,
        propensity_min=float(np.min(scores)),
        propensity_max=float(np.max(scores)),
        propensity_mean=float(np.mean(scores)),
        propensity_q1=q1,
        propensity_q3=q3,
        notes=notes,
    )
