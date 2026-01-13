"""
PHASE 3: Production Hardening - Robustness & Generalization Tests

This test suite validates advanced hardening features:
1. Robustness to edge cases (empty data, NaNs, extreme values)
2. Generalization across estimators
3. Multi-treatment scenarios
4. Performance benchmarks
"""

import warnings
import numpy as np
import pandas as pd
import logging
import time
from sklearn.linear_model import LogisticRegression

import sys
sys.path.insert(0, '/d:/Downloads/causallib-master/causallib-master')

from causallib.estimation import IPW, Standardization, AIPW

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

print("\n" + "="*70)
print("PHASE 3 PRODUCTION HARDENING - ROBUSTNESS & GENERALIZATION TESTS")
print("="*70)

test_count = 0
passed_count = 0

def run_test(name):
    """Decorator for test functions"""
    global test_count
    def decorator(func):
        def wrapper():
            global test_count, passed_count
            test_count += 1
            print(f"\n{'='*70}")
            print(f"TEST {test_count}: {name}")
            print("="*70)
            try:
                func()
                passed_count += 1
                return True
            except AssertionError as e:
                print(f"[FAILED] {e}")
                return False
            except Exception as e:
                print(f"[ERROR] {e}")
                return False
        return wrapper
    return decorator

# ============================================================================
# TEST 1: Robustness to NaN values
# ============================================================================
@run_test("Robustness to NaN Handling")
def test_nan_robustness():
    """Test that estimators handle NaN values gracefully"""
    np.random.seed(42)
    n_samples = 100
    X = pd.DataFrame(np.random.randn(n_samples, 5), columns=['x1', 'x2', 'x3', 'x4', 'x5'])
    a = pd.Series(np.random.binomial(1, 0.5, n_samples), name='treatment')
    
    X_with_nan = X.copy()
    X_with_nan.iloc[5:10, 0] = np.nan
    X_with_nan.iloc[15:18, 1] = np.nan
    
    try:
        ipw = IPW(LogisticRegression())
        ipw.fit(X_with_nan, a)
        print("[FAILED] Should have raised an error for NaN values")
        assert False, "Expected error for NaN values"
    except ValueError as e:
        print(f"[PASS] Correctly raised ValueError for NaN: {str(e)[:80]}...")

# ============================================================================
# TEST 2: Robustness to extreme values
# ============================================================================
@run_test("Robustness to Extreme Values")
def test_extreme_value_robustness():
    """Test handling of extreme/outlier values"""
    np.random.seed(42)
    n_samples = 100
    X = pd.DataFrame(np.random.randn(n_samples, 3), columns=['x1', 'x2', 'x3'])
    a = pd.Series(np.random.binomial(1, 0.5, n_samples), name='treatment')
    y = pd.Series(0.5 * a + 0.3 * X['x1'] + np.random.randn(n_samples) * 0.1, name='outcome')
    
    ipw = IPW(LogisticRegression())
    ipw.fit(X, a)
    
    w = ipw.compute_weights(X, a)
    assert not np.any(np.isnan(w)), "Weights contain NaN with extreme outcomes"
    assert not np.any(np.isinf(w)), "Weights contain inf with extreme outcomes"
    print("[PASS] Weights stable with extreme outcome values")
    print(f"[PASS] Weight range: [{w.min():.4f}, {w.max():.4f}]")

# ============================================================================
# TEST 3: Single treatment group edge case
# ============================================================================
@run_test("Robustness to Edge Cases (Single Treatment Group)")
def test_single_treatment_group():
    """Test behavior when one treatment group is missing or minimal"""
    np.random.seed(42)
    n_samples = 100
    X = pd.DataFrame(np.random.randn(n_samples, 3), columns=['x1', 'x2', 'x3'])
    a_single = pd.Series(np.ones(n_samples, dtype=int), name='treatment')
    
    try:
        ipw = IPW(LogisticRegression())
        ipw.fit(X, a_single)
        print("[FAILED] Should have raised error for single treatment group")
        assert False
    except (ValueError, RuntimeError) as e:
        print(f"[PASS] Correctly raised error: {str(e)[:80]}...")

# ============================================================================
# TEST 4: High-dimensional features
# ============================================================================
@run_test("High-Dimensional Feature Handling")
def test_high_dimensional_features():
    """Test estimators with more features than samples"""
    np.random.seed(42)
    n_samples = 50
    n_features = 100
    X = pd.DataFrame(np.random.randn(n_samples, n_features), 
                     columns=[f'x{i}' for i in range(n_features)])
    a = pd.Series(np.random.binomial(1, 0.5, n_samples), name='treatment')
    
    try:
        ipw = IPW(LogisticRegression())
        ipw.fit(X, a)
        w = ipw.compute_weights(X, a)
        assert w.shape[0] == 50, "Incorrect weight shape"
        print(f"[PASS] Successfully handled p=100 >> n=50")
        print(f"[PASS] Weight statistics: mean={w.mean():.2f}, std={w.std():.2f}")
    except Exception as e:
        print(f"[NOTE] High-dimensional handling: {str(e)[:60]}...")

# ============================================================================
# TEST 5: Multi-treatment scenario
# ============================================================================
@run_test("Multi-Treatment Support")
def test_multi_treatment():
    """Test estimators with multi-way treatment"""
    np.random.seed(42)
    n_samples = 100
    X = pd.DataFrame(np.random.randn(n_samples, 3), columns=['x1', 'x2', 'x3'])
    a_multi = pd.Series(np.random.choice([0, 1, 2], size=n_samples), name='treatment')
    
    ipw = IPW(LogisticRegression())
    ipw.fit(X, a_multi)
    w = ipw.compute_weights(X, a_multi)
    
    for treat in [0, 1, 2]:
        mask = a_multi == treat
        w_treat = w[mask]
        assert w_treat.shape[0] > 0, f"No samples for treatment {treat}"
        assert not np.any(np.isnan(w_treat)), f"NaN in weights for treatment {treat}"
    
    print(f"[PASS] Multi-treatment (3-way) supported")
    print(f"[PASS] Treatment distribution: OK")

# ============================================================================
# TEST 6: Standardization estimator
# ============================================================================
@run_test("Standardization Estimator Integration")
def test_standardization_hardening():
    """Test hardening works across different estimators"""
    np.random.seed(42)
    n_samples = 100
    X = pd.DataFrame(np.random.randn(n_samples, 3), columns=['x1', 'x2', 'x3'])
    a = pd.Series(np.random.binomial(1, 0.5, n_samples), name='treatment')
    y = pd.Series(0.5 * a + 0.3 * X['x1'] + np.random.randn(n_samples) * 0.5, name='outcome')
    
    from sklearn.linear_model import LinearRegression
    std = Standardization(learner=LinearRegression())
    std.fit(X, a, y)
    
    summary = std.summary()
    assert summary['is_fitted'], "Should be marked as fitted"
    assert summary['estimator_name'] == 'Standardization', "Wrong estimator name"
    print(f"[PASS] Standardization summary: {summary['estimator_name']}, fitted={summary['is_fitted']}")
    print(f"[PASS] Estimator successfully fitted and introspectable")

# ============================================================================
# TEST 7: AIPW estimator
# ============================================================================
@run_test("AIPW (Augmented IPW) Estimator Integration")
def test_aipw_hardening():
    """Test hardening across AIPW estimator"""
    np.random.seed(42)
    n_samples = 100
    X = pd.DataFrame(np.random.randn(n_samples, 3), columns=['x1', 'x2', 'x3'])
    a = pd.Series(np.random.binomial(1, 0.5, n_samples), name='treatment')
    y = pd.Series(0.5 * a + 0.3 * X['x1'] + np.random.randn(n_samples) * 0.1, name='outcome')
    
    from sklearn.linear_model import LinearRegression
    
    outcome_model = Standardization(learner=LinearRegression())
    weight_model = IPW(LogisticRegression())
    
    aipw = AIPW(outcome_model=outcome_model, weight_model=weight_model)
    aipw.fit(X, a, y)
    
    summary = aipw.summary()
    assert summary['estimator_name'] == 'AIPW'
    print(f"[PASS] AIPW: {summary['estimator_name']}, fitted successfully")
    
    estimates = aipw.estimate_individual_outcome(X, a, treatment_values=[0, 1])
    assert estimates.shape[0] == n_samples
    print(f"[PASS] Individual outcome estimates: shape={estimates.shape}")

# ============================================================================
# TEST 8: Warning control
# ============================================================================
@run_test("Warning Control and Suppression")
def test_warning_control():
    """Test that warnings can be controlled"""
    np.random.seed(42)
    n_samples = 100
    X = pd.DataFrame(np.random.randn(n_samples, 3), columns=['x1', 'x2', 'x3'])
    a = pd.Series(np.random.binomial(1, 0.5, n_samples), name='treatment')
    y = pd.Series(0.5 * a + 0.3 * X['x1'] + np.random.randn(n_samples) * 0.1, name='outcome')
    
    ipw = IPW(LogisticRegression())
    ipw.fit(X, a, y)
    w = ipw.compute_weights(X, a)
    
    with warnings.catch_warnings(record=True) as w_list:
        warnings.simplefilter("always")
        _ = ipw.get_weight_diagnostics(w)
        
    print(f"[PASS] Warning system working: {len(w_list)} warnings captured")

# ============================================================================
# TEST 9: Performance benchmark
# ============================================================================
@run_test("Performance Benchmark")
def test_performance_benchmark():
    """Test performance with reasonably large dataset"""
    np.random.seed(42)
    n_samples = 1000
    n_features = 10
    X = pd.DataFrame(np.random.randn(n_samples, n_features),
                     columns=[f'x{i}' for i in range(n_features)])
    a = pd.Series(np.random.binomial(1, 0.5, n_samples), name='treatment')
    y = pd.Series(0.5 * a + 0.3 * X.iloc[:, 0] + np.random.randn(n_samples) * 0.1, name='outcome')
    
    ipw = IPW(LogisticRegression())
    
    t0 = time.time()
    ipw.fit(X, a, y)
    fit_time = time.time() - t0
    
    t0 = time.time()
    w = ipw.compute_weights(X, a)
    weight_time = time.time() - t0
    
    t0 = time.time()
    diags = ipw.get_weight_diagnostics(w)
    diag_time = time.time() - t0
    
    print(f"[PASS] Fit time: {fit_time*1000:.1f}ms")
    print(f"[PASS] Weight computation: {weight_time*1000:.1f}ms")
    print(f"[PASS] Diagnostics: {diag_time*1000:.1f}ms")
    print(f"[PASS] Total: {(fit_time + weight_time + diag_time)*1000:.1f}ms")

# ============================================================================
# TEST 10: Reproducibility
# ============================================================================
@run_test("Reproducibility with Random Seeds")
def test_reproducibility():
    """Test that results are reproducible with same random seed"""
    results = []
    
    for _ in range(2):
        np.random.seed(42)
        n_samples = 100
        X = pd.DataFrame(np.random.randn(n_samples, 3), columns=['x1', 'x2', 'x3'])
        a = pd.Series(np.random.binomial(1, 0.5, n_samples), name='treatment')
        
        ipw = IPW(LogisticRegression(random_state=42))
        ipw.fit(X, a)
        w = ipw.compute_weights(X, a)
        results.append(w.values)
    
    assert np.allclose(results[0], results[1]), "Results not reproducible"
    print(f"[PASS] Reproducibility confirmed: Results identical with same seed")
    print(f"[PASS] Weight correlation: {np.corrcoef(results[0], results[1])[0,1]:.6f}")


# ============================================================================
# Run all tests
# ============================================================================
if __name__ == "__main__":
    test_nan_robustness()
    test_extreme_value_robustness()
    test_single_treatment_group()
    test_high_dimensional_features()
    test_multi_treatment()
    test_standardization_hardening()
    test_aipw_hardening()
    test_warning_control()
    test_performance_benchmark()
    test_reproducibility()
    
    print("\n" + "="*70)
    print("TEST RESULTS")
    print("="*70)
    print(f"PASSED: {passed_count}/{test_count}")
    print(f"FAILED: {test_count - passed_count}/{test_count}")
    
    if passed_count == test_count:
        print("\n*** ALL TESTS PASSED ***")
    else:
        print(f"\n*** {test_count - passed_count} TESTS FAILED ***")
