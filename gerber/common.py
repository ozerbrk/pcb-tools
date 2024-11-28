#! /usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from . import rs274x
from . import excellon
from . import ipc356
from .exceptions import ParseError
from .utils import detect_file_format
import chardet


# In gerber/common.py
def read(filename):
    with open(filename, 'rb') as f:
        data_bytes = f.read()

    # Detect encoding
    result = chardet.detect(data_bytes)
    encoding = result['encoding']
    confidence = result['confidence']
    print(f"Detected encoding '{encoding}' with confidence {confidence} for file '{filename}'")

    if encoding:
        data = data_bytes.decode(encoding)
    else:
        # Fallback to 'latin-1' if encoding cannot be detected
        data = data_bytes.decode('latin-1')

    return loads(data, filename)

def loads(data, filename=None):
    """ Read gerber or excellon file contents from a string and return a
    representative object.

    Parameters
    ----------
    data : string
        Source file contents as a string.

    filename : string, optional
        String containing the filename of the data source.

    Returns
    -------
    file : CncFile subclass
        CncFile object representing the data, either GerberFile, ExcellonFile,
        or IPCNetlist. Returns None if data is not of the proper type.
    """

    fmt = detect_file_format(data)
    if fmt == 'rs274x':
        print("File name: ", filename, "Detected file format: RS-274X")
        return rs274x.loads(data, filename=filename)
    elif fmt == 'excellon':
        print("File name: ", filename, "Detected file format: Excellon")
        return excellon.loads(data, filename=filename)
    elif fmt == 'ipc_d_356':
        print("File name: ", filename, "Detected file format: IPC-D-356")
        return ipc356.loads(data, filename=filename)
    else:
        raise ParseError('Unable to detect file format')
