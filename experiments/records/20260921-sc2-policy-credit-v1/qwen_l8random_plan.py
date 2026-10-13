"""Pre-registered L8 random96 versus same96; frozen before new GPU dispatch."""
import hashlib
import json
import math
from pathlib import Path

from acceptance_hook import EVAL_SEEDS
from qwen_heldout_plan import SEEDS as L7_SEEDS
from qwen_l8_plan import SEEDS as PILOT_SEEDS
from qwen_l8_common64_plan import SEEDS as OLD_L8_SEEDS

OLD_ROOT = Path('/var/jfsCache/sc2-qwen-l8random96-197-20260927-r1')
OLD_EVAL_ROOT = Path('/var/jfsCache/sc2-qwen-l8random-paired192-197-20260927-r1')
OLD_SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l8random96-197-source-20260927-r1')
R2_ROOT = Path('/var/jfsCache/sc2-qwen-l8random96-197-20260927-r2')
R2_EVAL_ROOT = Path('/var/jfsCache/sc2-qwen-l8random-paired192-197-20260927-r2')
R2_SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l8random96-197-source-20260927-r2')
ROOT = Path('/var/jfsCache/sc2-qwen-l8random96-197-20260928-r3')
EVAL_ROOT = Path('/var/jfsCache/sc2-qwen-l8random-paired192-197-20260928-r3')
SOURCE_PARENT = Path('/var/jfsCache/sc2-qwen-l8random96-197-source-20260928-r3')
SELECTION_ROOT = ROOT/'selection'
PARTS = ('qwen-random/short', 'qwen-random/long')
ARMS = ('original', 'same96', 'random96')
CHECKPOINTS = {
    'same96': Path('/var/jfsCache/sc2-qwen-l8same96-197-20260926-r2/qwen-same/long/runs/train96/checkpoints/global_step_96'),
    'random96': ROOT/PARTS[1]/'runs/train96/checkpoints/global_step_96',
}
# random.Random(2026092708).sample(range(65536, 2**32-1), 64), no outcomes consulted.
SEEDS = [
    208764042,4033831095,4273283954,3286156970,4222622236,2828046710,3821897171,2801178166,
    4159820916,2397134230,2295537531,1085176974,888413657,1864623588,1821246725,4288245617,
    1928083807,1606439848,1750180001,2157129030,3845869480,2583316505,1044797244,499463978,
    1185563293,3466613764,3939152471,3446644127,3079316308,2907693452,3583644975,963713801,
    2410879157,2855928203,2339311949,2425639993,1084325355,4154416030,3145046334,2615958828,
    2949091419,3347882770,49608851,2923560418,2207328776,3771748923,2500500153,631587272,
    2564915539,564610756,512751299,1177360828,667732584,3070107292,2889412589,1274792528,
    1974511954,4088181271,890353330,556409708,3673009292,602393243,777611869,3056685215,
]
SEED_SHA256 = '7a2d619653c24c1ad40b50e9a9aea00a3b264885b70c02b5aff519a7547baebd'
STAGES = [f'b{b:02d}-{arm}' for b in range(8) for arm in ARMS[b%3:]+ARMS[:b%3]]
ANALYSIS_SEED, BOOTSTRAP_SAMPLES = 2026092709, 100000
SAVED_STEPS = (2,32,64,96)
SELECTION_ARMS = tuple('cp'+str(s) for s in SAVED_STEPS)
SELECTION_CHECKPOINTS = {'cp'+str(s): ROOT/PARTS[0 if s==2 else 1]/
    ('runs/train2' if s==2 else 'runs/train96')/f'checkpoints/global_step_{s}' for s in SAVED_STEPS}
# Random(2026092710), frozen before any new GPU/result; distinct from test64.
SELECTION_SEEDS = [
    1676024359,3311359371,1803677045,815351849,1041855993,1414892806,1208799724,3570661004,
    1987344794,766069959,1101924832,695227373,3425665911,3829899699,1620930396,1292716698,
    1926059137,3984229549,2604737463,515375665,2592848477,1342102133,3206101674,242255854,
    224364611,2434082538,3912059029,920478274,2851824023,3927879658,1918684695,1027136304,
]
SELECTION_SHA256 = '0f47acf2c792395cb17d73d678bbe8ad618b2c89c1ff5a4d85733465fa2a372c'
SELECTION_STAGES = [f'b{b:02d}-{arm}' for arm in SELECTION_ARMS for b in range(4)]


def validate():
    excluded = set(range(101)) | set(EVAL_SEEDS) | set(L7_SEEDS) | set(PILOT_SEEDS) | set(OLD_L8_SEEDS)
    if (len(SEEDS)!=64 or len(set(SEEDS))!=64 or set(SEEDS)&excluded
            or any(not 65536<=s<2**32-1 for s in SEEDS)
            or hashlib.sha256(json.dumps(SEEDS,separators=(',',':')).encode()).hexdigest()!=SEED_SHA256):
        raise ValueError('Frozen distinct new evaluation seeds required')
    if (len(SELECTION_SEEDS)!=32 or len(set(SELECTION_SEEDS))!=32
            or set(SELECTION_SEEDS)&(excluded|set(SEEDS))
            or hashlib.sha256(json.dumps(SELECTION_SEEDS,separators=(',',':')).encode()).hexdigest()!=SELECTION_SHA256):
        raise ValueError('Independent frozen selection seeds required')


def stage_spec(stage):
    validate()
    if stage not in STAGES+SELECTION_STAGES: raise ValueError('Undeclared paired stage')
    batch=int(stage[1:3]);arm=stage[4:]
    if stage in SELECTION_STAGES:
        return dict(batch=batch,arm=arm,seeds=SELECTION_SEEDS[batch*8:batch*8+8],
                    expected_step=int(arm[2:]),checkpoint=SELECTION_CHECKPOINTS[arm])
    return dict(batch=batch,arm=arm,seeds=SEEDS[batch*8:batch*8+8],
                expected_step=0 if arm=='original' else 96,checkpoint=CHECKPOINTS.get(arm))


def paired_statistics(control, treatment):
    """Fixed64 paired binary wins; ties must be encoded as nonwins, separately reported."""
    import numpy as np
    if len(control)!=64 or len(treatment)!=64 or any(x not in (0,1) for x in [*control,*treatment]):
        raise ValueError('Exactly64 ordered paired binary outcomes required')
    delta=np.asarray(treatment,dtype=np.int8)-np.asarray(control,dtype=np.int8)
    gain=int((delta==1).sum());loss=int((delta==-1).sum());discordant=gain+loss
    p=min(1.,2*sum(math.comb(discordant,k) for k in range(min(gain,loss)+1))/2**discordant) if discordant else 1.
    rng=np.random.default_rng(ANALYSIS_SEED)
    bootstrap=delta[rng.integers(0,64,size=(BOOTSTRAP_SAMPLES,64))].mean(axis=1)
    return dict(difference=float(delta.mean()),gains=gain,losses=loss,
        paired_bootstrap_95=np.quantile(bootstrap,[.025,.975],method='linear').tolist(),
        exact_two_sided_mcnemar=p,analysis_seed=ANALYSIS_SEED,resamples=BOOTSTRAP_SAMPLES)
