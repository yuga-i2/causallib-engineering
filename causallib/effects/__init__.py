"""
Effects module initialization - public API.

(C) Copyright 2019 IBM Corp.
Licensed under the Apache License, Version 2.0
"""

from .calculation import (
    EffectType,
    calculate_effect,
    is_scalar_outcome,
)

__all__ = [
    "EffectType",
    "calculate_effect",
    "is_scalar_outcome",
]
