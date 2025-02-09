import sys, os, subprocess, time
from subprocess import PIPE
from common import BASE_DIR, BENCHMARK_DIR

IMAGE_NAME = "smartian-artifact"
ITYFUZZ_IMAGE = "ityfuzz-artifact"
MAX_INSTANCE_NUM = 12
AVAILABLE_BENCHMARKS = ["B1", "B1-noarg", "B2", "B3"]
SUPPORTED_TOOLS = ["smartian", "sFuzz", "mythril", "ityfuzz"]


def run_cmd(cmd_str, check=True):
    print("[*] Executing command '%s'" % cmd_str)
    args = cmd_str.split()
    try:
        p = subprocess.run(args, check=check, stdout=PIPE, stderr=PIPE)
        return p.stdout
    except Exception as e:
        print(e)
        exit(1)


def run_cmd_in_docker(container, cmd_str, check=True):
    print("[*] Executing '%s' in container %s" % (cmd_str, container))
    docker_prefix = "docker exec -d %s /bin/bash -c" % container
    args = docker_prefix.split() + [cmd_str]
    try:
        p = subprocess.run(args, check=check, stdout=PIPE, stderr=PIPE)
        return p.stdout
    except Exception as e:
        print(e)
        exit(1)

def run_cmd_in_docker_with_output(container, cmd_str):
    print("[*] Executing '%s' in container %s" % (cmd_str, container))
    docker_prefix = f"docker exec {container} /bin/bash -c"
    args = docker_prefix.split() + [cmd_str]
    result = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0 or result.stderr:
        print(f"Error executing command in Docker: {result.stderr}")
    return result.stdout

def check_cpu_count():
    n_str = run_cmd("sysctl -n hw.ncpu")
    try:
        if int(n_str) < MAX_INSTANCE_NUM:
            print("Not enough CPU cores, please decrease MAX_INSTANCE_NUM")
            exit(1)
    except Exception as e:
        print(e)
        print("Failed to count the number of CPU cores, abort")
        exit(1)

def decide_outdir(benchmark, tool):
    prefix = benchmark + "-" + tool
    i = 0
    while True:
        i += 1
        outdir = os.path.join(BASE_DIR, "output", "%s-%d" % (prefix, i))
        if not os.path.exists(outdir):
            return outdir

def decide_bench_dirname(benchmark):
    if benchmark.startswith("B"):
        return benchmark.split("-")[0]
    else:
        print("Unexpected benchmark: %s" % benchmark)
        exit(1)

def get_targets(benchmark):
    list_name = benchmark + ".list"
    list_path = os.path.join(BENCHMARK_DIR, "assets", list_name)
    f = open(list_path, "r")
    targets = []
    for line in f:
        line = line.strip()
        if line != "":
            line = line.split(',')
            targets.append(line)
    f.close()
    return targets

def fetch_works(targets):
    works = []
    for i in range(MAX_INSTANCE_NUM):
        if len(targets) <= 0:
            break
        works.append(targets.pop(0))
    return works

def spawn_containers(targets, image=IMAGE_NAME):
    for i in range(len(targets)):
        targ = targets[i][0]
        cmd = "docker run --rm -m=6g --cpuset-cpus=%d -it -d --name %s %s" % \
                (i, targ, image)
        run_cmd(cmd)

def run_fuzzing(benchmark, targets, tool, timelimit, opt):
    bench_dirname = decide_bench_dirname(benchmark)
    for targ, name in targets:
        src = "/home/test/benchmarks/%s/sol/%s.sol" % (bench_dirname, targ)
        bin = "/home/test/benchmarks/%s/bin/%s.bin" % (bench_dirname, targ)
        abi = "/home/test/benchmarks/%s/abi/%s.abi" % (bench_dirname, targ)
        args = "%d %s %s %s %s '%s'" % (timelimit, src, bin, abi, name, opt)
        script = "/home/test/scripts/run_%s.sh" % tool
        cmd = "%s %s" % (script, args)
        run_cmd_in_docker(targ, cmd)
    time.sleep(timelimit + 3)

def measure_coverage(benchmark, targets, tool):
    bench_dirname = decide_bench_dirname(benchmark)
    plot_intv = 1 # Plot coverage for each minute.
    for targ, name in targets:
        bin = "/home/test/benchmarks/%s/bin/%s.bin" % (bench_dirname, targ)
        abi = "/home/test/benchmarks/%s/abi/%s.abi" % (bench_dirname, targ)
        args = "%s %s %s %s %d" % (tool, bin, abi, name, plot_intv)
        script = "/home/test/scripts/run_replayer.sh"
        cmd = "%s %s" % (script, args)
        run_cmd_in_docker(targ, cmd)
    time.sleep(3)

def store_outputs(targets, outdir):
    for targ, _ in targets:
        cmd = "docker cp %s:/home/test/output %s/%s" % (targ, outdir, targ)
        run_cmd(cmd)

def cleanup_containers(targets):
    for targ, _ in targets:
        cmd = "docker kill %s" % targ
        run_cmd(cmd)

def main():
    if len(sys.argv) != 4 and len(sys.argv) != 5:
        print("Usage: %s <benchmark> <tool> <timelimit> (cmdopt)" % \
              sys.argv[0])
        exit(1)

    benchmark = sys.argv[1]
    tool = sys.argv[2]
    timelimit = int(sys.argv[3])
    opt = sys.argv[4] if len(sys.argv) == 5 else ""

    check_cpu_count()
    if benchmark not in AVAILABLE_BENCHMARKS:
        print("Unavailable benchmark: %s" % benchmark)
        exit(1)
    if tool not in SUPPORTED_TOOLS:
        print("Unsupported tool: %s" % tool)
        exit(1)
    image_name = IMAGE_NAME if tool != "ityfuzz" else ITYFUZZ_IMAGE

    outdir = decide_outdir(benchmark, tool)
    os.makedirs(outdir)
    targets = get_targets(benchmark)
    while len(targets) > 0:
        work_targets = fetch_works(targets)
        spawn_containers(work_targets, image_name)
        run_fuzzing(benchmark, work_targets, tool, timelimit, opt)
        measure_coverage(benchmark, work_targets, tool)
        store_outputs(work_targets, outdir)
        cleanup_containers(work_targets)

if __name__ == "__main__":
    main()
