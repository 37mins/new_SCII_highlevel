import json
import tempfile
import unittest
from pathlib import Path

from agent_system.memory.sc2_long_loop_memory import SC2LongLoopMemory


class SC2LongLoopMemoryTest(unittest.TestCase):
    def resource_targets(self):
        return {
            "recommended_mineral_collection_rate": "600 minerals/min",
            "recommended_vespene_collection_rate": "120 vespene/min",
            "recommended_mineral_utilization": "75%",
            "recommended_vespene_utilization": "50%",
            "recommended_total_supply_growth_rate": "12 supply/min",
        }

    def test_completed_rollout_updates_persists_and_retrieves_memory(self):
        response = {
            "resource_memory": self.resource_targets(),
            "army_memory": [{
                "opponent_units": ["Siege Tank"],
                "counters": ["Viking"],
                "fallback": "Build a Starport",
                "rationale": "Attack from the air",
            }],
        }

        with tempfile.TemporaryDirectory() as directory:
            memory_path = Path(directory) / "long_loop_memory.json"
            memory = SC2LongLoopMemory(
                llm_generate=lambda prompt: response,
                memory_path=str(memory_path),
            )
            memory.reset(batch_size=1)
            memory.store({
                "done": [False],
                "won": [False],
                "truncated": [False],
                "telemetry": [{
                    "game_time_seconds": 60,
                    "cumulative_minerals_collected": 500,
                    "cumulative_vespene_collected": 80,
                    "cumulative_minerals_spent": 350,
                    "cumulative_vespene_spent": 40,
                    "supply_used": 12,
                    "visible_enemy_units": {"Siege Tank": 1},
                }],
            })
            memory.store({
                "done": [True],
                "won": [True],
                "truncated": [False],
                "telemetry": [{
                    "game_time_seconds": 120,
                    "cumulative_minerals_collected": 1000,
                    "cumulative_vespene_collected": 160,
                    "cumulative_minerals_spent": 700,
                    "cumulative_vespene_spent": 80,
                    "supply_used": 25,
                    "visible_enemy_units": {"Siege Tank": 2},
                }],
            })

            updates = memory.finalize_batch()
            contexts, lengths = memory.fetch(
                history_length=0,
                current_obs=["current observation"],
                telemetry=[{
                    "game_time_seconds": 180,
                    "cumulative_minerals_collected": 1200,
                    "cumulative_vespene_collected": 240,
                    "cumulative_minerals_spent": 900,
                    "cumulative_vespene_spent": 120,
                    "supply_used": 37,
                    "visible_enemy_units": {"Siege Tank": 3},
                }],
            )

            self.assertIn("batch-1:env-0", updates)
            self.assertTrue(memory_path.is_file())
            self.assertEqual(json.loads(memory_path.read_text(encoding="utf-8")), response)
            self.assertEqual(SC2LongLoopMemory(memory_path=str(memory_path)).memory, response)
            summary_log = Path(directory) / "memory_summary_io.jsonl"
            self.assertTrue(summary_log.is_file())
            summary_entry = json.loads(summary_log.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(summary_entry["rollout_id"], "batch-1:env-0")
            self.assertEqual(summary_entry["status"], "saved")
            self.assertIn("Here is the game replay", summary_entry["prompt"])
            self.assertEqual(summary_entry["response"], response)
            self.assertIn("Mineral collection rate is 400.00", contexts[0])
            self.assertIn("Opponent detected: Siege Tank", contexts[0])
            self.assertEqual(lengths, [3])

    def test_summary_io_keeps_raw_invalid_output_and_prompt(self):
        with tempfile.TemporaryDirectory() as directory:
            memory_path = Path(directory) / "long_loop_memory.json"
            memory = SC2LongLoopMemory(memory_path=str(memory_path))
            memory.reset(batch_size=1)
            memory.store({
                "done": [True], "won": [False], "truncated": [False],
                "telemetry": [{"visible_enemy_units": {"Marine": 1}}],
            })
            with self.assertWarnsRegex(RuntimeWarning, "model output must be valid JSON"):
                memory.finalize_batch(llm_generate=lambda _: "not valid JSON response")

            log_path = Path(directory) / "memory_summary_io.jsonl"
            entry = json.loads(log_path.read_text(encoding="utf-8").splitlines()[0])
            self.assertEqual(entry["status"], "failed")
            self.assertEqual(entry["response"], "not valid JSON response")
            self.assertIn("This game has ended", entry["prompt"])
            self.assertIn("model output must be valid JSON", entry["error"])
            self.assertFalse(memory_path.exists())

    def test_resource_targets_keep_numbers_when_marked_too_low(self):
        memory = SC2LongLoopMemory()
        targets = self.resource_targets()
        targets["recommended_mineral_collection_rate"] = "600 minerals/min (too low)"
        targets["recommended_vespene_collection_rate"] = 120
        parsed = memory._parse_model_output({
            "resource_memory": targets,
            "army_memory": [],
        })
        self.assertEqual(parsed["resource_memory"]["recommended_mineral_collection_rate"], "600 minerals/min (too low)")
        self.assertEqual(parsed["resource_memory"]["recommended_vespene_collection_rate"], "120")
        targets["recommended_total_supply_growth_rate"] = "too low"
        with self.assertRaisesRegex(ValueError, "numeric target"):
            memory._parse_model_output({
                "resource_memory": targets,
                "army_memory": [],
            })

    def test_resource_memory_defaults_to_named_null_targets(self):
        memory = SC2LongLoopMemory()
        self.assertEqual(memory.resource_memory, dict.fromkeys(self.resource_targets()))

    def test_model_resource_memory_requires_exact_dictionary_keys(self):
        memory = SC2LongLoopMemory()
        missing = self.resource_targets()
        del missing["recommended_mineral_collection_rate"]
        extra = {**self.resource_targets(), "unexpected": "1"}
        renamed = self.resource_targets()
        renamed["mineral_collection_rate"] = renamed.pop("recommended_mineral_collection_rate")
        for invalid in (list(self.resource_targets().values()), missing, extra, renamed):
            with self.subTest(resource_memory=invalid):
                with self.assertRaisesRegex(ValueError, "resource_memory must"):
                    memory._parse_model_output({"resource_memory": invalid, "army_memory": []})

    def test_resource_retrieval_uses_names_not_dictionary_order(self):
        targets = dict(reversed(list(self.resource_targets().items())))
        targets["recommended_mineral_collection_rate"] = "600 minerals/min (too low)"
        memory = SC2LongLoopMemory(initial_resource_memory=targets)
        contexts, lengths = memory.fetch(0, ["observation"], telemetry=[{
            "game_time_seconds": 60,
            "cumulative_minerals_collected": 600,
            "cumulative_vespene_collected": 120,
            "cumulative_minerals_spent": 450,
            "cumulative_vespene_spent": 60,
        }])
        self.assertEqual(lengths, [1])
        self.assertIn("Mineral collection rate is 600.00", contexts[0])
        self.assertIn("marked too low", contexts[0])

    def test_fetch_resource_reminder_thresholds_respect_too_low_tag(self):
        def check(metric_key, recommendation, current):
            targets = dict.fromkeys(self.resource_targets())
            targets[metric_key] = recommendation
            memory = SC2LongLoopMemory(initial_resource_memory=targets)
            telemetry = {
                "game_time_seconds": 60,
                "cumulative_minerals_collected": 100,
                "cumulative_vespene_collected": 100,
                "cumulative_minerals_spent": 100,
                "cumulative_vespene_spent": 100,
                "supply_used": 0,
            }
            if metric_key == "recommended_mineral_collection_rate":
                telemetry["cumulative_minerals_collected"] = current
            elif metric_key == "recommended_vespene_collection_rate":
                telemetry["cumulative_vespene_collected"] = current
            elif metric_key == "recommended_mineral_utilization":
                telemetry["cumulative_minerals_spent"] = current
            elif metric_key == "recommended_vespene_utilization":
                telemetry["cumulative_vespene_spent"] = current
            context, _ = memory.fetch(0, ["observation"], telemetry=[telemetry])
            return context[0]

        cases = (
            ("recommended_mineral_collection_rate", "100 minerals/min", 99, True),
            ("recommended_mineral_collection_rate", "100 minerals/min", 100, False),
            ("recommended_vespene_collection_rate", "100 vespene/min (too low)", 80, True),
            ("recommended_mineral_utilization", "100% (too low)", 110, True),
            ("recommended_vespene_utilization", "100% (too low)", 111, False),
        )
        for key, recommendation, current, should_remind in cases:
            with self.subTest(key=key, recommendation=recommendation, current=current):
                context = check(key, recommendation, current)
                self.assertEqual("Metric below target:" in context, should_remind)

    def test_fetch_matches_only_currently_visible_positive_enemy_units(self):
        memory = SC2LongLoopMemory(
            initial_army_memory=[{
                "opponent_units": ["Marine"],
                "counters": ["Marauder"],
                "fallback": "Build a Factory",
                "rationale": "Marauders trade well against Marines.",
            }]
        )
        for detected, expected in (({"Marine": 0}, False), ({"Marauder": 2}, False), ({"Marine": 1}, True)):
            with self.subTest(detected=detected):
                memory.reset(batch_size=1)
                contexts, _ = memory.fetch(0, ["observation"], telemetry=[{
                    "visible_enemy_units": detected,
                }])
                self.assertEqual("Recommended counters: Marauder" in contexts[0], expected)

    def test_legacy_bare_too_low_is_migrated_to_null(self):
        with tempfile.TemporaryDirectory() as directory:
            memory_path = Path(directory) / "long_loop_memory.json"
            memory_path.write_text(json.dumps({
                "resource_memory": ["10", "20", "30%", "40%", "too low"],
                "army_memory": [],
            }), encoding="utf-8")
            memory = SC2LongLoopMemory(memory_path=str(memory_path))
        self.assertEqual(memory.resource_memory, {
            "recommended_mineral_collection_rate": "10",
            "recommended_vespene_collection_rate": "20",
            "recommended_mineral_utilization": "30%",
            "recommended_vespene_utilization": "40%",
            "recommended_total_supply_growth_rate": None,
        })

    def test_update_prompt_orders_replay_memory_outcome_and_json_contract(self):
        memory = SC2LongLoopMemory(
            initial_resource_memory={
                **dict.fromkeys(self.resource_targets()),
                "recommended_vespene_collection_rate": "100 vespene/min",
            },
            initial_army_memory=[],
        )
        records = [{
            "telemetry": {"visible_enemy_units": {"Marine": 2}},
            "won": True,
        }]
        won_prompt = memory._build_update_prompt("won-rollout", records)
        self.assertLess(won_prompt.index("This game has ended."), won_prompt.index("Here is the game replay"))
        self.assertLess(won_prompt.index("Here is the game replay"), won_prompt.index('"resource_memory": {'))
        self.assertLess(won_prompt.index('"resource_memory": {'), won_prompt.index("The game was won."))
        self.assertIn('"recommended_mineral_collection_rate": null', won_prompt)
        self.assertIn('"recommended_vespene_collection_rate": "100 vespene/min"', won_prompt)
        self.assertIn("If a previous resource metric is null, use this game's measured value directly.", won_prompt)
        self.assertIn("append `(too low)` after the unit when the target is insufficient", won_prompt)
        self.assertIn("include at least one relevant army_memory entry", won_prompt)
        self.assertIn("`resource_memory` must be a JSON object with exactly these five keys", won_prompt)
        for key in self.resource_targets():
            self.assertIn(f"`{key}`", won_prompt)
        self.assertIn("`army_memory` must be a list of objects with exactly four fields", won_prompt)
        self.assertIn("`opponent_units` (1-2 exact enemy unit names", won_prompt)
        self.assertLess(won_prompt.index("The game was won."), won_prompt.index("Output only a valid JSON object"))

        records[0]["won"] = False
        lost_prompt = memory._build_update_prompt("lost-rollout", records)
        self.assertIn("The game was lost.", lost_prompt)
        self.assertIn("could materially improve the outcome", lost_prompt)
        self.assertIn("revise an existing response", lost_prompt)

    def test_replay_uses_filtered_count_deltas_without_changing_metrics_or_records(self):
        memory = SC2LongLoopMemory()
        records = [
            {"telemetry": {
                "game_time_seconds": 60, "minerals": 100, "vespene": 25,
                "cumulative_minerals_collected": 600,
                "cumulative_vespene_collected": 120,
                "cumulative_minerals_spent": 450,
                "cumulative_vespene_spent": 60,
                "supply_used": 12, "supply_cap": 15, "supply_army": 0,
                "own_units": {"SCV": 12},
                "own_structures": {"CommandCenter": 1},
                "visible_enemy_units": {"Marine": 5},
                "visible_enemy_structures": {"Barracks": 1},
            }},
            {"telemetry": {
                "game_time_seconds": 120, "minerals": 150, "vespene": 50,
                "cumulative_minerals_collected": 1200,
                "cumulative_vespene_collected": 240,
                "cumulative_minerals_spent": 900,
                "cumulative_vespene_spent": 120,
                "supply_used": 25,
                "own_units": {"SCV": 17, "Marine": 3},
                "own_structures": {"CommandCenter": 1, "Barracks": 1},
                "visible_enemy_units": {"Marine": 3, "Marauder": 1},
                "visible_enemy_structures": {},
            }},
            {"telemetry": {
                "game_time_seconds": 180, "minerals": 175, "vespene": 80,
                "cumulative_minerals_collected": 1800,
                "cumulative_vespene_collected": 360,
                "cumulative_minerals_spent": 1350,
                "cumulative_vespene_spent": 180,
                "supply_used": 20,
                "own_units": {"SCV": 12},
                "own_structures": {"CommandCenter": 1, "Barracks": 1},
                "visible_enemy_units": {}, "visible_enemy_structures": {},
            }, "won": False},
        ]
        original = json.dumps(records)
        prompt = memory._build_update_prompt("rollout", records)
        replay_text = prompt.split("per decision point:\n", 1)[1].split("\n\n", 1)[0]
        replay = json.loads(replay_text)
        self.assertEqual(replay[0]["telemetry"]["own_units"], {"SCV": 12})
        self.assertEqual(replay[1]["telemetry"], {
            "game_time_seconds": 120, "minerals": 150, "vespene": 50,
            "own_units": {"SCV": 5, "Marine": 3},
            "own_structures": {"Barracks": 1},
            "visible_enemy_units": {"Marine": -2, "Marauder": 1},
            "visible_enemy_structures": {"Barracks": -1},
        })
        self.assertEqual(replay[2]["telemetry"]["own_units"], {"SCV": -5, "Marine": -3})
        self.assertEqual(replay[2]["telemetry"]["own_structures"], {})
        self.assertEqual(replay[2]["telemetry"]["visible_enemy_units"], {"Marine": -3, "Marauder": -1})
        self.assertFalse(replay[2]["won"])
        self.assertNotIn("won", replay[0])
        for record in replay:
            self.assertNotIn("supply_used", record["telemetry"])
            self.assertNotIn("cumulative_minerals_collected", record["telemetry"])
        self.assertIn("Mineral collection rate: 600.00 minerals/min", prompt)
        self.assertIn("Vespene collection rate: 120.00 vespene/min", prompt)
        self.assertIn("Mineral utilization (spent / collected): 75.00 %", prompt)
        self.assertIn("Total supply growth rate: 4.00 supply/min", prompt)
        self.assertIn("Negative visible-enemy changes may reflect lost vision", prompt)
        self.assertEqual(json.dumps(records), original)

    def test_replay_missing_maps_do_not_create_false_disappearances(self):
        memory = SC2LongLoopMemory()
        records = [
            {"telemetry": {"own_units": {"SCV": 12}}},
            {"telemetry": {"minerals": 100}},
            {"telemetry": {"own_units": {"SCV": 17}}, "won": True},
        ]
        for unused in range(2):
            prompt = memory._build_update_prompt("rollout", records)
            replay, _ = json.JSONDecoder().raw_decode(prompt.split("per decision point:\n", 1)[1])
            self.assertEqual(replay[0]["telemetry"]["own_units"], {"SCV": 12})
            self.assertNotIn("own_units", replay[1]["telemetry"])
            self.assertEqual(replay[2]["telemetry"]["own_units"], {"SCV": 5})

    def test_resource_prompt_uses_non_decreasing_targets_and_explicit_loss_branches(self):
        memory = SC2LongLoopMemory()
        for won in (True, False):
            with self.subTest(won=won):
                prompt = memory._build_update_prompt("rollout", [{"won": won}])
                self.assertIn("Treat resource targets as minimum performance goals", prompt)
                self.assertIn("higher collection rates, utilization, and supply growth are preferable", prompt)
                self.assertIn("Do not lower established numeric targets", prompt)
                self.assertIn("Preserve existing targets when measurements are unavailable", prompt)
                self.assertIn("does not establish that a target was met", prompt)
                if won:
                    self.assertIn("raise it when supported by a higher measured value", prompt)
                    self.assertIn("a win below target does not justify lowering the target", prompt)
                else:
                    self.assertIn("If any measured metric fell below its target, preserve all existing resource targets unchanged", prompt)
                    self.assertIn("provisionally treat them as valid, and focus reflection on unit matchup weaknesses", prompt)
                    self.assertIn("If all targets were met", prompt)
                    self.assertIn("retain that metric's numeric target and append '(too low)'", prompt)

    def test_army_prompt_requires_focused_causal_entries_for_both_outcomes(self):
        memory = SC2LongLoopMemory()
        for won in (True, False):
            with self.subTest(won=won):
                prompt = memory._build_update_prompt("rollout", [{
                    "telemetry": {"visible_enemy_units": {"Marine": 2, "Marauder": 1}},
                    "won": won,
                }])
                self.assertIn("prioritize matchups with the clearest causal mechanism", prompt)
                self.assertIn("co-occurrence or the game result alone is not causal evidence", prompt)
                self.assertIn("one enemy unit type, or two only when their interaction requires a joint response", prompt)
                self.assertIn("each must address that entry's target", prompt)
                self.assertIn("Split or narrow existing broad entries", prompt)
                self.assertIn("Keep rationale to 1-2 concise sentences linking a specific unit property", prompt)
                self.assertIn("omit replay narration and repeated advice", prompt)
                self.assertNotIn("complete reasoning", prompt)

    def test_empty_army_memory_is_rejected_when_enemy_units_were_seen(self):
        response = {
            "resource_memory": self.resource_targets(),
            "army_memory": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            memory_path = Path(directory) / "long_loop_memory.json"
            memory = SC2LongLoopMemory(memory_path=str(memory_path))
            memory.reset(batch_size=1)
            memory.store({
                "done": [True],
                "won": [False],
                "truncated": [False],
                "telemetry": [{"visible_enemy_units": {"Marine": 3}}],
            })
            with self.assertWarnsRegex(RuntimeWarning, "must include a matchup"):
                memory.finalize_batch(llm_generate=lambda _: response)
            self.assertFalse(memory_path.exists())

    def test_empty_army_memory_is_allowed_without_enemy_evidence(self):
        response = {
            "resource_memory": self.resource_targets(),
            "army_memory": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            memory_path = Path(directory) / "long_loop_memory.json"
            memory = SC2LongLoopMemory(memory_path=str(memory_path))
            memory.reset(batch_size=1)
            memory.store({
                "done": [True],
                "won": [False],
                "truncated": [False],
                "telemetry": [{"visible_enemy_units": {"Marine": 0}}],
            })
            memory.finalize_batch(llm_generate=lambda _: response)
            self.assertTrue(memory_path.exists())
            self.assertEqual(memory.army_memory, [])


if __name__ == "__main__":
    unittest.main()
