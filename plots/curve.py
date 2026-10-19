import argparse
import csv
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
NUMBER = r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"
METRICS = re.compile(
	rf"\b(training/epoch|training/global_step|episode/success_rate):\s*({NUMBER})"
)


def read_points(log_path):
	content = log_path.read_bytes()
	points = {}
	required = {"training/epoch", "training/global_step", "episode/success_rate"}
	for line in content.decode("utf-8", errors="replace").splitlines():
		fields = dict(METRICS.findall(line))
		if not required <= fields.keys():
			continue
		step = int(float(fields["training/global_step"]))
		epoch = int(float(fields["training/epoch"])) + 1
		rate = float(fields["episode/success_rate"])
		if not 0 <= rate <= 1:
			raise ValueError(f"Invalid success rate at step {step}: {rate}")
		points[step] = (step, epoch, rate * 100)
	if not points:
		raise ValueError(f"No training epoch/win-rate records found in {log_path}")
	return [points[step] for step in sorted(points)], hashlib.sha256(content).hexdigest()


def main():
	parser = argparse.ArgumentParser(
		description="Plot logged training win rate against one-based epoch for a run.",
		epilog="Example: python plots/curve.py qwen-long-loop-20261017-152356",
	)
	parser.add_argument("run_id", help="Directory name under runs/; not a path")
	parser.add_argument("--output", type=Path, help="Output PNG path (default: plots/<run_id>-win-rate.png)")
	args = parser.parse_args()
	if args.run_id in {".", ".."} or Path(args.run_id).name != args.run_id:
		parser.error("run_id must be a directory name, not a path")

	log_path = REPO / "runs" / args.run_id / "console.log"
	if not log_path.is_file():
		log_path = REPO / "outputs" / f"{args.run_id}.nohup.log"
	if not log_path.is_file():
		parser.error(f"No console.log or nohup log found for {args.run_id}")
	points, log_sha256 = read_points(log_path)
	output = args.output or REPO / "plots" / f"{args.run_id}-win-rate.png"
	if output.suffix.lower() != ".png":
		parser.error("--output must use a .png extension")
	output.parent.mkdir(parents=True, exist_ok=True)

	import matplotlib

	matplotlib.use("Agg")
	import matplotlib.pyplot as plt

	fig, ax = plt.subplots(figsize=(10, 4.5))
	ax.plot([point[1] for point in points], [point[2] for point in points],
			color="#147d92", linewidth=1.4, marker=".", markersize=4)
	ax.set(xlabel="Training Epoch (1-based)", ylabel="Training Win Rate (%)",
		   ylim=(-2, 102), title=args.run_id)
	ax.grid(alpha=0.25)
	fig.tight_layout()
	fig.savefig(output, dpi=180, metadata={
		"Description": (
			f"run_id={args.run_id}; source={log_path}; source_sha256={log_sha256}; "
			f"captured_at={datetime.now(timezone.utc).isoformat()}; "
			"metric=episode/success_rate; script=plots/curve.py; "
			"training batches only, not independent evaluation; skipped empty batches excluded"
		),
	})
	plt.close(fig)
	csv_path = output.with_suffix(".csv")
	with csv_path.open("w", encoding="utf-8", newline="") as stream:
		writer = csv.writer(stream)
		writer.writerow(["global_step", "epoch_1based", "training_win_rate_percent"])
		writer.writerows(points)
	print(f"Source: {log_path}\nPoints: {len(points)}\nPNG: {output}\nCSV: {csv_path}")


if __name__ == "__main__":
	main()
