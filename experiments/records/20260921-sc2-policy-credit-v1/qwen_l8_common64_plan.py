"""Frozen September27 L8 original/own CP96/own CP192 evaluation, no training."""
import hashlib
import json
from pathlib import Path

from acceptance_hook import EVAL_SEEDS
from qwen_heldout_plan import SEEDS as L7_SEEDS
from qwen_l8_plan import SEEDS as PILOT_SEEDS

ARMS = ('original', 'cp96', 'cp192')
PARENT = Path('/var/jfsCache/sc2-qwen-l8same192-197-20260926-r2')
CHECKPOINTS = {
    'cp96': Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r2/qwen-same/long/runs/train96/checkpoints/global_step_96'),
    'cp192': PARENT/'runs/train192/checkpoints/global_step_192',
}
# random.Random(20260927).sample(range(65536, 2**32-1), 64), before any outcomes.
SEEDS = [
    3891768967,1026095769,2089620454,1345181480,4261733069,517441573,306282740,332998533,
    2126563309,1737280231,4144425004,1552057234,2927579824,458875698,1335723408,304110307,
    794804262,3377981709,2853357102,1999786904,1256325171,1091215703,30384615,572594696,
    1508631485,3553266427,2312665391,3259011717,3817305670,4122700548,2694247594,2642042481,
    843065588,2735015391,52509861,3761861802,2166857442,611962411,2236608459,3867500739,
    3992467251,300992239,1212858108,878654179,2667106006,3314926993,1837049318,483388772,
    1820737278,506518546,235724644,3815455702,2629183280,152788249,2989722140,2965380064,
    1738353009,159971924,548719149,3859010269,4263833908,1112594666,2601943755,1359494153,
]
SEED_SHA256 = 'ac8647f0b3f4e14d25f88a1508d55cd94c6ce6cf82ac8e73a2c386ca2b6e011b'
STAGES = [f'b{b:02d}-{arm}' for b in range(8) for arm in ARMS[b % 3:]+ARMS[:b % 3]]


def validate():
    if (len(SEEDS) != 64 or len(set(SEEDS)) != 64
            or set(SEEDS) & (set(range(101)) | set(EVAL_SEEDS) | set(L7_SEEDS) | set(PILOT_SEEDS))
            or any(not 65536 <= s < 2**32-1 for s in SEEDS)
            or hashlib.sha256(json.dumps(SEEDS,separators=(',',':')).encode()).hexdigest() != SEED_SHA256):
        raise ValueError('Frozen distinct held-out seeds required')


def stage_spec(stage):
    validate()
    if stage not in STAGES: raise ValueError('Undeclared common64 stage')
    b = int(stage[1:3]); arm = stage[4:]
    return dict(batch=b, arm=arm, seeds=SEEDS[b*8:b*8+8],
        expected_step={'original':0,'cp96':96,'cp192':192}[arm], checkpoint=CHECKPOINTS.get(arm))
