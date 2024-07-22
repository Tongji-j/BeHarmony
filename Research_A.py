import time
import random
from web3 import Web3
import json
import statistics
import threading
from queue import Queue

# Set up the log file
log_file = open("logPBFT.txt", "w")

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
hash = Example.constructor().transact({'from': node.eth.accounts[0]})
tx_receipt = node.eth.wait_for_transaction_receipt(hash)
contract = node.eth.contract(address=tx_receipt.contractAddress, abi=contract_abi)

# Set default account
default_account = node.eth.accounts[0]
node.eth.defaultAccount = default_account

# RSU accounts
rsus = node.eth.accounts[0:5]  # 5 RSU accounts

# Randomly generate signature and address information
def generate_signature():
    return Web3.keccak(text=str(random.randint(0, int(1e10)))).hex()
malicious_nodes = random.sample(rsus, random.randint(0, 1))

# Create global state and lock
global_state = {
    'prepare_counts': {rsu: {'prepare': 0, 'not_prepare': 0} for rsu in rsus},
    'commit_counts': {rsu: {'commit': 0, 'not_commit': 0} for rsu in rsus},
    'verify_results': [],
    'primary_rsu': random.choice(rsus),
    'threshold': 3,  # 2f + 1 for f=1
    'f': 1
}
state_lock = threading.Lock()

def rsu_thread(rsu, request_msg, state, state_lock, q, identity, address):
    global contract
    f = state['f']
    threshold = state['threshold']
    malicious_nodes = random.sample(rsus, random.randint(0, 1))
    
    with state_lock:
        primary_rsu = state['primary_rsu']

    # Pre-prepare phase
    if rsu == primary_rsu:
        pre_prepare_msg = f"pre-prepare message from {primary_rsu}"
        log_print(pre_prepare_msg)
    
    # Prepare phase
    if rsu in malicious_nodes:
        prepare_msg = "not_prepare"
    else:
        prepare_msg = "prepare"

    with state_lock:
        for target_rsu in rsus:
            state['prepare_counts'][target_rsu][prepare_msg] += 1

    # Commit phase
    with state_lock:
        prepare_count = state['prepare_counts'][rsu]['prepare']
        not_prepare_count = state['prepare_counts'][rsu]['not_prepare']

    if prepare_count + not_prepare_count >= threshold:
        if prepare_count >= f + 1:
            if rsu in malicious_nodes:
                commit_msg = "not_commit"
            else:
                commit_msg = "commit"

            log_print(rsu)
            with state_lock:
                for target_rsu in rsus:
                    state['commit_counts'][target_rsu][commit_msg] += 1

    # Reply phase
    with state_lock:
        commit_count = state['commit_counts'][rsu]['commit']
        not_commit_count = state['commit_counts'][rsu]['not_commit']

    if commit_count + not_commit_count >= threshold:
        if commit_count >= f + 1:
            if rsu in malicious_nodes:
                response = not contract.functions.verifyI(identity, address).call({'from': rsu})
            else:
                response = contract.functions.verifyI(identity, address).call({'from': rsu})
            
            with state_lock:
                state['verify_results'].append(response)
                reply_msg = f"reply message from {rsu} with result {response}"
                log_print(reply_msg)
    
    q.put(state)

def bft_process(identity, address):
    request_msg = f"request message from client with identity {identity} and address {address}"
    threads = []
    q = Queue()
    
    for rsu in rsus:
        t = threading.Thread(target=rsu_thread, args=(rsu, request_msg, global_state, state_lock, q, identity, address))
        t.start()
        threads.append(t)
    

    for t in threads:
        t.join()

    final_state = q.get()
    true_count = final_state['verify_results'].count(True)
    false_count = final_state['verify_results'].count(False)
    final_result = True if true_count >= final_state['threshold'] else False

    return final_result

# Run BFT process and record time
def run_bft_experiment(n, filename):
    times = []
    for i in range(n):
        start_time = time.time()  # Record start time
        identity = generate_signature()
        address = generate_signature()
        bft_process(identity, address)
        elapsed_time = time.time() - start_time  # Calculate elapsed time
        if i > 0:
            times.append(elapsed_time)
        log_print(f"Experiment {i}/{n-1} completed in {elapsed_time} seconds.")
    with open(filename, "w") as result_file:
        for t in times:
            result_file.write(f"{t}\n")
        success_count = len(times)
        result_file.write("\n")
        result_file.write(f"Total Experiments: {n-1}\n")
        result_file.write(f"Successful Experiments: {success_count}\n")
        if success_count > 0:
            avg_time = statistics.mean(times)
            tps = 1 / avg_time
            result_file.write(f"Average Time: {avg_time} seconds\n")
            result_file.write(f"TPS: {tps}\n")

# Record multiple experimental results
def record_bft_experiments():
    experiment_counts = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
    # experiment_counts = [1]
    for count in experiment_counts:
        log_print(f"Running {count} experiments...")
        run_bft_experiment(count + 1, f"result_bft_time_{count}.txt")

record_bft_experiments()