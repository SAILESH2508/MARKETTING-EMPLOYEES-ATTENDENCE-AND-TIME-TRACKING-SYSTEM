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
                warnings.filterwarnings(
                    "ignore", category=UserWarning, module="matplotlib"
                )
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
        fig.subplots_adjust(
            left=0.1, right=0.9, top=0.9, bottom=0.1, hspace=0.4, wspace=0.3
        )
    else:
        fig.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.15)

    return fig, axes


def enable_pie_hover(canvas, fig, ax, wedges, labels, values, is_currency=True):
    """Enable interactive hover tooltips and segment highlighting for Matplotlib pie charts."""
    import math

    annot = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(15, 15),
        textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.5", fc="#1F2A38", ec="#E94560", lw=1.5, alpha=0.95),
        arrowprops=dict(arrowstyle="->", color="#E94560", lw=1.5),
        color="white",
        fontweight="bold",
        fontsize=10,
        zorder=100,
    )
    annot.set_visible(False)

    def update_annot(wedge, label, value):
        theta = (wedge.theta1 + wedge.theta2) / 2.0
        # Position tooltip roughly at the center of the wedge radius
        r = wedge.r * 0.5
        x = r * math.cos(math.radians(theta))
        y = r * math.sin(math.radians(theta))
        annot.xy = (x, y)
        val_str = f"₹{value:,.2f}" if is_currency else f"{value}"
        annot.set_text(f"{label}\n{val_str}")

    def hover(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            hovered = False
            for i, wedge in enumerate(wedges):
                cont, _ = wedge.contains(event)
                if cont:
                    wedge.set_alpha(1.0)
                    wedge.set_edgecolor("white")
                    wedge.set_linewidth(2.5)
                    update_annot(wedge, labels[i], values[i])
                    annot.set_visible(True)
                    hovered = True
                else:
                    wedge.set_alpha(0.5)
                    wedge.set_edgecolor("none")
                    wedge.set_linewidth(0)
            if hovered:
                canvas.draw_idle()
            else:
                if vis:
                    annot.set_visible(False)
                    for w in wedges:
                        w.set_alpha(0.9)
                        w.set_edgecolor("none")
                        w.set_linewidth(0)
                    canvas.draw_idle()
        else:
            if vis:
                annot.set_visible(False)
                for w in wedges:
                    w.set_alpha(0.9)
                    w.set_edgecolor("none")
                    w.set_linewidth(0)
                canvas.draw_idle()

    canvas.mpl_connect("motion_notify_event", hover)


def enable_bar_hover(canvas, fig, ax, bars, labels, values, is_horizontal=False, is_currency=False):
    """Enable interactive hover tooltips and bar highlighting for vertical/horizontal Matplotlib bar charts."""
    annot = ax.annotate(
        "",
        xy=(0, 0),
        xytext=(15, 15),
        textcoords="offset points",
        bbox=dict(boxstyle="round,pad=0.5", fc="#1F2A38", ec="#E94560", lw=1.5, alpha=0.95),
        arrowprops=dict(arrowstyle="->", color="#E94560", lw=1.5),
        color="white",
        fontweight="bold",
        fontsize=10,
        zorder=100,
    )
    annot.set_visible(False)

    def update_annot(bar, label, value):
        if is_horizontal:
            # Horizontal bar: coordinate is at the end edge
            x = bar.get_width()
            y = bar.get_y() + bar.get_height() / 2.0
        else:
            # Vertical bar: coordinate is at the top edge
            x = bar.get_x() + bar.get_width() / 2.0
            y = bar.get_height()

        annot.xy = (x, y)
        val_str = f"₹{value:,.2f}" if is_currency else f"{value}"
        annot.set_text(f"{label}\n{val_str}")

    def hover(event):
        vis = annot.get_visible()
        if event.inaxes == ax:
            hovered = False
            for i, bar in enumerate(bars):
                cont, _ = bar.contains(event)
                if cont:
                    bar.set_alpha(1.0)
                    bar.set_edgecolor("white")
                    bar.set_linewidth(2.5)
                    update_annot(bar, labels[i], values[i])
                    annot.set_visible(True)
                    hovered = True
                else:
                    bar.set_alpha(0.5)
                    bar.set_edgecolor("none")
                    bar.set_linewidth(0)
            if hovered:
                canvas.draw_idle()
            else:
                if vis:
                    annot.set_visible(False)
                    for b in bars:
                        b.set_alpha(0.9)
                        b.set_edgecolor("none")
                        b.set_linewidth(0)
                    canvas.draw_idle()
        else:
            if vis:
                annot.set_visible(False)
                for b in bars:
                    b.set_alpha(0.9)
                    b.set_edgecolor("none")
                    b.set_linewidth(0)
                canvas.draw_idle()

    canvas.mpl_connect("motion_notify_event", hover)

