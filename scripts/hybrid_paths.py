"""library_js for callers that must not import numpy-heavy hybrid at module load."""
import sys

import common as C

sys.path.insert(0, str(C.MOTION / "tools"))


def library_js(scenes):
    import hybrid
    return hybrid.library_js(scenes)
