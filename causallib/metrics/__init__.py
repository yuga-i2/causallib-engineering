"""
Metrics Module

Evaluation metrics for causal inference quality:

Propensity Metrics:
  - weighted_roc_auc_error: Weighted ROC-AUC for propensity scores
  - ici_error: Integrated Calibration Index

Weight Metrics:
  - covariate_balancing_error: Balance quality post-weighting
  - covariate_imbalance_count_error: Number of imbalanced covariates

Outcome Metrics:
  - balanced_residuals_error: Residual balance validation

Use these to assess estimator quality and covariate balance.
"""
from .propensity_metrics import weighted_roc_auc_error, expected_roc_auc_error
from .propensity_metrics import weighted_roc_curve_error, expected_roc_curve_error
from .propensity_metrics import ici_error
from .weight_metrics import covariate_balancing_error
from .weight_metrics import covariate_imbalance_count_error
from .outcome_metrics import balanced_residuals_error

from .scorers import get_scorer, get_scorer_names
