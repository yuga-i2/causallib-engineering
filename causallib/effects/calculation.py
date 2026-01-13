"""
Centralized effect calculation logic for all estimators.

This module provides a single source of truth for treatment effect computation
(diff, ratio, odds ratio). All estimators should use these functions rather than
duplicating logic.

Design rationale:
- Prevents bugs from code duplication
- Enables consistent validation of effect calculations
- Single point for enhancement (e.g., confidence intervals, sensitivity analysis)
- Makes effect types explicit and testable

(C) Copyright 2019 IBM Corp.
Licensed under the Apache License, Version 2.0
"""

from typing import Union, List, Optional
import pandas as pd
import numpy as np


class EffectType:
    """
    Container for supported effect types with validation.
    
    Current supported effects:
    - 'diff': Simple difference (outcome1 - outcome2)
    - 'ratio': Ratio (outcome1 / outcome2)
    - 'or': Odds ratio ((outcome1/(1-outcome1)) / (outcome2/(1-outcome2)))
    """
    DIFF = "diff"
    RATIO = "ratio"
    ODDS_RATIO = "or"
    
    VALID = {DIFF, RATIO, ODDS_RATIO}
    
    @classmethod
    def validate(cls, effect_type: Union[str, List[str]]) -> List[str]:
        """
        Validate effect type(s) against supported options.
        
        Args:
            effect_type: Single effect type string or list of effect types
            
        Returns:
            List[str]: Validated effect types as list
            
        Raises:
            ValueError: If invalid effect type provided
        """
        if isinstance(effect_type, str):
            effect_types = [effect_type]
        else:
            effect_types = list(effect_type)
        
        invalid = set(effect_types) - cls.VALID
        if invalid:
            raise ValueError(
                f"Invalid effect type(s): {invalid}. "
                f"Supported: {cls.VALID}"
            )
        
        return effect_types


def _effect_diff(outcome_1, outcome_2) -> Union[float, pd.Series, pd.DataFrame]:
    """
    Calculate simple difference: outcome_1 - outcome_2
    
    Args:
        outcome_1: Scalar, Series, or DataFrame of outcomes
        outcome_2: Matching shape as outcome_1
        
    Returns:
        Same type as inputs: scalar, Series, or DataFrame
    """
    return outcome_1 - outcome_2


def _effect_ratio(outcome_1, outcome_2) -> Union[float, pd.Series, pd.DataFrame]:
    """
    Calculate ratio: outcome_1 / outcome_2
    
    Args:
        outcome_1: Scalar, Series, or DataFrame of outcomes
        outcome_2: Matching shape as outcome_1
        
    Returns:
        Same type as inputs
        
    Raises:
        ValueError: If outcome_2 contains zeros
    """
    if isinstance(outcome_2, (int, float)):
        if outcome_2 == 0:
            raise ValueError("Cannot compute ratio: denominator (outcome_2) is zero")
    else:
        if (outcome_2 == 0).any():
            raise ValueError(
                "Cannot compute ratio: denominator (outcome_2) contains zero(s). "
                f"Found {(outcome_2 == 0).sum()} zero values."
            )
    
    return outcome_1 / outcome_2


def _effect_odds_ratio(outcome_1, outcome_2) -> Union[float, pd.Series, pd.DataFrame]:
    """
    Calculate odds ratio for binary outcomes in [0, 1].
    
    OR = (outcome_1 / (1 - outcome_1)) / (outcome_2 / (1 - outcome_2))
    
    Args:
        outcome_1: Scalar or vector of probabilities in [0, 1]
        outcome_2: Scalar or vector of probabilities in [0, 1]
        
    Returns:
        Same type as inputs
        
    Raises:
        ValueError: If outcomes are outside [0, 1] (invalid probabilities)
    """
    # Validate outcomes are probability-like (for odds ratio interpretation)
    def _validate_probability_range(val, name):
        if isinstance(val, (int, float)):
            if not (0 <= val <= 1):
                raise ValueError(
                    f"Odds ratio requires {name} in [0, 1] (valid probabilities). "
                    f"Got {val}."
                )
        else:
            if (val < 0).any() or (val > 1).any():
                raise ValueError(
                    f"Odds ratio requires {name} in [0, 1]. "
                    f"Found range: [{val.min():.4f}, {val.max():.4f}]"
                )
    
    _validate_probability_range(outcome_1, "outcome_1")
    _validate_probability_range(outcome_2, "outcome_2")
    
    odds_1 = outcome_1 / (1 - outcome_1)
    odds_2 = outcome_2 / (1 - outcome_2)
    
    return odds_1 / odds_2


# Dispatcher dict for effect calculation
_EFFECT_CALCULATORS = {
    EffectType.DIFF: _effect_diff,
    EffectType.RATIO: _effect_ratio,
    EffectType.ODDS_RATIO: _effect_odds_ratio,
}


def calculate_effect(
    outcome_1: Union[float, pd.Series, pd.DataFrame],
    outcome_2: Union[float, pd.Series, pd.DataFrame],
    effect_types: Union[str, List[str]] = "diff",
) -> Union[pd.Series, pd.DataFrame]:
    """
    Compute treatment effect(s) from two potential outcomes.
    
    Central function for effect estimation across all causallib estimators.
    Handles scalar (population) and vector (individual/CATE) effect estimation.
    
    Args:
        outcome_1: First potential outcome (e.g., treated outcome, Y(1))
        outcome_2: Second potential outcome (e.g., control outcome, Y(0))
        effect_types: Effect type(s) to compute.
                     Single string or list of strings.
                     Options: 'diff', 'ratio', 'or'
        
    Returns:
        pd.Series if outcome_1 and outcome_2 are scalars (population effect).
                  Index is effect_type, values are computed effects.
        pd.DataFrame if outcome_1/outcome_2 are vectors (individual effects).
                     Index is sample indices, columns are effect types.
                     
    Examples:
        >>> # Population effect
        >>> calculate_effect(0.3, 0.6)
        >>> # Output: Series(['diff': -0.3, 'ratio': 0.5, 'or': 0.2857...])
        
        >>> # Individual effects
        >>> y1 = pd.Series([0.2, 0.4, 0.5])
        >>> y0 = pd.Series([0.1, 0.2, 0.3])
        >>> calculate_effect(y1, y0, effect_types=['diff', 'ratio'])
        >>> # Output: DataFrame with columns ['diff', 'ratio']
        
    Raises:
        ValueError: If effect_types invalid or outcomes incompatible
    """
    # Validate effect types
    effect_types = EffectType.validate(effect_types)
    if isinstance(effect_types, str):
        effect_types = [effect_types]
    
    # Compute each effect type
    results = {}
    for effect_type in effect_types:
        calculator = _EFFECT_CALCULATORS[effect_type]
        try:
            effect = calculator(outcome_1, outcome_2)
            results[effect_type] = effect
        except Exception as e:
            raise ValueError(
                f"Failed to compute effect type '{effect_type}': {str(e)}"
            ) from e
    
    # Format output: scalar -> Series, vector -> DataFrame
    is_scalar = isinstance(outcome_1, (int, float, np.number))
    
    if is_scalar:
        # Population effect: return Series with effect_types as index
        return pd.Series(results)
    else:
        # Individual effects: return DataFrame with sample indices and effect type columns
        # Use concat to preserve indices and column names
        return pd.concat(results, axis="columns", names=["effect_type"])


def is_scalar_outcome(outcome) -> bool:
    """
    Check if outcome is scalar (population-level) or vector (individual-level).
    
    Args:
        outcome: Outcome value to check
        
    Returns:
        True if scalar, False if vector
    """
    return isinstance(outcome, (int, float, np.number))
