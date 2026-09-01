"""词法召回核心：search() + 归一化 + 降级链（模糊/拼音）。

排序算法（两级，确定性启发式）：
1. 组间：_group_score —— 查询词为组首词(+3.0) > 组越短越可信(+1/N) > 位置越靠前(-0.01×pos)；
2. 组内：组首词置顶 → 跨组词频降序 → 与查询词的字符相似度降序（可选 sim_rerank）
   → 词典原位置升序兜底，保证结果稳定可解释。
"""
from __future__ import annotations

import warnings
from difflib import SequenceMatcher
from functools import lru_cache

from ._index import SynGroup, get_index
from ._text import normalize

__all__ = ["search", "add_synonyms", "load_user_dict"]

_VALID_ORIGINS = ("all", "wiki", "cndict", "user")


def _group_score(group: SynGroup, query: str) -> float:
    """组间排序权重：查询词为组首词(3.0) > 组越短越可信(1/N) > 位置越靠前(-0.01×pos)。"""
    try:
        hit_pos = group.words.index(query)
    except ValueError:
        hit_pos = len(group.words)
    return (3.0 if hit_pos == 0 else 0.0) + 1.0 / len(group.words) - 0.01 * hit_pos


def _similarity(a: str, b: str) -> float:
    """字符级相似度（difflib.SequenceMatcher，标准库、零依赖）。"""
    return SequenceMatcher(None, a, b).ratio()


def _ordered_group_words(
    group: SynGroup,
    query: str,
    word_freq: dict[str, int],
    sim_rerank: bool,
) -> list[str]:
    """组内输出顺序：组首词置顶 → 多字词优先（单字词殿后）→ 词频降序
    → (字符相似度降序，可选) → 原位置升序兜底。

    单字词（如"快/乐/欢/喜"）多为构词语素，跨组频次虚高且作为同义词价值低，
    因此统一排在多字词之后。
    """
    positions = {w: i for i, w in enumerate(group.words)}

    def key(w: str):
        return (
            0 if w == group.headword else 1,          # 组首词（主同义词）置顶
            0 if len(w) >= 2 else 1,                   # 多字词优先，单字词殿后
            -word_freq.get(w, 1),                      # 词频：跨组出现次数越多越靠前
            -_similarity(query, w) if sim_rerank else 0.0,  # 与查询词相似度（可选）
            positions[w],                              # 原位置兜底，保证稳定
        )

    return sorted(group.words, key=key)


def _word_score(group: SynGroup, w: str, group_score: float, word_freq: dict[str, int]) -> float:
    """单词分数：组间分 + 组首词(+2.0) + 跨组频次加分(+0.1×min(次数-1, 3))。"""
    score = group_score
    if w == group.headword:
        score += 2.0
    score += min(word_freq.get(w, 1) - 1, 3) * 0.1
    return round(score, 4)


def _exact_search(index, query: str, topK: int, origin: str, *, with_score: bool, sim_rerank: bool):
    """精确路径：查找所有包含该词的组，按权重合并去重。

    结果不含查询词自身（精确路径排除用户查询词；模糊/拼音兜底路径
    排除纠正后的目标词），topK 统计同义词数量。
    """
    hits = index.groups_of(query)
    if not hits:
        return []
    word_freq = index.word_freq

    scores = {gid: _group_score(index.groups[gid], query) for gid in hits}
    ranked = sorted(hits, key=scores.get, reverse=True)

    merged = []
    seen: set[str] = set()
    for gid in ranked:
        group = index.groups[gid]
        if origin != "all" and group.origin != origin:
            continue
        for w in _ordered_group_words(group, query, word_freq, sim_rerank):
            if w == query:  # 排除查询词自身
                continue
            if w in seen:
                continue
            seen.add(w)
            merged.append((w, _word_score(group, w, scores[gid], word_freq)) if with_score else w)
            if len(merged) >= topK:
                return merged
    return merged


def _best_fuzzy_candidate(index, query: str) -> str | None:
    """模糊匹配：对「同首字 + 长度相近(差<=1) + 至少2字」的候选做整词编辑距离打分。

    用 fuzz.ratio（整词 Levenshtein 相似度）而非 WRatio——WRatio 的 partial 逻辑
    会误偏向包含查询字符的长词。中文 2 字词错 1 字时相似度约 50%，因此采用
    「优势候选」规则：分数 >= 80 直接接受；>= 50 且明显高于第二名（>=10 分）
    才接受，避免多候选歧义时的误纠。
    """
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        warnings.warn("模糊匹配需要安装 rapidfuzz：pip install cnsyn[fuzzy]", UserWarning, stacklevel=3)
        return None
    candidates = [
        w for w in index.words
        if len(w) >= 2 and w[:1] == query[:1] and abs(len(w) - len(query)) <= 1
    ]
    if not candidates:
        return None
    matches = process.extract(query, candidates, scorer=fuzz.ratio, limit=5, score_cutoff=50)
    if not matches:
        return None
    best, score = matches[0][0], matches[0][1]
    second = matches[1][1] if len(matches) > 1 else 0
    if score >= 80 or (score >= 50 and score - second >= 10):
        return best
    return None


_pinyin_map: dict[str, tuple[str, ...]] | None = None
_pinyin_unavailable = False


def _best_pinyin_candidate(index, query: str) -> str | None:
    """拼音匹配：按全拼找到候选词（可选依赖 pypinyin），优先返回组首词。"""
    global _pinyin_map, _pinyin_unavailable
    if _pinyin_unavailable:
        return None
    if _pinyin_map is None:
        try:
            from pypinyin import lazy_pinyin
        except ImportError:
            _pinyin_unavailable = True
            warnings.warn("拼音匹配需要安装 pypinyin：pip install cnsyn[pinyin]", UserWarning, stacklevel=3)
            return None
        mapping: dict[str, list[str]] = {}
        for w in index.words:
            key = "".join(lazy_pinyin(w))
            mapping.setdefault(key, []).append(w)
        _pinyin_map = {k: tuple(v) for k, v in mapping.items()}

    from pypinyin import lazy_pinyin  # noqa: F811
    key = "".join(lazy_pinyin(query))
    candidates = _pinyin_map.get(key)
    if not candidates:
        return None
    for w in candidates:
        if w in index.headwords:
            return w
    return candidates[0]


@lru_cache(maxsize=8192)
def search(
    word: str,
    topK: int = 10,
    origin: str = "all",
    *,
    fuzzy: bool = False,
    pinyin: bool = False,
    with_score: bool = False,
    sim_rerank: bool = False,
) -> list[str] | list[tuple[str, float]]:
    """查询中文同义词（词法召回）。

    Parameters
    ----------
    word : str
        查询词。
    topK : int, optional
        最多返回的同义词数量，默认 10。
    origin : {'all', 'wiki', 'cndict'}, optional
        词源过滤，默认 'all'（全部）。
    fuzzy : bool, optional
        精确未命中时启用模糊匹配（需安装 rapidfuzz，默认 False）。
    pinyin : bool, optional
        精确未命中时启用拼音匹配（需安装 pypinyin，默认 False）。
    with_score : bool, optional
        返回 (词, 分数) 元组而非词列表，默认 False。
    sim_rerank : bool, optional
        组内按与查询词的字符相似度重排（实验性），默认 False。

    Returns
    -------
    list[str] 或 list[tuple[str, float]]
        同义词列表（按权重排序，不含查询词自身）；未命中返回 []。

    Examples
    --------
    >>> import cnsyn
    >>> cnsyn.search("高兴", topK=3)
    ['开心', '欢喜', '乐意']
    >>> cnsyn.search("高兴", topK=3, with_score=True)
    [('开心', 3.2172), ('欢喜', 3.2172), ('乐意', 3.2172)]
    """
    if origin not in _VALID_ORIGINS:
        raise ValueError(f"origin 必须是 {_VALID_ORIGINS} 之一，收到 {origin!r}")
    if topK < 1:
        raise ValueError("topK 必须 >= 1")

    query = normalize(word)
    index = get_index()

    result = _exact_search(index, query, topK, origin, with_score=with_score, sim_rerank=sim_rerank)
    if result or not (fuzzy or pinyin):
        if not result:
            warnings.warn(f"'{word}' 未在词典中找到", UserWarning, stacklevel=2)
        return result

    if fuzzy:
        candidate = _best_fuzzy_candidate(index, query)
        if candidate:
            result = _exact_search(index, normalize(candidate), topK, origin, with_score=with_score, sim_rerank=sim_rerank)
            if result:
                return result

    if pinyin:
        candidate = _best_pinyin_candidate(index, query)
        if candidate:
            result = _exact_search(index, normalize(candidate), topK, origin, with_score=with_score, sim_rerank=sim_rerank)
            if result:
                return result

    warnings.warn(f"'{word}' 未在词典中找到（含模糊/拼音兜底）", UserWarning, stacklevel=2)
    return []


def add_synonyms(words: list[str]) -> None:
    """运行时添加一个同义词组（内存态，重启进程后丢失；origin='user'）。

    Parameters
    ----------
    words : list[str]
        同义词组内的词，至少 2 个不同词（自动归一化/去重，保留顺序）。

    Examples
    --------
    >>> import cnsyn
    >>> cnsyn.add_synonyms(["垃圾", "废物", "渣滓"])
    >>> cnsyn.search("垃圾", origin="user")
    ['废物', '渣滓']
    """
    cleaned = tuple(dict.fromkeys(normalize(w) for w in words if w.strip()))
    if len(cleaned) < 2:
        raise ValueError(f"同义词组至少需要 2 个不同的词，收到 {words!r}")
    get_index().add_group(SynGroup("user", cleaned))
    search.cache_clear()


def load_user_dict(path: str) -> int:
    """批量加载用户词典文件：每行一个同义词组（空格分隔），返回加载的组数。

    过滤规则与内置词典一致：不足 2 词的行被跳过，单字词保留。
    加载后立即对 search() 生效（内存态，文件由用户自行保存）。
    """
    index = get_index()
    count = 0
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            words = tuple(dict.fromkeys(normalize(w) for w in line.split()))
            if len(words) >= 2:
                index.add_group(SynGroup("user", words))
                count += 1
    if count:
        search.cache_clear()
    return count
