"""
Datasets Module

Provides real-world and simulated datasets for causal inference:
- load_nhefs: National Health and Nutrition Examination Survey
- load_nhefs_survival: NHEFS with survival outcomes
- load_acic16: ACIC 2016 benchmark dataset
- CausalSimulator: Generate synthetic causal graphs and data

Use these datasets to demonstrate, test, and benchmark estimators.
"""
from .data_loader import load_nhefs, load_nhefs_survival, load_acic16
from ..simulation.CausalSimulator3 import CausalSimulator3 as CausalSimulator, generate_random_topology
