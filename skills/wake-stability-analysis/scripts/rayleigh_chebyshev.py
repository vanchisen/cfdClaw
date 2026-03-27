#!/usr/bin/env python3
"""rayleigh_chebyshev.py

Temporal stability analysis for a parallel base flow U(y) using the inviscid
Orr–Sommerfeld (Rayleigh) equation and Chebyshev collocation.

Rayleigh equation (inviscid):
  (U - c) * (phi'' - alpha^2 phi) - U'' * phi = 0

Recast as generalized eigenvalue problem for phase speed c:
  (U * L - U'') phi = c * (L) phi
where L = D2 - alpha^2 I.

Boundary conditions used here (box truncation):
  phi(ymin) = 0, phi(ymax) = 0

Unstable temporal modes satisfy Im(omega) > 0 where omega = alpha * c.

Dependencies:
  numpy, scipy

Usage:
  python rayleigh_chebyshev.py

You can also import and call rayleigh_temporal(Ufun, alpha, ...).
"""

from __future__ import annotations

import numpy as np
from numpy import pi
from scipy.linalg import eig


def cheb(N: int):
    """Chebyshev differentiation matrix on [-1,1] with N+1 points.

    Returns
    -------
    x : (N+1,) array
        Chebyshev points in [-1,1]
    D : (N+1,N+1) array
        First-derivative matrix with respect to x

    Reference: Trefethen, Spectral Methods in MATLAB.
    """
    if N == 0:
        return np.array([1.0]), np.array([[0.0]])

    x = np.cos(pi * np.arange(N + 1) / N)
    c = np.ones(N + 1)
    c[0] = 2.0
    c[-1] = 2.0
    c = c * ((-1.0) ** np.arange(N + 1))

    X = np.tile(x, (N + 1, 1))
    dX = X - X.T

    D = (c[:, None] / c[None, :]) / (dX + np.eye(N + 1))
    D = D - np.diag(np.sum(D, axis=1))
    return x, D


def rayleigh_temporal(
    Ufun,
    alpha: float,
    N: int = 200,
    ymin: float = -20.0,
    ymax: float = 20.0,
    return_evecs: bool = False,
):
    """Solve the temporal Rayleigh stability problem for a given U(y) and real alpha.

    Parameters
    ----------
    Ufun : callable
        Base flow function U(y). Must accept a NumPy array.
    alpha : float
        Real streamwise wavenumber.
    N : int
        Number of Chebyshev intervals. Uses N+1 collocation points.
    ymin, ymax : float
        Truncation domain in y.
    return_evecs : bool
        If True, return eigenvectors as well.

    Returns
    -------
    y : (N+1,) array
        Physical y grid.
    c : (N+1,) complex array
        Phase speed eigenvalues.
    omega : (N+1,) complex array
        Temporal frequency eigenvalues (omega = alpha*c).
    eigvecs : (N+1,N+1) complex array, optional
        Eigenvectors corresponding to c.

    Notes
    -----
    - Unstable temporal modes satisfy Im(omega) > 0.
    - This is the inviscid (Rayleigh) limit; no viscosity term.
    - For wakes/mixing layers, a large enough |y| domain is needed.
    """

    # alpha may be complex for spatio-temporal analysis
    if alpha == 0:
        raise ValueError("alpha must be nonzero")
    if ymax <= ymin:
        raise ValueError("ymax must be > ymin")

    x, D = cheb(N)

    # map x in [-1,1] to y in [ymin,ymax]
    y = 0.5 * (ymax - ymin) * x + 0.5 * (ymax + ymin)

    # chain rule: d/dy = (2/(ymax-ymin)) d/dx
    scale = 2.0 / (ymax - ymin)
    Dy = scale * D
    D2y = Dy @ Dy

    U = np.asarray(Ufun(y), dtype=float)
    Upp = D2y @ U  # spectral second derivative

    I = np.eye(N + 1)
    L = D2y - (alpha ** 2) * I

    # generalized EVP: (U*L - U'') phi = c * (L) phi
    A = np.diag(U) @ L - np.diag(Upp)
    B = L.copy()

    # Dirichlet BCs: phi(ymin)=phi(ymax)=0.
    # Implement by eliminating the boundary unknowns (use interior points only).
    # This avoids introducing infinite eigenvalues from singular B rows.
    interior = np.arange(1, N)  # 1..N-1
    Aii = A[np.ix_(interior, interior)]
    Bii = B[np.ix_(interior, interior)]

    eigvals, eigvecs = eig(Aii, Bii)

    c = eigvals
    omega = alpha * c

    # filter non-finite eigenvalues (can arise from numerical issues)
    finite = np.isfinite(c.real) & np.isfinite(c.imag)
    c = c[finite]
    omega = omega[finite]
    eigvecs = eigvecs[:, finite]

    # sort by growth rate
    idx = np.argsort(np.imag(omega))[::-1]
    c = c[idx]
    omega = omega[idx]
    eigvecs = eigvecs[:, idx]

    if return_evecs:
        # Reconstruct full eigenvectors including boundary zeros
        full = np.zeros((N + 1, eigvecs.shape[1]), dtype=complex)
        full[1:N, :] = eigvecs
        return y, c, omega, full
    return y, c, omega


def example_wake_profile(U0: float = 1.0, deficit: float = 0.6, delta: float = 1.0):
    """Simple symmetric wake-like profile: U(y) = U0 - deficit * sech^2(y/delta)."""

    def U(y):
        return U0 - deficit * (1.0 / np.cosh(y / delta)) ** 2

    return U


def _main():
    Ufun = example_wake_profile(U0=1.0, deficit=0.7, delta=1.0)
    alpha = 0.7

    y, c, omega = rayleigh_temporal(Ufun, alpha, N=220, ymin=-20, ymax=20)

    print("Top 10 modes by imag(omega):")
    for j in range(10):
        print(
            f"{j:2d}: c = {c[j]: .6f}, omega = {omega[j]: .6f}, "
            f"growth Im(omega) = {omega[j].imag: .6e}"
        )


if __name__ == "__main__":
    _main()
