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
            self.assertIn("Mineral collection rate is 400.00", contexts[0])
            self.assertIn("Opponent detected: Siege Tank", contexts[0])
            self.assertEqual(lengths, [3])


if __name__ == "__main__":
    unittest.main()
