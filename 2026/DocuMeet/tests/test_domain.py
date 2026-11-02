import copy

import pytest

from gather.domain import (align_words, make_segments, merge_speakers, new_meeting,
                           normalize_asr, reassign_segment, sample_ranges, timestamp)
from gather.storage import Store


def word(text, start, end):
    return dict(word=text, start=start, end=end)


def test_alignment_uses_audio_intervals_leaves_silence_unknown_and_flags_overlap():
    words = [word("Hello", .2, .5), word("everyone", 1.1, 1.5), word("yes", 2.1, 2.4), word("later", 5, 5.2)]
    spans = [dict(start=0, end=2, speaker="a"), dict(start=1, end=3, speaker="b")]
    result = align_words(words, spans)
    assert [w["speaker"] for w in result] == ["a", "a", "b", "unknown"]
    assert [w["overlap"] for w in result] == [False, True, False, False]
    assert "speaker" not in words[0]


def test_alignment_across_one_hour_keeps_timestamps_and_supports_six_people():
    spans = [dict(start=i * 10, end=i * 10 + 9, speaker=f"s{i % 6}") for i in range(360)]
    words = [word(str(i), i * 10 + 1, i * 10 + 2) for i in range(360)]
    aligned = align_words(words, spans)
    assert all(w["speaker"] == f"s{i % 6}" for i, w in enumerate(aligned))
    assert timestamp(aligned[-1]["end"]) == "00:59:52"


def test_sentence_crossing_a_speaker_turn_is_split_by_word_timing():
    words = [word("Can", 0, .3), word("we?", .3, 1), word("Yes.", 1.2, 2)]
    spans = [dict(start=0, end=1.1, speaker="a"), dict(start=1.1, end=2.1, speaker="b")]
    segments = make_segments(align_words(words, spans))
    assert [s["text"] for s in segments] == ["Can we?", "Yes."]
    assert [s["speaker"] for s in segments] == ["a", "b"]


def test_missing_word_timestamps_are_rejected_instead_of_fabricated():
    with pytest.raises(ValueError, match="word timestamps"):
        normalize_asr({"segments": [{"start": 0, "end": 10, "text": "Hello"}]})


def test_clean_voice_samples_exclude_other_speakers():
    spans = [dict(start=0, end=12, speaker="a"), dict(start=3, end=8, speaker="b")]
    ranges = sample_ranges(spans, "a")
    assert ranges
    assert all(end <= 3 or start >= 8 for start, end in ranges)


def test_merge_and_reassignment_survive_database_reload(tmp_path):
    store = Store(tmp_path)
    meeting = store.create("Design review")
    meeting["speakers"] = {"a": {"name": "Alex", "color": 0}, "b": {"name": "Voice 2", "color": 1}, "c": {"name": "Chris", "color": 2}}
    meeting["words"] = [dict(word("Hi", 0, 1), speaker="b"), dict(word("Okay", 2, 3), speaker="c")]
    meeting["segments"] = make_segments(meeting["words"])
    meeting["intervals"] = [dict(start=0, end=1, speaker="b")]
    merge_speakers(meeting, "b", "a")
    reassign_segment(meeting, meeting["segments"][1]["id"], "a")
    store.save(meeting)
    loaded = Store(tmp_path).get(meeting["id"])
    assert "b" not in loaded["speakers"]
    assert {s["speaker"] for s in loaded["segments"]} == {"a"}
    assert {w["speaker"] for w in loaded["words"]} == {"a"}
    assert loaded["intervals"][0]["speaker"] == "a"


def test_self_merge_does_not_destroy_data():
    meeting = new_meeting("Test")
    meeting["speakers"] = {"a": {"name": "Alex"}}
    with pytest.raises(ValueError):
        merge_speakers(meeting, "a", "a")
    assert "a" in meeting["speakers"]
