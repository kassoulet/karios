# -*- coding: utf-8 -*-
# Copyright (c) 2025 Telespazio France.
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
"""Global rotation+translation preprocessing via rotated-template matching.

Pipeline:
    1. Pad the reference image by MAX_SHIFT_PX on every side. cv2.matchTemplate
       needs the template to be strictly smaller than the reference, so padding
       buys us the search range for translation.
    2. Sweep candidate rotations in [-15°, +15°] in 1° steps. For each angle,
       rotate the WHOLE monitored image about its center and run
       cv2.matchTemplate(TM_CCOEFF_NORMED) against the padded reference.
    3. The angle with the highest NCC peak determines rotation; the peak
       location minus (MAX_SHIFT_PX, MAX_SHIFT_PX) gives the translation
       (range: ±MAX_SHIFT_PX pixels).
    4. Apply that rotation+translation to the monitored image (and mask) via
       cv2.warpAffine, then crop monitored, reference, and mask to the bounding
       box of their overlap.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from osgeo import gdal

from karios.core.image import GdalRasterImage

logger = logging.getLogger(__name__)

ROTATION_RANGE_DEG = 15
ROTATION_STEP_DEG = 1
MAX_SHIFT_PX = 128  # half-width of the translation search around (0, 0)


_NUMPY_TO_GDAL_DTYPE = {
    np.dtype("uint8"): gdal.GDT_Byte,
    np.dtype("int16"): gdal.GDT_Int16,
    np.dtype("uint16"): gdal.GDT_UInt16,
    np.dtype("int32"): gdal.GDT_Int32,
    np.dtype("uint32"): gdal.GDT_UInt32,
    np.dtype("float32"): gdal.GDT_Float32,
    np.dtype("float64"): gdal.GDT_Float64,
}


@dataclass
class GlobalAlignment:
    """Outcome of detect_global_alignment()."""

    rotation_deg: float
    dx: int
    dy: int
    score: float


def _to_uint8(arr: np.ndarray) -> np.ndarray:
    if arr.dtype == np.uint8:
        return arr
    a = arr.astype(np.float32)
    finite = np.isfinite(a)
    if not finite.any():
        return np.zeros(arr.shape, dtype=np.uint8)
    lo = float(a[finite].min())
    hi = float(a[finite].max())
    if hi > lo:
        a = np.clip(((a - lo) / (hi - lo)) * 255.0, 0, 255)
    else:
        a = np.zeros_like(a)
    return a.astype(np.uint8)


def detect_global_alignment(
    mon_arr: np.ndarray, ref_arr: np.ndarray
) -> GlobalAlignment:
    """Sweep rotation angles, find the best (angle, dx, dy) via template matching.

    The whole monitored image is used as the template against a zero-padded
    reference (padding = MAX_SHIFT_PX on each side), so the translation search
    range is ±MAX_SHIFT_PX pixels.
    """
    mon = _to_uint8(mon_arr)
    ref = _to_uint8(ref_arr)

    mh, mw = mon.shape

    ref_padded = cv2.copyMakeBorder(
        ref,
        MAX_SHIFT_PX,
        MAX_SHIFT_PX,
        MAX_SHIFT_PX,
        MAX_SHIFT_PX,
        cv2.BORDER_CONSTANT,
        value=0,
    )

    angles = np.arange(
        -ROTATION_RANGE_DEG,
        ROTATION_RANGE_DEG + 1e-6,
        ROTATION_STEP_DEG,
    )

    best_angle = 0.0
    best_dx = 0
    best_dy = 0
    best_score = -np.inf

    for angle in angles:
        rot_m = cv2.getRotationMatrix2D((mw / 2.0, mh / 2.0), float(angle), 1.0)
        rotated = cv2.warpAffine(mon, rot_m, (mw, mh), borderValue=0)
        result = cv2.matchTemplate(ref_padded, rotated, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val > best_score:
            best_score = float(max_val)
            best_angle = float(angle)
            # max_loc is in padded-ref coords; (MAX_SHIFT_PX, MAX_SHIFT_PX)
            # corresponds to zero translation.
            best_dx = int(max_loc[0] - MAX_SHIFT_PX)
            best_dy = int(max_loc[1] - MAX_SHIFT_PX)

    logger.info(
        "Global alignment: rotation=%.1f° dx=%d dy=%d (NCC=%.3f)",
        best_angle,
        best_dx,
        best_dy,
        best_score,
    )
    return GlobalAlignment(best_angle, best_dx, best_dy, best_score)


def _gdal_dtype_for(np_dtype: np.dtype) -> int:
    return _NUMPY_TO_GDAL_DTYPE.get(np.dtype(np_dtype), gdal.GDT_Float32)


def _write_geotiff(
    path: Path,
    data: np.ndarray,
    x_min: float,
    y_max: float,
    x_res: float,
    y_res: float,
    projection: str,
    nodata: Optional[float],
    gdal_dtype: Optional[int] = None,
) -> None:
    driver = gdal.GetDriverByName("GTiff")
    h, w = data.shape
    dtype = gdal_dtype if gdal_dtype is not None else _gdal_dtype_for(data.dtype)
    dataset = driver.Create(str(path), w, h, 1, dtype, options=["COMPRESS=LZW"])
    if projection:
        dataset.SetProjection(projection)
    dataset.SetGeoTransform((x_min, x_res, 0, y_max, 0, y_res))
    band = dataset.GetRasterBand(1)
    band.WriteArray(data)
    if nodata is not None:
        band.SetNoDataValue(nodata)
    dataset.FlushCache()
    band = None
    dataset = None


def apply_global_alignment(
    monitored: GdalRasterImage,
    reference: GdalRasterImage,
    mask: Optional[GdalRasterImage],
    out_dir: Path,
) -> tuple[
    GdalRasterImage,
    GdalRasterImage,
    Optional[GdalRasterImage],
    GlobalAlignment,
]:
    """Detect rotation+translation, apply to monitored (and mask), crop all to overlap.

    Returns (aligned_mon, cropped_ref, aligned_mask, alignment_info). The new
    rasters are written to `out_dir` with updated geotransforms so the rest of
    the pipeline can operate on them as if they were the originals.
    """
    mon_arr = monitored.array
    ref_arr = reference.array

    if mon_arr.shape != ref_arr.shape:
        raise RuntimeError(
            f"Global alignment requires equal-sized inputs; got "
            f"mon={mon_arr.shape} ref={ref_arr.shape}"
        )

    alignment = detect_global_alignment(mon_arr, ref_arr)

    h, w = mon_arr.shape
    warp_m = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), alignment.rotation_deg, 1.0)
    warp_m[0, 2] += alignment.dx
    warp_m[1, 2] += alignment.dy

    # Float warp for monitored so interpolation is well-defined; cast back to
    # the source dtype on write. Border filled with no-data when declared.
    border_mon = (
        float(monitored.no_data_value)
        if monitored.no_data_value is not None
        else 0.0
    )
    aligned_mon = cv2.warpAffine(
        mon_arr.astype(np.float32),
        warp_m,
        (w, h),
        flags=cv2.INTER_LINEAR,
        borderValue=border_mon,
    )

    # Determine which pixels survived the warp (i.e., are not border fill).
    if monitored.no_data_value is not None:
        mon_valid = aligned_mon != monitored.no_data_value
    else:
        ones = np.ones_like(mon_arr, dtype=np.uint8)
        mon_valid = cv2.warpAffine(ones, warp_m, (w, h), borderValue=0) > 0

    if reference.no_data_value is not None:
        ref_valid = ref_arr != reference.no_data_value
    else:
        ref_valid = np.ones_like(ref_arr, dtype=bool)

    overlap = mon_valid & ref_valid
    if not overlap.any():
        raise RuntimeError("Global alignment found no overlap region; aborting")

    row_idx = np.where(np.any(overlap, axis=1))[0]
    col_idx = np.where(np.any(overlap, axis=0))[0]
    y_start, y_end = int(row_idx[0]), int(row_idx[-1]) + 1
    x_start, x_end = int(col_idx[0]), int(col_idx[-1]) + 1

    logger.info(
        "Cropping to overlap: rows %d..%d cols %d..%d (was %dx%d -> %dx%d)",
        y_start,
        y_end,
        x_start,
        x_end,
        h,
        w,
        y_end - y_start,
        x_end - x_start,
    )

    aligned_mon_cropped = aligned_mon[y_start:y_end, x_start:x_end].astype(mon_arr.dtype)
    ref_cropped = ref_arr[y_start:y_end, x_start:x_end]

    new_x_min = reference.x_min + x_start * reference.x_res
    new_y_max = reference.y_max + y_start * reference.y_res

    mon_stem = Path(monitored.file_name).stem
    mon_suffix = Path(monitored.file_name).suffix or ".tif"
    ref_stem = Path(reference.file_name).stem
    ref_suffix = Path(reference.file_name).suffix or ".tif"
    mon_out = out_dir / f"{mon_stem}_global_aligned{mon_suffix}"
    ref_out = out_dir / f"{ref_stem}_global_cropped{ref_suffix}"

    _write_geotiff(
        mon_out,
        aligned_mon_cropped,
        new_x_min,
        new_y_max,
        reference.x_res,
        reference.y_res,
        reference.projection,
        monitored.no_data_value,
    )
    _write_geotiff(
        ref_out,
        ref_cropped,
        new_x_min,
        new_y_max,
        reference.x_res,
        reference.y_res,
        reference.projection,
        reference.no_data_value,
    )

    aligned_mask = None
    if mask is not None:
        warped_mask = cv2.warpAffine(
            mask.array.astype(np.uint8),
            warp_m,
            (w, h),
            flags=cv2.INTER_NEAREST,
            borderValue=0,
        )
        cropped_mask = warped_mask[y_start:y_end, x_start:x_end]
        mask_stem = Path(mask.file_name).stem
        mask_suffix = Path(mask.file_name).suffix or ".tif"
        mask_out = out_dir / f"{mask_stem}_global_cropped{mask_suffix}"
        _write_geotiff(
            mask_out,
            cropped_mask,
            new_x_min,
            new_y_max,
            reference.x_res,
            reference.y_res,
            reference.projection,
            None,
            gdal_dtype=gdal.GDT_Byte,
        )
        aligned_mask = GdalRasterImage(str(mask_out))

    return (
        GdalRasterImage(str(mon_out)),
        GdalRasterImage(str(ref_out)),
        aligned_mask,
        alignment,
    )
