"""
Explicit assumption metadata for causal estimators.

This module defines canonical assumptions for each estimator class,
making them visible to users and engineers without reading source code.

Assumptions are surfaced in:
- summary() output
- diagnostic reports
- docstrings and help()
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum


class AssumptionCategory(Enum):
    """Categories of causal assumptions."""
    
    CONSISTENCY = "consistency"  # Treatment value is well-defined
    NO_UNMEASURED_CONFOUNDING = "no_unmeasured_confounding"  # All confounders measured
    POSITIVITY = "positivity"  # Overlap / common support
    CAUSAL_DIAGRAM = "causal_diagram"  # DAG assumptions
    FUNCTION_FORM = "function_form"  # Linearity, additivity, etc.
    INDEPENDENCE = "independence"  # Independence assumptions
    STABLE_UNIT_TREATMENT_VALUE = "sutva"  # SUTVA
    NO_INTERFERENCE = "no_interference"  # Units don't affect each other


@dataclass
class Assumption:
    """Represents a single causal assumption."""
    
    name: str
    category: AssumptionCategory
    description: str
    is_testable: bool  # Can this assumption be checked empirically?
    is_automatically_validated: bool  # Does causallib check this automatically?
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'category': self.category.value,
            'description': self.description,
            'is_testable': self.is_testable,
            'is_automatically_validated': self.is_automatically_validated,
        }
    
    def __repr__(self) -> str:
        return f"Assumption(name='{self.name}', category={self.category.value})"


# Standard assumptions for different estimator classes

IPW_ASSUMPTIONS = [
    Assumption(
        name="No Unmeasured Confounding",
        category=AssumptionCategory.NO_UNMEASURED_CONFOUNDING,
        description="All confounders that affect both treatment and outcome are observed in X",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="Positivity (Overlap)",
        category=AssumptionCategory.POSITIVITY,
        description="All treatment groups have positive probability in all strata of X",
        is_testable=True,
        is_automatically_validated=True,
    ),
    Assumption(
        name="Consistency",
        category=AssumptionCategory.CONSISTENCY,
        description="The treatment value is well-defined and does not vary across observations",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="SUTVA",
        category=AssumptionCategory.STABLE_UNIT_TREATMENT_VALUE,
        description="No interference: treatment assignment of one unit does not affect outcomes of others",
        is_testable=False,
        is_automatically_validated=False,
    ),
]

STANDARDIZATION_ASSUMPTIONS = [
    Assumption(
        name="No Unmeasured Confounding",
        category=AssumptionCategory.NO_UNMEASURED_CONFOUNDING,
        description="All confounders that affect both treatment and outcome are observed in X",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="Consistency",
        category=AssumptionCategory.CONSISTENCY,
        description="The treatment value is well-defined and does not vary across observations",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="Correct Model Specification",
        category=AssumptionCategory.FUNCTION_FORM,
        description="The outcome model correctly specifies the relationship between X, A, and Y",
        is_testable=True,
        is_automatically_validated=False,
    ),
    Assumption(
        name="SUTVA",
        category=AssumptionCategory.STABLE_UNIT_TREATMENT_VALUE,
        description="No interference: treatment assignment of one unit does not affect outcomes of others",
        is_testable=False,
        is_automatically_validated=False,
    ),
]

DOUBLY_ROBUST_ASSUMPTIONS = [
    Assumption(
        name="No Unmeasured Confounding (Weak)",
        category=AssumptionCategory.NO_UNMEASURED_CONFOUNDING,
        description="Either propensity model OR outcome model is correctly specified (not both required)",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="Positivity (Overlap)",
        category=AssumptionCategory.POSITIVITY,
        description="All treatment groups have positive probability in all strata of X",
        is_testable=True,
        is_automatically_validated=True,
    ),
    Assumption(
        name="Consistency",
        category=AssumptionCategory.CONSISTENCY,
        description="The treatment value is well-defined and does not vary across observations",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="SUTVA",
        category=AssumptionCategory.STABLE_UNIT_TREATMENT_VALUE,
        description="No interference: treatment assignment of one unit does not affect outcomes of others",
        is_testable=False,
        is_automatically_validated=False,
    ),
]

MATCHING_ASSUMPTIONS = [
    Assumption(
        name="No Unmeasured Confounding",
        category=AssumptionCategory.NO_UNMEASURED_CONFOUNDING,
        description="All confounders that affect both treatment and outcome are observed in X",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="Consistency",
        category=AssumptionCategory.CONSISTENCY,
        description="The treatment value is well-defined and does not vary across observations",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="SUTVA",
        category=AssumptionCategory.STABLE_UNIT_TREATMENT_VALUE,
        description="No interference: treatment assignment of one unit does not affect outcomes of others",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="Good Overlap on Matched Features",
        category=AssumptionCategory.POSITIVITY,
        description="After matching, treatment groups have similar covariate distributions",
        is_testable=True,
        is_automatically_validated=False,
    ),
]

RLEARNER_ASSUMPTIONS = [
    Assumption(
        name="No Unmeasured Confounding",
        category=AssumptionCategory.NO_UNMEASURED_CONFOUNDING,
        description="All confounders that affect both treatment and outcome are observed in X",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="Consistency",
        category=AssumptionCategory.CONSISTENCY,
        description="The treatment value is well-defined and does not vary across observations",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="SUTVA",
        category=AssumptionCategory.STABLE_UNIT_TREATMENT_VALUE,
        description="No interference: treatment assignment of one unit does not affect outcomes of others",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="Honest Samples (Causal Forest)",
        category=AssumptionCategory.INDEPENDENCE,
        description="Honest splitting ensures valid confidence intervals and avoids overfitting",
        is_testable=False,
        is_automatically_validated=False,
    ),
]

XLEARNER_ASSUMPTIONS = [
    Assumption(
        name="No Unmeasured Confounding",
        category=AssumptionCategory.NO_UNMEASURED_CONFOUNDING,
        description="All confounders that affect both treatment and outcome are observed in X",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="Consistency",
        category=AssumptionCategory.CONSISTENCY,
        description="The treatment value is well-defined and does not vary across observations",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="SUTVA",
        category=AssumptionCategory.STABLE_UNIT_TREATMENT_VALUE,
        description="No interference: treatment assignment of one unit does not affect outcomes of others",
        is_testable=False,
        is_automatically_validated=False,
    ),
]

TMLE_ASSUMPTIONS = [
    Assumption(
        name="No Unmeasured Confounding",
        category=AssumptionCategory.NO_UNMEASURED_CONFOUNDING,
        description="All confounders that affect both treatment and outcome are observed in X",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="Positivity (Overlap)",
        category=AssumptionCategory.POSITIVITY,
        description="All treatment groups have positive probability in all strata of X",
        is_testable=True,
        is_automatically_validated=True,
    ),
    Assumption(
        name="Consistency",
        category=AssumptionCategory.CONSISTENCY,
        description="The treatment value is well-defined and does not vary across observations",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="SUTVA",
        category=AssumptionCategory.STABLE_UNIT_TREATMENT_VALUE,
        description="No interference: treatment assignment of one unit does not affect outcomes of others",
        is_testable=False,
        is_automatically_validated=False,
    ),
    Assumption(
        name="Correct Model Specification",
        category=AssumptionCategory.FUNCTION_FORM,
        description="The outcome model and propensity model are correctly specified",
        is_testable=True,
        is_automatically_validated=False,
    ),
]

# Map estimator class names to their assumptions
ESTIMATOR_ASSUMPTIONS: Dict[str, List[Assumption]] = {
    'IPW': IPW_ASSUMPTIONS,
    'WeightedStandardization': IPW_ASSUMPTIONS,
    'OverlapWeights': IPW_ASSUMPTIONS,
    'Standardization': STANDARDIZATION_ASSUMPTIONS,
    'AIPW': DOUBLY_ROBUST_ASSUMPTIONS,
    'PropensityFeatureStandardization': DOUBLY_ROBUST_ASSUMPTIONS,
    'WeightedStandardization': DOUBLY_ROBUST_ASSUMPTIONS,
    'MatchEstimator': MATCHING_ASSUMPTIONS,
    'RLearner': RLEARNER_ASSUMPTIONS,
    'XLearner': XLEARNER_ASSUMPTIONS,
    'TMLE': TMLE_ASSUMPTIONS,
}


def get_assumptions_for_estimator(estimator_class_name: str) -> List[Assumption]:
    """
    Get the list of assumptions for an estimator class.
    
    Args:
        estimator_class_name: Name of the estimator class (e.g., 'IPW', 'TMLE')
        
    Returns:
        List of Assumption objects for this estimator
    """
    return ESTIMATOR_ASSUMPTIONS.get(estimator_class_name, [])
