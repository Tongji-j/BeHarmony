from web3 import Web3
import json
import random
import time
import math
import sys
import statistics

# Set up log file
log_file = open("logB3.txt", "w")

def log_print(*args):
    message = " ".join(map(str, args))
    log_file.write(message + "\n")  # Write to log file

# Connect to the Geth node
node = Web3(Web3.HTTPProvider('http://127.0.0.1:8546'))

# Check connection
if not node.is_connected():
    raise Exception(f"Unable to connect to Ethereum node {node.provider.endpoint_uri}")

# Load smart contract
with open('build/contracts/IoVContract.json') as f:
    contract_json = json.load(f)
    contract_abi = contract_json['abi']
    bytecode = contract_json['bytecode']

# Deploy smart contract
Example = node.eth.contract(abi=contract_abi, bytecode=bytecode)
hash = Example.constructor().transact({
    'from': node.eth.accounts[0]
})
tx_receipt = node.eth.wait_for_transaction_receipt(hash)
contract = node.eth.contract(address=tx_receipt.contractAddress, abi=contract_abi)

# Set default account
default_account = node.eth.accounts[0]
node.eth.defaultAccount = default_account

# RSU and vehicle accounts
rsus = node.eth.accounts[0:6]  # 6 RSU accounts
car = node.eth.accounts[6]     # Vehicle account
components = node.eth.accounts[7:9]  # Component accounts (a and e)

# Vehicle communication range and speed
comm_range = 7
car_speed = 1

# Randomly generate signature and address information
def generate_signature():
    return Web3.keccak(text=str(random.randint(0, int(1e10)))).hex()

def generate_address():
    return Web3.keccak(text=str(random.randint(0, int(1e10))))[-20:].hex()

# Assign add to valid RSUs
adds = []
for i in range(len(rsus)):
    rsu_add = generate_address()
    signature_rsu = generate_signature()
    tx_hash = contract.functions.uploadI(str(rsus[i]), rsu_add, signature_rsu.encode()).transact({'from': rsus[i]})
    node.eth.wait_for_transaction_receipt(tx_hash)
    adds.append(rsu_add)

# Poisson distribution random points
def poisson_point(radius):
    L = math.exp(-radius)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1

# Initialize RSU positions
def initialize_rsus(car_position):
    rsu_positions = []
    for i in range(6):
        while True:
            distance = poisson_point(comm_range)
            angle = random.uniform(0, 2 * math.pi)
            x = car_position[0] + distance * math.cos(angle)
            y = car_position[1] + distance * math.sin(angle)
            if distance < comm_range:
                rsu_positions.append((x, y))
                break
    return rsu_positions

# Calculate distance
def calculate_distance(pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

# Simulate vehicle movement
def move_car(car_position):
    return (car_position[0] + car_speed, car_position[1])

# Expulsion process
def expulsion_process(index, old_rsu, old_rsu_add):
    log_print(f"Expulsion process: Verifying old RSU {old_rsu}, index {index}")
    valid_responses = 0
    for rsu in current_rsus:
        response = contract.functions.verifyI(str(old_rsu), old_rsu_add).call({'from': rsu})
        if response:
            valid_responses += 1
    if valid_responses > len(current_rsus) // 3:
        log_print(f"Old RSU {old_rsu}, index {index} verified successfully, expulsion allowed")
        current_rsus.discard(old_rsu)
        return True
    else:
        log_print(f"Old RSU {old_rsu}, index {index} verification failed, expulsion denied")
        return False

# Vehicle moving process function
def vehicle_moving():
    log_print("Starting vehicle moving process")

    ret = 0
    car_position = (0, 0)
    rsu_positions = initialize_rsus(car_position)

    # Initial 6 RSUs within communication range
    global current_rsus
    current_rsus = set(rsus[:6])

    end = False
    for step in range(10):  # Simulate 10 time steps
        car_position = move_car(car_position)

        # Detect if new RSU enters communication range
        for i, rsu_position in enumerate(rsu_positions):
            if calculate_distance(car_position, rsu_position) > comm_range:
                log_print(f"Detected loss of contact with an RSU")
                start_time = time.time()  # Expulsion process start time
                if expulsion_process(i, rsus[i], adds[i]):
                    elapsed_time = time.time() - start_time  # Calculate expulsion process time
                    ret = (1, elapsed_time)
                else:
                    elapsed_time = time.time() - start_time  # Calculate expulsion process time
                    ret = (0, elapsed_time)
                end = True
                break
        
        # time.sleep(1)  # Simulate vehicle travel time interval
        # Check if the process is completed
        if end:
            break
    if not end:
        log_print(f"No RSU communication disconnection detected during the experiment")
        ret = (2, None)
     
    log_print("Vehicle moving process ended")
    return ret

# Simulate communication
def simulate_communication():
    return vehicle_moving()

# Run experiments and record time
def run_experiments(n, filename):
    times = []
    success_count = 0
    disconnect_count = 0
    for i in range(n):
        log_print(f"Experiment {i+1}/{n}")
        result, elapsed_time = simulate_communication()
        if elapsed_time is not None:
            times.append(elapsed_time)
            log_print(f"Completion time: {elapsed_time} seconds")
        if result == 1:
            success_count += 1
        elif result == 2:
            disconnect_count += 1
        log_print("---------------------------------------------------------")

    
    with open(filename, "w") as result_file:
        for t in times:
            result_file.write(f"{t}\n")
        result_file.write("\n")
        result_file.write(f"Total attempts: {n}\n")
        result_file.write(f"Successful attempts: {success_count}\n")
        result_file.write(f"Invalid experiments: {disconnect_count}\n")
        if success_count > 0:
            avg_time = statistics.mean(times)
            tps = 1 / avg_time
            result_file.write(f"Average time: {avg_time} seconds\n")
            result_file.write(f"TPS: {tps}\n")

# Record multiple experiment results
def record_experiments():
    experiment_counts = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
    for count in experiment_counts:
        log_print(f"Running {count} experiments...")
        run_experiments(count, f"result_rsu_out_time_{count}.txt")

record_experiments()

# Close log file
log_file.close()