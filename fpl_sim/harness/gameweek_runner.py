from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fpl_sim.agents.cohere_agent import CohereAgent
from fpl_sim.harness.context_builder import build_gameweek_brief, build_system_prompt, load_skill
from fpl_sim.harness.reports import format_decision_report, format_result_report, format_squad_table
from fpl_sim.paths import data_dir, repo_root
from fpl_sim.simulator.pricing import team_value_tenths
from fpl_sim.simulator.rules import FPLRulesEngine
from fpl_sim.simulator.ruleset import Ruleset
from fpl_sim.simulator.scoring import score_gameweek
from fpl_sim.simulator.state_transition import accrue_free_transfers, members_from_ids, refresh_selling_prices
from fpl_sim.storage.memory import InMemoryStore
from fpl_sim.storage.protocol import ManagerStore
from fpl_sim.tools.context import ToolContext
from fpl_sim.tools.schemas import CORE_V1, EXTENDED
from fpl_sim.tracking.mlflow_tracker import MLflowTracker, load_yaml
from fpl_sim.tracking.tracing import parent_span, set_outputs, span_trace_id
from fpl_sim.types import PendingDecision, SessionStats, SquadMember, tenths_to_millions
from fpl_sim.world.context import WorldContext
from fpl_sim.world.historical_csv_world import HistoricalCSVWorld
from fpl_sim.world.repository import FPLWorldRepository


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Simulation:
    config: dict[str, Any]
    rules: FPLRulesEngine
    repo: FPLWorldRepository
    store: ManagerStore
    tracker: MLflowTracker
    agent: Any
    simulation_id: str | None = None
    last_decision_text: str = ""
    last_result_text: str = ""
    last_result: dict[str, Any] | None = None
    _permanent_player_ids: list[int] = field(default_factory=list)
    _permanent_purchase_prices: dict[int, int] = field(default_factory=dict)
    _permanent_bank_tenths: int = 0

    @classmethod
    def from_config(
        cls,
        path: str | Path = "configs/baseline.yaml",
        store: ManagerStore | None = None,
        agent: Any = None,
        start_mlflow: bool = True,
    ) -> Simulation:
        config = load_yaml(path)
        ruleset = Ruleset.load(config.get("simulation", {}).get("ruleset_path"))
        rules = FPLRulesEngine(ruleset)
        world = HistoricalCSVWorld(
            root=data_dir(),
            dataset_version=str(config.get("world", {}).get("dataset_version", "v1")),
        )
        repo = FPLWorldRepository(world, WorldContext(season=config["simulation"]["season"], current_gw=1))
        resolved_store = store
        if resolved_store is None:
            try:
                from fpl_sim.storage.supabase import SupabaseStore

                resolved_store = SupabaseStore()
            except Exception:
                resolved_store = InMemoryStore()
        tracker = MLflowTracker()
        if start_mlflow:
            tracker.start(config)
            tracker.log_artifacts(
                [
                    repo_root() / "configs" / "baseline.yaml",
                    repo_root() / "skills" / "baseline" / "SKILL.md",
                    repo_root() / "configs" / "rules" / "fpl_2025_26.yaml",
                ]
            )
        tool_set = config.get("tools", {}).get("set", "core_v1")
        tool_names = EXTENDED if tool_set == "extended_v1" else CORE_V1
        if agent is None:
            model = config["model"]
            limits = config.get("agent", {})
            agent = CohereAgent(
                model=model["name"],
                temperature=float(model.get("temperature", 0.3)),
                seed=model.get("seed"),
                max_tool_calls=int(limits.get("max_tool_calls_per_gw", 40)),
                max_turns=int(limits.get("max_turns_per_gw", 40)),
                tool_names=tool_names,
            )
        return cls(
            config=config,
            rules=rules,
            repo=repo,
            store=resolved_store,
            tracker=tracker,
            agent=agent,
        )

    @property
    def current_gw(self) -> int:
        if not self.simulation_id:
            return 1
        sim = self.store.get_simulation(self.simulation_id)
        return int(sim["current_gw"]) if sim else 1

    def select_initial_team(self) -> str:
        self.repo.set_context(WorldContext(season=self._season(), current_gw=1, phase="pre_deadline"))
        sim = self.store.create_simulation(
            name=self.config["simulation"].get("name", "simulation"),
            season=self._season(),
            mode=self.config["simulation"].get("mode", "historical"),
            config_name=self.config.get("experiment", {}).get("name", "baseline"),
            mlflow_run_id=self.tracker.run_id,
            current_gw=1,
            chip_entitlements=self.rules.rules.chip_entitlements,
        )
        self.simulation_id = sim["id"]
        self.tracker.set_tags({"simulation_id": self.simulation_id})
        self.store.upsert_gameweek(
            self.simulation_id,
            1,
            status="in_progress",
            bank=100.0,
            free_transfers=self.rules.rules.gw1_free_transfers,
            points_before=0,
            transfer_hit=0,
        )
        pending = PendingDecision()
        stats = SessionStats()
        manager_state = {
            "bank_tenths": self.rules.rules.initial_budget_tenths,
            "free_transfers": self.rules.rules.gw1_free_transfers,
            "total_points": 0,
            "player_ids": [],
            "purchase_prices": {},
        }
        ctx = ToolContext(
            repo=self.repo,
            rules=self.rules,
            pending=pending,
            stats=stats,
            manager_state=manager_state,
            entitlements=self.store.list_chips(self.simulation_id),
            gw1=True,
        )
        brief = build_gameweek_brief(
            self.repo,
            gw1=True,
            bank_tenths=manager_state["bank_tenths"],
            free_transfers=0,
            total_points=0,
            squad_ids=None,
            previous=None,
        )
        trace_id = None
        with parent_span(
            "select_initial_team",
            inputs={"gameweek": 1},
            attributes={"gameweek": 1},
        ) as gw_span:
            result = self.agent.run(
                self._system_prompt(),
                brief,
                ctx,
                metadata={"gameweek": 1, "phase": "select_initial_team"},
            )
            trace_id = span_trace_id(gw_span)
            set_outputs(gw_span, {"locked": ctx.finalized, "tool_calls": ctx.stats.tool_calls})
        if not ctx.finalized:
            last = (result.get("text") or "").strip()
            raise RuntimeError(
                "Agent did not lock GW1 with submit_lineup, so no squad was saved. "
                f"turns={ctx.stats.turns} tool_calls={ctx.stats.tool_calls} "
                f"invalid_actions={ctx.stats.invalid_actions} "
                f"pending_players={ctx.pending.player_ids} "
                f"last_text={last[:500]!r}. "
                "Check the Databricks Traces tab for this run."
            )
        self._lock_pending(gw=1, ctx=ctx, points_before=0, available_fts=0, trace_id=trace_id)
        self.last_decision_text = format_decision_report(1, pending, self.repo.current_player_map())
        self.tracker.log_metrics(
            {
                "tool_calls": stats.tool_calls,
                "invalid_actions": stats.invalid_actions,
                "tool_errors": stats.tool_errors,
                "input_tokens": stats.input_tokens,
                "output_tokens": stats.output_tokens,
                "latency_ms": stats.latency_ms,
            },
            step=1,
        )
        return self.last_decision_text

    def resolve_current(self) -> str:
        if not self.simulation_id:
            raise RuntimeError("No simulation. Run select_initial_team() first.")
        gw = self.current_gw
        row = self.store.get_gameweek(self.simulation_id, gw)
        if not row or row["status"] != "locked":
            raise RuntimeError(f"GW{gw} is not locked.")
        self.repo.set_context(WorldContext(season=self._season(), current_gw=gw, phase="post_gameweek"))
        squad = self.store.list_squad(row["id"])
        players = self.repo.current_player_map()
        starters = [p["player_id"] for p in squad if p["is_starter"]]
        bench = [p["player_id"] for p in sorted(
            [x for x in squad if x.get("bench_order")], key=lambda x: x["bench_order"]
        )]
        reserve = next(p["player_id"] for p in squad if not p["is_starter"] and p.get("bench_order") is None)
        captain = next(p["player_id"] for p in squad if p["is_captain"])
        vice = next(p["player_id"] for p in squad if p["is_vice_captain"])
        chip = None
        if row.get("active_chip_entitlement_id"):
            chips = {c["id"]: c for c in self.store.list_chips(self.simulation_id)}
            chip = chips.get(row["active_chip_entitlement_id"], {}).get("chip_type")
        perf = self.repo.gw_performance_map(gw)
        minutes = {pid: int(perf.get(pid, {}).get("minutes", 0)) for pid in [p["player_id"] for p in squad]}
        raw = {pid: int(perf.get(pid, {}).get("total_points", 0)) for pid in [p["player_id"] for p in squad]}
        scored = score_gameweek(
            [p["player_id"] for p in squad],
            starters,
            bench,
            reserve,
            captain,
            vice,
            chip,
            minutes,
            raw,
            players,
            self.rules.rules,
        )
        hit = int(row.get("transfer_hit") or 0)
        net = scored.gross_points + hit
        total_after = int(row.get("points_before") or 0) + net
        self.store.replace_player_points(
            row["id"],
            [
                {
                    "player_id": s.player_id,
                    "raw_points": s.raw_points,
                    "multiplier": s.multiplier,
                    "counted_points": s.counted_points,
                    "started": s.started,
                    "bench_order": s.bench_order,
                    "auto_subbed_in": s.auto_subbed_in,
                    "auto_subbed_out": s.auto_subbed_out,
                }
                for s in scored.scores
            ],
        )
        self.store.upsert_gameweek(
            self.simulation_id,
            gw,
            status="completed",
            gross_points=scored.gross_points,
            net_points=net,
            total_points_after=total_after,
            resolved_at=_utcnow(),
        )
        self.store.update_simulation(self.simulation_id, total_points=total_after)
        awards = self.repo.awards_for_gw(gw) or {}
        cap_name = None
        if scored.captain_id and scored.captain_id in players:
            cap_name = players[scored.captain_id].web_name
        self.last_result = {
            "gw": gw,
            "gross_points": scored.gross_points,
            "transfer_hit": hit,
            "net_points": net,
            "fpl_average": awards.get("average_manager_score"),
            "fpl_highest": awards.get("highest_manager_score"),
            "captain_name": cap_name,
            "captain_contribution": scored.captain_contribution,
            "bench_points": scored.bench_points,
            "season_total": total_after,
            "chip": chip,
        }
        self.last_result_text = format_result_report(
            gw,
            gross=scored.gross_points,
            hit=hit,
            net=net,
            fpl_average=awards.get("average_manager_score"),
            fpl_highest=awards.get("highest_manager_score"),
            season_total=total_after,
            captain_name=cap_name,
            captain_contribution=scored.captain_contribution,
            bench_points=scored.bench_points,
        )
        self.tracker.log_metrics(
            {
                "gw_points": net,
                "gross_points": scored.gross_points,
                "transfer_hit": hit,
                "captain_points": scored.captain_contribution,
                "bench_points": scored.bench_points,
                "total_points": total_after,
            },
            step=gw,
        )
        if gw >= 38:
            self.store.update_simulation(
                self.simulation_id, status="completed", completed_at=_utcnow()
            )
            self.tracker.end()
        return self.last_result_text

    def lock_next(self) -> str:
        if not self.simulation_id:
            raise RuntimeError("No simulation. Run select_initial_team() first.")
        completed_gw = self.current_gw
        done = self.store.get_gameweek(self.simulation_id, completed_gw)
        if not done or done["status"] != "completed":
            raise RuntimeError(f"Resolve GW{completed_gw} before locking the next Gameweek.")
        if completed_gw >= 38:
            return "Season complete. No GW39."
        next_gw = completed_gw + 1
        self.repo.set_context(WorldContext(season=self._season(), current_gw=next_gw, phase="pre_deadline"))
        prev_chip = None
        if done.get("active_chip_entitlement_id"):
            chips = {c["id"]: c for c in self.store.list_chips(self.simulation_id)}
            prev_chip = chips.get(done["active_chip_entitlement_id"], {}).get("chip_type")
        if prev_chip == "freehit":
            start_ids = list(self._permanent_player_ids)
            purchases = dict(self._permanent_purchase_prices)
            bank = int(self._permanent_bank_tenths)
        else:
            prev_squad = self.store.list_squad(done["id"])
            start_ids = [p["player_id"] for p in prev_squad]
            purchases = {
                p["player_id"]: int(round(float(p["purchase_price"]) * 10)) for p in prev_squad
            }
            bank = int(round(float(done["bank"]) * 10))
        stored_fts = int(done.get("free_transfers") or 0)
        available_fts = accrue_free_transfers(stored_fts, self.rules.rules, prev_chip)
        players = self.repo.current_player_map()
        members = members_from_ids(start_ids, players, purchases)
        members = refresh_selling_prices(members, players)
        team_value = team_value_tenths([m.selling_price_tenths for m in members], bank)
        self.store.upsert_gameweek(
            self.simulation_id,
            next_gw,
            status="in_progress",
            bank=tenths_to_millions(bank),
            free_transfers=available_fts,
            team_value=tenths_to_millions(team_value),
            points_before=int(done.get("total_points_after") or 0),
            transfer_hit=0,
        )
        pending = PendingDecision(player_ids=list(start_ids))
        stats = SessionStats()
        manager_state = {
            "bank_tenths": bank,
            "free_transfers": available_fts,
            "team_value_tenths": team_value,
            "total_points": int(done.get("total_points_after") or 0),
            "player_ids": list(start_ids),
            "purchase_prices": purchases,
        }
        ctx = ToolContext(
            repo=self.repo,
            rules=self.rules,
            pending=pending,
            stats=stats,
            manager_state=manager_state,
            entitlements=self.store.list_chips(self.simulation_id),
            gw1=False,
        )
        brief = build_gameweek_brief(
            self.repo,
            gw1=False,
            bank_tenths=bank,
            free_transfers=available_fts,
            total_points=int(done.get("total_points_after") or 0),
            squad_ids=start_ids,
            previous=self.last_result,
        )
        trace_id = None
        with parent_span(
            f"lock_gw{next_gw}",
            inputs={"gameweek": next_gw},
            attributes={"gameweek": next_gw},
        ) as gw_span:
            self.agent.run(
                self._system_prompt(),
                brief,
                ctx,
                metadata={"gameweek": next_gw, "phase": "lock_next"},
            )
            trace_id = span_trace_id(gw_span)
            set_outputs(gw_span, {"locked": ctx.finalized, "tool_calls": ctx.stats.tool_calls})
        if not ctx.finalized:
            raise RuntimeError(f"Agent did not lock GW{next_gw} with submit_lineup. Nothing was saved.")
        self._lock_pending(
            gw=next_gw,
            ctx=ctx,
            points_before=int(done.get("total_points_after") or 0),
            available_fts=available_fts,
            trace_id=trace_id,
        )
        hit = 0
        locked = self.store.get_gameweek(self.simulation_id, next_gw)
        if locked:
            hit = int(locked.get("transfer_hit") or 0)
        self.last_decision_text = format_decision_report(
            next_gw, pending, self.repo.current_player_map(), transfer_hit=hit
        )
        self.tracker.log_metrics(
            {
                "tool_calls": stats.tool_calls,
                "invalid_actions": stats.invalid_actions,
                "tool_errors": stats.tool_errors,
                "input_tokens": stats.input_tokens,
                "output_tokens": stats.output_tokens,
                "latency_ms": stats.latency_ms,
            },
            step=next_gw,
        )
        return self.last_decision_text

    def advance(self) -> str:
        result = self.resolve_current()
        if self.current_gw >= 38:
            return result
        completed = self.store.get_gameweek(self.simulation_id, self.current_gw)
        if completed and completed["status"] == "completed" and self.current_gw >= 38:
            return result
        # current_gw still points at the GW we just resolved until lock_next updates it
        resolved_gw = completed["gw"] if completed else self.current_gw
        if resolved_gw >= 38:
            return result
        decision = self.lock_next()
        return f"{result}\n\n{decision}"

    def run_season(self) -> str:
        reports = [self.select_initial_team()]
        while True:
            reports.append(self.advance())
            if self.store.get_simulation(self.simulation_id)["status"] == "completed":
                break
        return "\n\n".join(reports)

    def _lock_pending(
        self,
        gw: int,
        ctx: ToolContext,
        points_before: int,
        available_fts: int,
        trace_id: str | None = None,
    ) -> None:
        pending = ctx.pending
        players = self.repo.current_player_map()
        purchases = dict(ctx.manager_state.get("draft_purchase_prices") or ctx.manager_state.get("purchase_prices") or {})
        if not purchases:
            purchases = {pid: players[pid].now_cost for pid in pending.player_ids or []}
        bank = int(ctx.manager_state.get("draft_bank_tenths") or ctx.manager_state.get("bank_tenths") or 0)
        chip_id = None
        if pending.chip_type:
            match = next(
                (
                    c
                    for c in self.store.list_chips(self.simulation_id)
                    if c["chip_type"] == pending.chip_type and c.get("used_gw") is None
                    and int(c["available_from_gw"]) <= gw <= int(c["expires_after_gw"])
                ),
                None,
            )
            if match:
                chip_id = match["id"]
                self.store.mark_chip_used(chip_id, gw)
        hit = 0
        remaining_fts = available_fts
        if pending.transfers:
            priced = self.rules.validate_transfers(
                list(ctx.manager_state.get("player_ids") or pending.player_ids),
                pending.transfers,
                players,
                dict(ctx.manager_state.get("purchase_prices") or purchases),
                int(ctx.manager_state.get("bank_tenths") or bank),
                available_fts,
                pending.chip_type,
            )
            if not priced.accepted:
                raise RuntimeError(f"Transfers became invalid at lock: {priced.errors}")
            hit = int(priced.data["transfer_hit"])
            remaining_fts = int(priced.data["remaining_fts"])
            bank = int(priced.data["bank_tenths"])
            purchases = priced.data["purchase_prices"]
            self.store.add_transfers(
                self.store.get_gameweek(self.simulation_id, gw)["id"],
                [
                    {
                        "player_out_id": m["player_out_id"],
                        "player_in_id": m["player_in_id"],
                        "sell_price": tenths_to_millions(m["sell_price_tenths"]),
                        "buy_price": tenths_to_millions(m["buy_price_tenths"]),
                    }
                    for m in priced.data["moves"]
                ],
            )
        members = members_from_ids(
            pending.player_ids,
            players,
            purchases,
            pending.starters,
            pending.bench_outfield,
            pending.reserve_gk,
            pending.captain_id,
            pending.vice_captain_id,
        )
        value = team_value_tenths([m.selling_price_tenths for m in members], bank)
        gw_row = self.store.get_gameweek(self.simulation_id, gw)
        self.store.replace_squad(
            gw_row["id"],
            [
                {
                    "player_id": m.player_id,
                    "purchase_price": tenths_to_millions(m.purchase_price_tenths),
                    "selling_price": tenths_to_millions(m.selling_price_tenths),
                    "is_starter": m.is_starter,
                    "bench_order": m.bench_order,
                    "is_captain": m.is_captain,
                    "is_vice_captain": m.is_vice_captain,
                }
                for m in members
            ],
        )
        self.store.upsert_gameweek(
            self.simulation_id,
            gw,
            status="locked",
            bank=tenths_to_millions(bank),
            free_transfers=remaining_fts,
            team_value=tenths_to_millions(value),
            points_before=points_before,
            transfer_hit=hit,
            active_chip_entitlement_id=chip_id,
            mlflow_trace_id=trace_id,
            decision_locked_at=_utcnow(),
        )
        self.store.update_simulation(self.simulation_id, current_gw=gw)
        if pending.chip_type != "freehit":
            self._permanent_player_ids = list(pending.player_ids or [])
            self._permanent_purchase_prices = dict(purchases)
            self._permanent_bank_tenths = bank

    def squad_report(self) -> str:
        if not self.simulation_id:
            return "No simulation."
        gw = self.store.get_gameweek(self.simulation_id, self.current_gw)
        if not gw:
            return "No gameweek."
        squad = self.store.list_squad(gw["id"])
        members = [
            SquadMember(
                player_id=p["player_id"],
                purchase_price_tenths=int(round(float(p["purchase_price"]) * 10)),
                selling_price_tenths=int(round(float(p["selling_price"]) * 10)),
                is_starter=p["is_starter"],
                bench_order=p.get("bench_order"),
                is_captain=p["is_captain"],
                is_vice_captain=p["is_vice_captain"],
            )
            for p in squad
        ]
        return format_squad_table(members, self.repo.current_player_map())

    def _season(self) -> str:
        return self.config["simulation"]["season"]

    def _system_prompt(self) -> str:
        skill_cfg = self.config.get("skill", {})
        text = ""
        if skill_cfg.get("enabled", True):
            text = load_skill(skill_cfg.get("path"))
        return build_system_prompt(text)
