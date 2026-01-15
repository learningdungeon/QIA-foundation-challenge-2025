import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel, QSource, SourceStatus, QuantumMemory
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks
from netsquid.components.models.qerrormodels import FibreLossModel, DepolarNoiseModel
from netsquid.components.models import FixedDelayModel

def run_30km_bridge(num_runs=20):
    total_successful_bridging = 0
    
    # 1. Setup Models
    loss_model = FibreLossModel(p_loss_init=0.1, p_loss_length=0.25) 
    delay_model = FixedDelayModel(delay=5000) # 5 microseconds of travel
    
    # Aggressive noise model to FORCE a visible drop (1% per channel)
    # Using time_independent=True here because we want it to hit the qubit on arrival
    noise_model = DepolarNoiseModel(depolar_rate=0.01, time_independent=True)

    for i in range(num_runs):
        ns.sim_reset()
        
        # 2. Define Nodes
        alice = Node("Alice", port_names=["out_to_bob"], qmemory=QuantumMemory("AMem", 1))
        bob = Node("Bob", port_names=["in_from_alice", "out_to_charlie"], qmemory=QuantumMemory("BMem", 2))
        charlie = Node("Charlie", port_names=["in_from_bob", "out_to_david"], qmemory=QuantumMemory("CMem", 2))
        david = Node("David", port_names=["in_from_charlie"], qmemory=QuantumMemory("DMem", 1))
        
        # 3. Setup Channels with NOISE MODELS attached
        # This ensures the qubit is corrupted during flight
        c1 = QuantumChannel("C_AB", length=10, models={
            "delay_model": delay_model, 
            "loss_model": loss_model, 
            "quantum_noise_model": noise_model})
        c2 = QuantumChannel("C_BC", length=10, models={
            "delay_model": delay_model, 
            "loss_model": loss_model, 
            "quantum_noise_model": noise_model})
        c3 = QuantumChannel("C_CD", length=10, models={
            "delay_model": delay_model, 
            "loss_model": loss_model, 
            "quantum_noise_model": noise_model})
        
        # 4. Sources
        sampler = StateSampler([ks.b00])
        s1 = QSource("S1", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
        s2 = QSource("S2", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
        s3 = QSource("S3", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
        alice.add_subcomponent(s1)
        bob.add_subcomponent(s2)
        charlie.add_subcomponent(s3)
        
        # 5. Connections
        s1.ports["qout0"].connect(alice.qmemory.ports["qin0"])
        s1.ports["qout1"].forward_output(alice.ports["out_to_bob"])
        alice.ports["out_to_bob"].connect(c1.ports["send"])
        c1.ports["recv"].connect(bob.ports["in_from_alice"])
        bob.ports["in_from_alice"].forward_input(bob.qmemory.ports["qin0"])
        
        s2.ports["qout0"].connect(bob.qmemory.ports["qin1"]) 
        s2.ports["qout1"].forward_output(bob.ports["out_to_charlie"])
        bob.ports["out_to_charlie"].connect(c2.ports["send"])
        c2.ports["recv"].connect(charlie.ports["in_from_bob"])
        charlie.ports["in_from_bob"].forward_input(charlie.qmemory.ports["qin0"])
        
        s3.ports["qout0"].connect(charlie.qmemory.ports["qin1"])
        s3.ports["qout1"].forward_output(charlie.ports["out_to_david"])
        charlie.ports["out_to_david"].connect(c3.ports["send"])
        c3.ports["recv"].connect(david.ports["in_from_charlie"])
        david.ports["in_from_charlie"].forward_input(david.qmemory.ports["qin0"])

        # 6. Run
        s1.trigger(); s2.trigger(); s3.trigger()
        ns.sim_run()

        # 7. Bob Swap
        q_A = bob.qmemory.peek(0)[0]
        q_C_local = bob.qmemory.peek(1)[0]
        if q_A and q_C_local:
            ns.qubits.operate([q_A, q_C_local], ns.CNOT)
            ns.qubits.operate(q_A, ns.H)
            m1, _ = ns.qubits.measure(q_A)
            m2, _ = ns.qubits.measure(q_C_local)

            # 8. Charlie Swap
            q_Alice_at_Char = charlie.qmemory.peek(0)[0]
            q_D_local = charlie.qmemory.peek(1)[0]
            if q_Alice_at_Char and q_D_local:
                ns.qubits.operate([q_Alice_at_Char, q_D_local], ns.CNOT)
                ns.qubits.operate(q_Alice_at_Char, ns.H)
                m3, _ = ns.qubits.measure(q_Alice_at_Char)
                m4, _ = ns.qubits.measure(q_D_local)

                # 9. David Corrections
                q_david_final = david.qmemory.peek(0)[0]
                if q_david_final:
                    if (m2 + m4) % 2 == 1: ns.qubits.operate(q_david_final, ns.X)
                    if (m1 + m3) % 2 == 1: ns.qubits.operate(q_david_final, ns.Z)

                    # 10. Final Verification
                    q_alice_final = alice.qmemory.peek(0)[0]
                    if q_alice_final:
                        f = ns.qubits.fidelity([q_alice_final, q_david_final], ks.b00)
                        total_successful_bridging += 1
                        print(f"Run {i}: Corrected Fidelity: {f:.4f}")

    print(f"\nTotal Successes: {total_successful_bridging} / {num_runs}")

if __name__ == "__main__":
    run_30km_bridge()