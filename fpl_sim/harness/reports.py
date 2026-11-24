from __future__ import annotations

import html
from typing import Any

from fpl_sim.types import tenths_to_millions

_CLUB_COLOURS = {
    "Arsenal": "#ef0107",
    "Aston Villa": "#670e36",
    "Bournemouth": "#da291c",
    "Brentford": "#e30613",
    "Brighton": "#0057b8",
    "Burnley": "#6c1d45",
    "Chelsea": "#034694",
    "Crystal Palace": "#1b458f",
    "Everton": "#003399",
    "Fulham": "#000000",
    "Leeds": "#1d428a",
    "Liverpool": "#c8102e",
    "Man City": "#6cabdd",
    "Man Utd": "#da291c",
    "Newcastle": "#241f20",
    "Nott'm Forest": "#dd0000",
    "Sunderland": "#eb172b",
    "Spurs": "#132257",
    "West Ham": "#7a263a",
    "Wolves": "#fdb913",
}


def _esc(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def _kit_colour(team_name: str) -> str:
    return _CLUB_COLOURS.get(team_name, "#1f3d2b")


def format_decision_report(gw: int, pending, players: dict, transfer_hit: int = 0) -> str:
    transfers = []
    for move in pending.transfers:
        out_p = players.get(move.player_out_id)
        in_p = players.get(move.player_in_id)
        out_n = out_p.web_name if out_p else move.player_out_id
        in_n = in_p.web_name if in_p else move.player_in_id
        transfers.append(f"{out_n} -> {in_n}")
    cap = players.get(pending.captain_id)
    vice = players.get(pending.vice_captain_id)
    lines = [
        f"GW{gw} DECISION",
        "",
        "Transfers:",
        ("\n".join(transfers) if transfers else "None"),
        "",
        f"Chip:\n{pending.chip_type or 'None'}",
        "",
        f"Captain:\n{cap.web_name if cap else pending.captain_id}",
        f"Vice:\n{vice.web_name if vice else pending.vice_captain_id}",
    ]
    if transfer_hit:
        lines.insert(5, f"Transfer hit: {transfer_hit}")
    return "\n".join(lines)


def format_result_report(
    gw: int,
    *,
    gross: int,
    hit: int,
    net: int,
    fpl_average: int | None,
    fpl_highest: int | None,
    season_total: int,
    captain_name: str | None,
    captain_contribution: int,
    bench_points: int,
) -> str:
    return "\n".join(
        [
            f"GW{gw} RESULT",
            "",
            f"Gross points:       {gross}",
            f"Transfer hit:       {hit}",
            f"Net points:         {net}",
            f"FPL average:        {fpl_average}",
            f"Highest:            {fpl_highest}",
            f"Season total:       {season_total}",
            "",
            f"Captain: {captain_name}",
            f"Captain contribution: {captain_contribution}",
            "",
            f"Bench points: {bench_points}",
        ]
    )


def format_squad_table(members, players: dict) -> str:
    lines = []
    for member in members:
        player = players.get(member.player_id)
        if not player:
            continue
        role = "XI"
        if member.is_captain:
            role = "C"
        elif member.is_vice_captain:
            role = "VC"
        elif not member.is_starter:
            role = f"B{member.bench_order}" if member.bench_order else "GK2"
        lines.append(
            f"{role:3} {player.web_name:16} {player.position:3} {player.team_name:12} "
            f"£{tenths_to_millions(member.selling_price_tenths):.1f}m"
        )
    return "\n".join(lines)


def gw_opponent_labels(repo: Any, gw: int) -> dict[int, str]:
    """Map club id -> 'vs Opponent (H/A)' for fixtures assigned to this Gameweek."""
    by_team: dict[int, list[str]] = {}
    for fx in repo.current_fixtures():
        assigned = fx.get("assigned_gw")
        if assigned in (None, ""):
            continue
        if int(assigned) != int(gw):
            continue
        home_id = int(fx.get("home_team_id") or 0)
        away_id = int(fx.get("away_team_id") or 0)
        home_n = str(fx.get("home_team_name") or "Home")
        away_n = str(fx.get("away_team_name") or "Away")
        by_team.setdefault(home_id, []).append(f"vs {away_n} (H)")
        by_team.setdefault(away_id, []).append(f"vs {home_n} (A)")
    return {tid: " / ".join(parts) for tid, parts in by_team.items()}


_CHIP_SHORT = {"wildcard": "WC", "freehit": "FH", "bboost": "BB", "3xc": "TC"}


def _player_point_rows(store: Any, manager_gameweek_id: str) -> list[dict[str, Any]]:
    getter = getattr(store, "list_player_points", None)
    if callable(getter):
        return getter(manager_gameweek_id) or []
    client = getattr(store, "client", None)
    if client is None:
        return []
    return (
        client.table("player_points")
        .select("*")
        .eq("manager_gameweek_id", manager_gameweek_id)
        .execute()
        .data
        or []
    )


def counted_points_from_store(store: Any, manager_gameweek_id: str) -> dict[int, int]:
    """Points for the pitch view.

    Starters (and auto-subs / chips) use counted_points, which already applies
    captain / triple-captain. Unused bench still shows raw_points — FPL does that
    on the pitch even though those points do not add to the manager score.
    """
    rows = _player_point_rows(store, manager_gameweek_id)
    out: dict[int, int] = {}
    for r in rows:
        pid = int(r["player_id"])
        counted = int(r.get("counted_points") or 0)
        raw = int(r.get("raw_points") or 0)
        multiplier = int(r.get("multiplier") or 0)
        out[pid] = counted if multiplier else raw
    return out


def _active_chip_type(store: Any, simulation_id: str, gw_row: dict[str, Any]) -> str | None:
    chip_id = gw_row.get("active_chip_entitlement_id")
    if not chip_id:
        return None
    chips = {c["id"]: c for c in store.list_chips(simulation_id)}
    row = chips.get(chip_id)
    return None if row is None else str(row.get("chip_type"))


def _chip_strip_html(chips: list[dict[str, Any]], gw: int, active_chip: str | None) -> str:
    pills = []
    marked_on = False
    for c in chips:
        short = _CHIP_SHORT.get(str(c.get("chip_type")), str(c.get("chip_type")))
        start = int(c["available_from_gw"])
        end = int(c["expires_after_gw"])
        used = c.get("used_gw")
        ctype = c.get("chip_type")
        label = f"{short} {start}–{end}"
        on = False
        if used not in (None, "") and int(used) == int(gw):
            on = True
        elif (
            not marked_on
            and active_chip == ctype
            and used in (None, "")
            and start <= int(gw) <= end
        ):
            on = True
            marked_on = True
        if on:
            klass = "fpl-chip fpl-chip-on"
            label += " · ON"
            marked_on = True
        elif used not in (None, ""):
            klass = "fpl-chip fpl-chip-used"
            label += f" · GW{int(used)}"
        elif start <= int(gw) <= end:
            klass = "fpl-chip fpl-chip-ready"
        else:
            klass = "fpl-chip fpl-chip-later"
        pills.append(f'<span class="{klass}">{_esc(label)}</span>')
    return f'<div class="fpl-chips">{"".join(pills)}</div>'


def _autosub_notes(rows: list[dict[str, Any]], players: dict) -> dict[int, str]:
    ins = [int(r["player_id"]) for r in rows if r.get("auto_subbed_in")]
    outs = [int(r["player_id"]) for r in rows if r.get("auto_subbed_out")]
    notes: dict[int, str] = {}
    for out_id, in_id in zip(outs, ins):
        in_p = players.get(in_id)
        out_p = players.get(out_id)
        in_n = in_p.web_name if in_p else str(in_id)
        out_n = out_p.web_name if out_p else str(out_id)
        notes[in_id] = f"▲ in for {out_n}"
        notes[out_id] = f"▼ out → {in_n}"
    for pid in ins:
        notes.setdefault(pid, "▲ auto-sub in")
    for pid in outs:
        notes.setdefault(pid, "▼ auto-sub out")
    return notes


def simulation_squad_pitch_html(sim: Any) -> str:
    gw_row = sim.store.get_gameweek(sim.simulation_id, sim.current_gw)
    squad = sim.store.list_squad(gw_row["id"])
    players = sim.repo.current_player_map()
    gw = int(gw_row["gw"])
    active = _active_chip_type(sim.store, sim.simulation_id, gw_row)
    return format_squad_pitch_html(
        squad,
        players,
        bank=gw_row.get("bank"),
        team_value=gw_row.get("team_value"),
        gw=gw,
        opponents_by_team=gw_opponent_labels(sim.repo, gw),
        title=f"GW{gw} locked squad",
        chips=sim.store.list_chips(sim.simulation_id),
        active_chip=active,
        bench_boost=active == "bboost",
    )


def simulation_result_pitch_html(sim: Any) -> str:
    gw_row = sim.store.get_gameweek(sim.simulation_id, sim.current_gw)
    squad = sim.store.list_squad(gw_row["id"])
    players = sim.repo.current_player_map()
    gw = int(gw_row["gw"])
    rows = _player_point_rows(sim.store, gw_row["id"])
    active = _active_chip_type(sim.store, sim.simulation_id, gw_row)
    multipliers = {int(r["player_id"]): int(r.get("multiplier") or 0) for r in rows}
    return format_squad_pitch_html(
        squad,
        players,
        bank=gw_row.get("bank"),
        team_value=gw_row.get("team_value"),
        gw=gw,
        opponents_by_team=gw_opponent_labels(sim.repo, gw),
        points_by_player=counted_points_from_store(sim.store, gw_row["id"]),
        title=f"GW{gw} result",
        gross_points=gw_row.get("gross_points"),
        transfer_hit=gw_row.get("transfer_hit"),
        net_points=gw_row.get("net_points"),
        chips=sim.store.list_chips(sim.simulation_id),
        active_chip=active,
        multipliers_by_player=multipliers,
        autosub_notes=_autosub_notes(rows, players),
        bench_boost=active == "bboost",
    )


def format_squad_pitch_html(
    squad: list[dict[str, Any]],
    players: dict,
    *,
    bank: float | None,
    team_value: float | None = None,
    gw: int | None = None,
    opponents_by_team: dict[int, str] | None = None,
    points_by_player: dict[int, int] | None = None,
    title: str | None = None,
    gross_points: int | None = None,
    transfer_hit: int | None = None,
    net_points: int | None = None,
    chips: list[dict[str, Any]] | None = None,
    active_chip: str | None = None,
    multipliers_by_player: dict[int, int] | None = None,
    autosub_notes: dict[int, str] | None = None,
    bench_boost: bool = False,
) -> str:
    """FPL-style pitch + bench. Card value is selling price; header shows remaining bank."""
    starters = [p for p in squad if p.get("is_starter")]
    reserve = next((p for p in squad if not p.get("is_starter") and p.get("bench_order") is None), None)
    bench_out = sorted(
        [p for p in squad if p.get("bench_order")],
        key=lambda p: int(p["bench_order"]),
    )
    opp_map = opponents_by_team or {}
    pts_map = points_by_player or {}
    mult_map = multipliers_by_player or {}
    sub_map = autosub_notes or {}
    scored = points_by_player is not None

    def _card(row: dict[str, Any] | None, *, bench_label: str | None = None) -> str:
        if row is None:
            return '<div class="fpl-card fpl-empty"></div>'
        pid = int(row["player_id"])
        player = players.get(pid)
        name = player.web_name if player else str(pid)
        team = player.team_name if player else ""
        pos = player.position if player else ""
        team_id = int(player.team_id) if player else 0
        sell = float(row.get("selling_price") or 0)
        opp = opp_map.get(team_id) or "Blank"
        badges = ""
        cap_mult = int(mult_map.get(pid, 0) or 0)
        if row.get("is_captain") or cap_mult >= 2:
            badges += (
                '<span class="fpl-badge fpl-tc">TC</span>'
                if active_chip == "3xc" and cap_mult >= 3
                else '<span class="fpl-badge fpl-c">C</span>'
            )
        if row.get("is_vice_captain") and cap_mult < 2:
            badges += '<span class="fpl-badge fpl-v">V</span>'
        label = f'<div class="fpl-slot">{_esc(bench_label)}</div>' if bench_label else ""
        under = f'<div class="fpl-opp">{_esc(opp)}</div>'
        if scored:
            pts = int(pts_map.get(pid, 0))
            under += f'<div class="fpl-pts">{pts} pts</div>'
        note = sub_map.get(pid)
        if note:
            under += f'<div class="fpl-sub">{_esc(note)}</div>'
        return (
            f'<div class="fpl-wrap">{label}'
            f'<div class="fpl-card" style="--kit:{_kit_colour(team)}">'
            f'<div class="fpl-shirt"><span class="fpl-club">{_esc(team)}</span>'
            f'<span class="fpl-pos">{_esc(pos)}</span></div>'
            f'{badges}'
            f'<div class="fpl-plate">'
            f'<div class="fpl-name">{_esc(name)}</div>'
            f'<div class="fpl-price">£{sell:.1f}</div>'
            f'</div></div>{under}</div>'
        )

    rows_html = []
    for pos in ("GK", "DEF", "MID", "FWD"):
        group = [
            p
            for p in starters
            if (players.get(int(p["player_id"])).position if players.get(int(p["player_id"])) else "") == pos
        ]
        if not group:
            continue
        cards = "".join(_card(p) for p in group)
        rows_html.append(f'<div class="fpl-row">{cards}</div>')

    bench_cards = [_card(reserve, bench_label="GKP")]
    labels = {1: "1.", 2: "2.", 3: "3."}
    for i, row in enumerate(bench_out, start=1):
        player = players.get(int(row["player_id"]))
        pos = player.position if player else "OUT"
        bench_cards.append(_card(row, bench_label=f"{labels.get(i, f'{i}.')} {pos}"))
    bank_txt = "—" if bank is None else f"£{float(bank):.1f}m"
    value_txt = "" if team_value is None else f'<span>TV £{float(team_value):.1f}m</span>'
    score_txt = ""
    if net_points is not None:
        hit = int(transfer_hit or 0)
        gross = int(gross_points) if gross_points is not None else int(net_points) - hit
        score_txt = f"<span>Net {int(net_points)}</span><span>Gross {gross}</span>"
        if hit:
            score_txt += f"<span>Hit {hit}</span>"
    heading = title or (f"GW{gw} locked squad" if gw else "Locked squad")
    chip_html = _chip_strip_html(chips or [], int(gw or 0), active_chip) if chips else ""
    if active_chip:
        chip_name = _CHIP_SHORT.get(active_chip, active_chip)
        heading = f"{heading} · {chip_name}"
    bench_class = "fpl-bench fpl-bb" if bench_boost else "fpl-bench"
    return f"""
<style>
.fpl-pitch-root {{font-family: Inter, system-ui, sans-serif; color:#fff; max-width:820px;}}
.fpl-bar {{display:flex; justify-content:space-between; align-items:center; background:linear-gradient(90deg,#00ff87,#00e0ff); color:#37003c; padding:10px 16px; border-radius:12px 12px 0 0; font-weight:800;}}
.fpl-bar small {{font-weight:700; opacity:.85;}}
.fpl-meta {{display:flex; gap:16px;}}
.fpl-field {{background:linear-gradient(#1f8a3b,#157a32 55%,#0f6a2a); padding:22px 12px 18px; display:flex; flex-direction:column; gap:18px;}}
.fpl-row {{display:flex; justify-content:center; gap:18px; flex-wrap:wrap;}}
.fpl-chips {{display:flex; flex-wrap:wrap; gap:8px; padding:10px 12px; background:#2a0a3d;}}
.fpl-chip {{font-size:11px; font-weight:800; padding:4px 8px; border-radius:999px; background:#4a2a5a; color:#eee;}}
.fpl-chip-ready {{background:#204a38; color:#b6ffd4;}}
.fpl-chip-on {{background:#00ff87; color:#37003c;}}
.fpl-chip-used {{background:#3a3a3a; color:#aaa; text-decoration:line-through;}}
.fpl-chip-later {{background:#241535; color:#8877aa;}}
.fpl-bench {{background:#e8eef2; color:#37003c; padding:14px 12px 18px; border-radius:0 0 12px 12px; display:flex; justify-content:center; gap:16px; flex-wrap:wrap;}}
.fpl-bb {{background:#fff4cc; box-shadow:inset 0 0 0 3px #f5c400;}}
.fpl-bb::before {{content:"BENCH BOOST"; display:block; width:100%; text-align:center; font-size:11px; font-weight:900; letter-spacing:.08em; color:#8a6a00; margin-bottom:8px;}}
.fpl-wrap {{width:122px; text-align:center;}}
.fpl-slot {{font-size:11px; font-weight:800; letter-spacing:.04em; margin-bottom:6px; color:#5a2a6a;}}
.fpl-card {{position:relative; width:122px;}}
.fpl-shirt {{min-height:58px; border-radius:10px 10px 0 0; background:var(--kit,#1f3d2b); display:flex; flex-direction:column; align-items:center; justify-content:flex-end; gap:2px; padding:8px 4px 6px; font-weight:800; text-shadow:0 1px 2px #0008;}}
.fpl-club {{font-size:9px; line-height:1.1; max-width:114px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; opacity:.95; color:#fff;}}
.fpl-pos {{font-size:11px; letter-spacing:.04em; color:#fff;}}
.fpl-bench .fpl-club, .fpl-bench .fpl-pos {{color:#fff;}}
.fpl-plate {{background:#fff; color:#25003a; border-radius:0 0 10px 10px; padding:6px 6px 8px; box-shadow:0 6px 14px #0003;}}
.fpl-name {{font-size:12px; font-weight:800; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}}
.fpl-price {{font-size:12px; font-weight:700; color:#37003c;}}
.fpl-opp {{margin-top:6px; font-size:10px; font-weight:700; line-height:1.2; opacity:.92;}}
.fpl-field .fpl-opp {{color:#eaffea;}}
.fpl-bench .fpl-opp {{color:#5a2a6a;}}
.fpl-pts {{margin-top:2px; font-size:12px; font-weight:800;}}
.fpl-field .fpl-pts {{color:#00ff87;}}
.fpl-bench .fpl-pts {{color:#37003c;}}
.fpl-badge {{position:absolute; top:-8px; width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:11px; font-weight:900;}}
.fpl-c {{left:-6px; background:#00ff87; color:#37003c;}}
.fpl-tc {{left:-6px; background:#ffd000; color:#37003c; font-size:9px;}}
.fpl-v {{right:-6px; background:#96e6ff; color:#37003c;}}
.fpl-sub {{margin-top:2px; font-size:10px; font-weight:800;}}
.fpl-field .fpl-sub {{color:#ffe566;}}
.fpl-bench .fpl-sub {{color:#8a2a00;}}
.fpl-empty {{height:90px;}}
</style>
<div class="fpl-pitch-root">
  <div class="fpl-bar"><span>{_esc(heading)}</span><div class="fpl-meta">{score_txt}<span>Bank {_esc(bank_txt)}</span>{value_txt}</div></div>
  {chip_html}
  <div class="fpl-field">{''.join(rows_html)}</div>
  <div class="{bench_class}">{''.join(bench_cards)}</div>
</div>
"""
