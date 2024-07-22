from web3 import Web3
import json
import random
import time
import statistics

# Set up the log file
log_file = open("logA1.txt", "w")

def log_print(*args):
    message = " ".join(map(str, args))
    log_file.write(message + "\n")  # Write to the log file

# Connect to the Geth node
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
cars = node.eth.accounts[5:7]       # Vehicle accounts
components = node.eth.accounts[7:13] # Component accounts (abcdef)

# Randomly generate signature and address information
def generate_signature():
    return Web3.keccak(text=str(random.randint(0, int(1e10)))).hex()

def generate_address():
    return Web3.keccak(text=str(random.randint(0, int(1e10))))[-20:].hex()

# Randomly select an RSU node
def select_random_rsu():
    return random.choice(rsus)

# BeMutual process function
def bemutual_process():
    start_time = time.time()  # Record start time
    log_print("Step 1-2: Upload mapping information of each component to the RSU's blockchain")
    signature_a = generate_signature()
    add_a = generate_address()
    signature_b = generate_signature()
    add_b = generate_address()
    signature_c = generate_signature()
    add_c = generate_address()
    signature_d = generate_signature()
    add_d = generate_address()
    signature_e = generate_signature()
    signature_f = generate_signature()

    tx_hash1 = contract.functions.uploadI(str(components[0]), add_a, signature_a.encode()).transact({'from': components[0]})
    node.eth.wait_for_transaction_receipt(tx_hash1)
    tx_hash2 = contract.functions.uploadI(str(components[1]), add_b, signature_b.encode()).transact({'from': components[1]})
    node.eth.wait_for_transaction_receipt(tx_hash2)
    tx_hash3 = contract.functions.uploadI(str(components[2]), add_c, signature_c.encode()).transact({'from': components[2]})
    node.eth.wait_for_transaction_receipt(tx_hash3)
    tx_hash4 = contract.functions.uploadI(str(components[3]), add_d, signature_d.encode()).transact({'from': components[3]})
    node.eth.wait_for_transaction_receipt(tx_hash4)
    tx_hash5 = contract.functions.uploadII(str(cars[0]), str(components[0]), add_a, "label_a", signature_e.encode(), "label_e").transact({'from': components[4]})
    node.eth.wait_for_transaction_receipt(tx_hash5)
    tx_hash6 = contract.functions.uploadII(str(cars[1]), str(components[3]), add_d, "label_d", signature_f.encode(), "label_f").transact({'from': components[5]})
    node.eth.wait_for_transaction_receipt(tx_hash6)

    log_print("Step 3-5: Car 1's e sends identity request to Car 2's b, then to c, then to f")
    log_print("a sends request to b")
    log_print("b sends request to c")
    log_print("c sends request to f")

    log_print("Step 6-9: f verifies with d and responds")
    rsu = select_random_rsu()
    response = contract.functions.verifyI(str(components[1]), add_b).call({'from': rsu})
    if response:
        log_print("RSU verification successful, transmitting public key")
        # Simulate public key transmission
        public_key = generate_signature()
    else:
        log_print("RSU verification failed")
        return None

    log_print("Step 10-11: c responds to b, b responds to e")
    # The actual response process is abbreviated here with print statements, can be detailed as needed
    log_print("c responds to b")
    log_print("b responds to e")

    log_print("Step 12-14: e verifies with a, a verifies with RSU, RSU responds to a, a responds to e")
    log_print("e verifies with a")
    response = contract.functions.verifyI(str(components[2]), add_c).call({'from': rsu})
    if response:
        log_print("RSU verification successful, transmitting session key")
        session_key = generate_signature()
    else:
        log_print("RSU verification failed")
        return None

    log_print("Step 15-17: e sends session key to b, b sends it to c, c sends it to f")
    # The actual key transmission process is abbreviated here with print statements, can be detailed as needed
    log_print("e sends session key to b")
    log_print("b sends session key to c")
    log_print("c sends session key to f")

    log_print("Session establishment successful")
    end_time = time.time()  # Record end time
    elapsed_time = end_time - start_time
    return elapsed_time

# Simulate communication and record time
def simulate_communication():
    return bemutual_process()

# Run experiments and record time
def run_experiments(n, filename):
    times = []
    for i in range(n):
        log_print(f"Experiment {i+1}/{n}")
        elapsed_time = simulate_communication()
        if elapsed_time is not None:
            times.append(elapsed_time)
            log_print(f"Completion time: {elapsed_time} seconds")
        log_print("---------------------------------------------------------")
    with open(filename, "w") as result_file:
        for t in times:
            result_file.write(f"{t}\n")
        success_count = len(times)
        result_file.write("\n")
        result_file.write(f"Total experiments: {n}\n")
        result_file.write(f"Successful experiments: {success_count}\n")
        if success_count > 0:
            avg_time = statistics.mean(times)
            tps = 1 / avg_time
            result_file.write(f"Average time: {avg_time} seconds\n")
            result_file.write(f"TPS: {tps}\n")

# Record multiple experiments
def record_experiments():
    # experiment_counts = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
    experiment_counts = [1]
    for count in experiment_counts:
        log_print(f"Running {count} experiments...")
        run_experiments(count, f"result_time_{count}.txt")

record_experiments()

# Close the log file
log_file.close()