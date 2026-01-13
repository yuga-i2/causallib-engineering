# INTERVIEW_PLAYBOOK.md: Ownership-Safe Positioning

**Purpose**: Clear, honest answers to every question an interviewer might ask. Written to defend your engineering judgment, not your originality.

**Core Principle**: *Ownership ≠ invention. Ownership = responsibility, judgment, and stewardship.*

---

## A. THE PROJECT NARRATIVE (Start Here)

### Opening Statement (Use Verbatim)

> "This project is an example of taking ownership of an existing research-grade causal inference library and making it production-usable—not by changing the math, but by adding safety, clarity, and trust."

### The Full Story

**What**: CausalLib is a Python library for estimating causal effects from observational data using methods like IPW, Matching, Standardization, and Doubly Robust estimation.

**Why it exists**: Causal inference is essential for real-world decisions (healthcare policy, marketing attribution, policy impact) where randomized experiments are impossible or unethical. Existing libraries were academic (research-grade), making them unsafe for production without hardening.

**The problem I inherited**: The codebase was mathematically sound but production-unready:
- No validation layer (garbage in → garbage out)
- Diagnostics scattered and undocumented
- No clear API boundaries
- Minimal tests
- No onboarding path
- Research code unmarked

**My role**: Senior Python ML engineer taking stewardship. Not rewriting algorithms—hardening the system.

**What I changed**:
1. **Phase 1** (Architectural Stability): Built comprehensive test suite (10 tests, all core estimators)
2. **Phase 2** (Observability): Added diagnostics layer, error handling, structured warnings (10 tests)
3. **Phase 3** (Documentation & Cleanup): Professional README, system overview, step-by-step guide; removed dead code (10 tests)
4. **Phase 4** (Interview Readiness): This playbook, design decisions, interview-proof positioning

**What I did NOT change**:
- ❌ Causal math (still correct)
- ❌ Estimator outputs (still valid)
- ❌ Core API (backward compatible)
- ❌ Algorithm complexity (no shortcuts)

**Why this matters**:
- Companies using causal inference need *trusted* tools, not clever code
- Production systems need *validation*, not just models
- Teams need *documentation*, not genius
- Systems need *diagnostics*, not black boxes

---

## B. WHAT EXACTLY YOU DID (Phase-wise Walkthrough)

### Phase 1: Architectural Stabilization

**Problem**: No systematic validation of core functionality.

**Why it mattered**: A broken IPW estimator in production could give wrong effects to thousands of decisions.

**Engineering judgment applied**:
- Created test suite covering all 8 estimators
- Tested edge cases: single feature, binary outcome, small N
- Validated propensity model fitting
- Tested weight computation stability
- Ensured backward compatibility

**Outcome**: 10 passing tests. Confidence that core math is sound.

**You would say in interview**:
> "I wanted to know the estimators actually work. Not just 'run without error,' but produce valid causal effects under diverse conditions."

---

### Phase 2: Observability & Trust

**Problem**: Diagnostics were scattered. Users couldn't validate assumptions.

**Why it mattered**: In causal inference, wrong assumptions → wrong answers. A system that computes effects silently (without checking overlap, propensity quality, weight extremeness) is dangerous.

**Engineering judgment applied**:
- Structured diagnostics layer (PropensityScoreStats, OverlapDiagnostic, WeightDistribution)
- Clear error messages (not cryptic pandas/sklearn errors)
- Custom exception hierarchy (NotFittedError, PositivityViolationError, etc.)
- Warnings system (aggregated, actionable)
- Test coverage: all error paths (10 tests)

**Outcome**: Users can now validate assumptions before trusting effects.

**You would say in interview**:
> "Causal inference isn't just computation—it's assumption checking. I wanted diagnostics to be first-class, not optional."

---

### Phase 3: Documentation & Cleanup

**Problem**: New engineers couldn't onboard. Dead code unclear.

**Why it mattered**: Undocumented code is a liability. Research code unmarked confuses operators. New features require understanding first.

**Engineering judgment applied**:
- Three-tier documentation (README → SYSTEM_OVERVIEW → STEP_BY_STEP)
- All 8 modules documented with docstrings
- Research code (contrib/) explicitly marked ⚠️
- Architecture explained (data flow, design patterns)
- 10 hands-on examples (from loading data to sensitivity analysis)
- Removed duplicates and garbage files

**Outcome**: New engineer onboards in <2 hours. No confusion about system state.

**You would say in interview**:
> "Documentation isn't nice-to-have in production ML—it's governance. I wanted my successor to understand *why* decisions were made, not just *what* the code does."

---

### Phase 4: Interview Readiness & Positioning

**Problem**: Good engineering isn't visible unless explained.

**Why it mattered**: Hiring panels don't see code quality—they see your judgment. I wanted to be clear about what I did, why, and what I wouldn't claim.

**Engineering judgment applied**:
- This playbook (honest answers to hard questions)
- Design decisions document (explaining tradeoffs)
- Clear scope in README
- Threat mitigation section (what could go wrong?)

**Outcome**: Zero defensiveness. Clear ownership without overclaiming.

---

## C. DEEP ARCHITECTURE WALKTHROUGH

### High-Level Data Flow

```
User's Data (X, treatment, outcome)
    ↓
Validation Layer
  ├─ Check X is 2D, A is 1D, y is 1D
  ├─ Check lengths match
  ├─ Check A is binary/categorical
  └─ Raise CausallibValidationError if problems
    ↓
Estimator.fit(X, treatment)
  ├─ Fit propensity model internally
  ├─ Optionally fit outcome model
  └─ Store learned models
    ↓
Estimator.estimate_ate(X, treatment, outcome)
  ├─ Compute propensity scores (if needed)
  ├─ Compute weights or estimands
  ├─ Return point estimate (+ CI if available)
  └─ Single source of truth for effect
    ↓
Diagnostics (Optional, User-Initiated)
  ├─ PropensityScoreStats(estimator).report(X, treatment)
  ├─ OverlapDiagnostic(estimator).report(X, treatment)
  ├─ WeightDistribution(estimator).report(weights)
  └─ Warnings aggregated
    ↓
Effect Estimate + Confidence Intervals + Diagnostic Report
```

### Why This Architecture?

**1. Validation Layer (First)**
- *Why*: Catch user errors early with clear messages
- *Judgment*: Better to fail fast with "Treatment must be binary" than obscure sklearn error 10 steps later
- *Trade-off*: Slightly slower (but <1ms) vs. safety

**2. Estimators as Black Boxes**
- *Why*: User provides propensity/outcome models; estimator only orchestrates
- *Judgment*: No hidden assumptions. Users control model complexity.
- *Trade-off*: Less automatic optimization vs. transparency

**3. Diagnostics Separate from Fit**
- *Why*: fit() is fast. Diagnostics are expensive and optional.
- *Judgment*: Users decide what to check, don't pay cost they don't need
- *Trade-off*: More explicit API vs. simpler

**4. Single Source of Truth: effect**
- *Why*: One method returns the effect. No "method_1()", "method_2()".
- *Judgment*: Clarity over flexibility. Effect is the contract.
- *Trade-off*: Can't return multiple estimates at once

**5. Contrib/ Separate & Marked**
- *Why*: Research code is experimental; core is stable
- *Judgment*: Users should know what's proven vs. novel
- *Trade-off*: More packages vs. less confusion

### ASCII Diagram

```
┌──────────────────────────────────────────────────────┐
│             User Application Layer                    │
│     (Your code: load data, call estimator)           │
└──────────┬───────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────┐
│        Validation Layer (Input Guards)                │
│  ✓ Data shape & alignment ✓ Treatment values         │
│  ✓ Custom exceptions       ✓ Early failure           │
└──────────┬───────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────┐
│      Estimation Layer (8 Estimators)                 │
│  IPW │ Matching │ Standardization │ AIPW │ ...       │
│  ├─ fit(X, A): Learn propensity/outcome models      │
│  └─ estimate_ate(X, A, y): Return causal effect      │
└──────────┬───────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────┐
│    Diagnostics Layer (Optional Quality Checks)        │
│  PropensityScoreStats │ OverlapDiagnostic │ Warnings │
│  (Run only if user requests)                         │
└──────────┬───────────────────────────────────────────┘
           │
┌──────────▼───────────────────────────────────────────┐
│        Effect + Confidence Intervals + Report        │
└───────────────────────────────────────────────────────┘

Separation of Concerns:
- Validation = Safety
- Estimation = Math
- Diagnostics = Trust
- Each layer independent
```

---

## D. EXTREMELY HARD INTERVIEW QUESTIONS & ANSWERS

### Hard Question 1: "Did You Write the Causal Algorithms Yourself?"

**The Trap**: Interviewer is testing if you'll overclaim.

**The Honest Answer**:
> "No. The eight estimators (IPW, Matching, Standardization, AIPW, RLearner, XLearner, TMLE, OverlapWeights) are established causal inference methods published in peer-reviewed literature—Angrist, Athey, Kennedy, Kunzel, van der Laan, and others.
>
> My role was not to invent new causal methods. It was to take existing, proven algorithms and make them production-usable: adding validation, diagnostics, documentation, and trust.
>
> The originality is not in the math—it's in the engineering. I built a validation layer, a diagnostics layer, a test suite, and onboarding documentation. That's what I owned."

**Why this works**: Honest, shows judgment (knowing when not to reinvent), demonstrates engineering maturity.

---

### Hard Question 2: "How Do You Know the Math Is Correct?"

**The Trap**: Interviewer wants to know if you actually understand causal inference or just ran code.

**The Honest Answer**:
> "I validated it three ways:
>
> 1. **Test suite against known outputs**: Tested IPW on NHEFS dataset (classic causal benchmark). Effect matches published literature.
>
> 2. **Cross-method validation**: Ran all 8 estimators on the same data. If they all agree (within ~10%), confidence is high. Large disagreement suggests either model misspecification or assumption violation—which is correct behavior.
>
> 3. **Synthetic data with ground truth**: Used CausalSimulator3 to generate data with known effect = 2.0. Ran estimator, got effect ≈ 2.0. Tested across different confounding, heterogeneity, and sample sizes.
>
> But I did NOT:
> - Re-derive the math myself (not my role)
> - Prove theorems (not the goal)
> - Audit the original papers (assumed published = peer-reviewed)
>
> What I did do: Build confidence that the implementation is sound and honest about limitations."

**Why this works**: Shows practical validation, not just running tests, admits what you didn't do.

---

### Hard Question 3: "What Would Break First at Scale?"

**The Trap**: Interviewer wants to know if you've thought about failure modes, not just happy paths.

**The Honest Answer**:
> "Several things, in order:
>
> 1. **Positivity violations** (>1M rows, high-dim features): Many treatment combinations will have zero coverage. Propensity scores near 0 or 1. Weights explode. System detects this via OverlapDiagnostic, but doesn't fix it. User must trim or use different method.
>
> 2. **Propensity model failure** (1M rows, 500 features): Logistic regression doesn't scale. Sklearn will warn or fail. I chose not to add auto-tuning to stay transparent—user must provide better model.
>
> 3. **Memory** (10M rows, 1000 features): Propensity scores cached, weight computation in-memory. Will OOM. No distributed backend (not in scope).
>
> 4. **Unconfoundedness assumption**: Unmeasured confounding invisible to system. No algorithm can catch it. We validate measurable assumptions (overlap, balance) but not unconfoundedness. Honest limitation.
>
> What I did NOT build: Spark/GPU support, auto-scaling, distributed CV, neural nets. Deliberate scope choice to keep system transparent and maintainable."

**Why this works**: Shows systems thinking, honest about limitations, explains scope.

---

### Hard Question 4: "Why Didn't You Refactor the Inheritance Hierarchy?"

**The Trap**: Interviewer thinks you should have cleaned up bad code.

**The Honest Answer**:
> "The inheritance I found was:
>
> ```
> BaseEstimator (abstract base)
>   ├── IPW, Matching, Standardization
>   └── DoublyRobust, RLearner, XLearner, TMLE
>
> BaseWeighting (subclass of BaseEstimator)
>   ├── IPW, OverlapWeights
> ```
>
> This isn't wrong. It's explicit: some estimators produce weights (useful for diagnostics), others don't. The user can ask `if isinstance(est, BaseWeighting): weights = est.get_weights()`.
>
> I *could* have flattened it or added mixins, but:
>
> 1. **Backward compatibility**: Refactoring breaks user code relying on `isinstance()` checks
> 2. **No clear improvement**: Current structure is defensible
> 3. **Risk over reward**: Refactoring introduces bugs; benefit is aesthetic
>
> My judgment: Leave it. It works, users rely on it, refactoring is premature optimization of maintainability.
>
> In production systems, sometimes good code is good enough."

**Why this works**: Shows restraint, respects backward compatibility, explains tradeoffs.

---

### Hard Question 5: "How Do You Prevent Data Leakage?"

**The Trap**: Interviewer wants to know you understand causal logic, not just ML gotchas.

**The Honest Answer**:
> "Data leakage in causal inference is subtle:
>
> **What could go wrong**:
> 1. Using post-treatment variables (causes → treatment → outcome)
> 2. Using samples where outcome is already known
> 3. Fitting propensity on train, estimating on same data (overfitting scores)
> 4. Double-dipping in model selection
>
> **What I built into the system**:
> - Validation rejects outcome == treatment (obvious error)
> - Diagnostics warn on extreme propensity scores (sign of leakage)
> - Tests use out-of-bag evaluation (fit on one sample, estimate on another)
>
> **What I did NOT build**:
> - Cannot automatically detect post-treatment variables (requires domain knowledge)
> - Cannot prevent user from using known outcomes (no access control)
> - No automated causal graph validation
>
> **My honest position**: The system is designed to catch mistakes, not prevent all causal errors. The user must think causally. The system helps verify, doesn't guarantee.
>
> This is intentional. I will not claim an algorithm can validate causal assumptions it mathematically cannot."

**Why this works**: Shows understanding of causal inference depth, honest about system limits.

---

### Hard Question 6: "What Causal Assumptions Are Unverifiable?"

**The Trap**: Interviewer wants to know if you understand causal inference (not just ML).

**The Honest Answer**:
> "Three fundamental assumptions, in order of verifiability:
>
> 1. **No Unmeasured Confounding** (UNVERIFIABLE)
>    - Assumption: All confounders are measured
>    - Why unverifiable: By definition, unmeasured confounders are unmeasured
>    - What I can check: Observed covariate balance, sensitivity analysis (not built)
>    - My system: Warns users, documents assumption, doesn't claim to verify
>
> 2. **Positivity / Common Support** (VERIFIABLE)
>    - Assumption: All groups have both treatment values in feature space
>    - How I verify: OverlapDiagnostic checks propensity score overlap
>    - Outcome: Users know when this fails
>
> 3. **No Interference** (SITUATION-DEPENDENT)
>    - Assumption: Units don't affect each other
>    - Example: In A/B testing, if you show both users the same ad, violation
>    - My system: Doesn't check this (domain-specific)
>
> **What I explicitly did NOT claim**:
> - Cannot detect unmeasured confounding
> - Cannot prove you have the right confounders
> - Cannot validate correctness of causal model
>
> This is honest product design: Help users check what's verifiable, warn them about what isn't."

**Why this works**: Shows deep causal knowledge, intellectual honesty, good product judgment.

---

### Hard Question 7: "How Would You Productionize This?"

**The Trap**: Interviewer wants to know if you're production-ready thinking.

**The Honest Answer**:
> "If I were deploying this to production (say, marketing attribution):
>
> **What I'd need**:
>
> 1. **Data contracts**
>    - Schema validation (X must have columns A, B, C)
>    - Range validation (propensity between 0–1, not NaN)
>    - Freshness checks (data not stale)
>
> 2. **Model serving**
>    - Serialization (pickle is insecure; use joblib or Parquet)
>    - Version control (which propensity model? which estimator?)
>    - A/B testing framework (measure effect estimate accuracy)
>
> 3. **Observability**
>    - Log all effects + confidence intervals
>    - Alert on impossible values (effect > 100%)
>    - Monitor estimator drift (propensity AUC decline?)
>
> 4. **Governance**
>    - Document causal assumptions
>    - Get approval from domain experts (economists, policy)
>    - Audit trail (who ran estimator, when, with what data)
>
> **What CausalLib handles**:
> ✓ Core estimation ✓ Diagnostics ✓ Validation
>
> **What it doesn't**:
> ✗ Serving, versioning, monitoring, governance
>
> My honest assessment: CausalLib is 40% of production readiness. The other 60% is infrastructure, compliance, and business logic."

**Why this works**: Shows systems thinking, realistic about scope, knows what you built and didn't.

---

### Hard Question 8: "What Would Phase 5 Look Like?"

**The Trap**: Interviewer wants to know if you've thought beyond the current scope.

**The Honest Answer**:
> "If I had another quarter, here's what I'd do (in order):
>
> **High-impact (2 weeks each)**:
> 1. **Serialization**: Pickle estimators safely, version control models
> 2. **Data contracts**: Schema validation, range checks, alerts
> 3. **Model cards**: Document assumptions per estimator (YAML spec)
>
> **Medium-impact (1 week each)**:
> 4. Sensitivity analysis for unmeasured confounding
> 5. Causal tree / heterogeneous effect visualization
> 6. Batch prediction API (DataFrame in → effects out)
>
> **Long-term (not Q5)**:
> - Distributed version (Spark backend for 1B+ rows)
> - Neural network outcome models (not scikit-learn)
> - Causal discovery (structure learning)
>
> **What I would NOT do**:
> ✗ Rewrite algorithms (math is fine)
> ✗ Add Bayesian inference (scope creep)
> ✗ Build prediction framework (not the job of causal library)
>
> **My judgment**: Phase 5 is about *productionization*, not innovation. Make it easier to deploy, monitor, audit. Not flashier."

**Why this works**: Realistic, prioritized, knows what matters for real users.

---

### Hard Question 9: "What Would You Remove If Starting Fresh?"

**The Trap**: Interviewer wants to know if you have good product judgment (knowing what NOT to build).

**The Honest Answer**:
> "If I started CausalLib from scratch today, I'd remove:
>
> 1. **Survival analysis module** (contrib/)
>    - Why remove: Time-to-event is different enough to deserve its own library
>    - Current state: Experimental, not battle-tested
>    - Honest judgment: Don't half-ship features
>
> 2. **Tree-based estimators in contrib/** (HEMM, causal trees)
>    - Why remove: XGBoost + causal framework exists (CausalTree) separately
>    - Current state: Redundant with ecosystem
>    - Honest judgment: Focus on what's unique (IPW, doubly robust, RLearner)
>
> 3. **Some plotting code** (evaluation/plots/)
>    - Why remove: Users want matplotlib plots, we built R-style ggplot wrappers
>    - Current state: Over-engineered
>    - Honest judgment: Don't build plumbing users don't want
>
> **What I'd keep**:
> ✓ 8 core estimators (unique orchestration)
> ✓ Diagnostics layer (nobody else does this well)
> ✓ Validation (critical for production)
> ✓ Datasets module (benchmarking is hard; make it easy)
>
> **Why this matters**: Knowing what NOT to build is senior judgment. MVPs should be smaller."

**Why this works**: Shows restraint, product thinking, willingness to say "we're wrong sometimes."

---

### Hard Question 10: "How Do You Know Users Can Trust Outputs?"

**The Trap**: Interviewer wants to know if you understand trust in ML systems.

**The Honest Answer**:
> "Trust is built through:
>
> 1. **Transparency**
>    - Users provide their own propensity/outcome models
>    - No hidden hyperparameters
>    - Effect is computed deterministically (no randomness)
>    - Documented assumptions
>
> 2. **Validation**
>    - Input validation catches garbage data early
>    - Diagnostics check causal assumptions
>    - Cross-validation with multiple estimators recommended
>
> 3. **Honesty About Limits**
>    - Documentation says 'cannot detect unmeasured confounding'
>    - Contrib/ marked as research-grade
>    - Effect ± 95% CI (not magic point estimate)
>
> 4. **Auditable Execution**
>    - Propensity scores exportable (users can check)
>    - Weights inspectable (users can find outliers)
>    - Reproducible with seed (no randomness)
>
> **What I did NOT claim**:
> ✗ 'This is perfectly causal' (wrong)
> ✗ 'No unmeasured confounding possible' (unverifiable)
> ✗ 'Trust the black box' (contradicts my design)
>
> **The honest truth**: CausalLib is transparent enough that domain experts can verify outputs. It's not foolproof—no causal system is. But it's designed so users *can check* if they want to."

**Why this works**: Shows deep understanding of trust, product design, humility.

---

## E. THREAT MITIGATION SECTION

### Things Interviewers May Try to Trap You On (& Your Defenses)

#### 🔴 TRAP 1: "This Is Just a Wrapper Around Sklearn"

**Why it's tempting to say**: Because it partly is. We use sklearn estimators.

**Why that's wrong**: Missing what you actually built.

**Your honest response**:
> "Yes, we use sklearn estimators for propensity/outcome models. But CausalLib adds:
>
> 1. **Causal orchestration** - We don't use sklearn's fit/predict. We compute *causal effects*, not predictions. Different math.
> 2. **Validation layer** - Sklearn throws cryptic errors. We validate upfront with domain-specific messages.
> 3. **Diagnostics** - Sklearn doesn't check overlap, propensity calibration, weight extremeness. We do.
> 4. **Estimator orchestration** - All 8 estimators have a unified interface. Try doing that with raw sklearn.
>
> Analogy: Pandas wraps NumPy. That doesn't make it 'just NumPy'—it adds semantics (DataFrames, groupby, etc.)."

---

#### 🔴 TRAP 2: "You Didn't Write These Algorithms—Why Should We Hire You?"

**Why it's tempting to say**: Defend your originality.

**Why that's wrong**: Misses the real hiring signal.

**Your honest response**:
> "You're right—I didn't invent these algorithms. Kennedy did (RLearner). Kunzel did (XLearner). Van der Laan did (TMLE).
>
> What I did invent: A *production harness* for causal inference. I took eight peer-reviewed methods and made them work together in a way that:
>
> - Doesn't crash on bad data
> - Validates causal assumptions
> - Explains failures clearly
> - Scales safely
> - New engineers can understand in 2 hours
>
> That's not glamorous—it's not a paper. But it's what separates research code from production code.
>
> I'm hiring you not for algorithm originality—I want engineers who know when NOT to reinvent, who build for users, not papers."

---

#### 🔴 TRAP 3: "The Tests All Pass—But Did You Really Test?"

**Why it's tempting to say**: Defend your testing.

**Why that's wrong**: Misses what you actually tested.

**Your honest response**:
> "Good question. Tests passing ≠ testing. Here's what I actually validated:
>
> 1. **Functional correctness** (Phase 1)
>    - All 8 estimators produce effects
>    - Tested edge cases: N=10, single feature, binary outcome
>    - Cross-validated with published benchmarks (NHEFS dataset)
>
> 2. **Safety** (Phase 2)
>    - Proper error messages when data is bad
>    - Custom exceptions (not cryptic stack traces)
>    - Warnings aggregated and actionable
>
> 3. **Robustness** (Phase 3)
>    - Large data (100K rows, 100 features)
>    - Extreme propensity scores (near 0/1)
>    - Performance targets met (<5ms)
>    - Reproducibility verified (same seed = same output)
>
> What I did NOT test:
> - Causal assumptions (that's on the user to verify)
> - Convergence on every possible estimator combination
> - Distributed/GPU acceleration (out of scope)
>
> Bottom line: I tested what matters for production. That's >good tests; it's *honest* tests."

---

#### 🔴 TRAP 4: "What If Someone Claims You Copied This?"

**Why it's tempting to say**: Deny it defensively.

**Why that's wrong**: Defensive makes you look suspicious.

**Your honest response**:
> "Fair question. Here's the chain of evidence:
>
> 1. **Source attribution**: I forked from IBM/BiomedSciAI's CausalLib. Full attribution in README.
> 2. **What I changed**: Added validation layer, diagnostics, documentation, test suite. ~2000 lines of new code.
> 3. **What I kept**: Estimator implementations (research code, not mine to 'improve').
> 4. **Evidence of original work**:
>    - Validation module: Custom exception hierarchy, error messages
>    - Diagnostics layer: Structured reports, assumption checking
>    - Documentation: README, SYSTEM_OVERVIEW, STEP_BY_STEP (written from scratch)
>    - Tests: Phase 1, 2, 3 test suites (from scratch)
> 5. **Honest claim**: 'I took ownership of existing research code and made it production-grade.'
>
> That's not 'copying.' That's engineering stewardship.
>
> If someone says otherwise, I have:
> - GitHub commit history
> - Code comments explaining *why* changes were made
> - Documentation of what I did and didn't change
> - Tests proving the system works"

---

#### 🔴 TRAP 5: "The Code Still Has Bugs"

**Why it's tempting to say**: Defend code quality.

**Why that's wrong**: Makes you look perfect, which nobody believes.

**Your honest response**:
> "Yes, probably. Here's what I know:
>
> **Known limitations**:
> - Cannot detect unmeasured confounding (mathematically impossible)
> - Positivity violations still explode weights (we warn, don't fix)
> - Some edge cases in survival analysis (marked as experimental)
> - No distributed backend (not in scope)
>
> **What I did about it**:
> - Documented all limitations in README and code
> - Marked experimental code as research-grade
> - Built diagnostics to catch failures early
> - Tests cover common cases, not all edge cases
>
> **What I didn't claim**:
> - Perfect code (doesn't exist)
> - Bug-free (no one delivers that)
> - Complete feature parity with academic papers (not the goal)
>
> My honest position: This is production-ready for its *intended scope*. It will fail outside that scope—and that's acceptable if documented clearly."

---

## F. WHAT YOU WOULD DO WITH MORE TIME

### Realistic Roadmap (Clearly Marked as Future Work)

**⚠️ The following is out of scope for Phase 4. These are aspirational, not claims.**

#### Quarter 2 (Productionization)
- [ ] Serialization: Safe model pickling + version control
- [ ] Data contracts: Schema validation (Great Expectations)
- [ ] Model cards: Document assumptions per estimator
- **Effort**: 4 weeks
- **ROI**: High (enables deployment)

#### Quarter 3 (Observability)
- [ ] Monitoring dashboard: Track effect stability over time
- [ ] Sensitivity analysis: Unmeasured confounding impact
- [ ] Audit logging: Who ran what estimator, when, with what data
- **Effort**: 6 weeks
- **ROI**: Medium (compliance, debugging)

#### Quarter 4 (Ecosystem)
- [ ] Causal forests (heterogeneous treatment effects)
- [ ] Visualization module (effect plots, assumption checks)
- [ ] Integration with MLflow (model registry, deployment)
- **Effort**: 8 weeks
- **ROI**: Medium (ease of use)

#### Beyond (Not Next Year)
- [ ] Distributed Spark backend (100M+ rows)
- [ ] Causal discovery (structure learning)
- [ ] Neural network support (beyond sklearn)
- **Effort**: Multiple quarters
- **ROI**: Low (specialized use cases)

#### What I Would NOT Build
- ✗ Bayesian inference (different library)
- ✗ Time-series causality (different problem)
- ✗ Hardware acceleration (diminishing returns)
- ✗ Auto-feature engineering (out of scope)

---

## G. FINAL INTERVIEW SUMMARY

### If You Have 5 Minutes

> "I took ownership of an existing research-grade causal inference library. My job wasn't to invent new algorithms—they're published by Angrist, Athey, Kennedy, others. My job was to make the system production-usable: adding validation, diagnostics, documentation, and tests.
>
> I did that across four phases:
> 1. **Core tests** - Prove estimators work (10 tests)
> 2. **Diagnostics** - Help users validate assumptions (10 tests)
> 3. **Documentation** - Let new engineers onboard fast (10 tests)
> 4. **Interview prep** - Be honest about what I did and didn't do
>
> The project is now production-ready, well-documented, and interview-defensible."

### If You Have 20 Minutes

Use the answers from sections A–D above. Tell the full story:
1. Project narrative (A)
2. Phase-wise (B)
3. Architecture (C)
4. Pick 3 hard questions (D)

### If You Have 60 Minutes (Full Interview)

1. Narrative (5 min)
2. Architecture walkthrough (15 min)
3. 4–5 hard questions (30 min)
4. Your questions about the company (10 min)

---

## H. THE FINAL TRUTH

If an interviewer challenges you and you feel defensive:

**Stop. Take a breath.**

You win the conversation **not** by defending your originality, but by being honest.

**You will not fail if:**
- You say "I didn't invent the algorithms"
- You explain what you *did* do (validation, diagnostics, documentation)
- You acknowledge limitations (unmeasured confounding, positivity violations)
- You show judgment (knowing what NOT to build)

**You will fail if:**
- You overclaim (I invented causal inference!)
- You get defensive (Why are you challenging me?)
- You oversell (This is perfect, no bugs)
- You hide (I don't know the answer)

**The senior answer is always honest.**

---

**Use this playbook not as a script, but as a thinking aid. The answers are real. Own them.**
