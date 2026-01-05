
"""
Safe Chart Wrapper
Provides safe matplotlib chart creation with proper error handling
"""

import matplotlib.pyplot as plt
import warnings

def safe_chart_create(chart_function):
    """Decorator for safe chart creation"""
    def wrapper(*args, **kwargs):
        try:
            # Suppress matplotlib warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")
                return chart_function(*args, **kwargs)
        except Exception as e:
            print(f"Chart creation error: {e}")
            return None
    return wrapper

def safe_tight_layout(fig):
    """Safely apply tight_layout"""
    try:
        fig.tight_layout()
    except:
        try:
            fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
        except:
            pass

def create_safe_figure(figsize=(8, 6), **kwargs):
    """Create figure with safe defaults"""
    fig, ax = plt.subplots(figsize=figsize, **kwargs)
    fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)
    return fig, ax

def create_safe_subplots(nrows, ncols, figsize=(10, 8), **kwargs):
    """Create subplots with safe spacing"""
    fig, axes = plt.subplots(nrows, ncols, figsize=figsize, **kwargs)
    
    if nrows > 1 or ncols > 1:
        fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, 
                           hspace=0.4, wspace=0.3)
    else:
        fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)
    
    return fig, axes
