# SPDX-FileCopyrightText: 2026 James R. Barlow
# SPDX-License-Identifier: MPL-2.0

"""Synthesize minimal ICC profiles from PDF CalRGB/CalGray parameters.

PDF's CalRGB and CalGray colour spaces (ISO 32000-2 §8.6.5.2/§8.6.5.3) describe a
calibrated space with a ``WhitePoint``, per-channel ``Gamma`` and (for CalRGB) a
3x3 ``Matrix`` whose columns are the CIE XYZ tristimuli of the R/G/B primaries.

Pillow has no way to consume these parameters directly. Instead we build a minimal
ICC v4 matrix/TRC profile (or a gray TRC profile) carrying the same calibration and
attach it to the extracted image, so the colour intent survives into the saved file
for any consumer that honours embedded profiles. We do not run a colour transform
ourselves -- the raw samples are still handed to Pillow as ``L``/``RGB``.

The colorant tags are chromatically adapted to the D50 profile-connection-space
white using the Bradford transform, with the adaptation recorded in the ``chad``
tag, as required for a conformant v4 matrix profile.
"""

from __future__ import annotations

import struct
from collections.abc import Sequence

Vec3 = tuple[float, float, float]
Mat3 = tuple[Vec3, Vec3, Vec3]

# ICC D50 profile connection space white point.
D50: Vec3 = (0.9642, 1.0, 0.8249)

# Bradford cone-response transform and its inverse (standard published values).
_BRADFORD: Mat3 = (
    (0.8951, 0.2664, -0.1614),
    (-0.7502, 1.7135, 0.0367),
    (0.0389, -0.0685, 1.0296),
)
_BRADFORD_INV: Mat3 = (
    (0.9869929, -0.1470543, 0.1599627),
    (0.4323053, 0.5183603, 0.0492912),
    (-0.0085287, 0.0400428, 0.9684867),
)


def _matvec(m: Mat3, v: Sequence[float]) -> Vec3:
    return (
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    )


def _matmul(a: Mat3, b: Mat3) -> Mat3:
    return tuple(  # type: ignore[return-value]
        tuple(sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3))
        for i in range(3)
    )


def _adaptation_matrix(src_white: Sequence[float], dst_white: Vec3 = D50) -> Mat3:
    """Bradford chromatic-adaptation matrix mapping *src_white* to *dst_white*."""
    cone_s = _matvec(_BRADFORD, src_white)
    cone_d = _matvec(_BRADFORD, dst_white)
    scale: Mat3 = (
        (cone_d[0] / cone_s[0], 0.0, 0.0),
        (0.0, cone_d[1] / cone_s[1], 0.0),
        (0.0, 0.0, cone_d[2] / cone_s[2]),
    )
    return _matmul(_BRADFORD_INV, _matmul(scale, _BRADFORD))


def _s15f16(x: float) -> bytes:
    """Encode a number as a signed 15.16 fixed-point big-endian int32."""
    return struct.pack('>i', round(x * 65536))


def _xyz_type(x: float, y: float, z: float) -> bytes:
    return b'XYZ \x00\x00\x00\x00' + _s15f16(x) + _s15f16(y) + _s15f16(z)


def _curve_type(gamma: float) -> bytes:
    # curveType with a single u8Fixed8 entry encoding a pure power curve.
    blob = b'curv\x00\x00\x00\x00' + struct.pack('>I', 1)
    blob += struct.pack('>H', round(gamma * 256))
    return blob


def _sf32_type(m: Mat3) -> bytes:
    blob = b'sf32\x00\x00\x00\x00'
    for row in m:
        for value in row:
            blob += _s15f16(value)
    return blob


def _mluc_type(text: str) -> bytes:
    # multiLocalizedUnicodeType with a single en-US record (UTF-16BE).
    encoded = text.encode('utf-16-be')
    header = b'mluc\x00\x00\x00\x00' + struct.pack('>II', 1, 12)
    record = b'enUS' + struct.pack('>II', len(encoded), 28)
    return header + record + encoded


def _assemble(colour_space: bytes, tags: list[tuple[bytes, bytes]]) -> bytes:
    """Assemble an ICC v4 profile from a colour-space signature and tag blobs."""
    n = len(tags)
    table_size = 4 + 12 * n
    data_start = 128 + table_size

    offset = data_start
    table = struct.pack('>I', n)
    data = b''
    for sig, blob in tags:
        if offset % 4:  # 4-byte alignment between tag data elements
            pad = 4 - (offset % 4)
            data += b'\x00' * pad
            offset += pad
        table += sig + struct.pack('>II', offset, len(blob))
        data += blob
        offset += len(blob)

    body = table + data
    size = 128 + len(body)

    header = bytearray(128)
    struct.pack_into('>I', header, 0, size)
    header[8:12] = struct.pack('>I', 0x04400000)  # version 4.4
    header[12:16] = b'mntr'  # display device class
    header[16:20] = colour_space
    header[20:24] = b'XYZ '  # PCS
    header[36:40] = b'acsp'  # mandatory signature
    header[64:68] = struct.pack('>I', 0)  # perceptual rendering intent
    header[68:80] = _xyz_type(*D50)[8:20]  # PCS illuminant (D50)

    return bytes(header) + body


def build_calrgb_icc(
    white_point: Sequence[float], gamma: Sequence[float], matrix: Sequence[float]
) -> bytes:
    """Build an ICC RGB matrix/TRC profile from CalRGB parameters.

    Args:
        white_point: the CalRGB ``WhitePoint`` (X, Y, Z).
        gamma: per-channel ``Gamma`` (default would be (1, 1, 1)).
        matrix: the 9-element column-major ``Matrix`` mapping linear RGB to XYZ.
    """
    # PDF Matrix is column-major: [Xr Yr Zr  Xg Yg Zg  Xb Yb Zb]. Reshape to a
    # row-major RGB->XYZ matrix whose columns are the primary tristimuli.
    rgb2xyz: Mat3 = (
        (matrix[0], matrix[3], matrix[6]),
        (matrix[1], matrix[4], matrix[7]),
        (matrix[2], matrix[5], matrix[8]),
    )
    adapt = _adaptation_matrix(white_point)
    adapted = _matmul(adapt, rgb2xyz)

    tags = [
        (b'desc', _mluc_type('pikepdf CalRGB')),
        (b'cprt', _mluc_type('No copyright, use freely')),
        (b'wtpt', _xyz_type(*D50)),
        (b'chad', _sf32_type(adapt)),
        (b'rXYZ', _xyz_type(adapted[0][0], adapted[1][0], adapted[2][0])),
        (b'gXYZ', _xyz_type(adapted[0][1], adapted[1][1], adapted[2][1])),
        (b'bXYZ', _xyz_type(adapted[0][2], adapted[1][2], adapted[2][2])),
        (b'rTRC', _curve_type(gamma[0])),
        (b'gTRC', _curve_type(gamma[1])),
        (b'bTRC', _curve_type(gamma[2])),
    ]
    return _assemble(b'RGB ', tags)


def build_calgray_icc(white_point: Sequence[float], gamma: float) -> bytes:
    """Build an ICC gray TRC profile from CalGray parameters."""
    adapt = _adaptation_matrix(white_point)
    tags = [
        (b'desc', _mluc_type('pikepdf CalGray')),
        (b'cprt', _mluc_type('No copyright, use freely')),
        (b'wtpt', _xyz_type(*D50)),
        (b'chad', _sf32_type(adapt)),
        (b'kTRC', _curve_type(gamma)),
    ]
    return _assemble(b'GRAY', tags)
