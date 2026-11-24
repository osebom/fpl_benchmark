from fpl_sim.simulator.chip_validation import chip_is_eligible
from fpl_sim.simulator.ruleset import Ruleset


def test_chip_windows(rules):
    entitlements = list(rules.rules.chip_entitlements)
    # attach ids
    for i, row in enumerate(entitlements):
        row = dict(row)
        row["id"] = str(i)
        row["used_gw"] = None
        entitlements[i] = row

    wc_gw1 = rules.validate_chip("wildcard", 1, entitlements, None)
    assert not wc_gw1.accepted

    tc_gw1 = rules.validate_chip("3xc", 1, entitlements, None)
    assert tc_gw1.accepted

    wc_gw2 = rules.validate_chip("wildcard", 2, entitlements, None)
    assert wc_gw2.accepted

    fh_gw20 = rules.validate_chip("freehit", 20, entitlements, None)
    assert fh_gw20.accepted

    first_half_tc = rules.validate_chip("3xc", 25, entitlements, None)
    # second-half TC should be eligible
    assert first_half_tc.accepted


def test_one_chip_per_gw(rules):
    entitlements = [{**row, "id": str(i), "used_gw": None} for i, row in enumerate(rules.rules.chip_entitlements)]
    result = rules.validate_chip("bboost", 3, entitlements, already_selected="3xc")
    assert not result.accepted


def test_used_chip_not_reused():
    chip = {"chip_type": "3xc", "available_from_gw": 1, "expires_after_gw": 19, "used_gw": 2}
    assert not chip_is_eligible(chip, 3)


def test_ruleset_has_eight_entitlements():
    rules = Ruleset.load()
    assert len(rules.chip_entitlements) == 8
