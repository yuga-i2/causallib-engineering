"""
Base weight estimator interface for propensity-based causal models.

This module defines the interface for weight-based causal estimators
(IPW, overlap weighting, etc.) that balance treatment groups through
propensity score weighting.

Architecture:
    WeightEstimator (base interface)
        └─ PropensityEstimator (specific propensity-based implementation)

Key design:
    - Separates propensity score computation from weighting logic
    - Supports stabilized and unstabilized weighting
    - Handles binary and multi-valued treatments
    - integrate with propensity module for computation

(C) Copyright 2019 IBM Corp.
Licensed under the Apache License, Version 2.0
"""

import abc
import logging
from typing import Optional, Union, List, Any

import pandas as pd
import numpy as np

from ..utils.general_tools import create_repr_string, get_iterable_treatment_values

# Configure logger for this module (disabled by default, users can enable via logging config)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

class WeightEstimator:
    """
    Base interface for weight-based causal inference methods.
    
    Core responsibility:
        Learn propensity scores P(A|X) and compute individual weights
        to balance treatment and control groups.
        
    Key distinction from IndividualOutcomeEstimator:
        - WeightEstimator: models treatment assignment (propensity)
        - IndividualOutcomeEstimator: models outcome prediction (counterfactuals)
        
    Mathematical foundation:
        IPW weight: w_i = 1 / P(A=a_i|X_i)
        Stabilized: w_i = P(A=a_i) / P(A=a_i|X_i)
        
    Production notes:
        - Learner must have predict_proba() for probabilistic predictions
        - Weight computation uses propensity module for consistency
        - Extreme weights (>100) indicate positivity violations
    """

    def __init__(self, learner: Any, use_stabilized: bool = False, *args, **kwargs):
        """
        Initialize weight estimator.

        Args:
            learner: Initialized sklearn classifier with predict_proba()
            use_stabilized: If True, apply stabilization to reduce weight variance
                           (multiply by marginal treatment prevalence)
        """
        self.learner = learner
        self.use_stabilized = use_stabilized

    @abc.abstractmethod
    def fit(
        self,
        X: pd.DataFrame,
        a: pd.Series,
        y: Optional[pd.Series] = None,
    ) -> "WeightEstimator":
        """
        Fit propensity model: learn P(A|X).

        Args:
            X: Covariate matrix (n_samples, n_features)
            a: Treatment assignment (n_samples,)
            y: Outcome (IGNORED - kept for sklearn Pipeline compatibility)

        Returns:
            self: Fitted estimator with learner_ attribute

        Post-condition:
            - learner fitted on (X, a)
            - treatment_values_ set to unique values in a
            - check_is_fitted(self) returns True
        """
        raise NotImplementedError

    @abc.abstractmethod
    def compute_weights(
        self,
        X: pd.DataFrame,
        a: pd.Series,
        treatment_values: Optional[Union[Any, List[Any]]] = None,
        use_stabilized: Optional[bool] = None,
        **kwargs,
    ) -> Union[pd.Series, pd.DataFrame]:
        """
        Compute inverse probability weights.
        
        Core method: returns w_i = 1 / P(A=a_i|X_i) or stabilized version.

        Args:
            X: Covariate matrix
            a: Treatment assignment
            treatment_values: Specific treatment value(s) to weight for.
                            If None, uses observed assignment (yields Series).
                            If scalar/list, returns weights for those values (DataFrame if list).
            use_stabilized: Override self.use_stabilized (default: None = use instance setting)
            **kwargs: Subclass-specific options (e.g., clip_min, clip_max for IPW)

        Returns:
            pd.Series if treatment_values=None: shape (n_samples,)
            pd.DataFrame if treatment_values=list: shape (n_samples, len(treatment_values))
            
        Raises:
            NotFittedError: If estimator not yet fit
            ValueError: If treatment_values not in training treatment set
        """
        raise NotImplementedError

    @abc.abstractmethod
    def compute_weight_matrix(
        self,
        X: pd.DataFrame,
        a: pd.Series,
        use_stabilized: Optional[bool] = None,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Compute weight matrix for ALL treatment values.
        
        Returns weights w_ij = 1 / P(A=j|X_i) for all samples i and treatments j.

        Args:
            X: Covariate matrix
            a: Treatment assignment (used for stabilization only)
            use_stabilized: Override instance setting
            **kwargs: Subclass-specific options

        Returns:
            pd.DataFrame of shape (n_samples, n_treatments)
            Columns are treatment values, index matches X.index
        """
        raise NotImplementedError

    @staticmethod
    def _compute_stratified_weighted_aggregate(
        y: pd.Series,
        sample_weight: Optional[pd.Series] = None,
        stratify_by: Optional[pd.Series] = None,
        treatment_values: Optional[List[Any]] = None,
    ) -> pd.Series:
        """
        Compute weighted mean stratified by treatment groups.
        
        Shared utility for aggregating weighted outcomes.

        Args:
            y: Outcome values
            sample_weight: Per-sample weights. If None, equal weights.
            stratify_by: Categorical variable to stratify by (usually treatment).
                        If None, computes overall weighted mean.
            treatment_values: Specific strata to compute (subset of stratify_by values)

        Returns:
            pd.Series with stratum values as index, weighted aggregates as values
        """
        if sample_weight is None:
            sample_weight = pd.Series(data=1.0, index=y.index)
        if treatment_values is None and stratify_by is None:
            stratify_by = pd.Series(data=0, index=y.index)

        treatment_values = get_iterable_treatment_values(treatment_values, stratify_by)

        res = {}
        for treatment_value in treatment_values:
            subgroup_mask = stratify_by == treatment_value
            aggregated_value = np.average(y[subgroup_mask], weights=sample_weight[subgroup_mask])
            res[treatment_value] = aggregated_value
        res = pd.Series(res)
        return res

    def evaluate_balancing(self, X: pd.DataFrame, a: pd.Series, y: pd.Series, w: pd.Series) -> None:
        """
        Diagnostic method: evaluate covariate balance post-weighting.
        
        Production note: Not yet implemented. Placeholder for future balance diagnostics
        (e.g., standardized mean differences, KS tests).
        """
        pass  # TODO: Implement balance diagnostics (SMD, KS test, etc.)

    def get_weight_diagnostics(self, weights: pd.Series) -> dict:
        """
        Compute weight distribution diagnostics and issue warnings if needed.
        
        Non-breaking addition: returns structured diagnostic data without printing.
        Warnings are issued via Python's warnings module at DEBUG level.
        
        Args:
            weights: Computed weights from compute_weights()
            
        Returns:
            dict with keys:
                - 'min_weight': Minimum weight value
                - 'max_weight': Maximum weight value
                - 'mean_weight': Mean weight value
                - 'std_weight': Standard deviation of weights
                - 'n_extreme': Number of extreme weights (>3 std from mean)
                - 'pct_extreme': Percentage of extreme weights
                - 'effective_sample_size': Kish's effective sample size
                
        Example:
            >>> estimator = IPW(learner)
            >>> estimator.fit(X, a, y)
            >>> w = estimator.compute_weights(X, a)
            >>> diag = estimator.get_weight_diagnostics(w)
            >>> print(diag['effective_sample_size'])
        """
        from ..diagnostics import compute_weight_distribution, warn_extreme_weights
        
        logger.debug(f"Computing weight diagnostics for {len(weights)} weights")
        
        wd = compute_weight_distribution(weights)
        
        # Issue warning if extreme weights detected
        if wd.n_extreme > 0:
            logger.warning(f"Detected {wd.n_extreme} extreme weights ({wd.pct_extreme:.1f}%)")
            warn_extreme_weights({
                'min_weight': wd.min_weight,
                'max_weight': wd.max_weight,
                'n_extreme': wd.n_extreme,
                'pct_extreme': wd.pct_extreme,
            }, stacklevel=3)
        
        return {
            'min_weight': wd.min_weight,
            'max_weight': wd.max_weight,
            'mean_weight': wd.mean_weight,
            'median_weight': wd.median_weight,
            'std_weight': wd.std_weight,
            'n_extreme': wd.n_extreme,
            'pct_extreme': wd.pct_extreme,
            'effective_sample_size': wd.effective_sample_size,
        }

    def __repr__(self):
        repr_string = create_repr_string(self)
        return repr_string


class PropensityEstimator(WeightEstimator):
    """
    Specialized weight estimator for propensity score-based methods.
    
    Requires learner with predict_proba() for probability estimation.
    Used as base for IPW, overlap weighting, and other propensity-based methods.
    
    Subclasses implement specific weight computation schemes:
    - IPW: w = 1 / p(a|X)
    - Overlap: w = min(p(a|X), 1-p(a|X)) for binary treatment
    """

    def __init__(self, learner: Any, use_stabilized: bool = False, *args, **kwargs):
        """
        Initialize propensity estimator with probability learner.

        Args:
            learner: sklearn classifier with predict_proba() method
            use_stabilized: If True, stabilize weights using marginal treatment prevalence
            
        Raises:
            LearnerInterfaceError: If learner lacks predict_proba() method
        """
        super(PropensityEstimator, self).__init__(learner, use_stabilized=use_stabilized)
        
        # Validate learner supports probability prediction
        from ..validation import check_learner_has_method
        check_learner_has_method(
            learner,
            "predict_proba",
            f"{learner.__class__.__name__} (in PropensityEstimator)"
        )

    @abc.abstractmethod
    def compute_propensity(
        self,
        X: pd.DataFrame,
        a: pd.Series,
        treatment_values: Optional[Union[Any, List[Any]]] = None,
        **kwargs,
    ) -> Union[pd.Series, pd.DataFrame]:
        """
        Compute propensity scores P(A|X).

        Args:
            X: Covariate matrix
            a: Treatment assignment
            treatment_values: Specific treatment(s) to compute propensity for
            **kwargs: Subclass-specific options (e.g., clipping)

        Returns:
            pd.Series or DataFrame of propensity score estimates
        """
        raise NotImplementedError

    @abc.abstractmethod
    def compute_propensity_matrix(
        self,
        X: pd.DataFrame,
        a: pd.Series,
        **kwargs,
    ) -> pd.DataFrame:
        """
        Compute propensity score matrix for ALL treatment values.
        
        Returns P(A=j|X) for all samples and all treatment values.

        Args:
            X: Covariate matrix
            a: Treatment assignment
            **kwargs: Subclass-specific options

        Returns:
            pd.DataFrame of shape (n_samples, n_treatments)
        """
        raise NotImplementedError
