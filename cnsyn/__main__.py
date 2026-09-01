"""cnsyn 命令行入口：python -m cnsyn <词> [选项]。"""
from __future__ import annotations

import argparse
import json
import sys

from ._search import add_synonyms, load_user_dict, search


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="cnsyn",
        description="中文同义词查询（词法召回）",
    )
    parser.add_argument("word", nargs="?", help="要查询的词")
    parser.add_argument("--add", metavar='"词1 词2 ..."', help="运行时添加一个同义词组（空格分隔）")
    parser.add_argument("--load", metavar="FILE", help="加载用户词典文件（每行一组）")
    parser.add_argument("--topk", type=int, default=10, help="最多返回数量（默认 10）")
    parser.add_argument(
        "--origin",
        choices=("all", "wiki", "cndict", "user"),
        default="all",
        help="词源过滤（默认 all）",
    )
    parser.add_argument("--fuzzy", action="store_true", help="未命中时启用模糊匹配（需 rapidfuzz）")
    parser.add_argument("--pinyin", action="store_true", help="未命中时启用拼音匹配（需 pypinyin）")
    parser.add_argument("--score", action="store_true", help="返回 (词, 分数) 结果")
    parser.add_argument("--sim", action="store_true", help="组内按与查询词的字符相似度重排（实验性）")
    parser.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = parser.parse_args(argv)

    if args.add is not None:
        add_synonyms(args.add.split())
        print(f"已添加同义词组：{args.add}", file=sys.stderr)
    if args.load is not None:
        n = load_user_dict(args.load)
        print(f"已加载 {n} 个自定义同义词组：{args.load}", file=sys.stderr)
    if args.word is None:
        if args.add is None and args.load is None:
            parser.print_help()
            return 2
        return 0

    try:
        result = search(
            args.word,
            topK=args.topk,
            origin=args.origin,
            fuzzy=args.fuzzy,
            pinyin=args.pinyin,
            with_score=args.score,
            sim_rerank=args.sim,
        )
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    elif args.score:
        if result:
            print("、".join(f"{w}({s})" for w, s in result))
        else:
            print(f"未找到 '{args.word}' 的同义词")
    elif result:
        print("、".join(result))
    else:
        print(f"未找到 '{args.word}' 的同义词")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())