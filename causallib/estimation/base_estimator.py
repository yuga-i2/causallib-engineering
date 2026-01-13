"""
Base estimator interfaces for causal inference models.

This module defines the core abstraction hierarchy for causallib:

Architecture:
    EffectEstimator (base interface)
        ├─ PopulationOutcomeEstimator (aggregated outcomes)
        └─ IndividualOutcomeEstimator (individual/CATE predictions)

Key design decisions:
    1. Separation of concerns: potential outcome prediction → effect estimation
    2. Support for both population and individual level estimates
    3. Sklearn-compatible BaseEstimator inheritance for interoperability
    4. Abstract methods enforce implementation of fit, estimate_*

Production notes:
    - All estimators validate inputs via causallib.validation module
    - Use effects.calculate_effect() for unified effect computation
    - check_is_fitted() enforces state machine: unfitted → fitted → predicted

(C) Copyright 2019 IBM Corp.
Licensed under the Apache License, Version 2.0
"""
import abc
import warnings
from typing import Optional, Union, List, Any

import pandas as pd
import numpy as np
from numpy import isscalar

from sklearn.base import BaseEstimator

from ..utils.general_tools import create_repr_string


class EffectEstimator(BaseEstimator):
    """
    Base interface for treatment effect estimation from potential outcomes.
    
    Core responsibility:
        Transform two potential outcomes (Y(1), Y(0)) into causal effects.
        
    Supports:
        - Population-level effects: scalar potential outcomes → scalar effects
        - Individual-level effects: vector potential outcomes → vector effects
        - Multiple effect types: difference, ratio, odds ratio
        
    Production notes:
        - All subclasses must implement fit() and estimate_*outcome*() methods
        - Effect computation delegated to effects.calculate_effect()
        - Effect types validated and documented in effects.EffectType
        
    Mathematical foundation:
        - Effect is invariant to population vs individual level (arithmetic is same)
        - Returns pd.Series for population (1 effect per type)
        - Returns pd.DataFrame for individual (1 effect per sample)
    """

    def estimate_effect(
        self,
        outcome_1: Union[float, pd.Series, pd.DataFrame],
        outcome_2: Union[float, pd.Series, pd.DataFrame],
        effect_types: Union[str, List[str]] = "diff",
    ) -> Union[pd.Series, pd.DataFrame]:
        """
        Estimate treatment effect from two potential outcomes.
        
        Dispatches to effects.calculate_effect() for unified computation.

        Args:
            outcome_1: First potential outcome (e.g., Y(1) = treated outcome)
            outcome_2: Second potential outcome (e.g., Y(0) = control outcome)
            effect_types: Effect type(s) to compute: 'diff', 'ratio', 'or'
                         Can be single string or list of strings

        Returns:
            If scalars (population level):
                pd.Series with effect_types as index and effect values
            If vectors (individual level):
                pd.DataFrame with samples as index, effect_types as columns

        Examples:
            >>> estimator = SomeEstimator()
            >>> # Population effect (both scalar)
            >>> eff = estimator.estimate_effect(0.3, 0.6, 'diff')
            >>> # Output: Series with effect=-0.3
            
            >>> # Individual effects (both vectors)
            >>> y1 = pd.Series([0.2, 0.4])  # Treated outcomes
            >>> y0 = pd.Series([0.1, 0.2])  # Control outcomes
            >>> eff = estimator.estimate_effect(y1, y0, ['diff', 'ratio'])
            >>> # Output: DataFrame with 2 rows, 2 columns
        """
        # Import here to avoid circular dependency at module load time
        from ..effects import calculate_effect
        
        # Delegate to centralized effect calculation
        return calculate_effect(outcome_1, outcome_2, effect_types)

    def summary(self) -> dict:
        """
        Return structured summary of estimator state and diagnostics.
        
        Provides introspection without printing or side effects. Suitable for:
        - Logging and debugging
        - Documenting estimation context
        - Programmatic inspection
        
        Returns:
            dict with keys:
                - 'estimator_name': Short name of this estimator
                - 'estimator_class': Full class name
                - 'is_fitted': Whether fit() has been called
                - 'treatment_values': Treatment values observed at fit time (if fitted)
                - 'n_samples': Number of samples used in fit (if fitted)
                - 'outcome_type': 'classification', 'regression', or 'unknown'
                - 'assumptions': List of causal assumptions for this estimator
                - 'warnings': Accumulated warnings during fit/estimation
                - 'propensity_stats': Propensity score stats (if available)
                - 'weight_distribution': Weight stats (if available)
                - 'overlap_diagnostic': Overlap assessment (if available)
                
        Example:
            >>> estimator = IPW(LogisticRegression())
            >>> estimator.fit(X, a, y)
            >>> info = estimator.summary()
            >>> print(info['estimator_name'])
            >>> print(info['n_samples'])
            >>> print(info['assumptions'])
        """
        from ..diagnostics import get_assumptions_for_estimator, get_accumulated_warnings
        
        # Determine if fitted by checking for expected attributes
        # Different estimators use different conventions, so check multiple signals
        is_fitted = False
        
        if hasattr(self, 'learner_'):  # Some estimators use sklearn convention with underscore
            is_fitted = self.learner_ is not None
        elif hasattr(self, 'learner'):  # IPW and others use 'learner' (no underscore)
            learner = self.learner
            # Check if learner itself is fitted (has classes_ for classifiers, coef_ for regressors)
            is_fitted = (
                hasattr(learner, 'classes_') or  # Classification
                hasattr(learner, 'coef_') or  # Regression/Logistic
                hasattr(learner, '_is_fitted')  # Some custom models
            )
        
        summary_dict = {
            'estimator_name': self.__class__.__name__,
            'estimator_class': f"{self.__class__.__module__}.{self.__class__.__name__}",
            'is_fitted': is_fitted,
            'treatment_values': getattr(self, 'treatment_values_', None),
            'n_samples': getattr(self, 'n_samples_', None),
            'outcome_type': self._infer_outcome_type() if is_fitted else 'unknown',
            'assumptions': [a.to_dict() for a in get_assumptions_for_estimator(self.__class__.__name__)],
            'warnings': get_accumulated_warnings(),
            'propensity_stats': None,  # To be filled by subclasses if applicable
            'weight_distribution': None,  # To be filled by subclasses if applicable
            'overlap_diagnostic': None,  # To be filled by subclasses if applicable
        }
        
        return summary_dict
    
    def _infer_outcome_type(self) -> str:
        """
        Infer whether fitted estimator handles classification or regression.
        
        Looks for common sklearn attributes on the learner.
        """
        if not hasattr(self, 'learner_'):
            return 'unknown'
        
        learner = self.learner_
        
        # Check for classification indicators
        if hasattr(learner, 'classes_') or hasattr(learner, 'n_classes_'):
            return 'classification'
        
        # Check for regression indicators
        if hasattr(learner, 'coef_') and not hasattr(learner, 'classes_'):
            return 'regression'
        
        # Check class name for hints
        class_name = learner.__class__.__name__.lower()
        if 'classifier' in class_name or 'logistic' in class_name:
            return 'classification'
        if 'regressor' in class_name or 'regression' in class_name:
            return 'regression'
        
        return 'unknown'


class PopulationOutcomeEstimator(EffectEstimator):
    """
    Interface for estimating aggregated outcomes over subgroups.
    
    Core responsibility:
        Predict population-level (average) outcomes for treatment groups.
        
    Typical usage:
        - Compute ATE (average treatment effect) on entire population
        - Compute ATT (effect on treated) by stratifying on a==1
        - Compute ACDE (conditional direct effects) by stratifying on confounders
        
    Lifecycle:
        1. fit(X, a, y) - learn population outcome model
        2. estimate_population_outcome(X, a) - predict aggregated outcomes
        3. estimate_effect() - compute effects between outcomes
    """

    @abc.abstractmethod
    def estimate_population_outcome(
        self,
        X: pd.DataFrame,
        a: pd.Series,
        y: Optional[pd.Series] = None,
        treatment_values: Optional[List[Any]] = None,
    ) -> pd.Series:
        """
        Estimate aggregated outcome for treatment groups.

        Args:
            X: Covariate matrix
            a: Treatment assignment
            y: Observed outcome (usage varies by subclass)
            treatment_values: Specific treatment values to estimate for.
                            If None, computes for all observed values in a.

        Returns:
            pd.Series with treatment values as index, aggregated outcomes as values
        """
        raise NotImplementedError


class IndividualOutcomeEstimator(PopulationOutcomeEstimator, EffectEstimator):
    """
    Interface for estimating individual-level outcomes (CATE, heterogeneous effects).
    
    Core responsibility:
        Predict counterfactual outcomes Y(t) for each individual under each treatment t.
        
    Key design:
        - Uses composition pattern: aggregates individual outcomes into population effects
        - Inherited by Standardization, XLearner, and direct outcome models
        - NOT inherited by weight-based models (IPW) - they use different mechanism
        
    Lifecycle:
        1. fit(X, a, y) - train outcome model
        2. estimate_individual_outcome(X, a, t) - predict per-unit outcomes Y(t)
        3. estimate_population_outcome(X, a) - aggregate to population level
        4. estimate_effect() - compute contrasts
        
    Production notes:
        - Must validate that learner supports chosen task (classification vs regression)
        - predict_proba parameter controls classification behavior (probabilities vs classes)
        - check_is_fitted() enforces that model was trained before prediction
    """

    def __init__(self, learner: Any, predict_proba: bool = False, *args, **kwargs):
        """
        Initialize individual outcome estimator.

        Args:
            learner: Initialized sklearn-compatible model.
                    Must have fit(X, a) and predict(X) or predict_proba(X).
            predict_proba: For classification learners, if True use predict_proba()
                          (returns probabilities) instead of predict() (returns classes).
                          Ignored for regression learners.
                          
        Design note:
            - learner is passed as-is; subclasses may clone or copy it
            - predict_proba can be overridden at predict time via method parameters
        """
        self.learner = learner
        self.predict_proba = predict_proba
        # Note: Intentionally not calling super().__init__() to avoid sklearn conflicts

    @staticmethod
    def _aggregate_population_outcome(
        y: pd.Series,
        agg_func: str = "mean",
    ) -> float:
        """
        Aggregate individual outcome vector to population scalar.

        Args:
            y: Individual outcomes (one per sample)
            agg_func: Aggregation method ('mean' or 'median')

        Returns:
            Single scalar value (float)
            
        Raises:
            LookupError: If agg_func not recognized
        """
        if agg_func == "mean":
            return y.mean()
        elif agg_func == "median":
            return y.median()
        else:
            raise LookupError(f"Unsupported aggregation function: {agg_func}")

    def estimate_population_outcome(
        self,
        X: pd.DataFrame,
        a: pd.Series,
        y: Optional[pd.Series] = None,
        treatment_values: Optional[List[Any]] = None,
        agg_func: str = "mean",
    ) -> pd.Series:
        """
        Estimate population outcome by aggregating individual predictions.
        
        Implementation note:
            - Ignores observed y (uses predicted outcomes instead)
            - This is intentional: population outcome = aggregated predictions
            - Enables out-of-bag (honest) effect estimation

        Args:
            X: Covariate matrix
            a: Treatment assignment
            y: Observed outcome (IGNORED, kept for API compatibility)
            treatment_values: Specific treatment(s) to compute outcomes for
            agg_func: Aggregation function ('mean' or 'median')

        Returns:
            pd.Series with treatment values as index, aggregated outcome values
        """
        if y is not None:
            warnings.warn(
                "Argument 'y' (observed outcome) is not used when calculating "
                "population outcome for IndividualOutcomeEstimator. "
                "Instead, uses aggregated individual outcome predictions.",
                UserWarning
            )
        
        individual_outcomes = self.estimate_individual_outcome(X, a, treatment_values)
        population_outcomes = individual_outcomes.apply(
            self._aggregate_population_outcome,
            args=(agg_func,)
        )
        return population_outcomes

    def estimate_effect(
        self,
        outcome1: Union[pd.Series, float],
        outcome2: Union[pd.Series, float],
        agg: str = "population",
        effect_types: Union[str, List[str]] = "diff",
    ) -> Union[pd.Series, pd.DataFrame]:
        """
        Estimate treatment effect with optional aggregation.
        
        Handles both population and individual level effect estimation
        by optionally aggregating outcomes first.

        Args:
            outcome1: First potential outcome (scalar or vector)
            outcome2: Second potential outcome (scalar or vector)
            agg: 'population' to aggregate before computing effect,
                 'individual' to compute per-sample effects
            effect_types: Effect type(s) ('diff', 'ratio', 'or')

        Returns:
            pd.Series if population aggregation (scalar)
            pd.DataFrame if individual effects (vector)
        """
        if agg == "population":
            outcome1 = self._aggregate_population_outcome(outcome1)
            outcome2 = self._aggregate_population_outcome(outcome2)
        
        effect = super(IndividualOutcomeEstimator, self).estimate_effect(
            outcome1, outcome2, effect_types
        )
        return effect

    @abc.abstractmethod
    def estimate_individual_outcome(
        self,
        X: pd.DataFrame,
        a: pd.Series,
        treatment_values: Optional[List[Any]] = None,
        predict_proba: Optional[bool] = None,
    ) -> pd.DataFrame:
        """
        Estimate individual outcome under different treatment values.
        
        Core method: predicts Y(t) for each unit and each treatment value.

        Args:
            X: Covariate matrix (n_samples, n_features)
            a: Treatment assignment (n_samples,)
            treatment_values: Specific treatment value(s) to estimate outcomes for.
                            If None, estimates for all unique values in a.
            predict_proba: Override initialization setting for classification.
                          If None, uses self.predict_proba value.

        Returns:
            pd.DataFrame with:
                - Index: sample indices (matching X.index)
                - Columns: treatment values
                - Values: predicted outcomes Y(t) for each sample and treatment
                
        Example output for binary treatment:
                    0         1
            0    0.2       0.3
            1    0.4       0.5
            ...  ...       ...
        """
        raise NotImplementedError

    @abc.abstractmethod
    def fit(
        self,
        X: pd.DataFrame,
        a: pd.Series,
        y: pd.Series,
        sample_weight: Optional[pd.Series] = None,
    ) -> "IndividualOutcomeEstimator":
        """
        Fit individual outcome estimator to training data.

        Args:
            X: Covariate matrix (n_samples, n_features)
            a: Treatment assignment (n_samples,)
            y: Observed outcome (n_samples,)
            sample_weight: Per-sample weights (passed to learner)

        Returns:
            self: Fitted estimator
            
        Post-condition:
            - Internal learner fitted
            - treatment_values_ attribute set
            - check_is_fitted(self) returns True
        """
        raise NotImplementedError

    def __repr__(self):
        repr_string = create_repr_string(self)
        return repr_string