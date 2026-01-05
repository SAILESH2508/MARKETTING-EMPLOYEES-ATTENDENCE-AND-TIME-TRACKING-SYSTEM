
# Matplotlib Configuration
import matplotlib
import warnings

# Suppress specific matplotlib warnings
warnings.filterwarnings("ignore", message="This figure includes Axes that are not compatible with tight_layout")
warnings.filterwarnings("ignore", category=UserWarning, module="matplotlib")

# Set matplotlib backend and style
matplotlib.use('TkAgg')
matplotlib.rcParams.update({
    'figure.autolayout': False,
    'figure.constrained_layout.use': False,
    'axes.titlesize': 12,
    'axes.labelsize': 10,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'font.size': 10
})
