import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel, QSource, SourceStatus, QuantumMemory
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.components.models import FixedDelayModel

def run_30km_bridge(num_runs=20):
    total_swaps = 0
    
    for i in range(num_runs):
        ns.sim_reset()
        
        # 1. Define 4 Nodes
        alice = Node("Alice", port_names=["out_to_bob"])
        bob = Node("Bob", port_names=["in_from_alice", "out_to_charlie"], 
                   qmemory=QuantumMemory("BobMem", num_positions=2))
        charlie = Node("Charlie", port_names=["in_from_bob", "out_to_david"], 
                       qmemory=QuantumMemory("CharMem", num_positions=2))
        david = Node("David", port_names=["in_from_charlie"],
                     qmemory=QuantumMemory("DaveMem", num_positions=1))
        
        # 2. Setup Physical Models
        loss_model = FibreLossModel(p_loss_init=0.1, p_loss_length=0.25) 
        delay_model = FixedDelayModel(delay=5000)

        # 3. Setup Channels
        c1 = QuantumChannel("C_AB", length=10, models={"delay_model": delay_model, "loss_model": loss_model})
        c2 = QuantumChannel("C_BC", length=10, models={"delay_model": delay_model, "loss_model": loss_model})
        c3 = QuantumChannel("C_CD", length=10, models={"delay_model": delay_model, "loss_model": loss_model})
        
        # 4. Sources
        sampler = StateSampler([ks.b00])
        s1 = QSource("S1", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
        s2 = QSource("S2", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
        s3 = QSource("S3", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
        
        alice.add_subcomponent(s1)
        bob.add_subcomponent(s2)
        charlie.add_subcomponent(s3)
        
        # 5. Connect Alice -> Bob (S1)
        s1.ports["qout1"].forward_output(alice.ports["out_to_bob"])
        alice.ports["out_to_bob"].connect(c1.ports["send"])
        c1.ports["recv"].connect(bob.ports["in_from_alice"])
        bob.ports["in_from_alice"].forward_input(bob.qmemory.ports["qin0"])
        
        # 6. Segment 2: Bob <-> Charlie
        # S2 to Bob's Memory (Internal to Internal)
        s2.ports["qout0"].connect(bob.qmemory.ports["qin1"]) 
        # S2 to Bob's external port (Internal to Boundary)
        s2.ports["qout1"].forward_output(bob.ports["out_to_charlie"])
        
        bob.ports["out_to_charlie"].connect(c2.ports["send"])
        c2.ports["recv"].connect(charlie.ports["in_from_bob"])
        charlie.ports["in_from_bob"].forward_input(charlie.qmemory.ports["qin0"])
        
        # 7. Segment 3: Charlie <-> David
        # S3 to Charlie's Memory (Internal to Internal)
        s3.ports["qout0"].connect(charlie.qmemory.ports["qin1"])
        # S3 to Charlie's external port (Internal to Boundary)
        s3.ports["qout1"].forward_output(charlie.ports["out_to_david"])
        
        charlie.ports["out_to_david"].connect(c3.ports["send"])
        c3.ports["recv"].connect(david.ports["in_from_charlie"])
        david.ports["in_from_charlie"].forward_input(david.qmemory.ports["qin0"])
        # 8. Fire and Run
        s1.trigger(); s2.trigger(); s3.trigger()
        ns.sim_run(duration=100000)

        # 9. Perform the Entanglement Swap at Bob
        q_A = bob.qmemory.peek(0)[0]
        q_C = bob.qmemory.peek(1)[0]

        if q_A is not None and q_C is not None:
            ns.qubits.operate([q_A, q_C], ns.CNOT)
            ns.qubits.operate(q_A, ns.H)
            m1, _ = ns.qubits.measure(q_A)
            m2, _ = ns.qubits.measure(q_C)
            total_swaps += 1
            # Note: After measurement, q_A and q_C are destroyed (None)
            # 11. Final End-to-End Verification
        # Get the qubit that stayed at Alice (S1) and the one that arrived at David (S3)
        q_alice = s1.peek()[0] # Peek at the first qubit of the S1 pair
        q_david = david.qmemory.peek(0)[0]

        if q_alice is not None and q_david is not None:
            # Calculate fidelity between the distant pair
            f = ns.qubits.fidelity([q_alice, q_david], ks.b00)
            print(f"Success! Alice-David Fidelity: {f:.4f}")

    print(f"--- 30km Bridge Results ({num_runs} runs) ---")
    print(f"Successful Swaps: {total_swaps} / {num_runs}")

if __name__ == "__main__":
    run_30km_bridge()