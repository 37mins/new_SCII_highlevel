"""Preregistered, outcome-independent paired evaluation, no server operations."""
from acceptance_hook import EVAL_SEEDS

# random.Random(20260924).sample(range(65536, 2**32-1), 64); frozen before outcomes.
SEEDS = [
    65648715,3519458032,4034442911,2837899169,3924150504,2347007475,2710453253,3012843628,
    623721583,2399721872,2442427596,3375914349,3126576243,3500498238,245444012,3639096465,
    1832685125,1194574925,1579237516,3276083501,2797027350,1902577429,3227594480,2314285078,
    4002215147,1430675509,4034909016,1482555028,1896296495,2321525988,1048985655,3092097703,
    250495503,1132784194,885183971,1141376770,3608681438,155131317,371601908,2546723015,
    1587311189,3361377534,2019986884,3836539771,3250074151,1393970094,324377020,1095770565,
    1991975028,944453590,2157009893,2567868451,2121074481,3649114987,1973239524,3806249756,
    1944334706,1858689595,4136835963,3999611613,1916743140,4178914286,4262946149,4280531705,
]
STAGES = [f'b{b:02d}-{arm}' for b in range(8)
          for arm in (('original','cp96') if b % 2 == 0 else ('cp96','original'))]


def stage_spec(stage):
    if stage not in STAGES:
        raise ValueError('Undeclared held-out stage')
    if len(SEEDS) != 64 or len(set(SEEDS)) != 64 or set(SEEDS) & set(EVAL_SEEDS):
        raise ValueError('Distinct held-out seeds required')
    if not all(65536 <= s < 2**32-1 for s in SEEDS):
        raise ValueError('Held-out seeds must exclude training 0..100')
    batch = int(stage[1:3])
    return dict(batch=batch, arm=stage.split('-')[1], seeds=SEEDS[batch*8:batch*8+8],
                expected_step=96 if stage.endswith('cp96') else 0)
