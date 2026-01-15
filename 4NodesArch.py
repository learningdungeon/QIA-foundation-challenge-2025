import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel, QSource, SourceStatus, QuantumMemory
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.components.models import FixedDelayModel

def run_30km_bridge(num_runs=10):
    success_count = 0
    
    for i in range(num_runs):
        ns.sim_reset()
        
        # 1. Define 4 Nodes
        # The repeaters (Bob and Charlie) need 2 memory slots each
        alice = Node("Alice", port_names=["out_to_bob"])
        bob = Node("Bob", port_names=["in_from_alice", "out_to_charlie"], 
                   qmemory=QuantumMemory("BobMem", num_positions=2))
        charlie = Node("Charlie", port_names=["in_from_bob", "out_to_david"], 
                       qmemory=QuantumMemory("CharMem", num_positions=2))
        david = Node("David", port_names=["in_from_charlie"],
                     qmemory=QuantumMemory("DaveMem", num_positions=1))
        
        # 2. Setup Physical Models (Standard for 30km)
        loss_model = FibreLossModel(p_loss_init=0, p_loss_length=0.25) # Slightly higher loss for reality
        delay_model = FixedDelayModel(delay=5000)
        
        # 3. Setup Channels (Three 10km segments)
        c1 = QuantumChannel("C_AB", length=10, models={"delay_model": delay_model, "loss_model": loss_model})
        c2 = QuantumChannel("C_BC", length=10, models={"delay_model": delay_model, "loss_model": loss_model})
        c3 = QuantumChannel("C_CD", length=10, models={"delay_model": delay_model, "loss_model": loss_model})
        
        # 4. Sources - Define them and ADD them to the Nodes first
        sampler = StateSampler([ks.b00])
        s1 = QSource("S1", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
        s2 = QSource("S2", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
        s3 = QSource("S3", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
        
        # CRITICAL: Add sources as subcomponents BEFORE forwarding ports
        alice.add_subcomponent(s1)
        bob.add_subcomponent(s2)
        charlie.add_subcomponent(s3)
        
        # 5. Segment 1: Alice -> Bob
        # Source S1 is inside Alice. qout1 goes to Bob, qout0 stays at Alice.
        s1.ports["qout1"].forward_output(alice.ports["out_to_bob"])
        alice.ports["out_to_bob"].connect(c1.ports["send"])
        c1.ports["recv"].connect(bob.ports["in_from_alice"])
        bob.ports["in_from_alice"].forward_input(bob.qmemory.ports["qin0"])
        
        # 6. Segment 2: Bob -> Charlie
        # Source S2 is inside Bob. qout1 goes to Charlie, qout0 stays at Bob.
        s2.ports["qout1"].forward_output(bob.ports["out_to_charlie"])
        bob.ports["out_to_charlie"].connect(c2.ports["send"])
        c2.ports["recv"].connect(charlie.ports["in_from_bob"])
        charlie.ports["in_from_bob"].forward_input(charlie.qmemory.ports["qin0"])
        
        
        # 7. Connecting Segment 3: Charlie -> David
        s3.ports["qout1"].forward_output(charlie.ports["out_to_david"])
        charlie.ports["out_to_david"].connect(c3.ports["send"])
        c3.ports["recv"].connect(david.ports["in_from_charlie"])
        david.ports["in_from_charlie"].forward_input(david.qmemory.ports["qin0"])
        
        # 8. Fire all Sources and Run
        s1.trigger(); s2.trigger(); s3.trigger()
        ns.sim_run()

        # 9. End-to-End Check: Did qubits arrive at all destinations?
        if bob.qmemory.peek(0)[0] and charlie.qmemory.peek(0)[0] and david.qmemory.peek(0)[0]:
            success_count += 1

    print(f"--- 30km Bridge Results ({num_runs} runs) ---")
    print(f"Successes: {success_count} / {num_runs}")
    print(f"Success Rate: {(success_count/num_runs)*100}%")

if __name__ == "__main__":
    run_30km_bridge(num_runs=20)