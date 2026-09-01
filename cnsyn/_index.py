"""内存倒排索引：把包内词典文本加载为 word → 同义词组 的查询结构。

设计要点：
- 词典文本（chinese_dictionary/wiki.txt、cndict.txt）是唯一数据源，
  无需任何二进制索引文件；
- 首次调用 build() 时一次性构建（约 4.5 万组、几十毫秒），之后只读；
- 查询走 dict 精确查找，O(1)；
- 支持运行时通过 add_group() 增量追加自定义同义词组（origin='user'）。
"""
from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files

from ._text import normalize

__all__ = ["SynGroup", "LexicalIndex", "get_index"]


@dataclass(frozen=True)
class SynGroup:
    """一个同义词组（词典的一行）。"""

    origin: str                # "wiki" / "cndict" / "user"
    words: tuple[str, ...]     # 组内词（已归一化、去重、保序）

    @property
    def headword(self) -> str:
        """组首词（权重最高的词）。"""
        return self.words[0]


class LexicalIndex:
    """词 → 同义词组 的内存倒排索引。

    构建后通常只读；add_group() 支持运行时增量追加（自定义词源），
    追加会同步更新倒排表、词频与候选词池。
    """

    __slots__ = ("groups", "headwords", "_words", "_word2groups", "word_freq")

    def __init__(self, groups: list[SynGroup]):
        self.groups = list(groups)
        self.headwords = set(g.headword for g in self.groups)
        word2groups: dict[str, list[int]] = {}
        for gid, group in enumerate(self.groups):
            for word in group.words:
                word2groups.setdefault(word, []).append(gid)
        self._word2groups = word2groups
        self._words = list(word2groups.keys())
        # 跨组频次：一个词出现在多少个同义词组中（越高越常用，用于组内排序）
        self.word_freq = {w: len(gids) for w, gids in word2groups.items()}

    def groups_of(self, word: str) -> tuple[int, ...]:
        """返回包含该词的所有组 id（按词典顺序）。"""
        return tuple(self._word2groups.get(word, ()))

    @property
    def words(self) -> list[str]:
        """全部词典词（用于模糊/拼音候选）。"""
        return self._words

    def add_group(self, group: SynGroup) -> None:
        """运行时追加一个同义词组（如用户自定义 origin='user' 的组）。

        追加后词频与候选词池同步更新；调用方负责清空 search() 的结果缓存。
        """
        gid = len(self.groups)
        self.groups.append(group)
        self.headwords.add(group.headword)
        for w in group.words:
            is_new = w not in self._word2groups
            self._word2groups.setdefault(w, []).append(gid)
            self.word_freq[w] = self.word_freq.get(w, 0) + 1
            if is_new:
                self._words.append(w)

    @classmethod
    def build(cls, base=None) -> "LexicalIndex":
        """从包内 chinese_dictionary/ 目录下的 wiki.txt、cndict.txt 构建索引。

        base 可注入其他目录（测试/自定义词典），默认指向包内数据。
        处理管道：分词 → 归一化 → 去重保序 → 过滤不足 2 词的组（空行/单元素噪音组）。
        注意：这里只过滤组内【词的数量】不足 2 的组，不剔除单字词
        （如"乐/欢/喜/快"等构词语素仍保留在组内）。
        """
        base = base if base is not None else files(__package__).joinpath("chinese_dictionary")
        groups: list[SynGroup] = []
        for origin, fname in (("wiki", "wiki.txt"), ("cndict", "cndict.txt")):
            with (base / fname).open(encoding="utf-8") as fh:
                for line in fh:
                    words = tuple(dict.fromkeys(normalize(w) for w in line.split()))
                    if len(words) >= 2:  # 过滤空行/单元素噪音组
                        groups.append(SynGroup(origin, words))
        return cls(groups)


_index: LexicalIndex | None = None


def get_index() -> LexicalIndex:
    """惰性获取全局索引单例（首次调用时构建并缓存）。"""
    global _index
    if _index is None:
        _index = LexicalIndex.build()
    return _index
