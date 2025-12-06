"""
Employee Dashboard - Main Entry Point
This file imports from modular components for better organization
"""

import warnings
warnings.filterwarnings("ignore", category=FutureWarning, module="sklearn")

# Import in correct order to avoid circular dependencies
# 1. First import UI helpers (no dependencies)
from dashboard_modules.ui_helpers import *

# 2. Then ML functions (depends on ui_helpers)
from dashboard_modules.ml_functions import *

# 3. Then chart functions (depends on ui_helpers)
from dashboard_modules.chart_functions import *

# 4. Then summary functions (depends on ui_helpers and ml_functions)
from dashboard_modules.summary_functions import *

# 5. Then analytics functions (depends on ui_helpers and ml_functions)
from dashboard_modules.analytics_functions import *

# 6. Then action functions (depends on ui_helpers and summary_functions)
from dashboard_modules.action_functions import *

# 7. Then main dashboard (depends on all above)
from dashboard_modules.main_dashboard import *

# 8. Finally app setup (depends on main_dashboard)
from dashboard_modules.app_setup import *

# Main execution
if __name__ == "__main__":
    setup_database_and_start_app()
