import numpy as np
from application import AnonymousTransmissionProgram
from squidasm.run.stack.config import StackNetworkConfig
from squidasm.run.stack.run import run

nodes = ["Alice", "Bob", "Charlie", "David"]

# Goal 5: Import your noisy network configuration
cfg = StackNetworkConfig.from_file("config.yaml")

# Create instances (Note: Alice is the sender, send_bit=True)
alice_program = AnonymousTransmissionProgram(node_name="Alice", node_names=nodes, send_bit=True)
bob_program = AnonymousTransmissionProgram(node_name="Bob", node_names=nodes)
charlie_program = AnonymousTransmissionProgram(node_name="Charlie", node_names=nodes)
david_program = AnonymousTransmissionProgram(node_name="David", node_names=nodes)

programs = {
    "Alice": alice_program, 
    "Bob": bob_program,
    "Charlie": charlie_program, 
    "David": david_program
}

# Goal 5: Run the simulation 100 times to create reliable results
NUM_RUNS = 100
print(f"Executing {NUM_RUNS} simulation runs...")
results = run(config=cfg, programs=programs, num_times=NUM_RUNS)

# --- POST-PROCESSING DATA ---
# Alice is at index 0, David is at index 3
# Let's check success from David's perspective
success_count = 0
total_duration = 0
expected_byte = [1, 0, 1, 1, 0, 1, 0, 1] # Ensure this matches your application.py

for i in range(NUM_RUNS):
    # results[node_index][run_index]
    run_data = results[3][i] 
    
    if run_data["received_byte"] == expected_byte:
        success_count += 1
    
    total_duration += run_data["duration_ns"]

# Goal 3 & 5: Calculate and Print Averages
avg_success_prob = (success_count / NUM_RUNS) * 100
avg_speed = (8 * 1e9) / (total_duration / NUM_RUNS) # Bits per second

print("\n" + "="*30)
print("   FINAL ANALYST REPORT")
print("="*30)
print(f"Average Success Probability: {avg_success_prob:.2f}%")
print(f"Average Transmission Speed:   {avg_speed:.2f} bps")
print("="*30)