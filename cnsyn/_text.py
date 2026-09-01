"""文本归一化工具。"""
from __future__ import annotations

import unicodedata

__all__ = ["normalize"]


def normalize(text: str) -> str:
    """归一化：NFKC（全角→半角、兼容字符）→ 去除首尾空白 → 小写。

    中文本身无大小写，小写主要用于拼音/拉丁字母输入；简繁转换不在此列。
    """
    return unicodedata.normalize("NFKC", text).strip().lower()
