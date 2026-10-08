"""Iterative proportional fitting (IPF): balance a table of flows so its rows and columns match known totals (M4).

Used for Tier C, the modeled allocation of trade between exporters and importers when bilateral flows are not
published. It starts from a prior (the best available pattern of who trades with whom) and repeatedly rescales
rows to match each exporter's total and columns to match each importer's total, until both match within a
tolerance. Cells that are zero in the prior stay zero.

The result is only as good as the prior. With no measured pattern, the prior is uniform and the method spreads
each exporter's oil across importers in proportion to their size, which can draw routes that do not exist.
For that reason Tier C arcs are not published until a defensible prior is available (README, docs/SOURCES.md).
"""

import numpy as np


def ipf(prior, row_totals, col_totals, tol=1e-6, max_iter=1000):
    """Return (table, iterations). Raises ValueError if the totals cannot be matched.

    prior: 2-D array of non-negative weights (exporters in rows, importers in columns).
    row_totals, col_totals: target sums; they must add to the same grand total (within tol, relative).
    """
    x = np.array(prior, dtype=float)
    r = np.array(row_totals, dtype=float)
    c = np.array(col_totals, dtype=float)
    if (x < 0).any() or (r < 0).any() or (c < 0).any():
        raise ValueError("prior and totals must be non-negative")
    if not np.isclose(r.sum(), c.sum(), rtol=tol * 10, atol=tol):
        raise ValueError(f"row totals ({r.sum():.4f}) and column totals ({c.sum():.4f}) must match")
    if ((x.sum(axis=1) == 0) & (r > 0)).any() or ((x.sum(axis=0) == 0) & (c > 0)).any():
        raise ValueError("a row or column has a positive total but an all-zero prior")
    for i in range(1, max_iter + 1):
        rs = x.sum(axis=1)
        x *= np.divide(r, rs, out=np.zeros_like(r), where=rs > 0)[:, None]
        cs = x.sum(axis=0)
        x *= np.divide(c, cs, out=np.zeros_like(c), where=cs > 0)[None, :]
        if np.allclose(x.sum(axis=1), r, rtol=tol, atol=tol) and np.allclose(x.sum(axis=0), c, rtol=tol, atol=tol):
            return x, i
    raise ValueError(f"did not converge in {max_iter} iterations")
