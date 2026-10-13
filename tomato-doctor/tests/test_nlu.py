import pytest


def found(matcher, text):
    return {m["symptom_id"]: m["present"] for m in matcher.match(text)["matches"]}


@pytest.mark.parametrize("text", [
    "இலையில் வெள்ளை தூள் போல இருக்கு",      # Tamil
    "white powder on the leaves",            # English
    "ilai la vellai podi irukku",            # Tanglish
    "whte powdr on leafs",                   # typos
])
def test_same_symptom_in_three_languages(matcher, text):
    assert found(matcher, text).get("white_powder") is True


def test_tamil_inflections_are_stemmed(matcher):
    # இலைகளில் / புள்ளிகள் are inflected forms of இலை / புள்ளி
    assert "leaf_spots" in found(matcher, "இலைகளில் பழுப்பு புள்ளிகள் இருக்கு")


def test_shared_filler_words_do_not_cause_false_matches(matcher):
    # v1 bug: this input was diagnosed as Target Spot because of shared words
    got = found(matcher, "இலையில் வெள்ளை தூள் போல இருக்கு")
    assert "ring_spots" not in got and "target_ring" not in got


def test_generic_words_alone_do_not_match_specific_phrase(matcher):
    assert "caterpillar_seen" not in found(matcher, "my plant is wilting suddenly and leaves are still green")


@pytest.mark.parametrize("text", ["white powder on leaves but no insects", "வெள்ளை தூள் இருக்கு ஆனா பூச்சி பறக்கலை"])
def test_negation_produces_absent_evidence(matcher, text):
    got = found(matcher, text)
    assert got.get("white_powder") is True
    assert got.get("insects_fly_up") is False


def test_fixed_negative_idiom_is_a_symptom_not_a_negation(matcher):
    assert found(matcher, "செடி சரியா வளரலை").get("stunted") is True


def test_multiple_symptoms_in_one_sentence(matcher):
    got = found(matcher, "இலை சுருண்டு செடி குட்டையா இருக்கு வெள்ளை ஈ நிறைய")
    assert {"leaf_curl_up", "stunted", "insects_fly_up"} <= set(got)


def test_nonsense_matches_nothing(matcher):
    assert matcher.match("xyz random words")["matches"] == []


def test_prefers_phrase_in_farmers_script(matcher):
    m = matcher.match("இலையில் வெள்ளை தூள் போல இருக்கு")["matches"][0]
    assert m["lang"] == "ta"
