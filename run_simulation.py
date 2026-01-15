import time
import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel, QSource, SourceStatus, QuantumMemory
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks
from netsquid.components.models import DepolarNoiseModel, FixedDelayModel

# Import the protocol logic you commented in application.py
from application import anonymous_transmit_bit, majority_vote

ALICE_SECRET = 0  # The bit Alice is sending anonymously

def simulate_abcd_chain():
    """
    Physical Layer Simulation: Alice -> Bob -> Charlie -> David (30km).
    This implements the 'Anonymous Entanglement' primitive from the 
    Christandl & Wehner research paper.
    """
    ns.sim_reset()
    
    # 1. Setup Nodes
    alice = Node("Alice", port_names=["out_B"], qmemory=QuantumMemory("A_Mem", num_positions=1))
    bob = Node("Bob", port_names=["in_A", "out_C"], qmemory=QuantumMemory("B_Mem", num_positions=1))
    charlie = Node("Charlie", port_names=["in_B", "out_D"], qmemory=QuantumMemory("C_Mem", num_positions=1))
    david = Node("David", port_names=["in_C"], qmemory=QuantumMemory("D_Mem", num_positions=1))
    
    # 2. Setup Noise (Goal 5: Fidelity 0.97)
    noise_model = DepolarNoiseModel(depolar_rate=0.03)
    for node in [bob, charlie, david]:
        node.qmemory.models["quantum_noise_model"] = noise_model

    # 3. Setup 10km Fibers
    delay = 50000 
    def connect(n1, n2, p1, p2, name):
        chan = QuantumChannel(name, length=10, models={"delay_model": FixedDelayModel(delay=delay)})
        n1.ports[p1].connect(chan.ports["send"])
        chan.ports["recv"].connect(n2.ports[p2])

    connect(alice, bob, "out_B", "in_A", "Ch_AB")
    connect(bob, charlie, "out_C", "in_B", "Ch_BC")
    connect(charlie, david, "out_D", "in_C", "Ch_CD")

    # Routing
    bob.ports["in_A"].forward_input(bob.qmemory.ports["qin0"])
    charlie.ports["in_B"].forward_input(charlie.qmemory.ports["qin0"])
    david.ports["in_C"].forward_input(david.qmemory.ports["qin0"])

    # 4. Source Logic (EPR/Bell Pair)
    source = QSource("EPR_Source", state_sampler=StateSampler([ks.b00]), num_ports=2, status=SourceStatus.EXTERNAL)
    alice.add_subcomponent(source)
    source.ports["qout1"].forward_output(alice.ports["out_B"])
    source.ports["qout0"].connect(alice.qmemory.ports["qin0"])

    source.trigger()
    
    # 5. Alice applies the ANON protocol logic (Z-gate if bit is 1)
    # This is where Goal 1 & 2 meet the research paper logic
    ns.sim_run()
    m_alice = anonymous_transmit_bit(alice, secret_bit=ALICE_SECRET, is_sender=True)

    # 6. Propagation through Relays
    for relay, next_port in [(bob, "out_C"), (charlie, "out_D")]:
        ns.sim_run()
        if relay.qmemory.peek(0)[0] is not None:
            q, = relay.qmemory.pop(0)
            relay.ports[next_port].tx_output(q)

    # 7. Final Measurement at David
    ns.sim_run()
    if david.qmemory.peek(0)[0] is not None:
        m_david = anonymous_transmit_bit(david, is_sender=False)
        return 0 if m_alice == m_david else 1
    return 1

def run_metrics_loop(num_trials=100):
    success_count = 0
    start_wall_clock = time.time()

    print(f"Starting QIA Challenge Goal 5 Simulation...")

    for i in range(num_trials):
        round_results = []
        for _ in range(3): # Repetition Code Length 3
            outcome = simulate_abcd_chain()
            round_results.append(outcome)
        
        # Majority Vote (Goal 4)
        if majority_vote(round_results) == 0:
            success_count += 1

    total_time = time.time() - start_wall_clock
    accuracy = (success_count / num_trials) * 100
    speed = (num_runs / 8) / total_time if 'num_runs' in locals() else (num_trials / 8) / total_time

    print("\n" + "="*40)
    print("FINAL QIA SUBMISSION METRICS")
    print("="*40)
    print(f"Accuracy: {accuracy:.2f}%")
    print(f"Speed:    {speed:.4f} Bytes/sec")
    print("="*40)

if __name__ == "__main__":
    run_metrics_loop(100)