# nekRS stability notes (SquaElli)

## Working stability adjustments (from Y20)
The following `cyl.par` settings stabilized runs that previously blew up:
```
dt = targetCFL=1.2 + max=2e-3 + initial = 1e-3
regularization = hpfrt + nModes=1 + scalingCoeff=10
```

## When to apply
- Cases that blow up early
- Cases with extreme drag/lift spikes in `Hydro.dog`

## Apply pattern
1. Update the `dt` line in `cyl.par`.
2. Set the `regularization` line to `hpfrt` with `nModes=1` and `scalingCoeff=10`.
3. Resubmit the case on CCV.

## Notes
- Keep the rest of `cyl.par` unchanged unless explicitly testing stability controls.
- Keep backups of `cyl.par` before edits when comparing results.
