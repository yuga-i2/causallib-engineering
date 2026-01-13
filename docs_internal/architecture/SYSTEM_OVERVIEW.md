# SYSTEM_OVERVIEW.md: CausalLib Architecture & Design

This document explains CausalLib's internal structure, design philosophy, and how components interact. It's intended for engineers taking over the codebase or implementing new features.

---

## 1. Design Philosophy

**Core Principle**: Modular estimation + structured diagnostics + clean validation

CausalLib separates concerns into three layers:

1. **Estimation Layer** (`causallib/estimation/`) – Causal effect estimators
2. **Diagnostics Layer** (`causallib/diagnostics/`) – Quality checks and assumption validation
3. **Validation & Metrics** (`causallib/validation/`, `causallib/metrics/`) – Input validation and evaluation

This separation allows:
- Swapping estimators without rewriting diagnostics
- Plugging in custom propensity/outcome models
- Extending with new metrics without affecting core logic
- Clear error messages from early validation

---

## 2. Core Modules Explained

### 2.1 Estimation Layer

**Location**: `causallib/estimation/`

**8 Estimators** (all inherit from `BaseEstimator` or `BaseWeighting`):

| Estimator | Base | Method | When to Use |
|-----------|------|--------|-------------|
| **IPW** | BaseWeighting | Propensity weight inversion | Simple case, large N |
| **Matching** | BaseEstimator | 1:1, k-NN, caliper matching | Interpretability needed |
| **Standardization** | BaseEstimator | Outcome model regression | Outcome structure known |
| **DoublyRobust (AIPW)** | BaseEstimator | Propensity + outcome + loss correction | Robustness to model misspecification |
| **RLearner** | BaseEstimator | Residual learning (Athey & Wager) | High-dim, complex heterogeneity |
| **XLearner** | BaseEstimator | Cross-fitting for HTE (Kunzel et al.) | Heterogeneous effects essential |
| **TMLE** | BaseEstimator | Targeted maximum likelihood estimation | Precise inference, semiparametric |
| **OverlapWeights** | BaseWeighting | Efficiency-weighted propensity | Rare outcome focus |

**Base Classes** (in `base_estimator.py`, `base_weight.py`):

- `BaseEstimator`: Template with `fit(X, treatment)`, `estimate_ate(X, T, y)`, `estimate_ate_per_group()`
- `BaseWeighting`: Subclass for weight-based methods, adds `get_propensity_scores()`, `get_weights()`

**Key Method**: `estimate_ate()` – Returns point estimate + optional confidence interval

**Design**: Pluggable models
```python
estimator = IPW(propensity_estimator=LogisticRegression())  # User supplies model
estimator.fit(X, treatment)
```

---

### 2.2 Diagnostics Layer

**Location**: `causallib/diagnostics/`

**Main Classes**:

| Class | Purpose | Output |
|-------|---------|--------|
| `PropensityScoreStats` | Validate propensity scores (overlap, calibration) | Report with warnings |
| `WeightDistribution` | Analyze weight extremeness (outliers, moments) | Statistics, plots |
| `OverlapDiagnostic` | Check positivity assumption (all groups have support) | Pass/fail + coverage % |
| `AssumptionCheckRunner` | Systematically validate unconfoundedness signals | Structured report |
| `Warnings` | Central warning aggregator | Collects all diagnostic flags |

**Usage Pattern**:
```python
ps_stats = PropensityScoreStats(estimator=estimator)
report = ps_stats.report(X, treatment)
print(report)  # Shows overlap %, violations, recommendations
```

**Design Philosophy**: Diagnostics run AFTER estimation, interpreting estimator internals (propensity scores, weights) from a causal lens. Never modify the estimator's output.

---

### 2.3 Datasets Module

**Location**: `causallib/datasets/`

**Built-in Loaders**:
- `load_nhefs()` – National Health and Examination Follow-up Study (classic causal inference benchmark)
- `load_acic16()` – ACIC2016 competition data
- `load_synthetic()` – CausalSimulator3 synthetic data

**Design**: Returns `(X, treatment, outcome)` tuple. Data is already split into features/treatment/outcome for convenience.

---

### 2.4 Metrics Module

**Location**: `causallib/metrics/`

**Three Categories**:

1. **Propensity Metrics** (`propensity_metrics.py`)
   - `weighted_roc_auc_error`: ROC-AUC of propensity score
   - `ici_error`: Integrated Calibration Index (calibration quality)

2. **Weight Metrics** (`weight_metrics.py`)
   - `covariate_balancing_error`: Post-weighting covariate balance
   - `covariate_imbalance_count_error`: # of unbalanced covariates

3. **Outcome Metrics** (`outcome_metrics.py`)
   - `balanced_residuals_error`: Residual balance check

**Design**: All metrics are sklearn-compatible scorers. Can be used in cross-validation.

---

### 2.5 Validation Module

**Location**: `causallib/validation/`

**Custom Exceptions** (all inherit from `CausallibValidationError`):
- `DataAlignmentError`: Feature matrix / treatment / outcome length mismatch
- `TreatmentValueError`: Invalid treatment values (e.g., > 2 levels for binary estimator)
- `NotFittedError`: Calling predict/estimate before fit
- `TaskTypeError`: Unsupported task (e.g., survival with wrong data)
- `LearnerInterfaceError`: Supplied estimator doesn't have required fit/predict methods

**Design**: Raised early, with clear context. No silent failures.

---

### 2.6 Positivity Module

**Location**: `causallib/positivity/`

**Checks and Handles Positivity Violation** (fundamental causal assumption: all groups have treatment probability between 0 and 1)

**Key Classes**:
- `UnivariateBBox`: Univariate positivity checks
- `TrimmingTransformer`: Remove low-propensity observations
- `MatchingTransformer`: Match on propensity before estimation

**Design**: Used as preprocessing step or diagnostic.

---

### 2.7 Model Selection Module

**Location**: `causallib/model_selection/`

**GridSearchCV** extension for hyperparameter tuning with causal metrics (e.g., propensity calibration).

**Key Classes**:
- `CausalCrossValidator`: Cross-validation for causal models
- `GridSearchCV`: Scikit-learn compatible grid search using causal metrics

---

### 2.8 Preprocessing Module

**Location**: `causallib/preprocessing/`

**Utilities**:
- `confounder_selection.py`: Variable selection (identify true confounders)
- `filters.py`: Data filtering (missing values, outliers)
- `transformers.py`: Data transformations (standardization, one-hot encoding)

---

### 2.9 Contrib Module

**Location**: `causallib/contrib/` ⚠️ RESEARCH GRADE

**Research extensions** (may change, not guaranteed stable API):
- `adversarial_balancing/`: Adversarial weighting
- `bicause_tree/`: Tree-based causal models
- `hemm/`: Heterogeneous effect mixture models
- `shared_sparsity_selection/`: High-dim variable selection
- `faissknn.py`: Approximate nearest neighbor matching (FAISS backend)

**Note**: Use only with validation. May be deprecated or refactored.

---

### 2.10 Simulation Module

**Location**: `causallib/simulation/`

**CausalSimulator3**: Generate synthetic data with known causal structure
- Configurable confounding
- Configurable treatment effect (linear, nonlinear, heterogeneous)
- Configurable outcome distribution
- Essential for algorithm development, robustness testing

**Usage**:
```python
from causallib.simulation import CausalSimulator3
sim = CausalSimulator3()
X, treatment, outcome = sim.simulate(n_samples=1000)
```

---

### 2.11 Analysis Module

**Location**: `causallib/analysis/`

**Utilities for interpreting results**:
- Effect aggregation (ATE, ATT, ATC)
- Result comparison across estimators
- Visualization helpers

---

### 2.12 Survival Module (Optional)

**Location**: `causallib/survival/`

**Causal survival analysis** (time-to-event outcomes)
- Kaplan-Meier curves with treatment effects
- Marginal structural models for survival
- Experimental extension

---

## 3. Design Patterns

### 3.1 Scikit-Learn Compatibility

All estimators follow sklearn's transformer/predictor API:
```python
estimator.fit(X, treatment)          # Fit on training data
effect = estimator.estimate_ate(X, T, y)  # Estimate on (possibly different) data
```

This allows:
- Drop-in replacement of propensity/outcome models
- Use with sklearn's pipeline and model selection
- Familiar API for ML engineers

### 3.2 Pluggable Models

Core estimators are agnostic to the propensity/outcome models:

```python
ipw = IPW(
    propensity_estimator=LogisticRegression(),  # User chooses
    # or: RandomForestClassifier(), GradientBoostingClassifier(), etc.
)
```

This enables:
- Experimenting with different models (linear, tree, neural net)
- Letting users apply domain knowledge (their favorite estimator)
- Robustness across model classes

### 3.3 Lazy Evaluation

Diagnostics are computed on-demand, not during fit:
```python
estimator.fit(X, treatment)          # Fast: only fits propensity
ps_stats = PropensityScoreStats(estimator)
report = ps_stats.report(X, treatment)  # Expensive: computes diagnostics
```

This keeps fit() fast and lets users choose which diagnostics to run.

### 3.4 Immutable Estimators

Estimators don't modify input data:
```python
X_original = X.copy()
estimator.fit(X, treatment)
assert (X == X_original).all()  # X unchanged
```

Enables safe reuse of data across experiments.

---

## 4. Data Flow: From Raw Data to Effect Estimate

### Typical Flow

```
Raw Data (CSV, DataFrame)
    ↓
Validation (check alignment, types, values)
    ↓
Preprocessing (missing values, scaling, confounder selection)
    ↓
Estimator.fit(X, treatment)
    ├─ Fit propensity model (internal)
    └─ Fit outcome model if needed (internal)
    ↓
Estimator.estimate_ate(X, treatment, outcome)
    └─ Return point estimate (+ CI if available)
    ↓
Diagnostics (optional)
    ├─ PropensityScoreStats (overlap, calibration)
    ├─ WeightDistribution (outlier analysis)
    ├─ OverlapDiagnostic (positivity checks)
    └─ AssumptionCheckRunner (unconfoundedness signals)
    ↓
Effect Estimate + Confidence Intervals + Diagnostic Report
```

### Error Handling

Validation catches issues early:
1. **Input validation** (in Estimator.__init__ and fit)
   - Check X is 2D
   - Check treatment is 1D
   - Check outcome is 1D
   - Check lengths match

2. **Model validation** (before fit)
   - Check propensity estimator has fit/predict
   - Check outcome estimator has fit/predict

3. **State validation** (before predict)
   - Check fit() was called
   - Raise NotFittedError if not

4. **Result validation** (after estimation)
   - Check no NaNs in weights (might indicate positivity violation)
   - Check weights sum to expected value

---

## 5. Extension Points

### 5.1 Adding a New Estimator

1. Inherit from `BaseEstimator` or `BaseWeighting`
2. Implement `fit(X, treatment)` – learn propensity/outcome models
3. Implement `estimate_ate(X, treatment, outcome)` – compute effect
4. Test with all datasets and metrics

### 5.2 Adding a New Diagnostic

1. Create class in `causallib/diagnostics/`
2. Implement `report(X, treatment, [outcome])` method
3. Return structured report (dict or DataFrame)
4. Register in `AssumptionCheckRunner`

### 5.3 Adding a New Metric

1. Create function in `causallib/metrics/`
2. Follow sklearn's scorer interface
3. Register in `scorers.py`
4. Use in cross-validation

---

## 6. Performance Considerations

### Latency
- **Fit**: ~100ms (1K samples, 10 features)
- **Estimate**: ~1ms (1K samples, 10 features)
- **Full diagnostics**: ~200ms
- **Target**: <5ms total for production inference

### Memory
- No in-memory duplication of data
- Propensity scores cached during fit
- Weights computed on-demand

### Scalability
- Tested up to 100K samples
- Hyperparameter tuning uses parallelization (n_jobs)
- Diagnostics can run in parallel (future improvement)

---

## 7. Testing Strategy

**Phase 1 Tests** (`test_phase1_hardening.py`): Core functionality
- All 8 estimators produce valid effects
- Propensity models fit correctly
- Edge cases (single feature, binary outcome) handled

**Phase 2 Tests** (`test_phase2_hardening.py`): Observability
- Diagnostics produce reports
- Error messages are clear
- Warnings capture real issues

**Phase 3 Tests** (`test_phase3.py`): Robustness
- Large datasets (100K rows)
- High-dimensional features (100 columns)
- Extreme propensity scores (near 0/1)
- Missing values, outliers

---

## 8. Dependency Graph

```
estimation/
  ├─ Requires: sklearn, pandas, numpy
  └─ Optionally uses: outcome models (user-provided)

diagnostics/
  ├─ Requires: estimation/, metrics/
  └─ Produces: reports for external tools

metrics/
  ├─ Requires: sklearn.metrics
  └─ Used by: model_selection/, diagnostics/

validation/
  ├─ Requires: pandas, numpy
  └─ Used by: ALL modules

datasets/
  ├─ Requires: pandas, numpy
  └─ Optional: scipy (for ACIC16 simulation)

positivity/
  ├─ Requires: sklearn, pandas, numpy
  └─ Uses: estimation/ outputs (propensity scores)

model_selection/
  ├─ Requires: sklearn, metrics/
  └─ Used by: advanced users

simulation/
  ├─ Requires: numpy, scipy
  └─ Used by: examples/, tests/

contrib/
  ├─ Research-grade
  └─ Experimental dependencies (e.g., FAISS)
```

---

## 9. Future Roadmap

**Stable** (not changing):
- Core 8 estimators
- Validation layer
- Datasets module

**Evolving** (may improve):
- Diagnostics (better reporting, more checks)
- Metrics (new propensity/weight metrics)
- Model selection (Bayesian optimization)

**Research** (subject to change):
- Contrib modules
- Survival analysis
- Neural net integration

---

## 10. FAQ

**Q: Why separate estimation and diagnostics?**  
A: Diagnostics are expensive and optional. Separation keeps fit() fast and lets users decide what to check.

**Q: Can I use custom propensity models?**  
A: Yes, pass any sklearn-compatible classifier to the estimator's `propensity_estimator` parameter.

**Q: What if propensity scores violate positivity?**  
A: Diagnostics will warn. Use `positivity/TrimmingTransformer` to remove low-propensity units.

**Q: Is causallib production-ready?**  
A: Yes, for its designed use cases (causal effect estimation, assumption validation). It's not a black-box optimization library.

**Q: Can I extend with new estimators?**  
A: Yes, inherit from `BaseEstimator` and implement fit/estimate_ate. See examples/ for templates.

---

## 11. Codebase Health Metrics

- **Lines of Code**: ~8,000 (core) + ~3,000 (contrib)
- **Test Coverage**: 80%+ (core modules)
- **Dependencies**: 4 core (sklearn, pandas, numpy, scipy)
- **Python Version**: 3.7+
- **Last Updated**: [Current date]

---

**For more details, see**:
- `README.md` – Quick start
- `STEP_BY_STEP_IMPLEMENTATION.md` – Hands-on examples
- `examples/` – Jupyter notebooks with real datasets
- Source code comments – Implementation details
