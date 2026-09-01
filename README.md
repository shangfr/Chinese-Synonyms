# Chinese-Synonyms

Chinese Synonyms 中文同义词查询工具包（词法召回）。

cnsyn 是一个轻量、零运行时依赖的中文同义词查询组件：基于内存倒排索引，
把词典中的同义词组按权重排序返回。

- 词法召回：词 → 同义词组，O(1) 精确查询
- 零运行时依赖（仅 Python 标准库）
- 可选增强：模糊匹配（rapidfuzz）、拼音查询（pypinyin）
- 命令行工具：`python -m cnsyn` / `cnsyn`
- Apache License 2.0 授权协议

GitHub: https://github.com/shangfr/Chinese-Synonyms

## 安装

```bash
pip install cnsyn-2.0.0-py3-none-any.whl           # 或从源码：pip install -e .
pip install "cnsyn[fuzzy]"   # 可选：模糊匹配
pip install "cnsyn[pinyin]"  # 可选：拼音查询
```

要求 Python >= 3.9。

## 快速开始

```python
import cnsyn

cnsyn.search("垃圾")                   # ['废料', '废物', '废弃物', '破烂', ...]
cnsyn.search("垃圾", topK=3)           # 最多返回 3 个
cnsyn.search("高兴", origin="wiki")    # 仅 wiki 词库
cnsyn.search("高兴", origin="cndict")  # 仅中文同义词词典
cnsyn.search("laji", pinyin=True)      # 拼音查询（需 pypinyin）
cnsyn.search("垃及", fuzzy=True)       # 模糊匹配（错别字，需 rapidfuzz）
cnsyn.search("高兴", with_score=True)  # [(词, 分数), ...] 分数 = 组间分 + 组首词/频次加分
```

命令行：

```bash
python -m cnsyn 垃圾 --topk 5
cnsyn 高兴 --origin cndict --json
cnsyn laji --pinyin
cnsyn 垃及 --fuzzy
```

## 查询原理

- 词典按词源拆分为 `cnsyn/chinese_dictionary/wiki.txt`（维基百科同义词，28,043 行）
  与 `cndict.txt`（中文同义词词典，17,817 行）；构建时过滤不足 2 词的噪音组，
  实际索引约 29,678 个同义词组 / 117,373 个词。
- 首次调用时把词典加载为内存倒排索引 `word → 同义词组列表`（约 0.3 秒、
  内存占用小），之后查询 O(1)，单次精确查询约 5µs。
- 一个词可能命中多个同义词组，排序分两级（确定性启发式）：
  - **组间**：按「查询词为组首词(+3.0) > 组越短(+1/N) > 位置越靠前(-0.01×位置)」打分；
  - **组内**：组首词（主同义词）置顶 → 跨组词频降序 → 字符相似度降序（`sim_rerank`，
    实验性）→ 词典原位置兜底；合并时去重保序，结果稳定可解释。
- `with_score=True` 时返回 `(词, 分数)`：分数 = 组间分 + 组首词(+2.0) + 频次加分。
- 未命中时依次尝试：模糊匹配（rapidfuzz，可选）→ 拼音匹配（pypinyin，可选）
  → 返回空列表并发出 `UserWarning`。

## API

`cnsyn.search(word, topK=10, origin='all', *, fuzzy=False, pinyin=False) -> list[str]`

| 参数 | 说明 |
| --- | --- |
| `word` | 查询词 |
| `topK` | 最多返回的同义词数量，默认 10 |
| `origin` | 词源过滤：`'all'`（默认）/ `'wiki'` / `'cndict'` / `'user'` |
| `fuzzy` | 未命中时启用模糊匹配（需 `rapidfuzz`） |
| `pinyin` | 未命中时启用拼音匹配（需 `pypinyin`） |
| `with_score` | 返回 `(词, 分数)` 元组而非词列表 |
| `sim_rerank` | 组内按与查询词的字符相似度重排（实验性） |

返回查询词的同义词列表（按权重排序，**不含查询词自身**）；未命中返回 `[]` 并发出 `UserWarning`。

## 自定义同义词

支持运行时添加自己的同义词组（内存态，重启进程后丢失；文件请自行保存）：

```python
import cnsyn

# ① 运行时添加一个同义词组
cnsyn.add_synonyms(["垃圾", "废物", "渣滓"])

# ② 批量加载用户词典文件（每行一个同义词组，空格分隔）
cnsyn.load_user_dict("my_dict.txt")   # 返回加载的组数

# ③ 查询：origin='user' 只看自定义组；'all'（默认）包含所有
cnsyn.search("垃圾", origin="user")
cnsyn.search("垃圾")                  # 默认包含自定义组
```

命令行：

```bash
cnsyn --add "垃圾 废物 渣滓" 垃圾 --origin user
cnsyn --load my_dict.txt 垃圾
```

自定义组与内置词典一样参与权重排序（组首词置顶、词频加权）。

## 词典说明

- wiki：通过维基百科构建的中文同义词库（AitSimwords.txt），28,043 组；
- cndict：中文同义词字典（chinese_dictionary），17,817 组。

更新词典后无需构建二进制索引，重新加载即生效。
旧版合并词典 `sim_words.txt` 的拆分脚本见 `scripts/split_dictionary.py`。

## 开发

```bash
pip install -e ".[dev]"
pytest -q
```

## License

Apache License 2.0