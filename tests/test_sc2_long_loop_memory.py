import json
import tempfile
import unittest
from pathlib import Path

from agent_system.memory.sc2_long_loop_memory import SC2LongLoopMemory


class SC2LongLoopMemoryTest(unittest.TestCase):
    def test_completed_rollout_updates_persists_and_retrieves_memory(self):
        response = {
            "resource_memory": [
                "600 minerals/min",
                "120 vespene/min",
                "75%",
                "50%",
                "12 supply/min",
            ],
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
        parsed = memory._parse_model_output({
            "resource_memory": ["600 minerals/min (too low)", 120, "75%", "50%", "12 supply/min"],
            "army_memory": [],
        })
        self.assertEqual(parsed["resource_memory"][0], "600 minerals/min (too low)")
        with self.assertRaisesRegex(ValueError, "numeric target"):
            memory._parse_model_output({
                "resource_memory": ["600", "120", "75%", "50%", "too low"],
                "army_memory": [],
            })

    def test_legacy_bare_too_low_is_migrated_to_null(self):
        with tempfile.TemporaryDirectory() as directory:
            memory_path = Path(directory) / "long_loop_memory.json"
            memory_path.write_text(json.dumps({
                "resource_memory": ["10", "20", "30%", "40%", "too low"],
                "army_memory": [],
            }), encoding="utf-8")
            memory = SC2LongLoopMemory(memory_path=str(memory_path))
        self.assertIsNone(memory.resource_memory[4])

    def test_update_prompt_orders_replay_memory_outcome_and_json_contract(self):
        memory = SC2LongLoopMemory(
            initial_resource_memory=[None, "100 vespene/min", None, None, None],
            initial_army_memory=[],
        )
        records = [{
            "telemetry": {"visible_enemy_units": {"Marine": 2}},
            "won": True,
        }]
        won_prompt = memory._build_update_prompt("won-rollout", records)
        self.assertLess(won_prompt.index("This game has ended."), won_prompt.index("Here is the game replay"))
        self.assertLess(won_prompt.index("Here is the game replay"), won_prompt.index("previous memory JSON"))
        self.assertLess(won_prompt.index("previous memory JSON"), won_prompt.index("The game was won."))
        self.assertIn('"resource_memory": [null, "100 vespene/min"', won_prompt)
        self.assertIn("If a previous resource metric is null, use this game's measured value directly.", won_prompt)
        self.assertIn("append `(too low)` after the unit when the target is insufficient", won_prompt)
        self.assertIn("include at least one relevant army_memory entry", won_prompt)
        self.assertIn("`resource_memory` must contain exactly five strings or nulls, in this order", won_prompt)
        self.assertIn("`army_memory` must be a list of objects with exactly four fields", won_prompt)
        self.assertIn("`opponent_units` (non-empty list of exact enemy unit names", won_prompt)
        self.assertLess(won_prompt.index("The game was won."), won_prompt.index("Output only a valid JSON object"))

        records[0]["won"] = False
        lost_prompt = memory._build_update_prompt("lost-rollout", records)
        self.assertIn("The game was lost.", lost_prompt)
        self.assertIn("could materially improve the outcome", lost_prompt)
        self.assertIn("revise an existing response", lost_prompt)

    def test_empty_army_memory_is_rejected_when_enemy_units_were_seen(self):
        response = {
            "resource_memory": ["600 minerals/min", "120 vespene/min", "75%", "50%", "12 supply/min"],
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
            "resource_memory": ["600 minerals/min", "120 vespene/min", "75%", "50%", "12 supply/min"],
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
