"""
Shared figure style: palettes, boxed axes, side legends, 300 dpi.
=============================================================================

    from plot_style import EC, PC, boxed, side_legend, DPI

EC / PC       estimator and policy palettes
boxed(ax)     four spines, inward ticks, dotted grid behind the data
side_legend() boxed legend outside the axes, on the right

Changing a colour here changes it everywhere.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

# ----------------------------------------------------------------- palettes
# Estimators: light blue, navy, brick red, gold (plus a brown for MultiHarm
# when it is enabled).
EC = {
    "Hold":      "#4a7fb5",
    "Linear":    "#1f3d7a",
    "OscKalman": "#c8442a",
    "MultiHarm": "#8c564b",
    "GapAdapt":  "#f0b323",
}

# Policies: the same family, so the two figure types sit together on a page.
PC = {
    "Periodic": "#4a7fb5",
    "Adaptive": "#1f3d7a",
    "Lyapunov": "#c8442a",
}

# aliases, so existing scripts keep working after a one-line import change
COLORS = EC
PCOLORS = PC

POLICY_ORDER = ["Periodic", "Adaptive", "Lyapunov"]
METHOD_ORDER = ["Hold", "Linear", "OscKalman", "MultiHarm", "GapAdapt"]

DPI = 300                      # print quality
GRID_COLOR = "#b0b0b0"


def use_paper_style(base_font: float = 9.5) -> None:
    """Global rcParams: inward ticks, thin black spines."""
    plt.rcParams.update({
        "font.size": base_font,
        "font.family": "DejaVu Sans",
        "axes.linewidth": 0.8,
        "axes.edgecolor": "black",
        "axes.titlesize": base_font + 1,
        "axes.labelsize": base_font,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "xtick.major.size": 3,
        "ytick.major.size": 3,
        "legend.fontsize": base_font - 1,
        "savefig.dpi": DPI,
        "figure.dpi": 110,
    })


def boxed(ax, grid_axis: str = "y") -> None:
    """Four spines, inward ticks, faint dotted grid behind the data."""
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_linewidth(0.8)
    ax.grid(True, axis=grid_axis, ls=":", lw=0.7, color=GRID_COLOR, alpha=0.9)
    ax.set_axisbelow(True)
    ax.tick_params(direction="in", top=True, right=True)


def side_legend(ax, handles=None, labels=None, title=None, ncol: int = 1,
                **kw_override):
    """Boxed legend outside the axes, on the right.

    Extra kwargs pass through to Matplotlib; `loc` and `bbox_to_anchor` are
    ignored, since placing the legend outside is the point of this helper.
    """
    kw = dict(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=True,
              fancybox=False, edgecolor="black", framealpha=1.0,
              borderpad=0.6, labelspacing=0.7, handlelength=1.4,
              ncol=ncol)
    for drop in ("loc", "bbox_to_anchor"):
        kw_override.pop(drop, None)
    if "title" in kw_override:
        title = kw_override.pop("title")
    kw.update(kw_override)

    if handles is not None:
        if labels is None:
            labels = [h.get_label() for h in handles]
        leg = ax.legend(handles, labels, title=title, **kw)
    else:
        leg = ax.legend(title=title, **kw)
    leg.get_frame().set_linewidth(0.8)
    if title:
        leg.get_title().set_fontweight("bold")
    return leg


def finish(fig, path, tight: bool = True):
    """Save at print resolution with the legend included in the bounding box."""
    if tight:
        fig.tight_layout()
    fig.savefig(path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)


# applied on import, so a script only needs the import to pick up the style
use_paper_style()
