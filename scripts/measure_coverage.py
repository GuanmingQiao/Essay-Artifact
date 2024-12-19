
import math
import os
import json
import sys 
import tqdm
import matplotlib.pyplot as plt

total_time = 120
total_instr_possible = 0

# ItyFuzz coverage parsing
def parse_coverage(dir):
    global total_instr_possible
    spots = []
    max_instr_possible = {} # addr -> max_instr_possible
    for i in os.listdir(dir):
        if not i.endswith(".json"):
            continue

        cov = json.load(open(os.path.join(dir, i)))
        total_instr_cov = 0
        total_branch_cov = 0
        for (k, v) in cov.items():
            total_instr_cov += v["instruction_coverage"]
            total_branch_cov += v["branch_coverage"]
            max_instr_possible[k] = v["total_instructions"]
        ts = int(i.split("_")[1].split(".")[0])
        spots.append((ts, total_instr_cov, total_branch_cov))
    total_instr_possible += sum(max_instr_possible.values())
    return spots

def get_starting_time(addr):
    if len(results[addr]) == 0:
        return 0
    return min([i[0] for i in results[addr]])

if __name__ == "__main__":
    # sudo python3 scripts/measure_coverage.py output/result-B1-compare/ityfuzz/B1-noarg-ityfuzz-1 output/result-B1-compare/smartian/B1-noarg-smartian-1
    if len(sys.argv) != 3:
        print("Usage: python measure_coverage.py <ityfuzz_out> <smartian_out>")
        sys.exit(1)

    ityfuzz_out = sys.argv[1]
    smartian_out = sys.argv[2]
    
    results = {}
    for addr in tqdm.tqdm(os.listdir(ityfuzz_out)):
        # with open(f"{ityfuzz_out}/{addr}/log.txt") as f:
        #         if "Failed to deploy contract" in f.read():
        #             continue
        coverage_path = os.path.join(ityfuzz_out, addr, "coverage")
        cov = parse_coverage(coverage_path)
        results[addr] = cov


    starting_times = {
        addr: get_starting_time(addr) for addr in results
    }

    x_ityfuzz = [x for x in range(0, total_time)]
    y_ityfuzz = [0 for _ in x_ityfuzz]

    for i in range(total_time):
        y_at_i = 0
        for (addr, arr) in results.items():
            addr_y = []
            for (ts, ins, branch) in arr:
                # based on microsecond
                if (ts - starting_times[addr])/ 1000000 <= i:
                    addr_y.append(ins)
            if len(addr_y) > 0:
                y_at_i += max(addr_y)
        y_ityfuzz[i] = y_at_i
    print("ItyFuzz Data Fully Parsed!")


    # Smartian Coverage Parsing

    # second => set((addr, pc))
    covs = {i: set() for i in range(total_time)}

    for i in os.listdir(smartian_out):
        if not i.endswith(".json"):
            continue
        cov = json.load(open(os.path.join(smartian_out, i)))

        for fn, j in cov.items():
            ts = int(math.floor(float(fn.split("_")[1])))
            if "0x6b773032d99fb9aad6fc267651c446fa7f9301af" in j:
                for pc in j["0x6b773032d99fb9aad6fc267651c446fa7f9301af"]:
                    covs[ts].add((i, pc))

    # accumulate
    for i in tqdm.tqdm(range(1, total_time)):
        covs[i] = covs[i].union(covs[i-1])

    x_smartian = []
    y_smartian = []

    for k, v in covs.items():
        x_smartian.append(k)
        y_smartian.append(len(v))

    print("Smartian Data Fully Parsed!")


    print("ItyFuzz Final Coverage:", y_ityfuzz[-1])
    print("Smartian Final Coverage:", y_smartian[-1])
    print("Total Instruction Possible:", total_instr_possible)

    plt.ylim(0, max(y_ityfuzz[-1], y_smartian[-1]) * 1.1)
    plt.plot([0]+x_ityfuzz[1:], [0] + y_ityfuzz[1:])
    plt.plot([0]+x_smartian[1:], [0] + y_smartian[1:])
    plt.legend(["ItyFuzz", "Smartian"])
    plt.grid()
    plt.savefig("coverage.png")
