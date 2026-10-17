"""Which loop is being built: the card's 72-frame loop (default) or the site's hover burst (NESTBOLT_VARIANT=burst),
where the head races the same nest at about twice the speed in a 48-frame loop with a heavier spark shower and
bigger smoke."""

import os

NAME = os.environ.get("NESTBOLT_VARIANT", "loop")
BURST = NAME == "burst"
SUFFIX = "-burst" if BURST else ""
