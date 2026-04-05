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
    alpha: complex,
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

    # alpha may be complex for spatio-temporal (Briggs-Bers) analysis
    alpha = complex(alpha)
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


def _track_omega(
    Ufun,
    alpha: complex,
    N: int,
    ymin: float,
    ymax: float,
    omega_ref: complex | None = None,
    evec_ref: "np.ndarray | None" = None,
) -> "tuple[complex, np.ndarray]":
    """Return (omega, eigenvector) for the tracked mode at the given alpha.

    Tracking priority:
    1. If ``evec_ref`` is provided: select by maximum eigenvector overlap
       (most robust across large alpha steps).
    2. Else if ``omega_ref`` is provided: select by proximity in the complex
       omega-plane (good for small alpha steps).
    3. Else: return the most unstable mode (largest Im(omega)).
    """
    _, _, omega, evecs = rayleigh_temporal(
        Ufun, alpha, N=N, ymin=ymin, ymax=ymax, return_evecs=True
    )
    interior = np.arange(1, N)   # interior grid indices (matches Aii/Bii)
    evecs_int = evecs[interior, :]   # strip boundary rows (=0 by construction)

    if evec_ref is not None:
        ref_int = evec_ref[interior]
        # normalise to unit length for safe overlap computation
        norms = np.linalg.norm(evecs_int, axis=0)
        ref_norm = np.linalg.norm(ref_int)
        if ref_norm > 0 and np.any(norms > 0):
            overlaps = np.abs(evecs_int.conj().T @ ref_int) / (norms * ref_norm + 1e-300)
            idx = int(np.argmax(overlaps))
        else:
            idx = 0
    elif omega_ref is not None:
        idx = int(np.argmin(np.abs(omega - omega_ref)))
    else:
        idx = 0  # most unstable (already sorted)

    return complex(omega[idx]), evecs[:, idx]


def rayleigh_absolute(
    Ufun,
    alpha0: complex,
    N: int = 200,
    ymin: float = -20.0,
    ymax: float = 20.0,
    max_iter: int = 50,
    tol: float = 1e-8,
    dalpha: float = 1e-4,
):
    """Find the absolute-instability saddle point via Newton iteration in the
    complex alpha-plane (Briggs-Bers criterion).

    Seeks alpha_s such that  d(omega)/d(alpha) = 0.

    Parameters
    ----------
    Ufun : callable
        Base flow U(y).
    alpha0 : complex
        Initial guess for the saddle-point wavenumber.  A reasonable choice is
        the real alpha of the most-unstable temporal mode.
    N, ymin, ymax : int, float, float
        Chebyshev resolution and domain (passed to rayleigh_temporal).
    max_iter : int
        Maximum Newton iterations.
    tol : float
        Convergence tolerance on |d(omega)/d(alpha)|.
    dalpha : float
        Step size for centred finite differences in alpha.

    Returns
    -------
    alpha_s : complex
        Saddle-point wavenumber.
    omega_s : complex
        Corresponding complex frequency.
    converged : bool
        True if |d(omega)/d(alpha)| < tol on exit.
    n_iter : int
        Number of iterations taken.

    Notes
    -----
    Absolute instability is indicated when Im(omega_s) > 0 **and** the
    pinch-point condition is satisfied (two spatial branches from opposite
    Im(alpha) half-planes collide as Im(alpha) is reduced from large positive
    values).  This function finds the saddle point; pinch-point verification
    must be done separately.
    """
    alpha = complex(alpha0)

    # Seed from the most unstable mode at alpha0; get eigenvector for tracking
    omega_ref, evec_ref = _track_omega(Ufun, alpha, N, ymin, ymax)

    # Maximum allowed step magnitude in alpha per iteration (prevents runaway)
    max_step = 0.5

    converged = False
    for n_iter in range(1, max_iter + 1):
        # Evaluate omega at three nearby alpha values using eigenvector tracking
        o_p, _ = _track_omega(Ufun, alpha + dalpha, N, ymin, ymax, evec_ref=evec_ref)
        o_m, _ = _track_omega(Ufun, alpha - dalpha, N, ymin, ymax, evec_ref=evec_ref)
        o_c, evec_c = _track_omega(Ufun, alpha,            N, ymin, ymax, evec_ref=evec_ref)

        domega_dalpha    = (o_p - o_m) / (2.0 * dalpha)
        d2omega_dalpha2  = (o_p - 2.0 * o_c + o_m) / dalpha ** 2

        if abs(domega_dalpha) < tol:
            converged = True
            alpha_s = alpha
            omega_s = o_c
            break

        if abs(d2omega_dalpha2) < 1e-15:
            # degenerate curvature — can't take Newton step
            break

        step = domega_dalpha / d2omega_dalpha2
        # Damping: limit step magnitude to prevent runaway
        if abs(step) > max_step:
            step = step / abs(step) * max_step

        alpha = alpha - step
        omega_ref = o_c
        evec_ref = evec_c   # advance eigenvector reference

    else:
        alpha_s = alpha
        omega_s, _ = _track_omega(Ufun, alpha, N, ymin, ymax, evec_ref=evec_ref)

    return alpha_s, omega_s, converged, n_iter


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

    # --- Briggs-Bers saddle point ---
    print("\nSearching for absolute-instability saddle point ...")
    alpha0 = complex(alpha)  # start search from real axis

    alpha_s, omega_s, conv, n_it = rayleigh_absolute(
        Ufun, alpha0, N=220, ymin=-20, ymax=20, max_iter=60, tol=1e-8
    )
    print(f"  Converged: {conv}  (iterations: {n_it})")
    print(f"  alpha_s = {alpha_s.real:.6f} + {alpha_s.imag:.6f}j")
    print(f"  omega_s = {omega_s.real:.6f} + {omega_s.imag:.6f}j")
    if conv:
        verdict = "ABSOLUTELY UNSTABLE" if omega_s.imag > 0 else "convectively unstable / stable"
        print(f"  Im(omega_s) = {omega_s.imag:.4e}  =>  {verdict}")
        print("  (pinch-point verification still needed)")
    else:
        print("  WARNING: Newton did not converge — try a different alpha0 or finer N")


if __name__ == "__main__":
    _main()
