"""
QR point types for styled rendering (qrbtf compatibility).

Maps each module (row, col) to a semantic type so drawers can render
positioning patterns, alignment, timing, and data differently.
"""

from __future__ import annotations

from enum import IntEnum

from qrcode.util import PATTERN_POSITION_TABLE


class QRPointType(IntEnum):
    """Semantic type of a QR module, matching qrbtf frontend encoder."""

    DATA = 0
    POS_CENTER = 1   # Center of position detection pattern (finder)
    POS_OTHER = 2    # Outer part of position detection pattern
    ALIGN_CENTER = 3
    ALIGN_OTHER = 4
    TIMING = 5
    FORMAT = 6
    VERSION = 7


def get_type_table(modules_count: int) -> list[list[int]]:
    """
    Build a type table for the given QR size (modules_count x modules_count).
    Returns type_table[row][col] with QRPointType values.
    """
    n = modules_count
    type_table = [[QRPointType.DATA] * n for _ in range(n)]

    # Timing pattern: row 6 and col 6, between 8 and n-8
    for i in range(8, n - 7):
        type_table[i][6] = type_table[6][i] = QRPointType.TIMING

    # Position detection patterns: 3 corners, 7x7 each
    # Centers at (3,3), (3, n-4), (n-4, 3)
    position_centers = [(3, 3), (3, n - 4), (n - 4, 3)]
    for pr, pc in position_centers:
        type_table[pr][pc] = QRPointType.POS_CENTER
        for r in range(-4, 5):
            for c in range(-4, 5):
                if r == 0 and c == 0:
                    continue
                nr, nc = pr + r, pc + c
                if 0 <= nr < n and 0 <= nc < n:
                    type_table[nr][nc] = QRPointType.POS_OTHER

    # Alignment patterns (version >= 2)
    version = (modules_count - 17) // 4
    positions = PATTERN_POSITION_TABLE[version - 1] if version >= 2 else []
    for i in range(len(positions)):
        for j in range(len(positions)):
            row, col = positions[i], positions[j]
            if type_table[row][col] == QRPointType.DATA:
                type_table[row][col] = QRPointType.ALIGN_CENTER
                for r in range(-2, 3):
                    for c in range(-2, 3):
                        if (r, c) == (0, 0):
                            continue
                        nr, nc = row + r, col + c
                        if 0 <= nr < n and 0 <= nc < n and type_table[nr][nc] == QRPointType.DATA:
                            type_table[nr][nc] = QRPointType.ALIGN_OTHER

    # Format info: row 8 and col 8 (and symmetric)
    for i in range(9):
        if i != 6:
            type_table[i][8] = type_table[8][i] = QRPointType.FORMAT
        if i < 7:
            type_table[n - 1 - i][8] = QRPointType.FORMAT
        if i < 8:
            type_table[8][n - 1 - i] = QRPointType.FORMAT

    # Version info (version >= 7)
    if n >= 45:  # version 7+
        for i in range(n - 11, n - 8):
            for j in range(6):
                type_table[i][j] = type_table[j][i] = QRPointType.VERSION

    return type_table
