#!/usr/bin/env python3
"""一次性迁移脚本：把旧版合并词典 sim_words.txt 拆分为 wiki.txt / cndict.txt。

旧版 utils_index.py 用行号阈值 `num > 28043` 区分词源：
前 28043 行是 wiki 词库（即 AitSimwords.txt 的逐行拷贝，已用 md5 验证），
其余 17817 行是 cndict 词库（即 dict_synonym.txt 的逐行拷贝）。

用法：
    python scripts/split_dictionary.py <old_sim_words.txt> <outdir>
"""
from __future__ import annotations

import argparse
from pathlib import Path

WIKI_LINES = 28043  # 与旧版 build_index 阈值一致（已 md5 验证）


def line_count(path: Path) -> int:
    return sum(1 for _ in path.open(encoding="utf-8"))


def split(old_file: Path, outdir: Path, wiki_lines: int = WIKI_LINES) -> None:
    total = line_count(old_file)
    if total <= wiki_lines:
        raise SystemExit(f"错误：{old_file} 只有 {total} 行，无法按 {wiki_lines} 行拆分")
    outdir.mkdir(parents=True, exist_ok=True)
    wiki_path = outdir / "wiki.txt"
    cndict_path = outdir / "cndict.txt"
    with old_file.open(encoding="utf-8") as fh, \
         wiki_path.open("w", encoding="utf-8") as wiki, \
         cndict_path.open("w", encoding="utf-8") as cndict:
        for num, line in enumerate(fh, start=1):
            target = wiki if num <= wiki_lines else cndict
            target.write(line)
    print(f"wiki  : {wiki_lines} 行 -> {wiki_path}")
    print(f"cndict: {total - wiki_lines} 行 -> {cndict_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="拆分合并词典为 wiki.txt / cndict.txt")
    parser.add_argument("old_file", type=Path, help="旧版合并词典 sim_words.txt 路径")
    parser.add_argument("outdir", type=Path, help="输出目录（生成 wiki.txt / cndict.txt）")
    parser.add_argument("--wiki-lines", type=int, default=WIKI_LINES, help="wiki 词库行数阈值")
    args = parser.parse_args()
    split(args.old_file, args.outdir, args.wiki_lines)


if __name__ == "__main__":
    main()
