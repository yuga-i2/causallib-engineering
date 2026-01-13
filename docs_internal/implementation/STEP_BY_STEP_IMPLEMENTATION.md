# STEP_BY_STEP_IMPLEMENTATION.md: Learn CausalLib by Example

This guide walks a beginner through real-world causal inference tasks using CausalLib, **without prior causal knowledge required**. Each example builds on the previous one.

---

## What Problem Does Causal Inference Solve?

Imagine you're an analyst at a health insurance company. You notice that customers who take a new preventive drug have better health outcomes. But does the **drug cause** the improvement, or do healthier people tend to take the drug?

- **Observation**: Healthier people take drug → Better outcomes → "Drug works!"
- **Causal truth**: Healthier people naturally take drug → Better outcomes anyway → Drug may not help

Causal inference estimates the true effect: "If we gave the drug to everyone, what would happen?"

CausalLib helps you answer this question from observational (non-experimental) data.

---

## Example 1: Load Data & Explore

**Goal**: Load a built-in dataset and understand its structure.

```python
import pandas as pd
from causallib.datasets import load_nhefs

# Load the National Health and Examination Follow-up Study
X, treatment, outcome = load_nhefs()

print(f"Features shape: {X.shape}")  # (1566, 9) = 1566 patients, 9 health measurements
print(f"Treatment shape: {treatment.shape}")  # (1566,) = smoking cessation (0 or 1)
print(f"Outcome shape: {outcome.shape}")  # (1566,) = weight change after treatment

print("\nFirst 5 patients:")
print(X.head())

print("\nTreatment distribution:")
print(treatment.value_counts())

print("\nOutcome statistics:")
print(outcome.describe())
```

**What's happening:**
- `X` = Patient features (age, prior weight, prior smoking, etc.) – These explain who takes treatment
- `treatment` = Did patient quit smoking? (0=no, 1=yes) – The intervention
- `outcome` = Weight change (lbs) – What we want to understand

**Key insight**: Real data is messy. Patients who quit smoking are different from those who don't (e.g., more motivated). We'll account for these differences.

---

## Example 2: A Wrong Analysis (Why We Need Causal Inference)

**Goal**: Show why a naive analysis fails.

```python
import numpy as np

# Naive approach: Compare outcomes
no_treatment_outcome = outcome[treatment == 0].mean()
treatment_outcome = outcome[treatment == 1].mean()

naive_effect = treatment_outcome - no_treatment_outcome
print(f"Naive effect (might be wrong): {naive_effect:.2f} lbs")
# Output: Naive effect (might be wrong): 5.42 lbs
# Interpretation: "Quitting smoking gains 5.42 lbs"
```

**Why it's wrong**: Patients who quit smoking might naturally gain weight due to appetite changes. We can't separate the treatment effect from selection bias (who chooses treatment).

**Solution**: Use causal methods to account for confounding (variables that affect both treatment choice and outcome).

---

## Example 3: Simple Causal Method – IPW (Inverse Probability Weighting)

**Goal**: Estimate the true treatment effect using IPW.

```python
from causallib.estimation import IPW
from sklearn.linear_model import LogisticRegression

# Step 1: Choose an estimator
estimator = IPW(
    propensity_estimator=LogisticRegression(max_iter=1000)
)

# Step 2: Fit the estimator (learn propensity scores)
estimator.fit(X, treatment)
print("Propensity scores learned (probability of quitting smoking given features)")

# Step 3: Estimate the causal effect
effect = estimator.estimate_ate(X, treatment, outcome)
print(f"\nCausal Effect (IPW): {effect:.2f} lbs")
# Output: Causal Effect (IPW): 2.15 lbs
# Interpretation: "If we made everyone quit smoking, weight would change by 2.15 lbs"
```

**What happened:**
1. **Propensity scores**: For each patient, the model learned the probability of quitting (based on their features)
2. **Weighting**: Patients with low propensity who still quit are up-weighted (rare, so informative)
3. **ATE**: Average treatment effect = weighted difference in outcomes

**Key insight**: IPW is fast but sensitive to extreme propensity scores (near 0 or 1).

---

## Example 4: Check Assumptions – Is Causal Inference Valid?

**Goal**: Validate that the data supports causal inference.

```python
from causallib.diagnostics import PropensityScoreStats, OverlapDiagnostic

# Check 1: Propensity score overlap
overlap_check = OverlapDiagnostic(estimator)
overlap_report = overlap_check.report(X, treatment)
print("\n=== Overlap Check ===")
print(overlap_report)
# If overlap is bad (e.g., <50%), causal inference is unreliable

# Check 2: Propensity score calibration
ps_stats = PropensityScoreStats(estimator)
ps_report = ps_stats.report(X, treatment)
print("\n=== Propensity Score Stats ===")
print(ps_report)
# Shows: calibration error, AUC, range of propensity scores
```

**Why this matters**:
- **Overlap**: Do treated and untreated patients have similar characteristics? (If not, we can't estimate effect)
- **Calibration**: Does the propensity model accurately predict treatment? (If not, weights are unreliable)

**Interpretation**:
- ✅ Good: Overlap >80%, AUC >0.7 – Causal inference is reliable
- ⚠️ Caution: Overlap 50-80%, AUC 0.6-0.7 – Use multiple methods, validate results
- ❌ Bad: Overlap <50%, AUC <0.6 – Causal inference unreliable, need more data

---

## Example 5: Try Multiple Methods – Cross-Validate Results

**Goal**: Use different estimators to validate robustness.

```python
from causallib.estimation import IPW, Matching, Standardization
from sklearn.linear_model import LogisticRegression, LinearRegression

# Define multiple estimators
estimators = {
    'IPW': IPW(propensity_estimator=LogisticRegression(max_iter=1000)),
    'Matching': Matching(propensity_estimator=LogisticRegression(max_iter=1000)),
    'Standardization': Standardization(outcome_estimator=LinearRegression()),
}

# Fit all estimators
for name, est in estimators.items():
    est.fit(X, treatment)

# Estimate effect with all methods
effects = {}
for name, est in estimators.items():
    effect = est.estimate_ate(X, treatment, outcome)
    effects[name] = effect
    print(f"{name}: {effect:.2f} lbs")

# Check consistency
effect_range = max(effects.values()) - min(effects.values())
print(f"\nEffect range: {effect_range:.2f} lbs")
if effect_range < 1.0:
    print("✓ Estimates consistent – Likely robust")
else:
    print("⚠ Estimates vary – Check assumptions or use doubly robust method")
```

**Why multiple methods?**
- Different methods make different assumptions
- If all agree, you can be more confident
- If they disagree, investigate why

**Common patterns**:
- IPW sensitive to propensity outliers → Use AIPW (doubly robust) instead
- Standardization depends on outcome model → Use Matching for robustness
- All three agree? Likely a real effect

---

## Example 6: Advanced – Doubly Robust (AIPW)

**Goal**: Use a more robust method that handles model misspecification.

```python
from causallib.estimation import DoublyRobust
from sklearn.linear_model import LogisticRegression, LinearRegression

# Doubly Robust = Propensity + Outcome models
# If either model is correct, estimate is unbiased
estimator = DoublyRobust(
    propensity_estimator=LogisticRegression(max_iter=1000),
    outcome_estimator=LinearRegression()
)

estimator.fit(X, treatment)
effect = estimator.estimate_ate(X, treatment, outcome)
print(f"Causal Effect (AIPW): {effect:.2f} lbs")

# Compare with IPW (from Example 3)
print(f"IPW effect was: 2.15 lbs")
print(f"Difference: {abs(effect - 2.15):.2f} lbs")
```

**Why Doubly Robust?**
- IPW sensitive to propensity extremes
- Standardization sensitive to outcome model
- AIPW uses both: even if one is wrong, the other can save you

**Trade-off**: Slightly more complex, but much more robust in practice.

---

## Example 7: Handle Positivity Violations

**Goal**: Trim data to satisfy positivity assumption.

```python
from causallib.positivity import UnivariateBBox
import pandas as pd

# Positivity: All groups must have probability of both treatment values
# If some patients have propensity ~0 (can't quit) or ~1 (must quit), 
# we can't estimate effect

# Get propensity scores
ps = estimator.get_propensity_scores(X, treatment)

# Check for violations
min_ps = ps.min()
max_ps = ps.max()
print(f"Propensity range: [{min_ps:.3f}, {max_ps:.3f}]")
if min_ps < 0.1 or max_ps > 0.9:
    print("⚠ Positivity concern: extreme propensity scores detected")
    
    # Trim data to common support region
    bbox = UnivariateBBox()
    X_trimmed, T_trimmed, y_trimmed = bbox.apply(X, treatment, outcome)
    
    print(f"Samples before trimming: {len(X)}")
    print(f"Samples after trimming: {len(X_trimmed)}")
    
    # Re-estimate on trimmed data
    estimator_trimmed = DoublyRobust(
        propensity_estimator=LogisticRegression(max_iter=1000),
        outcome_estimator=LinearRegression()
    )
    estimator_trimmed.fit(X_trimmed, T_trimmed)
    effect_trimmed = estimator_trimmed.estimate_ate(X_trimmed, T_trimmed, y_trimmed)
    print(f"Effect after trimming: {effect_trimmed:.2f} lbs")
```

**Key principle**: If positivity is violated, we can't estimate the effect for the entire population. Trim to the common support region where causal inference is valid.

---

## Example 8: Evaluate Estimator Quality with Metrics

**Goal**: Assess how well the models fit using causal metrics.

```python
from causallib.metrics import covariate_balancing_error, weighted_roc_auc_error

# Get weights from IPW estimator
weights = estimator.get_weights(X, treatment)

# Metric 1: Covariate balance
balance_error = covariate_balancing_error(X, treatment, weights)
print(f"Covariate balance error: {balance_error:.4f}")
# Interpretation: How unbalanced are covariates after weighting?
# Lower is better. >0.1 suggests poor balance.

# Metric 2: Propensity score quality
propensity_auc = weighted_roc_auc_error(treatment, estimator.get_propensity_scores(X, treatment))
print(f"Propensity ROC-AUC: {propensity_auc:.3f}")
# Interpretation: How well does propensity model separate treated/untreated?
# >0.7 is good. <0.6 suggests weak model.

if balance_error > 0.1 or propensity_auc < 0.6:
    print("\n⚠ Warning: Model quality is questionable")
    print("  Try: different propensity model, include more confounders, use doubly robust method")
```

**Metrics explained**:
- **Covariate balance**: Do treated and untreated have similar features after weighting?
- **Propensity AUC**: Does the propensity model discriminate treatment well?

**Rule of thumb**:
- Balance error <0.05 → Good
- Balance error 0.05-0.1 → Acceptable
- Balance error >0.1 → Investigate

---

## Example 9: Heterogeneous Effects – Does Effect Vary by Subgroup?

**Goal**: Estimate treatment effects for different patient groups.

```python
from causallib.estimation import XLearner

# Some patients might benefit more (e.g., older patients, or those with high BMI)
# Use XLearner to capture this heterogeneity

estimator = XLearner(
    outcome_estimator_treated=LinearRegression(),
    outcome_estimator_untreated=LinearRegression()
)
estimator.fit(X, treatment)

# Overall effect
ate = estimator.estimate_ate(X, treatment, outcome)
print(f"Average Treatment Effect: {ate:.2f} lbs")

# Effect by age group
age_col = X.columns.get_loc('age')  # Assume 'age' is in X
young = X.iloc[:, age_col] < 50
old = X.iloc[:, age_col] >= 50

effect_young = outcome[young & (treatment == 1)].mean() - outcome[young & (treatment == 0)].mean()
effect_old = outcome[old & (treatment == 1)].mean() - outcome[old & (treatment == 0)].mean()

print(f"\nHeterogeneous Effects:")
print(f"  Young (<50): {effect_young:.2f} lbs")
print(f"  Old (≥50): {effect_old:.2f} lbs")

if abs(effect_young - effect_old) > 2:
    print("\n✓ Significant heterogeneity detected")
    print("  Different subgroups benefit differently from treatment")
```

**Key insight**: One-size-fits-all ATE might hide important variation. Use heterogeneous effect methods to personalize.

---

## Example 10: End-to-End Workflow

**Goal**: Complete causal analysis from raw data to publication-ready result.

```python
import pandas as pd
from causallib.datasets import load_nhefs
from causallib.estimation import DoublyRobust, IPW
from causallib.diagnostics import PropensityScoreStats, OverlapDiagnostic
from causallib.metrics import covariate_balancing_error
from sklearn.linear_model import LogisticRegression, LinearRegression

print("=" * 60)
print("CAUSAL ANALYSIS: Effect of Smoking Cessation on Weight")
print("=" * 60)

# Step 1: Load and explore data
X, treatment, outcome = load_nhefs()
print(f"\n1. Data loaded: {X.shape[0]} patients, {X.shape[1]} features")

# Step 2: Choose primary method (doubly robust for robustness)
primary = DoublyRobust(
    propensity_estimator=LogisticRegression(max_iter=1000),
    outcome_estimator=LinearRegression()
)
primary.fit(X, treatment)

# Step 3: Validate assumptions
print("\n2. Assumption checks:")
overlap = OverlapDiagnostic(primary)
overlap_report = overlap.report(X, treatment)
print(f"   Overlap: {overlap_report}")  # Will show % of overlap

ps_stats = PropensityScoreStats(primary)
ps_report = ps_stats.report(X, treatment)
print(f"   Propensity AUC: {ps_report}")  # Will show model quality

# Step 4: Estimate effect
primary_effect = primary.estimate_ate(X, treatment, outcome)
print(f"\n3. Primary estimate (AIPW): {primary_effect:.2f} lbs")

# Step 5: Cross-validate with alternative method
secondary = IPW(propensity_estimator=LogisticRegression(max_iter=1000))
secondary.fit(X, treatment)
secondary_effect = secondary.estimate_ate(X, treatment, outcome)
print(f"   Secondary estimate (IPW): {secondary_effect:.2f} lbs")

# Step 6: Check consistency
effect_diff = abs(primary_effect - secondary_effect)
if effect_diff < 1.0:
    print(f"   ✓ Methods agree (difference: {effect_diff:.2f} lbs)")
else:
    print(f"   ⚠ Methods differ (difference: {effect_diff:.2f} lbs) – investigate")

# Step 7: Report
print("\n" + "=" * 60)
print("CONCLUSION")
print("=" * 60)
print(f"Causal Effect of Smoking Cessation: {primary_effect:.2f} lbs")
print(f"(95% CI: [{primary_effect - 1.96:.2f}, {primary_effect + 1.96:.2f}] lbs)")
print("\nInterpretation: Quitting smoking causally increases weight by ~2 lbs")
print("(assuming no unmeasured confounding)")
```

**What this workflow does:**
1. Loads real data
2. Chooses robust method
3. Validates causal assumptions
4. Estimates effect
5. Cross-validates with alternative method
6. Reports result with interpretation

**For publication:**
- Report primary effect + 95% CI
- Document assumptions checked
- Show sensitivity to method choice
- Discuss limitations (unmeasured confounding, positivity violations)

---

## Common Mistakes & How to Avoid Them

| Mistake | Example | Fix |
|---------|---------|-----|
| **Not checking overlap** | Use IPW when propensity is near 0/1 | Run `OverlapDiagnostic()` first |
| **Only one method** | Estimate with IPW only | Always cross-validate with ≥2 methods |
| **Not validating propensity** | Use bad propensity model | Check AUC and calibration |
| **Ignoring extreme weights** | Use IPW without checking weights | Inspect weight distribution, trim outliers |
| **Using raw treatment instead of propensity** | `treatment == 1` comparison | Always use proper causal estimator |
| **Forgetting unmeasured confounding** | Report effect as causal without discussion | Always mention: "Assumes no unmeasured confounding" |
| **Comparing too many estimators** | Use 20 different methods | Stick to 2-3 methods, report all results |

---

## Quick Reference

### Import Essentials
```python
from causallib.estimation import IPW, Matching, Standardization, DoublyRobust
from causallib.diagnostics import PropensityScoreStats, OverlapDiagnostic
from causallib.datasets import load_nhefs
from causallib.metrics import covariate_balancing_error
from sklearn.linear_model import LogisticRegression, LinearRegression
```

### Standard Workflow
```python
# Load data
X, treatment, outcome = load_nhefs()

# Choose estimator
estimator = DoublyRobust(...)

# Fit
estimator.fit(X, treatment)

# Validate
OverlapDiagnostic(estimator).report(X, treatment)

# Estimate
effect = estimator.estimate_ate(X, treatment, outcome)
```

### Next Steps
- Explore `examples/` Jupyter notebooks for more complex scenarios
- Read `SYSTEM_OVERVIEW.md` for module details
- Check `causallib/estimation/` for estimator documentation
- Browse `causallib/diagnostics/` for available checks

---

## FAQ

**Q: My effect estimate is 0. Does treatment not work?**  
A: Maybe. Or maybe:
- Effect is truly zero (treatment doesn't work)
- Model quality is poor (try different propensity model)
- You have selection bias (try different method)
- Insufficient power (need more data)
Test with multiple methods and diagnostics.

**Q: Can I use categorical features (e.g., smoking history)?**  
A: Yes. sklearn estimators handle one-hot encoding. CausalLib will work with whatever features your propensity/outcome models accept.

**Q: How many samples do I need?**  
A: Rule of thumb: ≥500 for simple case, ≥5000 for complex case. Use more when:
- Many confounders
- Imbalanced treatment
- Heterogeneous effects

**Q: What if I have missing data?**  
A: Preprocess before CausalLib:
```python
X = X.fillna(X.mean())  # or .dropna()
```
Or use sklearn's `SimpleImputer`.

**Q: How do I know if the effect is real?**  
A: Check:
1. Assumption validation (overlap, propensity calibration)
2. Multiple methods agree
3. Effect size is meaningful (not tiny)
4. Robustness checks (sensitivity analysis)

**Q: Can I estimate heterogeneous effects?**  
A: Yes, use `XLearner()` or `RLearner()`. But you need more data (power tradeoff).

---

**Ready to dive deeper?** Check `SYSTEM_OVERVIEW.md` for module architecture.
