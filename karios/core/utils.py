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
import os
import re


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename by removing or replacing dangerous characters.

    Args:
        filename (str): The filename to sanitize.

    Returns:
        str: The sanitized filename.
    """
    if not filename:
        return "unnamed"

    # 1. Handle both types of separators to be platform-independent
    filename = filename.replace("\\", "/")

    # 2. Get the basename
    filename = os.path.basename(filename)

    # 3. Replace non-alphanumeric (except ._-) with underscore
    # This also removes potential path separators like / or \ on different OS
    filename = re.sub(r"[^\w\.\-]", "_", filename)

    # 4. Prevent traversal or empty names after sanitization
    if filename in ("..", ".", ""):
        return "unnamed"

    # 5. Handle Windows reserved names
    reserved_names = {
        "CON",
        "PRN",
        "AUX",
        "NUL",
        "COM1",
        "COM2",
        "COM3",
        "COM4",
        "COM5",
        "COM6",
        "COM7",
        "COM8",
        "COM9",
        "LPT1",
        "LPT2",
        "LPT3",
        "LPT4",
        "LPT5",
        "LPT6",
        "LPT7",
        "LPT8",
        "LPT9",
    }
    if filename.upper() in reserved_names:
        return f"_{filename}"

    return filename


def get_filename(path: str) -> str:
    """Extract path filename without extension

    Args:
        path (str): path to process

    Returns:
        str: filename without extension
    """
    return os.path.splitext(sanitize_filename(path))[0]
