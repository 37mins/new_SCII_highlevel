# What the eight-pair evaluations establish

Analysis checked September24 22:58Beijing, documentation-only; no server access,
new run, early stopping, runtime mutation or historical-status rewrite.

Sources: [fresh-same completion](qwen-l7same-fresh-complete-20260924.json),
[fresh-same pre/post/eval summary](qwen-l7same-fresh-curve-20260924-data.json),
[random completion](qwen-random-complete-spb-random-start-20260924.json).

Training execution and performance benefit are separate claims. Returned PPO
updates, finite positive gradients/update times and native checkpoint/load
receipts substantiate actual training execution; these win counts alone do not.
Neither nonzero gradients nor successful execution proves useful strategy learning.

Fresh same CP2post6/8 to CP96eval8/8 is an observed improvement of2 wins
(25 percentage points) on these eight reused pairs:2 defeat-to-victory,
0 victory-to-defeat,6 victory-to-victory. Under an illustrative exact conditional
two-sided McNemar/binomial test, only the2 discordant pairs inform direction:
2*P(Binomial(2,0.5)<=0)=0.5. Thus this is a positive descriptive signal, not
convincing statistical evidence of a general improvement. The calculation assumes
independent pairs and is not a confirmatory preregistered claim on these reused
seeds. Non-significance is not proof of no effect; p=0.5 is not the probability
that training is ineffective. Method: [NIST McNemar reference](https://www.itl.nist.gov/div898/software/dataplot/refman1/auxillar/mcnemar.htm).
The counts and p-value were recomputed with local Node from paired_eval_outcomes
and an exact binomial sum; assertions passed for8pairs,2improvements,0regressions.

CP2 is already trained, not the original baseline. The complete same trajectory
on the reused eight evaluation scenarios is original7/8 -> CP2post6/8 -> CP96eval8/8.
Against the original, final net gain is only1/8 (12.5 percentage points), not2/8.
This distinction does not erase the CP2-to-CP96 observed gain; it changes the
question from late-training change to the net benefit of the full training run.

Random CP2post8/8 -> CP96eval8/8 has no observed win gain or loss on these seeds.
It is ceiling-saturated: this result establishes neither improvement nor lack
of improvement on harder/new cases. Do not infer that same training outperforms
random training by comparing their change scores from unequal baselines.
Historical random ancestor non-bitwise and failed-r4 limits remain unchanged.

The already-authorized [128-game held-out evaluation](qwen-heldout128-197-20260924.md)
compares original Qwen with fresh-same CP96 on64new paired scenarios, zero updates.
It tests full-run performance benefit with more informative paired inference;
it is not CP2-versus-CP96, not same-versus-random, and not an architecture test.
Only completed64-pair results, effect size, confidence interval and discordant
counts can support its preregistered conclusion. Partial outcomes do not change
the stopping rule; repeated independent training runs would still be needed for
a robust claim about the training method beyond this one trained checkpoint.
