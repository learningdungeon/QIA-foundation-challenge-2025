import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel, QSource, SourceStatus, QuantumMemory
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks

def run_20km_network():
    ns.sim_reset()
    
    # 1. Define 3 Nodes
    # Bob now needs 2 memory slots (one for Alice's qubit, one for Charlie's)
    alice = Node("Alice", port_names=["out_to_bob"])
    bob = Node("Bob", port_names=["in_from_alice", "in_from_charlie"], 
               qmemory=QuantumMemory("BobMemory", num_positions=2))
    charlie = Node("Charlie", port_names=["out_to_bob"])
    
    # 2. Setup Sources
    sampler = StateSampler([ks.b00])
    source_AB = QSource("Source_AB", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
    source_BC = QSource("Source_BC", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
    
    alice.add_subcomponent(source_AB)
    charlie.add_subcomponent(source_BC)
    
    # 3. Setup Fibers (10km each = 20km total)
    delay_model = ns.components.models.FixedDelayModel(delay=5000)
    channel_AB = QuantumChannel("Fiber_AB", length=10, models={"delay_model": delay_model})
    channel_BC = QuantumChannel("Fiber_BC", length=10, models={"delay_model": delay_model})
    
    # 4. Connections: Alice -> Bob
    source_AB.ports["qout1"].forward_output(alice.ports["out_to_bob"])
    alice.ports["out_to_bob"].connect(channel_AB.ports["send"])
    channel_AB.ports["recv"].connect(bob.ports["in_from_alice"])
    bob.ports["in_from_alice"].forward_input(bob.qmemory.ports["qin0"])
    
    # 5. Connections: Charlie -> Bob
    source_BC.ports["qout1"].forward_output(charlie.ports["out_to_bob"])
    charlie.ports["out_to_bob"].connect(channel_BC.ports["send"])
    channel_BC.ports["recv"].connect(bob.ports["in_from_charlie"])
    bob.ports["in_from_charlie"].forward_input(bob.qmemory.ports["qin1"])
    
    # 6. Fire both sources
    source_AB.trigger()
    source_BC.trigger()
    ns.sim_run()

    # 7. Verification
    q0 = bob.qmemory.peek(0)[0]
    q1 = bob.qmemory.peek(1)[0]
    
    if q0 and q1:
        print(f"Success! Bob is holding qubits from both Alice and Charlie.")
        print(f"Memory Slot 0: {q0.name}")
        print(f"Memory Slot 1: {q1.name}")
    
    print(f"Final Simulation Time: {ns.sim_time()} ns")

if __name__ == "__main__":
    run_20km_network()