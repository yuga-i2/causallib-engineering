"""
Causal Effect Estimation Module

Core functionality for estimating treatment effects using various methods:
- IPW (Inverse Probability Weighting)
- Matching (Propensity score matching)
- Standardization (Outcome regression)
- Doubly Robust (AIPW, Weighted Standardization)
- Meta-learners (R-Learner, X-Learner)
- TMLE (Targeted Maximum Likelihood Estimation)
- Overlap Weighting

All estimators follow the sklearn interface and support:
- Binary, multi-way, and continuous treatments
- Population and individual-level effect estimation
- Automated diagnostics and assumption checking
"""
from .doubly_robust import AIPW, PropensityFeatureStandardization, WeightedStandardization
from .ipw import IPW
from .overlap_weights import OverlapWeights
from .standardization import Standardization, StratifiedStandardization
from .marginal_outcome import MarginalOutcomeEstimator
from .matching import Matching, PropensityMatching
from .rlearner import RLearner
from .xlearner import XLearner
from .tmle import TMLE

