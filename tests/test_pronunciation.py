from core.pronunciation import align, normalize, score, summarize


def test_normalize_contractions_numbers_punctuation():
    assert normalize("I'm sending 3 files, OK?") == ["i", "am", "sending", "three", "files", "ok"]


def test_normalize_curly_quotes_and_percent():
    assert normalize("We\u2019re on track") == ["we", "are", "on", "track"]
    assert normalize("12%") == ["twelve", "percent"]


def test_perfect_match_scores_100():
    tokens = align("Please send it by Friday.", "please send it by friday")
    assert score(tokens) == 100
    assert all(t.status == "correct" for t in tokens)


def test_substitution():
    tokens = align("Please send it by Friday", "Please send it until Friday")
    subs = [t for t in tokens if t.status == "substituted"]
    assert len(subs) == 1 and subs[0].word == "by" and subs[0].heard == "until"
    assert score(tokens) == 80


def test_missed_word():
    tokens = align("Please send it by Friday", "Please send by Friday")
    assert [t.word for t in tokens if t.status == "missed"] == ["it"]
    assert score(tokens) == 80


def test_extra_words_do_not_reduce_score():
    tokens = align("Please send it by Friday", "Please please send it by Friday")
    assert any(t.status == "extra" for t in tokens)
    assert score(tokens) == 100


def test_empty_transcript_scores_zero():
    tokens = align("Please send it by Friday", "")
    assert score(tokens) == 0
    assert summarize(tokens)["missed"] == ["please", "send", "it", "by", "friday"]


def test_empty_target():
    assert score(align("", "hello")) == 0