import netsquid as ns
import time
from netsquid.nodes import Node
from netsquid.components import QuantumChannel, QSource, SourceStatus, QuantumMemory
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks
from netsquid.components.models import DepolarNoiseModel, FixedDelayModel

def run_single_abcd_transmission():
    """Simulates one correlated bit between Alice and David using Memory routing."""
    ns.sim_reset()
    
    # 1. Define Nodes - Everyone gets memory now for stability
    alice = Node("Alice", port_names=["out_B"], qmemory=QuantumMemory("A_Mem", num_positions=1))
    bob = Node("Bob", port_names=["in_A", "out_C"], qmemory=QuantumMemory("B_Mem", num_positions=1))
    charlie = Node("Charlie", port_names=["in_B", "out_D"], qmemory=QuantumMemory("C_Mem", num_positions=1))
    david = Node("David", port_names=["in_C"], qmemory=QuantumMemory("D_Mem", num_positions=1))
    
    # 2. Setup Noise (Fidelity 0.97)
    noise_model = DepolarNoiseModel(depolar_rate=0.03)
    for node in [bob, charlie, david]:
        node.qmemory.models["quantum_noise_model"] = noise_model

    # 3. Connections Helper
    delay = 50000 
    def connect_nodes(node_from, node_to, port_from, port_to, name):
        chan = QuantumChannel(name, length=10, models={"delay_model": FixedDelayModel(delay=delay)})
        node_from.ports[port_from].connect(chan.ports["send"])
        chan.ports["recv"].connect(node_to.ports[port_to])
        return chan

    connect_nodes(alice, bob, "out_B", "in_A", "Ch_AB")
    connect_nodes(bob, charlie, "out_C", "in_B", "Ch_BC")
    connect_nodes(charlie, david, "out_D", "in_C", "Ch_CD")

    # 4. Memory Routing
    # Crucially: Alice's local qubit from the source goes to her own memory
    bob.ports["in_A"].forward_input(bob.qmemory.ports["qin0"])
    charlie.ports["in_B"].forward_input(charlie.qmemory.ports["qin0"])
    david.ports["in_C"].forward_input(david.qmemory.ports["qin0"])

    # 5. Source at Alice
    source = QSource("EPR_Source", state_sampler=StateSampler([ks.b00]), num_ports=2, status=SourceStatus.EXTERNAL)
    alice.add_subcomponent(source)
    
    # qout1 goes to Bob (30km journey starts)
    source.ports["qout1"].forward_output(alice.ports["out_B"])
    # qout0 stays at Alice (goes into her local memory)
    source.ports["qout0"].connect(alice.qmemory.ports["qin0"])

    source.trigger()
    
    # 6. EXECUTION: Alice measures her reference bit
    ns.sim_run()
    m_alice = None
    if alice.qmemory.peek(0)[0] is not None:
        q_a, = alice.qmemory.pop(0)
        ns.qubits.operate(q_a, ns.H) # X-basis
        m_alice, _ = ns.qubits.measure(q_a)

    # 7. Propagation through the relay nodes
    for relay, next_port in [(bob, "out_C"), (charlie, "out_D")]:
        ns.sim_run()
        if relay.qmemory.peek(0)[0] is not None:
            q, = relay.qmemory.pop(0)
            relay.ports[next_port].tx_output(q)

    # 8. Final measurement at David
    ns.sim_run()
    if david.qmemory.peek(0)[0] is not None:
        q_d, = david.qmemory.pop(0)
        ns.qubits.operate(q_d, ns.H) # X-basis
        m_david, _ = ns.qubits.measure(q_d)
        
        # Success if David matches Alice's reference
        return 0 if m_alice == m_david else 1
    
    return 1 # Error if qubit lost

def majority_vote_transmission():
    results = []
    for _ in range(3):
        res = run_single_abcd_transmission()
        results.append(res)
    return 0 if results.count(0) > results.count(1) else 1

def main():
    num_runs = 100
    successes = 0
    start_time = time.time()

    print(f"Goal 4: Executing ABCD Chain with Repetition Code (Length 3)...")

    for i in range(num_runs):
        if majority_vote_transmission() == 0:
            successes += 1

    elapsed = time.time() - start_time
    avg_success = (successes / num_runs) * 100
    speed = (num_runs / 8) / elapsed

    print("\n" + "="*40)
    print("QIA CHALLENGE GOAL 4: VERIFIED METRICS")
    print("="*40)
    print(f"Final Success Prob: {avg_success:.2f}%")
    print(f"Transmission Speed: {speed:.4f} Bytes/sec")
    print("="*40)

if __name__ == "__main__":
    main()