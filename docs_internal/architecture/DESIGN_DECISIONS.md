# DESIGN_DECISIONS.md: Why Things Are The Way They Are

**Purpose**: Document design tradeoffs and justify decisions. Not to defend, but to explain judgment.

When reviewing code, ask: *"Why was this decision made?"* This document answers that question.

---

## 1. ARCHITECTURE DECISIONS

### 1.1 Three-Layer Architecture (Validation → Estimation → Diagnostics)

**The Decision**: Separate validation, estimation, and diagnostics into distinct layers.

**Why**: Traditional ML libraries mix all three. This causes:
- Errors caught late (user runs estimator for 10 minutes, fails at the end)
- Diagnostics bundled with fit (users pay cost they may not need)
- Hard to extend (adding a diagnostic requires modifying estimator)

**Our approach**:
```
Validation (fast, early)  ← Catch user errors before expensive work
     ↓
Estimation (core work)     ← Do the math
     ↓
Diagnostics (optional)     ← Check assumptions if user wants to
```

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Early failure with clear errors | More explicit API (user must call diagnostics) |
| Fast fit() | Slight API fragmentation |
| Independent layers | More code to learn |

**Alternative we rejected**:
- All-in-one fit() with diagnostics
- **Why rejected**: Users doing cross-validation pay diagnostic cost 10x. Wrong incentive.

**Judgment call**: Clarity and composability > simplicity.

---

### 1.2 Estimators Orchestrate, Don't Compute

**The Decision**: Estimators accept user-provided propensity/outcome models. They don't train the ML models themselves.

**Why**: Causal inference isn't about "best model"—it's about user's domain knowledge.
- Economist knows propensity should be logistic
- Product manager knows outcome is skewed (needs special model)
- Researcher might use neural net

If we auto-select, we hide assumptions.

**Our approach**:
```python
from sklearn.linear_model import LogisticRegression
from causallib.estimation import IPW

estimator = IPW(propensity_estimator=LogisticRegression())  # User chooses
estimator.fit(X, treatment)
```

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Transparent assumptions | More work for users |
| Leverages domain knowledge | Can pick bad models |
| No hidden tuning | No auto-optimization |

**Alternative we rejected**:
- Auto-select best propensity model via cross-validation
- **Why rejected**: What's "best"? By what metric? AUC? Calibration? ICI? Wrong question.

**Judgment call**: Transparency > convenience.

---

### 1.3 Single Source of Truth: Effect

**The Decision**: One method returns the effect. No `.estimate_ate_binary()`, `.estimate_ate_continuous()`, `.estimate_effect_heterogeneous()`.

**Why**: Multiple effect methods mean:
- Different APIs to learn
- Subtle bugs (which method should I use?)
- Hard to swap estimators (change IPW → AIPW, must call different method)

**Our approach**:
```python
effect = estimator.estimate_ate(X, treatment, outcome)
```

Same method signature for all 8 estimators. Always returns scalar ATE (or vector for group-level).

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Consistent interface | Less flexibility |
| Easy estimator swapping | Edge cases harder to express |
| Clear semantics | Some power users want heterogeneous effects (separate method) |

**Alternative we rejected**:
- Multiple effect methods (`estimate_ate`, `estimate_hte`, `estimate_cate`)
- **Why rejected**: Users comparing methods should use same call signature

**Judgment call**: Consistency > expressiveness.

---

### 1.4 Diagnostics Are Optional, Not Built-In

**The Decision**: Diagnostics run after fit, on user request. Not part of fit().

**Example**:
```python
# No automatic diagnostics
estimator.fit(X, treatment)  # Fast

# User explicitly asks for checks
diagnostics = PropensityScoreStats(estimator)
report = diagnostics.report(X, treatment)  # Expensive, optional
```

**Why**: In production, fast fit is critical. Not all users care about diagnostics (they just want effects).

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Fast fit() | Diagnostics not automatic (users forget to check) |
| Diagnostic cost paid only once per user request | More code to call |
| Can parallelize diagnostics independently | Potential error if user doesn't validate |

**Alternative we rejected**:
- Diagnostics computed during fit, cached automatically
- **Why rejected**: Users doing CV on 100 hyperparameters pay 100x diagnostic cost

**Judgment call**: Performance > convenience.

---

### 1.5 Custom Exceptions, Not Cryptic Sklearn/Pandas

**The Decision**: Raise custom exceptions with domain-specific messages.

**Example**:
```python
# GOOD (what we do)
raise TreatmentValueError(
    f"Treatment must be binary. Found {treatment.unique()}"
)

# BAD (what sklearn does)
# ValueError: Unable to find unique propensities between 0 and 1
```

**Why**: Causal inference is hard enough without cryptic errors.

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Users understand what went wrong | More exception classes to maintain |
| Actionable error messages | Slight performance cost (not meaningful) |
| Consistent across estimators | Custom exceptions can be verbose |

**Alternative we rejected**:
- Re-raise sklearn exceptions with try/except
- **Why rejected**: Still cryptic after wrapping

**Judgment call**: User experience > code simplicity.

---

## 2. API DECISIONS

### 2.1 No Automatic Hyperparameter Tuning

**The Decision**: Estimators don't tune propensity/outcome models automatically.

**Why**: We don't know what "good" means for your problem:
- For propensity: Good = high AUC? High calibration? Low variance?
- For outcome: Good = low MSE? Low MAE? Low residual bias?

If we auto-tune, we hide the assumption.

**Our approach**:
```python
# User provides pre-tuned models (or accepts defaults)
from sklearn.linear_model import LogisticRegression
estimator = IPW(propensity_estimator=LogisticRegression(max_iter=1000))
```

**Trade-offs**:
| Pro | Con |
|-----|-----|
| No hidden assumptions | More work for users |
| Domain knowledge respected | Can shoot themselves in foot |
| Explicit, debuggable | More boilerplate |

**Alternative we rejected**:
- Auto GridSearchCV on propensity models
- **Why rejected**: What scoring metric? What params to search? Wrong place to hide decisions.

**Judgment call**: Transparency > convenience.

---

### 2.2 Backward Compatibility First

**The Decision**: Preserve the original API, add on top. Don't refactor.

**Why**: Users depend on current API. Breaking changes = broken production code.

**Example**: We kept the inheritance hierarchy even though it could be "cleaner":
```python
# This is how it is (and we keep it)
class BaseEstimator:
    def estimate_ate(self, ...): pass

class BaseWeighting(BaseEstimator):
    def get_weights(self, ...): pass
```

We could flatten it, but users using `isinstance(est, BaseWeighting)` would break.

**Trade-offs**:
| Pro | Con |
|-----|-----|
| No user code breaks | Some code feels inelegant |
| Predictable upgrades | Technical debt accumulated |
| Smooth migration | Harder to refactor later |

**Alternative we rejected**:
- Refactor to modern inheritance (mixins, ABCs)
- **Why rejected**: Users upgrading from v0.5 → v0.6 shouldn't need code changes

**Judgment call**: Stability > elegance.

---

### 2.3 fit(X, treatment) Not fit(X, y)

**The Decision**: Estimators take `(X, treatment)` in fit, not `(X, y)`.

**Why**: Causal inference is different from supervised learning.

```python
# Causal (what we do)
estimator.fit(X, treatment)  # Learn propensity of treatment given X

# vs Supervised (sklearn)
estimator.fit(X, y)  # Learn to predict y from X
```

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Correct causal semantics | Non-standard vs sklearn |
| Prevents using outcome in fit | More to explain to sklearn users |
| Clear what's being learned | Requires different mindset |

**Alternative we rejected**:
- Follow sklearn's fit(X, y) convention
- **Why rejected**: Outcome isn't available during fit. It's used only in estimate_ate().

**Judgment call**: Correctness > convention.

---

## 3. CODE ORGANIZATION DECISIONS

### 3.1 Contrib/ Folder Explicitly Marked Research-Grade

**The Decision**: Experimental code (Adversarial Balancing, HEMM, Causal Trees) goes in `contrib/` with ⚠️ warnings.

**Why**: Research code isn't production-ready. Need clear signals.

**Our approach**:
```python
# In causallib/contrib/__init__.py
"""
Contrib Module - Research & Experimental Extensions

⚠️ WARNING: Contrib modules are research-grade. Use only with careful validation.
Stability, API, and output formats may change between versions.
"""
```

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Users know what's stable | Some innovation hidden |
| Clear boundaries | Less discoverability of new methods |
| Safe upgrades | Contrib harder to promote to core |

**Alternative we rejected**:
- Mix research code with core, rely on docstrings
- **Why rejected**: Users don't always read docs. Explicit folder structure > docstring.

**Judgment call**: Safety > integration.

---

### 3.2 No Automated Causal Graph Validation

**The Decision**: We don't build a causal graph validator or structure learner.

**Why**: Causal graphs are *domain knowledge*, not computable from data:
- Is Age a confounder? Only your economist knows.
- Is treatment post-treatment? Only your system architect knows.
- Is there unconfoundedness? Mathematically unverifiable.

If we try to auto-validate, we'll fail silently or give false confidence.

**Our approach**: Document the assumption, let users decide.

```python
# In validation layer
# We check what's verifiable:
OverlapDiagnostic(estimator).report(X, treatment)  # ✓ Checkable

# We do NOT check:
# - Whether X contains all confounders (✗ unverifiable)
# - Whether DAG is correct (✗ requires domain knowledge)
```

**Trade-offs**:
| Pro | Con |
|-----|-----|
| No false confidence | Users must think causally |
| Honest about limits | Doesn't help naïve users |
| Forces accountability | More education needed |

**Alternative we rejected**:
- Auto-suggest confounders (ML + domain hints)
- **Why rejected**: Liability if wrong. Causal assumptions are user's responsibility.

**Judgment call**: Honesty > helpfulness.

---

### 3.3 Pandas Not Required, But Recommended

**The Decision**: Accept numpy arrays, but examples use pandas.

**Why**: Some users have pipelines using numpy. Some use pandas. Support both.

**Our approach**:
```python
# Both work
X = np.array(...)  # numpy
estimator.fit(X, treatment)

X = pd.DataFrame(...)  # pandas
estimator.fit(X, treatment)
```

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Flexible | More testing burden |
| Not forcing pandas on numpy users | Edge cases in both |
| Production systems often use numpy | Documentation examples are pandas |

**Alternative we rejected**:
- Require pandas (better for introspection)
- **Why rejected**: Numpy arrays are valid; don't force migration.

**Judgment call**: Inclusivity > simplicity.

---

### 3.4 No Deep Learning (Yet)

**The Decision**: Don't support neural network models for propensity/outcome.

**Why**: Deep learning adds complexity without clear benefit for causal inference:
- Harder to debug (what's the learned representation?)
- Harder to validate (black box)
- Slower for small-medium data (<100K rows)
- Requires GPU (out of scope)

**Our approach**: Stick with sklearn models (linear, trees, etc.)

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Simpler, debuggable | Modern practitioners might want NN |
| Works on laptops (no GPU) | Limits expressiveness on large data |
| Interpretable propensity/outcome | Can't learn complex interactions easily |

**Alternative we rejected**:
- Add PyTorch backend for neural networks
- **Why rejected**: Different concerns. Would need separate library.

**Judgment call**: Clarity > capability.

---

## 4. DEPENDENCY DECISIONS

### 4.1 Minimal Core Dependencies (sklearn, pandas, numpy, scipy)

**The Decision**: Keep dependencies minimal. Don't add heavy frameworks.

**Why**: Each dependency is:
- A risk (breaks, security issues, conflicts)
- A learning curve (users must know the dependency)
- A performance penalty (import time)

**Our approach**:
```
Core deps:
✓ numpy (numerical computation)
✓ scipy (statistics)
✓ sklearn (ML models)
✓ pandas (DataFrames, optional)

NOT in core:
✗ PyTorch (too heavy for base library)
✗ TensorFlow (same)
✗ R interface (separate package)
✗ Spark (separate package)
```

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Simple install | Some users want deep learning |
| Fast import | Can't do GPU/distributed |
| Clear responsibility boundaries | Users want everything in one place |

**Alternative we rejected**:
- Add PyTorch as optional dependency
- **Why rejected**: "Optional" often becomes required. Better separate.

**Judgment call**: Minimalism > completeness.

---

### 4.2 No GPU / Spark Backend (Intentional Out-of-Scope)

**The Decision**: CausalLib runs on CPU, single machine. No Spark, no CUDA.

**Why**: Different problem with different constraints.
- GPU: Useful for neural nets (we don't use them)
- Spark: Useful for 1B+ rows (we target <100M)
- Single machine: Simpler debugging, reproducibility

For distributed causal inference, users should:
1. Run CausalLib locally on samples
2. Use Spark wrapper for production data

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Simpler codebase | Can't scale to 1B rows |
| Easier debugging | Enterprise users might want Spark |
| Reproducible (no distributed randomness) | Performance limited |

**Alternative we rejected**:
- Abstract backend for Spark/GPU
- **Why rejected**: 80% of effort, 20% of users

**Judgment call**: Focus > completeness.

---

## 5. TESTING DECISIONS

### 5.1 Test Real Data, Not Just Synthetic

**The Decision**: Tests include both synthetic (known ground truth) and real data (NHEFS, ACIC16).

**Why**: Synthetic tests catch algorithms. Real data catches integration bugs.

**Our approach**:
```
Phase 1: Core functionality
  - Synthetic data with known effect
  - Edge cases (N=10, p=1, etc.)

Phase 2: Observability
  - Real datasets (NHEFS)
  - Realistic propensity/outcome models

Phase 3: Robustness
  - Large synthetic data (100K rows)
  - Real edge cases (extreme propensity)
```

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Catches real-world bugs | More maintenance (real data can change) |
| Realistic scenario validation | Tests can be flaky (data updates) |
| Users see their data works | Slower to run |

**Alternative we rejected**:
- Only synthetic tests
- **Why rejected**: Miss integration bugs

**Judgment call**: Realism > speed.

---

### 5.2 No Automatically Generated Tests

**The Decision**: Every test is written by hand. No hypothesis-based property testing.

**Why**: Causal inference isn't about invariants. It's about **correctness on real scenarios**.

**What we don't do**:
```python
# We don't do this (property-based)
@given(arrays())
def test_estimator_on_any_array(X):
    estimator.fit(X, treatment)  # Might work, might not
```

**Why it fails**: Random arrays != causal assumptions.

**What we do**:
```python
# Real scenario: propensity scores near 1
X, treatment, outcome = make_extreme_propensity_data()
estimator.fit(X, treatment)
effect = estimator.estimate_ate(X, treatment, outcome)
assert not np.isnan(effect)  # Should warn, not crash
```

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Tests are meaningful | More test code to write |
| Catch real bugs | Can't exhaustively check all cases |
| Easy to understand | Developers must think about scenarios |

**Alternative we rejected**:
- Hypothesis (property-based testing)
- **Why rejected**: Properties don't match causal inference semantics

**Judgment call**: Meaning > coverage.

---

## 6. DOCUMENTATION DECISIONS

### 6.1 Three-Tier Documentation (README → SYSTEM_OVERVIEW → STEP_BY_STEP)

**The Decision**: Three different docs for different audiences.

**Why**: One doc can't be short AND comprehensive.

**Our approach**:
- **README**: 5-min overview (what, why, quick start)
- **SYSTEM_OVERVIEW**: 30-min deep dive (architecture, design patterns)
- **STEP_BY_STEP**: 60-min hands-on (10 examples, from basic to advanced)

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Each doc is focused | Users might read wrong doc |
| Different paces supported | More docs to maintain |
| Suitable for different roles | Longer to onboard (if user doesn't read in order) |

**Alternative we rejected**:
- Single comprehensive README
- **Why rejected**: Too long, suits no one

**Judgment call**: Clarity > consolidation.

---

### 6.2 Code Comments Explain Why, Not What

**The Decision**: Comments explain design decisions, not obvious code.

**Bad comment**:
```python
# Increment i
i += 1
```

**Good comment**:
```python
# Don't use np.unique because it sorts; preserves user's order
unique_treatments = pd.Series(treatment).unique()
```

**Trade-offs**:
| Pro | Con |
|-----|-----|
| Explains non-obvious decisions | Some code is still hard to understand |
| Helps future maintainers | Requires good writers |
| Documents assumptions | More review burden |

**Alternative we rejected**:
- Docstring per function explaining everything
- **Why rejected**: Self-documenting code > verbose docstrings

**Judgment call**: Clarity > completeness.

---

## 7. DECISION NOT TO DECIDE (Deferred Decisions)

### What We Didn't Decide Yet (And Why)

**Serialization format** (Phase 5)
- Why deferred: No consensus on best practice
- When to revisit: When deploying to production

**Bayesian confidence intervals** (Phase 5)
- Why deferred: Different assumptions; separate library
- When to revisit: If frequentist CIs insufficient

**Distributed computation** (Phase ∞)
- Why deferred: Significant architectural change
- When to revisit: When users hit 100M+ rows regularly

**Auto-feature selection** (Phase ∞)
- Why deferred: Out of scope (confounder selection is user's job)
- When to revisit: If strong demand

---

## 8. SUMMARY TABLE

| Decision | Choice | Judgment | Trade-off |
|----------|--------|----------|-----------|
| Architecture | 3-layer (validation → estimation → diagnostics) | Clarity | Explicit API |
| Model tuning | User-provided, not auto-tuned | Transparency | More work |
| Effect API | Single method per estimator | Consistency | Less flexibility |
| Diagnostics | Optional, after fit | Performance | Must explicitly call |
| Exceptions | Custom, domain-specific | UX | More code |
| Contrib | Separate folder + ⚠️ warnings | Safety | Less integrated |
| Causal validation | Don't auto-validate graphs | Honesty | User responsibility |
| Dependencies | Minimal (numpy, scipy, sklearn) | Simplicity | Limited features |
| GPU/Spark | Out of scope | Focus | Limited scale |
| Testing | Real data + synthetic | Realism | Slower tests |
| Comments | Explain why, not what | Clarity | More judgment needed |
| Documentation | Three tiers | Audience-fit | More maintenance |

---

## 9. THE PHILOSOPHY

**Why This Library Looks the Way It Does**

This library is built on one principle: **Trust through transparency.**

We could:
- Auto-optimize (looks smart, is opaque)
- Hide warnings (looks clean, is dangerous)
- Mix research and production code (looks integrated, is confusing)
- Minimal documentation (looks confident, is unfriendly)

Instead, we:
- Require explicit choices (takes more work, respects user)
- Show all assumptions (longer code, user knows what's happening)
- Mark research code (looks less integrated, is safer)
- Extensive documentation (looks less confident, is friendlier)

**Every design decision reflects the same value: Users should understand what they're using.**

That's not flashy. But it's how production systems should be built.

---

**When reviewing this code, ask: "Is this decision transparent?"**

**If yes, it belongs here. If no, we made a mistake.**
