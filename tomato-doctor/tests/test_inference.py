import math

from tomatodoc.inference import UNKNOWN, report_likelihood
from tomatodoc.kg.graph import validate_seed
from tomatodoc.learning import plan_updates


def ev(sid, present=True, c=0.92, source="answer"):
    return {"symptom_id": sid, "present": present, "c": c, "source": source}


def test_seed_is_consistent(seed):
    assert validate_seed(seed) == []


def test_posterior_is_a_distribution(engine):
    post, _ = engine.posterior([ev("white_powder")])
    assert math.isclose(sum(post.values()), 1.0, rel_tol=1e-9)
    assert UNKNOWN in post


def test_no_evidence_asks_for_input(engine):
    assert engine.step([])["status"] == "need_input"


def test_discriminative_question_splits_white_dust_case(engine):
    """The motivating case of the project: 'white dust' could be powdery mildew
    or whitefly. The first question must be about insects, not an unrelated symptom."""
    st = engine.step([ev("white_powder", c=0.9, source="text")])
    assert st["status"] == "question"
    assert st["question"]["symptom_id"] in ("insects_fly_up", "pests_seen")


def test_answers_change_the_diagnosis(engine):
    base = [ev("white_powder", c=0.9, source="text")]
    yes = engine.posterior(base + [ev("insects_fly_up", True), ev("sticky_sooty", True)])[0]
    no = engine.posterior(base + [ev("insects_fly_up", False), ev("pests_seen", False)])[0]
    assert max(yes, key=yes.get) == "whitefly"
    assert max(no, key=no.get) == "powdery_mildew"


def test_weak_text_match_moves_posterior_less_than_strong(engine):
    weak = engine.posterior([ev("ring_spots", c=0.6, source="text")])[0]
    strong = engine.posterior([ev("ring_spots", c=0.95, source="text")])[0]
    assert strong["early_blight"] > weak["early_blight"]


def test_unrelated_evidence_raises_unknown(engine):
    # symptoms of completely different diseases at once -> "something else" grows
    mixed = [ev("fruit_holes"), ev("root_galls"), ev("white_ooze"), ev("leaf_tunnels")]
    post = engine.posterior(mixed)[0]
    single = engine.posterior([ev("fruit_holes")])[0]
    assert post[UNKNOWN] > single[UNKNOWN]


def test_season_prior_favours_seasonal_disease(engine):
    hot = engine.prior("hot_dry")
    humid = engine.prior("humid_monsoon")
    assert hot["spider_mite"] > humid["spider_mite"]
    assert humid["late_blight"] > hot["late_blight"]


def test_photo_evidence_is_fused(engine):
    photo = {"probs": {"late_blight": 0.95, "early_blight": 0.03, "healthy": 0.02}, "temperature": 0.6}
    post = engine.posterior([], photo=photo)[0]
    assert max(post, key=post.get) == "late_blight"


def test_question_budget_and_stop(engine):
    st = engine.step([ev("white_powder")], asked=["a"] * 6)
    assert st["status"] == "result"


def test_explanation_lists_evidence(engine):
    e = [ev("one_side_wilt"), ev("brown_inside_stem")]
    post, ll = engine.posterior(e)
    r = engine.result(post, ll, e)
    assert r["disease_id"] == "fusarium_wilt"
    assert {x["symptom_id"] for x in r["explanation"]["evidence"]} == {"one_side_wilt", "brown_inside_stem"}


def test_asymmetric_noise():
    # a confident report of a symptom the disease never shows is strong evidence against it
    assert report_likelihood(0.02, True, 0.92) < 0.05
    assert report_likelihood(0.9, False, 0.92) < 0.2


def test_learning_only_from_confirmed_truth(kg):
    evidence = [ev("white_powder", True, 0.9, "text") | {"layterm_id": "lt_white_dust"}, ev("insects_fly_up", False)]
    updates, suggestions = plan_updates(kg, evidence, "powdery_mildew")
    hs = {(u["src"], u["dst"]): u for u in updates if u["rel"] == "HAS_SYMPTOM"}
    assert hs[("powdery_mildew", "white_powder")]["d_alpha"] > 0
    assert ("powdery_mildew", "insects_fly_up") not in hs           # no such edge -> nothing to weaken
    lt = [u for u in updates if u["rel"] == "LAYTERM_MAPS_TO"][0]
    assert lt["src"] == "lt_white_dust" and lt["d_alpha"] > 0
    assert suggestions == []


def test_learning_suggests_new_edges(kg):
    _, suggestions = plan_updates(kg, [ev("leaf_tunnels", True, 0.95)], "early_blight")
    assert suggestions and suggestions[0]["s"] == "leaf_tunnels"


def test_weight_update_is_bounded(kg):
    for _ in range(500):
        kg.apply_edge_delta("HAS_SYMPTOM", "powdery_mildew", "white_powder", 1.0, 0.0)
    assert 0 < kg.theta("powdery_mildew", "white_powder") < 1
