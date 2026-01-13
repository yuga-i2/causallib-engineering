#!/usr/bin/env python
"""
Test script for Phase 1 production hardening.
Tests that new modules work and backward compatibility is maintained.
"""

import sys
import traceback

def test_new_modules():
    """Test that new modules import and work correctly."""
    print("\n=== TESTING NEW MODULES ===")
    
    try:
        from causallib.validation import (
            check_X_a, check_X_a_y, check_is_fitted,
            CausallibValidationError, NotFittedError
        )
        print("✓ validation module imports")
    except Exception as e:
        print(f"✗ validation module failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        from causallib.effects import calculate_effect, EffectType
        print("✓ effects module imports")
    except Exception as e:
        print(f"✗ effects module failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        from causallib.propensity import (
            extract_propensity_scores, compute_propensity_weights
        )
        print("✓ propensity module imports")
    except Exception as e:
        print(f"✗ propensity module failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        from causallib.diagnostics import __all__
        print("✓ diagnostics module imports")
    except Exception as e:
        print(f"✗ diagnostics module failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def test_effect_calculation():
    """Test centralized effect calculation."""
    print("\n=== TESTING EFFECT CALCULATION ===")
    
    try:
        from causallib.effects import calculate_effect
        import pandas as pd
        
        # Population effect (scalars)
        y1 = 0.3
        y0 = 0.6
        eff = calculate_effect(y1, y0, 'diff')
        assert eff['diff'] == -0.3, f"Expected diff=-0.3, got {eff['diff']}"
        print(f"✓ Population effect: diff={eff['diff']}")
        
        # Individual effects (vectors)
        y1_vec = pd.Series([0.2, 0.4, 0.5])
        y0_vec = pd.Series([0.1, 0.2, 0.3])
        eff_vec = calculate_effect(y1_vec, y0_vec, ['diff', 'ratio'])
        assert eff_vec.shape == (3, 2), f"Expected shape (3,2), got {eff_vec.shape}"
        print(f"✓ Individual effects: shape={eff_vec.shape}")
        
        return True
    except Exception as e:
        print(f"✗ Effect calculation failed: {e}")
        traceback.print_exc()
        return False


def test_validation():
    """Test validation functions."""
    print("\n=== TESTING VALIDATION ===")
    
    try:
        from causallib.validation import check_X_a, check_X_a_y, DataAlignmentError
        import pandas as pd
        
        # Valid case
        X = pd.DataFrame({'feat1': [1, 2], 'feat2': [3, 4]})
        a = pd.Series([0, 1])
        X_valid, a_valid = check_X_a(X, a)
        print("✓ Valid X,a pass validation")
        
        # Invalid case: misaligned indices
        a_bad = pd.Series([0, 1], index=[5, 6])
        try:
            check_X_a(X, a_bad)
            print("✗ Should have raised DataAlignmentError")
            return False
        except DataAlignmentError:
            print("✓ Detects misaligned indices")
        
        return True
    except Exception as e:
        print(f"✗ Validation tests failed: {e}")
        traceback.print_exc()
        return False


def test_backward_compatibility():
    """Test that existing APIs still work."""
    print("\n=== TESTING BACKWARD COMPATIBILITY ===")
    
    try:
        from causallib.estimation import IPW
        print("✓ IPW import works")
    except Exception as e:
        print(f"✗ IPW import failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        from causallib.datasets import load_nhefs
        print("✓ load_nhefs import works")
    except Exception as e:
        print(f"✗ load_nhefs import failed: {e}")
        traceback.print_exc()
        return False
    
    try:
        import causallib
        print("✓ causallib package imports")
    except Exception as e:
        print(f"✗ causallib import failed: {e}")
        traceback.print_exc()
        return False
    
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("PHASE 1 PRODUCTION HARDENING - TEST SUITE")
    print("=" * 70)
    
    results = []
    
    results.append(("New Modules", test_new_modules()))
    results.append(("Effect Calculation", test_effect_calculation()))
    results.append(("Validation", test_validation()))
    results.append(("Backward Compatibility", test_backward_compatibility()))
    
    print("\n" + "=" * 70)
    print("TEST RESULTS")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    
    if all_passed:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        return 0
    else:
        print("\n✗✗✗ SOME TESTS FAILED ✗✗✗")
        return 1


if __name__ == "__main__":
    sys.exit(main())
