"""cnsyn 词法召回核心测试。"""
import warnings

import pytest

import cnsyn
from cnsyn._index import get_index


def test_public_api():
    assert callable(cnsyn.search)
    assert "search" in cnsyn.__all__
    assert isinstance(cnsyn.__version__, str)


def test_search_known_word_excludes_query():
    result = cnsyn.search("高兴")
    assert isinstance(result, list)
    assert result
    assert "高兴" not in result  # 结果不含查询词自身


def test_search_topk():
    result = cnsyn.search("高兴", topK=3)
    assert len(result) <= 3
    assert "高兴" not in result


def test_search_origin_filter():
    wiki = cnsyn.search("高兴", origin="wiki")
    cndict = cnsyn.search("高兴", origin="cndict")
    assert isinstance(wiki, list) and isinstance(cndict, list)
    assert wiki and cndict


def test_search_origin_invalid():
    with pytest.raises(ValueError):
        cnsyn.search("高兴", origin="bad")


def test_search_topk_invalid():
    with pytest.raises(ValueError):
        cnsyn.search("高兴", topK=0)


def test_search_oov_warns_and_returns_empty():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = cnsyn.search("不存在的词xyzabc123")
    assert result == []
    assert any(issubclass(w.category, UserWarning) for w in caught)


def test_normalization_fullwidth_space():
    # 全角空格 + 尾部空白应归一化后命中
    result = cnsyn.search("高兴　", topK=3)
    assert result


def test_normalization_fullwidth_latin():
    # 全角字母归一化为半角；词典无此词 → 空 + 警告（忽略警告只断言空）
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert cnsyn.search("ＡＢＣ") == []


def test_search_stable_order():
    # 权重排序而非随机序
    assert cnsyn.search("高兴", topK=5) == cnsyn.search("高兴", topK=5)


def test_index_groups_quality():
    index = get_index()
    for group in list(index.groups)[:2000]:
        assert len(group.words) >= 2
        assert len(group.words) == len(set(group.words))


def test_index_origin_tags():
    # 至少包含内置词源（自定义 user 组可能被其他测试追加，用子集断言）
    index = get_index()
    assert {"wiki", "cndict"} <= {g.origin for g in index.groups}
def test_fuzzy_fallback():
    pytest.importorskip("rapidfuzz")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = cnsyn.search("垃及", fuzzy=True, topK=4)
    assert result
    assert "垃圾" not in result  # 纠正后的目标词也不出现在结果里
    assert "废物" in result


def test_fuzzy_ambiguous_rejected():
    pytest.importorskip("rapidfuzz")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert cnsyn.search("高心", fuzzy=True, topK=4) == []


def test_pinyin_fallback():
    pytest.importorskip("pypinyin")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        result = cnsyn.search("laji", pinyin=True, topK=4)
    assert result
    assert "垃圾" not in result
    assert "废物" in result

def test_with_score():
    result = cnsyn.search("高兴", topK=3, with_score=True)
    assert len(result) == 3
    for item in result:
        w, s = item
        assert isinstance(w, str) and isinstance(s, float)
    assert result[0][1] >= result[1][1]  # 首词分数不低于后续词


def test_headword_first():
    # cndict 组首词"高兴"被排除后：多字词优先、跨组频次降序（开心/欢喜/乐意 频次最高）
    result = cnsyn.search("高兴", topK=3)
    assert result[:3] == ["开心", "欢喜", "乐意"]


def test_freq_ranking():
    # cndict 组内：跨组频次高的词（废物/废料/废弃物）应排在低频词（渣滓）之前
    result = cnsyn.search("垃圾", origin="cndict", topK=10)
    assert result[0] == "废物"  # 组首词置顶
    assert result.index("废弃物") < result.index("渣滓")


def test_sim_rerank_opt_in():
    result = cnsyn.search("高兴", topK=5, sim_rerank=True)
    assert result
    assert len(result) <= 5
    assert all(isinstance(w, str) for w in result)
    assert "高兴" not in result

def test_add_synonyms():
    cnsyn.add_synonyms(["测试词甲", "测试词乙", "测试词丙"])
    # origin='user' 只看自定义组（组首词"测试词甲"被排除）
    assert cnsyn.search("测试词甲", origin="user") == ["测试词乙", "测试词丙"]
    # origin='all'（默认）包含自定义组
    assert "测试词乙" in cnsyn.search("测试词甲")


def test_add_synonyms_requires_two():
    with pytest.raises(ValueError):
        cnsyn.add_synonyms(["单"])


def test_add_synonyms_normalizes():
    cnsyn.add_synonyms(["测试词丁 ", "测试词戊", "测试词丁"])
    assert "测试词戊" in cnsyn.search("测试词丁", origin="user")


def test_load_user_dict(tmp_path):
    f = tmp_path / "user_dict.txt"
    f.write_text("独特词一 独特词二 独特词三\n单元素\n", encoding="utf-8")
    n = cnsyn.load_user_dict(str(f))
    assert n == 1  # 单元素行被跳过
    assert "独特词二" in cnsyn.search("独特词一", origin="user")
