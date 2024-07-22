from web3 import Web3
import json
import random
import time
import sys
import statistics
import math

# Set log file
log_file = open("logB2.txt", "w")

def log_print(*args):
    message = " ".join(map(str, args))
    log_file.write(message + "\n")  # Also write to log file

# Connect to the unique Geth node
node = Web3(Web3.HTTPProvider('http://127.0.0.1:8546'))

# Check connection
if not node.is_connected():
    raise Exception(f"Cannot connect to Ethereum node {node.provider.endpoint_uri}")

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

# Set default account
default_account = node.eth.accounts[0]
node.eth.defaultAccount = default_account

# RSU and vehicle accounts
rsus = node.eth.accounts[1:7]  # 6 RSU accounts
car = node.eth.accounts[0]     # Vehicle account
components = node.eth.accounts[8:10]  # Component accounts (a and e)

# Vehicle's communication range and speed
comm_range = 7
car_speed = 1

# Randomly generate signature and address information
def generate_signature():
    return Web3.keccak(text=str(random.randint(0, int(1e10)))).hex()

def generate_address():
    return Web3.keccak(text=str(random.randint(0, int(1e10))))[-20:].hex()

# Assign addresses to legal rsus
adds = []
for i in range(len(rsus)):
    rsu_add = generate_address()
    signature_rsu = generate_signature()
    if i == 5:
        tx_hash = contract.functions.uploadI(str(rsus[i]), rsu_add, signature_rsu.encode()).transact({'from': rsus[i]})
        node.eth.wait_for_transaction_receipt(tx_hash)
    adds.append(rsu_add)

# Poisson distribution random point generation
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
    for i in range(5):
        while True:
            distance = poisson_point(comm_range)
            angle = random.uniform(0, 2 * math.pi)
            x = car_position[0] + distance * math.cos(angle)
            y = car_position[1] + distance * math.sin(angle)
            if distance < comm_range:
                rsu_positions.append((x, y))
                break

    # The 6th RSU is in the vehicle's direction of travel but initially out of communication range
    distance = random.uniform(comm_range + 1, 10 * comm_range)
    angle = random.uniform(- math.pi, math.pi)
    x = car_position[0] + distance * math.cos(angle)
    y = car_position[1] + distance * math.sin(angle)
    rsu_positions.append((x, y))

    return rsu_positions

# Calculate distance
def calculate_distance(pos1, pos2):
    return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

# Simulate vehicle movement
def move_car(car_position):
    return (car_position[0] + car_speed, car_position[1])

# Admission process
def admission_process(new_rsu, new_rsu_add):
    log_print(f"Admission process: Verifying new RSU {new_rsu}")
    valid_responses = 0
    for rsu in current_rsus:
        response = contract.functions.verifyI(str(new_rsu), new_rsu_add).call({'from': rsu})
        if response:
            valid_responses += 1
    if valid_responses > len(current_rsus) // 3:
        log_print(f"RSU {new_rsu} verification succeeded, admission granted")
        current_rsus.add(new_rsu)
        return True
    else:
        log_print(f"RSU {new_rsu} verification failed, admission denied")
        return False

# Vehicle moving process function
def vehicle_moving(is_legal):
    log_print("Starting vehicle moving process")

    ret = 0
    car_position = (0, 0)
    rsu_positions = initialize_rsus(car_position)

    # Initial 5 RSUs are within communication range
    global current_rsus
    current_rsus = set(rsus[:5])

    end = False
    for step in range(10):  # Simulate 10 time steps
        car_position = move_car(car_position)

        # Check if a new RSU has entered the communication range
        for i, rsu_position in enumerate(rsu_positions):
            if calculate_distance(car_position, rsu_position) < comm_range:
                if rsus[i] not in current_rsus:
                    log_print(f"New RSU detected")
                    start_time = time.time()  # Admission process start time
                    if admission_process(rsus[i], adds[i]):
                        elapsed_time = time.time() - start_time  # Calculate admission process time
                        ret = (1, elapsed_time)
                    else:
                        elapsed_time = time.time() - start_time  # Calculate admission process time
                        ret = (0, elapsed_time)
                    end = True
                    break

        # Check if the process has been completed
        if end:
            break
    if not end:
        log_print(f"No new RSU detected")
        ret = (2, None)

    log_print("Vehicle moving process completed")
    return ret

# Simulate communication
def simulate_communication(is_legal):
    return vehicle_moving(is_legal)

# Run experiments and record time
def run_experiments(n, filename, is_legal):
    times = []
    success_count = 0
    dis_connect_count = 0
    for i in range(n):
        log_print(f"Experiment {i+1}/{n}")
        result, elapsed_time = simulate_communication(is_legal)
        if elapsed_time is not None:
            times.append(elapsed_time)
            log_print(f"Completion time: {elapsed_time} seconds")
        if result == is_legal:
            success_count += 1
        elif result == 2:
            dis_connect_count += 1
        log_print("---------------------------------------------------------")
        # time.sleep(1)  # Add delay to avoid overload

    with open(filename, "w") as result_file:
        for t in times:
            result_file.write(f"{t}\n")
        result_file.write("\n")
        result_file.write(f"Total number of experiments: {n}\n")
        result_file.write(f"Number of successful experiments: {success_count}\n")
        result_file.write(f"Number of invalid experiments: {dis_connect_count}\n")
        if success_count > 0:
            avg_time = statistics.mean(times)
            tps = 1 / avg_time
            result_file.write(f"Average time: {avg_time} seconds\n")
            result_file.write(f"TPS: {tps}\n")

# Record results of multiple experiments
def record_experiments():
    experiment_counts = [1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000]
    for count in experiment_counts:
        log_print(f"Running {count} experiments...")
        run_experiments(count, f"result_valid_rsu_time_without_limit_{count}.txt", is_legal=True)

record_experiments()

# Close log file
log_file.close()