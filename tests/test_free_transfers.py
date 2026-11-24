from fpl_sim.simulator.pricing import next_free_transfers, transfer_hit


def test_ft_cap_is_five():
    assert next_free_transfers(5, 1, 5) == 5
    assert next_free_transfers(4, 1, 5) == 5
    assert next_free_transfers(0, 1, 5) == 1


def test_hit_never_positive():
    _, hit, remaining = transfer_hit(0, 5)
    assert hit == 0
    assert remaining == 5
    _, hit, remaining = transfer_hit(6, 5, -4)
    assert hit == -4
    assert remaining == 0
