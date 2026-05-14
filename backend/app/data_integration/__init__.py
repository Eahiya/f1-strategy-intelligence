"""
F1 Strategy Platform v5.0 - Real Data Integration
Provides access to real F1 race data through FastF1 and historical datasets.
"""
from .fastf1_client import FastF1Client, RealDataProvider

__all__ = [
    'FastF1Client',
    'RealDataProvider'
]
