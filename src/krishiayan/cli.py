from __future__ import annotations

import argparse
import json
import sys

import numpy as np


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="krishiayan", description="Krishiayan soil intelligence CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sim = sub.add_parser("simulate", help="Emit a physically plausible probe packet")
    sim.add_argument("--scenario", default=None, help="pune-wheat-n-deficient | wet-soil | saline")
    sim.add_argument("--seed", type=int, default=7)
    sim.add_argument("--push", default=None, help="POST packet to this ingest URL")
    sim.add_argument("--device-id", default="KA-PROBE-SIM")
    sim.add_argument("--field-id", default=None)
    sim.add_argument("--scans", type=int, default=1)

    sub.add_parser("train", help="Train ML heads (wrapper around ml/train.py)")

    args = parser.parse_args(argv)
    if args.cmd == "simulate":
        return _simulate(args)
    if args.cmd == "train":
        from ml.train import main as train_main

        train_main()
        return 0
    return 1


def _simulate(args) -> int:
    from krishiayan.sim.probe import packet_from_truth
    from krishiayan.sim.world import sample_world

    rng = np.random.default_rng(args.seed)
    packets = []
    for i in range(args.scans):
        truth = sample_world(rng, scenario=args.scenario)
        pkt = packet_from_truth(truth, rng, device_id=args.device_id, field_id=args.field_id)
        packets.append(pkt.model_dump(mode="json"))
        if args.push:
            import httpx

            r = httpx.post(args.push, json=packets[-1], timeout=30)
            r.raise_for_status()
            print(json.dumps({"pushed": True, "scan": i, "response": r.json()}, default=str))
        else:
            print(json.dumps(packets[-1], indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
