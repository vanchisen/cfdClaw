# WakeInstability status

Work in progress based on Triantafyllou et al. (1986) JFM.

## What is included
- Original paper PDF plus text/markdown/page-image extraction assets
- Existing Rayleigh temporal-analysis scripts
- Approximate and more paper-faithful figure 4–7 reproduction scripts

## Current state
- The DNS/profile-based temporal scan scripts are **not** equivalent to paper figs. 4–7.
- `reproduce_triantafyllou_fig4_7.py` is an approximate prototype and is **not** the final validation path.
- `reproduce_triantafyllou_fig4_7_exact.py` is the current best direction.
- Current exact-model baseline gives generally good overall figure families, but one remaining mismatch remains:
  - **line 1 appears opposite to the paper** in the best current version.

## Recommended next step
Do **not** change the global sign convention for all curves. Continue from the current reverted baseline and investigate only a **local branch/continuation choice for line 1**.
