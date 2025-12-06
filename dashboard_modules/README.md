# Employee Dashboard Modules

The employee dashboard has been split into modular files for better organization and maintainability.

## File Structure

```
dashboard_modules/
├── __init__.py                 # Package initialization
├── ui_helpers.py              # 171 lines - UI components and helpers
├── ml_functions.py            # 261 lines - Machine learning models
├── chart_functions.py         # 293 lines - Chart and visualization functions
├── summary_functions.py       # 734 lines - Dashboard summary and cards
├── analytics_functions.py     # 278 lines - Performance analytics
├── main_dashboard.py          # 178 lines - Main dashboard window
├── action_functions.py        # 112 lines - Sign-in/out actions
└── app_setup.py               # 101 lines - Database setup and app start
```

## Module Breakdown

### 1. `ui_helpers.py` (171 lines)
**Purpose**: UI components and utility functions

**Contains**:
- `ToolTip` class - Tooltip widget for hover information
- `CustomButton` class - Styled button component
- `rounded_card()` - Create rounded card UI elements
- `create_scrollable_frame()` - Scrollable frame with mousewheel support
- `clear_content()` - Clear frame contents
- `fade_in()` - Fade-in animation effect
- `update_theme()` - Recursively update theme colors
- `append_status()` - Append status messages to text widget
- `get_db_data_safely()` - Thread-safe database access

### 2. `ml_functions.py` (261 lines)
**Purpose**: Machine learning models and predictions

**Contains**:
- `load_attendance_df()` - Load attendance data as DataFrame
- `get_ml_status()` - Get ML models status
- `train_punctuality_model()` - Train punctuality predictor
- `predict_punctuality_for_emp()` - Predict employee punctuality
- `train_anomaly_detector()` - Train anomaly detection model
- `run_anomaly_scan()` - Run anomaly detection scan
- `train_salary_predictor()` - Train salary prediction model
- `predict_salary()` - Predict employee salary
- `get_predicted_salary_value()` - Get salary prediction value
- `get_punctuality_probability()` - Get punctuality probability
- `compute_perfection_score()` - Calculate perfection score

### 3. `chart_functions.py` (293 lines)
**Purpose**: Chart and visualization displays

**Contains**:
- `show_heatmap()` - Display attendance heatmap
- `show_leaderboard()` - Display punctuality leaderboard
- `show_salary_pie()` - Display salary breakdown pie chart
- `show_attendance_bar()` - Display on-time vs late bar chart
- `show_face_log()` - Display face login history

### 4. `summary_functions.py` (734 lines)
**Purpose**: Dashboard summary cards and displays

**Contains**:
- `refresh_summary()` - Refresh summary display
- `show_default_summary()` - Main dashboard summary view
- Helper functions for building summary cards
- Productivity score calculations
- Quick stats displays
- ML insights cards

### 5. `analytics_functions.py` (278 lines)
**Purpose**: Performance analytics and trends

**Contains**:
- `show_performance_trends()` - Performance trends over time
- `show_work_patterns()` - Work pattern analysis
- `show_productivity_score()` - Comprehensive productivity score
- `auto_train_ml_models()` - Auto-train ML models on startup

### 6. `main_dashboard.py` (178 lines)
**Purpose**: Main dashboard window and layout

**Contains**:
- `employee_dashboard()` - Main dashboard window creation
- Tab creation and organization
- Navigation setup
- Theme toggle functionality

### 7. `action_functions.py` (112 lines)
**Purpose**: User actions and operations

**Contains**:
- `sign_in()` - Employee sign-in function
- `sign_out()` - Employee sign-out function
- `auto_reminder()` - Automatic reminder system
- `export_attendance_csv()` - Export attendance data

### 8. `app_setup.py` (101 lines)
**Purpose**: Application initialization

**Contains**:
- `setup_database_and_start_app()` - Database setup and app start
- Employee selection dialog
- First user creation flow

## Benefits of Modular Structure

### ✅ Better Organization
- Each file has a clear, single responsibility
- Easy to find specific functionality
- Logical grouping of related functions

### ✅ Improved Maintainability
- Smaller files are easier to read and understand
- Changes are isolated to specific modules
- Reduced risk of breaking unrelated functionality

### ✅ Enhanced Collaboration
- Multiple developers can work on different modules simultaneously
- Clear module boundaries reduce merge conflicts
- Easier code reviews with focused changes

### ✅ Easier Testing
- Individual modules can be tested independently
- Mock dependencies more easily
- Better test coverage

### ✅ Reusability
- Modules can be imported independently
- Functions can be reused in other projects
- Clear API boundaries

## Usage

### Running the Application
```python
python employee_dashboard.py
```

### Importing Specific Modules
```python
# Import specific functions
from dashboard_modules.ml_functions import train_punctuality_model
from dashboard_modules.chart_functions import show_heatmap

# Import entire module
import dashboard_modules.ui_helpers as ui
```

### Adding New Features
1. Identify the appropriate module for your feature
2. Add your function to that module
3. Ensure all dependencies are imported
4. Test the module independently
5. Update this README with your changes

## Dependencies

All modules share common dependencies:
- `tkinter` - GUI framework
- `matplotlib` - Charting and visualization
- `sqlite3` - Database access
- `pandas` - Data manipulation (optional, for ML)
- `sklearn` - Machine learning (optional)

## Future Improvements

Potential enhancements:
- Add unit tests for each module
- Create configuration file for themes and constants
- Implement logging system
- Add error handling decorators
- Create API documentation
- Add type hints for better IDE support
