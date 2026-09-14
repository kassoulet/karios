# -*- coding: utf-8 -*-
# Copyright (c) 2026 Telespazio France.
#
# This file is part of KARIOS.
# See https://github.com/telespazio-tim/karios for further info.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Radiometric stretch used to prepare rasters for the 8-bit only OpenCV calls.

OpenCV's corner detection and optical flow want 8-bit input, so every matcher
has to map its pixels onto 0-255 first. How that mapping is chosen matters more
than it looks: a stretch driven by the array's minimum and maximum is decided
entirely by its two most extreme pixels, so one outlier or one infinity squeezes
the whole scene into a handful of DN values and the Laplacian has nothing left
to find. Measured on a Landsat-8 / Sentinel-2 pair, a single stray pixel took
matching from 3983 key points to none.

Float rasters carry such pixels routinely, where integer sensor products
generally do not, which is why this reads as a "float problem" even though the
stretch is what is actually fragile. Taking the bounds from percentiles of the
finite pixels instead costs a little contrast and is indifferent to how extreme
the outliers are.
"""

import numpy as np
from numpy.typing import NDArray

# Stretch bounds: low and high percentile of the finite pixels.
DEFAULT_PERCENTILES = (2.0, 98.0)


def to_uint8(arr: NDArray, percentiles: tuple[float, float] = DEFAULT_PERCENTILES) -> NDArray:
    """Scale an array to uint8 from the percentiles of its finite pixels.

    Args:
        arr: pixel data, any dtype. Returned unchanged when already uint8.
        percentiles: (low, high) percentile pair bounding the stretch.

    Returns:
        NDArray: uint8 array of the same shape. All-zero when the array holds no
            finite pixel, or when the two percentiles coincide so there is no
            range to stretch.
    """
    if arr.dtype == np.uint8:
        return arr

    values = arr.astype(np.float32)
    finite = np.isfinite(values)
    if not finite.any():
        return np.zeros(arr.shape, np.uint8)

    # percentile, not nanpercentile: the subset is already free of NaN *and* of
    # the infinities nanpercentile would happily carry into the bounds.
    low, high = np.percentile(values[finite], percentiles)
    if high <= low:
        return np.zeros(arr.shape, np.uint8)

    return np.clip((values - low) / (high - low) * 255.0, 0, 255).astype(np.uint8)


def laplacian_to_uint8(
    response: NDArray, scale_percentile: float = 50.0, output_percentile: float = 98.0
) -> NDArray:
    """Rescale a signed Laplacian response to uint8 with a normalized asinh stretch.

    cv2.Laplacian's own CV_8U output clips every negative response to 0 and
    saturates large positive ones at 255 - measured on real imagery, that
    collapses 95%+ of pixels to the two extremes. A first attempt replaced
    that with a plain linear rescale, which fixed the sign and the saturation
    bug but matched worse across sensors than the original - what mattered
    for accuracy here is not a lower geometric RMSE but a uniform spread of
    key points over the whole scene, and a linear map gives low-contrast
    regions almost no separable signal for goodFeaturesToTrack to find
    corners in. A sigmoid (a second attempt) still saturates every response
    past its percentile bound to the same handful of output values, so it
    reproduces the same starvation, just less severely.

    An asinh stretch - the same tool used to display astronomical images
    where both faint structure and bright outliers must stay visible at once
    - keeps every distinct input mapped to a distinct output: it has no flat
    plateau anywhere, only ever-slower (logarithmic) growth for large
    responses. Weak texture in low-contrast regions stays separable instead
    of being crushed toward a single value, so those regions can still
    produce key points; genuine outliers are compressed gracefully rather
    than either dominating a linear scale or being lumped together at a hard
    saturation point.

    Two percentiles do two different jobs, both needed:

    - `scale_percentile` (the median by default) sets the asinh's "typical
      size" for this tile - a robust unit, not a threshold separating
      "normal" from "outlier": the same smooth function handles both.
    - `output_percentile` then normalizes asinh's *output* the same way
      `to_uint8` normalizes the raw image, so the stretch actually uses the
      available contrast on every tile. A fixed linear gain on the asinh
      output (an earlier version of this function) left that uncalibrated:
      how far the compressed response spreads across [0, 255] depended on
      the ratio between each tile's extreme values and its median, which
      varies tile to tile and sensor to sensor - some tiles came out
      washed out, others closer to saturated, an inconsistency that shows up
      as "the Laplacian doesn't look normalized" on a chip-by-chip
      inspection. Applying the percentile bound *after* asinh rather than
      directly on the raw response is what keeps this from reintroducing the
      original outlier-domination problem: the compression has already
      happened, so this percentile only calibrates contrast, not survival.

    Args:
        response: signed Laplacian response, any real dtype.
        scale_percentile: percentile of the response magnitude used to set
            the asinh's scale. Defaults to 50 (the median).
        output_percentile: percentile of the asinh output's magnitude used to
            normalize it to uint8. Defaults to 98.

    Returns:
        NDArray: uint8 array of the same shape, 128 where the response is
            exactly zero.
    """
    scale = np.percentile(np.abs(response), scale_percentile)
    if scale <= 0:
        return np.full(response.shape, 128, dtype=np.uint8)

    y = np.arcsinh(response.astype(np.float64) / scale)

    bound = np.percentile(np.abs(y), output_percentile)
    if bound <= 0:
        return np.full(response.shape, 128, dtype=np.uint8)

    # The only clip left is the unavoidable one: fitting into 8 bits. asinh's
    # own compression means it is reached only by truly extreme responses,
    # not the top few percent - `bound` calibrates contrast, it is not a
    # threshold that discards anything beyond it.
    return np.clip(np.round(y / bound * 127.0 + 128.0), 0, 255).astype(np.uint8)
