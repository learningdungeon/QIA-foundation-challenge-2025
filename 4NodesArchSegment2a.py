import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel, QSource, SourceStatus, QuantumMemory
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.components.models import FixedDelayModel

def run_30km_bridge(num_runs=20):
    total_successful_bridging = 0
    
    for i in range(num_runs):
        ns.sim_reset()
        
        # 1. Define 4 Nodes with proper Quantum Memory
        # Alice needs 1 slot, Bob/Charlie need 2 for swapping, David needs 1
        alice = Node("Alice", port_names=["out_to_bob"], 
                     qmemory=QuantumMemory("AliceMem", num_positions=1))
        bob = Node("Bob", port_names=["in_from_alice", "out_to_charlie"], 
                   qmemory=QuantumMemory("BobMem", num_positions=2))
        charlie = Node("Charlie", port_names=["in_from_bob", "out_to_david"], 
                       qmemory=QuantumMemory("CharMem", num_positions=2))
        david = Node("David", port_names=["in_from_charlie"],
                     qmemory=QuantumMemory("DaveMem", num_positions=1))
        
        # 2. Setup Physical Models
        loss_model = FibreLossModel(p_loss_init=0.1, p_loss_length=0.25) 
        delay_model = FixedDelayModel(delay=5000)

        # 3. Setup Channels (Three 10km Segments)
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
        
        # 5. Connect Alice (S1)
        # Port qout0 stays at Alice, qout1 goes to Bob
        s1.ports["qout0"].connect(alice.qmemory.ports["qin0"])
        s1.ports["qout1"].forward_output(alice.ports["out_to_bob"])
        alice.ports["out_to_bob"].connect(c1.ports["send"])
        c1.ports["recv"].connect(bob.ports["in_from_alice"])
        bob.ports["in_from_alice"].forward_input(bob.qmemory.ports["qin0"])
        
        # 6. Connect Bob (S2)
        # Port qout0 stays at Bob, qout1 goes to Charlie
        s2.ports["qout0"].connect(bob.qmemory.ports["qin1"]) 
        s2.ports["qout1"].forward_output(bob.ports["out_to_charlie"])
        bob.ports["out_to_charlie"].connect(c2.ports["send"])
        c2.ports["recv"].connect(charlie.ports["in_from_bob"])
        charlie.ports["in_from_bob"].forward_input(charlie.qmemory.ports["qin0"])
        
        # 7. Connect Charlie (S3)
        # Port qout0 stays at Charlie, qout1 goes to David
        s3.ports["qout0"].connect(charlie.qmemory.ports["qin1"])
        s3.ports["qout1"].forward_output(charlie.ports["out_to_david"])
        charlie.ports["out_to_david"].connect(c3.ports["send"])
        c3.ports["recv"].connect(david.ports["in_from_charlie"])
        david.ports["in_from_charlie"].forward_input(david.qmemory.ports["qin0"])

        # 8. Execute
        s1.trigger(); s2.trigger(); s3.trigger()
        ns.sim_run(duration=100000)

        # 9. REPEATER LOGIC: Swap at Bob
        q_A = bob.qmemory.peek(0)[0]
        q_C_local = bob.qmemory.peek(1)[0]

        if q_A and q_C_local:
            ns.qubits.operate([q_A, q_C_local], ns.CNOT)
            ns.qubits.operate(q_A, ns.H)
            ns.qubits.measure(q_A)
            ns.qubits.measure(q_C_local)

            # 10. REPEATER LOGIC: Swap at Charlie
            q_Alice_at_Char = charlie.qmemory.peek(0)[0]
            q_D_local = charlie.qmemory.peek(1)[0]

            if q_Alice_at_Char and q_D_local:
                ns.qubits.operate([q_Alice_at_Char, q_D_local], ns.CNOT)
                ns.qubits.operate(q_Alice_at_Char, ns.H)
                ns.qubits.measure(q_Alice_at_Char)
                ns.qubits.measure(q_D_local)

                # 11. Final Verification (Alice to David)
                q_alice_final = alice.qmemory.peek(0)[0] 
                q_david_final = david.qmemory.peek(0)[0]

                if q_alice_final and q_david_final:
                    f = ns.qubits.fidelity([q_alice_final, q_david_final], ks.b00)
                    total_successful_bridging += 1
                    print(f"Run {i}: Bridge Success! Fidelity: {f:.4f}")

    print(f"\n--- 30km Bridge Results ---")
    print(f"Successes: {total_successful_bridging} / {num_runs}")

if __name__ == "__main__":
    run_30km_bridge()