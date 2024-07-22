from web3 import Web3
import json
import random
import time
import statistics

# Connect to a single Geth node
node = Web3(Web3.HTTPProvider('http://127.0.0.1:8546'))

# Check connection
if not node.is_connected():
    raise Exception(f"Unable to connect to Ethereum node {node.provider.endpoint_uri}")

# Load the smart contract
with open('build/contracts/IoVContract.json') as f:
    contract_json = json.load(f)
    contract_abi = contract_json['abi']
    bytecode = contract_json['bytecode']

# Deploy the smart contract
Example = node.eth.contract(abi=contract_abi, bytecode=bytecode)
hash = Example.constructor().transact({
    'from': node.eth.accounts[0]
})
tx_receipt = node.eth.wait_for_transaction_receipt(hash)
contract = node.eth.contract(address=tx_receipt.contractAddress, abi=contract_abi)

# Set the default account
default_account = node.eth.accounts[0]
node.eth.defaultAccount = default_account

# Vehicle and RSU accounts
rsus = node.eth.accounts[0:5]       # RSU accounts
components = node.eth.accounts[7:13] # Component accounts (abcdef)

# Randomly generate signature and address information
def generate_signature():
    return Web3.keccak(text=str(random.randint(0, int(1e10)))).hex()

def generate_address():
    return Web3.keccak(text=str(random.randint(0, int(1e10))))[-20:].hex()

# Test TPS for uploadI transaction
def test_uploadI(n, filename):
    times = []
    for i in range(n):
        start_time = time.time()
        signature_a = generate_signature()
        add_a = generate_address()
        tx_hash = contract.functions.uploadI(str(components[0]), add_a, signature_a.encode()).transact({'from': components[0]})
        node.eth.wait_for_transaction_receipt(tx_hash)
        end_time = time.time()
        elapsed_time = end_time - start_time
        times.append(elapsed_time)

    with open(filename, "w") as result_file:
        for t in times:
            result_file.write(f"{t}\n")
        success_count = len(times)
        result_file.write("\n")
        result_file.write(f"Total number of experiments: {n}\n")
        result_file.write(f"Successful experiments: {success_count}\n")
        if success_count > 0:
            avg_time = statistics.mean(times)
            tps = 1 / avg_time
            result_file.write(f"Average time: {avg_time} seconds\n")
            result_file.write(f"TPS: {tps}\n")

# Test TPS for verifyI transaction
def test_verifyI(n, filename):
    times = []
    rsu = random.choice(rsus)
    signature_a = generate_signature()
    add_a = generate_address()
    tx_hash = contract.functions.uploadI(str(components[0]), add_a, signature_a.encode()).transact({'from': components[0]})
    node.eth.wait_for_transaction_receipt(tx_hash)

    for i in range(n):
        start_time = time.time()
        response = contract.functions.verifyI(str(components[0]), add_a).call({'from': rsu})
        end_time = time.time()
        elapsed_time = end_time - start_time
        times.append(elapsed_time)

    with open(filename, "w") as result_file:
        for t in times:
            result_file.write(f"{t}\n")
        success_count = len(times)
        result_file.write("\n")
        result_file.write(f"Total number of experiments: {n}\n")
        result_file.write(f"Successful experiments: {success_count}\n")
        if success_count > 0:
            avg_time = statistics.mean(times)
            tps = 1 / avg_time
            result_file.write(f"Average time: {avg_time} seconds\n")
            result_file.write(f"TPS: {tps}\n")

# Test TPS for updateI transaction
def test_updateI(n, filename):
    times = []
    rsu = random.choice(rsus)
    signature_a = generate_signature()
    add_a = generate_address()
    tx_hash = contract.functions.uploadI(str(components[0]), add_a, signature_a.encode()).transact({'from': components[0]})
    node.eth.wait_for_transaction_receipt(tx_hash)

    for i in range(n):
        start_time = time.time()
        new_add_a = generate_address()
        tx_hash = contract.functions.updateI(str(components[0]), add_a, new_add_a).transact({'from': components[0]})
        node.eth.wait_for_transaction_receipt(tx_hash)
        end_time = time.time()
        elapsed_time = end_time - start_time
        times.append(elapsed_time)

    with open(filename, "w") as result_file:
        for t in times:
            result_file.write(f"{t}\n")
        success_count = len(times)
        result_file.write("\n")
        result_file.write(f"Total number of experiments: {n}\n")
        result_file.write(f"Successful experiments: {success_count}\n")
        if success_count > 0:
            avg_time = statistics.mean(times)
            tps = 1 / avg_time
            result_file.write(f"Average time: {avg_time} seconds\n")
            result_file.write(f"TPS: {tps}\n")

# Run experiments and record time
def run_experiments():
    experiment_counts = range(1000, 11000, 1000)
    experiment_counts = [1]
    for count in experiment_counts:
        test_uploadI(count, f"result_upload_{count}.txt")
        test_verifyI(count, f"result_verify_{count}.txt")
        test_updateI(count, f"result_update_{count}.txt")

run_experiments()