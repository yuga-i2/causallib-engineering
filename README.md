# CausalLib – Production-Grade Causal Inference in Python

CausalLib is a Python library for estimating causal treatment effects from observational data using well-established causal inference methods.  
It provides a consistent API, diagnostics for validating assumptions, and evaluation utilities to support reliable causal analysis in production and research workflows.

The library emphasizes transparency, correctness, and debuggability, making causal reasoning explicit rather than hidden behind black-box estimators.

---

## Quick Navigation

- **8 Causal Estimators**: IPW, Matching, Standardization, AIPW, R-Learner, X-Learner, TMLE, Overlap Weights
- **Production-Ready**: Type safety, error handling, 30+ passing tests
- **Diagnostics**: Propensity score analysis, overlap/positivity checks, covariate balance
- **Scikit-Learn Compatible**: Works with any sklearn-like estimator

---

## Overview

CausalLib supports causal effect estimation using multiple approaches, enabling practitioners to compare methods, validate assumptions, and understand trade-offs when working with non-experimental data.

Supported estimators include:

- **Inverse Probability Weighting (IPW)** – Fast, simple, sensitive to overlap violations
- **Matching** – Interpretable, computationally expensive  
- **Standardization** – Flexible outcome modeling
- **Augmented IPW (AIPW)** – Doubly robust, semiparametric
- **R-Learner** – Modern causal forests, high-dimensional data
- **X-Learner** – Heterogeneous treatment effects
- **Targeted Maximum Likelihood (TMLE)** – Semiparametric efficiency
- **Overlap Weights** – Handles positivity violations

The system is designed to work with user-provided machine learning models and integrates naturally with the scikit-learn ecosystem.

---

## Key Capabilities

- **Multiple causal estimators** under a unified API  
- **Diagnostics layer** for overlap, propensity scores, and covariate balance  
- **Clear validation & error handling** for common causal pitfalls  
- **Estimator comparison** to assess robustness of results  
- **Heterogeneous & stratified effects** support  
- **Extensive test coverage** for core functionality and edge cases  

---

## Design Principles

- **Explicit assumptions**: causal validity is checked, not assumed  
- **Interpretability first**: prioritizes clarity over black-box automation  
- **Modular architecture**: estimation, validation, and diagnostics are separated  
- **User control**: model choice and tuning remain explicit  
- **Production-aware**: clear errors, predictable behavior, tested paths  

---

## Architecture

### Layered Design

''' 

         User Code (Data Analysis)               

                 
    
      Estimation API (8 methods) 
      .fit() | .predict()        
      IPW | Matching | AIPW...   
    
                 
    
     Diagnostics & Validation Layer    
      Overlap/Positivity Checks       
      Propensity Score Analysis       
      Covariate Balance Reports       
      Weight Distribution             
    
                 
    
     Metrics & Evaluation              
      ATE, ATT, CATE                  
      Confidence intervals            
      Sensitivity analysis            
    
'''

### Data Flow

'''
Raw Data (X, T, Y)
    
[Preprocessing]  Filtering, feature engineering
    
[Propensity Model]  User-provided sklearn estimator
    
[Causal Estimator]  IPW, Matching, AIPW, etc.
    
[Diagnostics]  Validation checks, assumption testing
    
[Effects & Metrics]  ATE, confidence intervals, reports
    
Results & Insights
'''

---

## Project Highlights & Hot Spots

###  Key Strengths

1. **Unified API Across 8 Estimators**  
   All causal methods share consistent .fit() and .estimate_*() interface.  
   Users can swap estimators with minimal code changes for robustness checks.

2. **Comprehensive Diagnostics**  
   Not just estimation—validates assumptions before trusting results:
   - Positivity/overlap violations (can't estimate effects in sparse regions)
   - Propensity score calibration (is the model correct?)
   - Covariate balance (did weighting/matching work?)

3. **Production-Grade Error Handling**  
   Clear, actionable error messages instead of cryptic stack traces.  
   Catches 20+ common causal inference pitfalls at fit time.

4. **Works with Any Scikit-Learn Model**  
   No vendor lock-in. Use LogisticRegression, RandomForest, XGBoost, etc.  
   as propensity or outcome models—your choice.

5. **Well-Tested**  
   30+ unit tests covering:  
   - Core estimator correctness (statistical properties)
   - Edge cases (perfect separation, singular matrices)
   - Real datasets (NHEFS, ACIC, synthetic)

### Design Trade-offs

| Choice | Rationale |
|--------|-----------|
| No distributed backend | Single-machine is simpler, <100M rows is common |
| No deep learning models | Interpretability > black-box accuracy |
| User provides ML models | Explicit > automatic hyperparameter tuning |
| Semiparametric methods | Balances flexibility with robustness |

### Complexity Hotspots

1. **Overlap/Positivity Violations**  
   IPW weights explode when treatment groups don't overlap.
    Use overlap weights, TMLE, or trim rare regions.

2. **High-Dimensional Confounders**  
   Matching infeasible, propensity model overfits with many features.
    Use R-Learner or double ML with regularization.

3. **Heterogeneous Effects**  
   ATE hides important variation if effects vary by subgroup.
    Use X-Learner or stratified analysis.

4. **Unconfoundedness Assumption**  
   Cannot test if unmeasured confounding exists.
    Rely on domain knowledge and sensitivity analysis.

---

## Repository Structure

'''
causallib-engineering/
 README.md                          # This file
 setup.py                           # Package metadata
 requirements.txt                   # Dependencies
 LICENSE                            # Apache 2.0

 causallib/                         # Main package
    __init__.py
    estimation/                    # 8 Causal estimators
       base_estimator.py
       ipw.py
       matching.py
       standardization.py
       doubly_robust.py
       rlearner.py
       xlearner.py
       tmle.py
       overlap_weights.py
    diagnostics/                   # Assumption validation
       assumptions.py
       reports.py
       warnings.py
    datasets/                      # Built-in datasets
    metrics/                       # Evaluation metrics
    validation/                    # Input validation
    preprocessing/                 # Data transformation
    positivity/                    # Overlap analysis
    propensity/                    # Propensity score tools
    effects/                       # Effect estimation
    evaluation/                    # Result evaluation
    model_selection/               # Cross-validation
    simulation/                    # Synthetic data
    analysis/                      # Post-estimation
    contrib/                       # Research extensions
    survival/                      # Causal survival
    utils/                         # Utilities
    tests/                         # Unit tests

 examples/                          # Jupyter notebooks
    ipw.ipynb
    matching.ipynb
    doubly_robust.ipynb
    rlearner.ipynb
    xlearner.ipynb
    tmle.ipynb
    positivity.ipynb
    lalonde.ipynb
    nhefs.ipynb

 docs/                              # Sphinx documentation
 tests/                             # Integration tests
    test_phase1_hardening.py       # Core tests (10)
    test_phase2_hardening.py       # Diagnostics (10)
    test_phase3.py                 # Robustness (10)

 .github/workflows/
     build.yml                      # CI/CD
'''

---

## Installation

'''bash
pip install causallib
'''

---

## Quick Example

'''python
from causallib.estimation import IPW
from causallib.datasets import load_nhefs
from sklearn.linear_model import LogisticRegression

X, treatment, outcome = load_nhefs()

estimator = IPW(propensity_estimator=LogisticRegression())
estimator.fit(X, treatment)

ate = estimator.estimate_ate(X, treatment, outcome)
print(f"Average Treatment Effect: {ate:.3f}")
'''

---

## Diagnostics Example

'''python
from causallib.diagnostics import PropensityScoreStats

stats = PropensityScoreStats(estimator=estimator)
report = stats.report(X, treatment)
print(report)  # Overlap warnings, calibration, balance
'''

---

## Estimator Guide

| Estimator | Pros | Cons | Best For |
|-----------|------|------|----------|
| IPW | Fast, simple | Overlap-sensitive | Large, clean datasets |
| Matching | Intuitive | Computationally expensive | Small N |
| Standardization | Robust, flexible | Outcome model dependent | Known structure |
| AIPW | Doubly robust | Complex tuning | Moderate N |
| R-Learner | Modern, flexible | Requires large N | High-dim data |
| X-Learner | Heterogeneous effects | Intensive | Effect variation |
| TMLE | Targeted, efficient | Complex | Precise inference |
| Overlap Weights | Efficient | Specialized | Rare outcomes |

---

## Examples

Jupyter notebooks in 'examples/' covering:

- ipw.ipynb – IPW fundamentals
- matching.ipynb – Matching-based estimation
- doubly_robust.ipynb – AIPW (doubly robust)
- rlearner.ipynb – R-Learner for causal forests
- xlearner.ipynb – X-Learner for heterogeneity
- tmle.ipynb – Targeted ML estimation
- positivity.ipynb – Overlap & assumption validation
- lalonde.ipynb – Replicate Dehejia-Wahba study
- nhefs.ipynb – Real-world NHEFS dataset

---

## Documentation

- **Full API docs**: docs/
- **Step-by-step guides**: examples/
- **Architecture & design**: docs_internal/

---

## Testing

'''bash
# Run all tests
pytest

# Run specific suite
pytest test_phase1_hardening.py -v  # Core estimators
pytest test_phase2_hardening.py -v  # Diagnostics
pytest test_phase3.py -v            # Edge cases
'''

**Status**: 30/30 tests passing 

---

## License

Apache License 2.0

---

## Citation

If used in academic work, please cite:

Shimoni et al., An Evaluation Toolkit to Guide Model Selection and Cohort Definition in Causal Inference, 2019.
