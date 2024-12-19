import os
import json
from web3 import Web3
import sys

def int_to_byte32(value):
    return Web3.to_hex(Web3.to_bytes(value).rjust(32, b'\0'))

NORMAL = {
    "input_type": "ABI",
    "caller": "0x35c9dfd76bf02107ff4f7128bd69716612d31ddb",
    "contract": "0x37e42b961ae37883bac2fc29207a5f88efa5db66",
    "direct_data": "",
    "txn_value": None, "step": False,
    "env": {
        "cfg": {
            "chain_id": "0x0000000000000000000000000000000000000000000000000000000000000001",
            "spec_id": "LATEST",
            "perf_analyse_created_bytecodes": "Analyse",
            "limit_contract_code_size": None
        },
        "block": {
            "number": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "coinbase": "0x0000000000000000000000000000000000000000",
            "timestamp": "0x0000000000000000000000000000000000000000000000000000000000000001",
            "difficulty": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "prevrandao": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "basefee": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "gas_limit": "0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
        },
        "tx": {
            "caller": "0x0000000000000000000000000000000000000000",
            "gas_limit": 18446744073709551615,
            "gas_price": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "gas_priority_fee": None,
            "transact_to": {"Call": "0x0000000000000000000000000000000000000000"},
            "value": "0x0000000000000000000000000000000000000000000000000000000000000000",
            "data": "0x",
            "chain_id": None,
            "nonce": None,
            "access_list": []
        }
    },
    "liquidation_percent": 0,
    "randomness": [0],
    "repeat": 1,
    "layer": 0,
    "call_leak": 4294967295
}

TEST = sys.argv[1]
BENCHMARKDIR = sys.argv[2]
ABI_PATH = f"{BENCHMARKDIR}/{TEST}/abi/"
BIN_PATH = f"{BENCHMARKDIR}/{TEST}/bin/"

def get_static_calls(addr):
    abi = json.load(open(ABI_PATH + addr + ".abi"))
    statics = []
    for i in abi:
        if "constant" in i and i["constant"] == True:
            statics.append(i["name"])
        if "stateMutability" in i and i["stateMutability"] in ["view", "pure"]:
            statics.append(i["name"])
    return statics


def copy_tests(addr, tool_name):
    abi = ABI_PATH + addr + ".abi"
    bin = BIN_PATH + addr + ".bin"
    os.system("rm -rf deployment-{tool_name}/{addr} && mkdir -p deployment-{tool_name}/{addr}".format(addr=addr, tool_name=tool_name))

    os.system("cp {abi} deployment-{tool_name}/{addr}/".format(abi=abi, addr=addr, tool_name=tool_name))
    os.system("cp {bin} deployment-{tool_name}/{addr}/".format(bin=bin, addr=addr, tool_name=tool_name))

    with open("deployment-{tool_name}/{addr}/{addr}.address".format(addr=addr, tool_name=tool_name), "w+") as fp:
        fp.write("6b773032d99fb9aad6fc267651c446fa7f9301af")


def convert(obj, statics):
    txs = obj["Txs"]
    results = []
    for i in txs:
        skip = False
        for static in statics:
            if static in i["Function"]:
                print(f"skipping: {static} in {i['Function']}")
                skip = True
                break
        if skip:
            continue
        result = NORMAL.copy()
        result["caller"] = "0x35c9dfd76bf02107ff4f7128bd69716612d31ddb"
        result["contract"] = "6b773032d99fb9aad6fc267651c446fa7f9301af"
        result["txn_value"] = int_to_byte32(int(i["Value"]))
        result["direct_data"] = i["Data"].lower()
        result["env"]["block"]["timestamp"] = int_to_byte32(int(i["Timestamp"] if "Timestamp" in i else "0"))
        result["env"]["block"]["number"] = int_to_byte32(int(i["Blocknum"] if "Blocknum" in i else "0"))
        results.append(result)
    if not txs:
        print("No transactions found")
    return "\n".join([json.dumps(x) for x in results])

if __name__ == "__main__":
    # sudo python3 scripts/convert_to_replayable.py B1 benchmarks output/result-B1-compare/mythril/B1-noarg-mythril-1 mythril
    if len(sys.argv) != 5:
        print("Usage: python convert_to_replayable.py <dataset_name> <path_to_dataset> <path_to_output_dir> <tool_name>")
        sys.exit(1)

    smartian_outs_path = sys.argv[3]
    tool_name = sys.argv[4]

    for addr in os.listdir(smartian_outs_path):
        base = f"{smartian_outs_path}/{addr}/testcase/"
        statics = get_static_calls(addr)
        copy_tests(addr, tool_name)
        for i in os.listdir(base):
            if i.endswith("_replayable"):
                continue
            fn = base + i
            with open(fn + "_replayable", "w+") as fp:
                conveted_tx = convert(json.load(open(fn)), statics)
                fp.write(conveted_tx)