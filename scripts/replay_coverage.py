import os
import json
import sys
from run_experiment import cleanup_containers, fetch_works, run_cmd_in_docker_with_output, spawn_containers


def run(addr, base_dir, tool_name):
    results = {}
    for replay in os.listdir(f"{base_dir}/{addr}/testcase/"):
        if replay.endswith("_replayable"):
            try:
                cmd = f"timeout 60s ./target/release/ityfuzz evm -t \"deployment-{tool_name}/{addr}/*\" --replay-file {base_dir}/{addr}/testcase/{replay} --run-forever"
                out = run_cmd_in_docker_with_output(addr, cmd)
                print(out)
                #out = out.decode("utf-8")
                out = out.split("\n")
                last_line = out[-2]
                results[replay] = json.loads(last_line)
            except Exception as e:
                print("Error", addr, replay, e)

    with open(f"{base_dir}/{addr}.json", "w+") as fp:
        json.dump(results, fp) 

if __name__ == "__main__":
    # sudo python3 scripts/replay_coverage.py output/result-B1-compare/smartian/B1-noarg-smartian-1/ smartian
    if len(sys.argv) != 3:
        print("Usage: python replay_coverage.py <base_directory> <tool_name>")
        sys.exit(1)

    base_dir = sys.argv[1]
    tool_name = sys.argv[2]
    addresses = [[d, ""] for d in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, d))]
    while len(addresses) > 0:
        work_targets = fetch_works(addresses)
        spawn_containers(work_targets, "evaluation-artifact")
        for addr in work_targets:
            run(addr[0], base_dir, tool_name)
        cleanup_containers(work_targets)