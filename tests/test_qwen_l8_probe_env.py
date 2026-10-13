"""Ensure L8 probes inherit the complete actual-launcher Ray environment."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] /
    'experiments/records/20260921-sc2-policy-credit-v1'))
from qwen_l8_cuda_probe_v2 import runtime_environment


class ProbeEnvironmentTests(unittest.TestCase):
    def config(self):
        return {'trainer': {'val_only': True, 'n_gpus_per_node': 8},
                'ray_init': {'runtime_env': {
                    'worker_process_setup_hook': 'qwen_l8_hook.install',
                    'env_vars': {'PYTHONPATH': '/frozen/runtime:/frozen/hook',
                        'SC2PATH': '/assets/StarCraftII', 'SC2_L8_STAGE': 'b01-random-cp96',
                        'SC2_DIFFICULTY': 'CheatVision', 'SC2_EXPECTED_DIFFICULTY': 'CheatVision',
                        'SC2_L8_RENDEZVOUS_LOW_PORT': '1', 'SC2_EVAL_SEEDS_LOG_PATH': '/cpu/seeds',
                        'SC2_RUNTIME_LOG_ROOT': '/cpu/log', 'SC2_EXECUTION_FAILURE_FEEDBACK': '0',
                        'TMPDIR': '/old/temp', 'RAY_TMPDIR': '/old/ray',
                        'ADDITIONAL_LAUNCHER_VALUE': 'must survive'}}}}

    def evaluate(self, cfg):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'resolved_config.json'
            path.write_text(json.dumps(cfg))
            return runtime_environment(path, Path('/tmp/probe-ray'))

    def test_all_environment_values_preserved_except_isolated_tmp(self):
        cfg = self.config()
        expected = copy.deepcopy(cfg['ray_init']['runtime_env'])
        expected['env_vars'].update(TMPDIR='/tmp/probe-ray', RAY_TMPDIR='/tmp/probe-ray')
        env, proof = self.evaluate(cfg)
        self.assertEqual(env, expected)
        self.assertEqual(proof['overridden_env_vars'], ['RAY_TMPDIR', 'TMPDIR'])
        self.assertEqual(len(proof['resolved_config_sha256']), 64)

    def test_r6_missing_sc2path_fails_before_ray(self):
        cfg = self.config()
        del cfg['ray_init']['runtime_env']['env_vars']['SC2PATH']
        with self.assertRaisesRegex(ValueError, 'Complete matching'):
            self.evaluate(cfg)

    def test_training_configuration_is_rejected(self):
        cfg = self.config()
        cfg['trainer']['val_only'] = False
        with self.assertRaisesRegex(ValueError, 'Complete matching'):
            self.evaluate(cfg)

    def test_wrong_hook_or_difficulty_is_rejected(self):
        for key, value in [('SC2_DIFFICULTY', 'VeryHard'), ('SC2PATH', '/different')]:
            cfg = self.config()
            cfg['ray_init']['runtime_env']['env_vars'][key] = value
            with self.assertRaisesRegex(ValueError, 'Complete matching'):
                self.evaluate(cfg)


if __name__ == '__main__':
    unittest.main()
