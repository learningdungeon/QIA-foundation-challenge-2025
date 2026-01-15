import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel, QSource, SourceStatus, QuantumMemory
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks

def run_abc_bit_flip_practice():
    ns.sim_reset()
    
    # 1. Define 3 Nodes
    alice = Node("Alice", port_names=["out_to_bob"])
    bob = Node("Bob", port_names=["in_from_alice", "out_to_charlie"], 
               qmemory=QuantumMemory("BobMemory", num_positions=1))
    charlie = Node("Charlie", port_names=["in_from_bob"], 
                  qmemory=QuantumMemory("CharlieMemory", num_positions=1))
    
    # 2. Setup Fiber 1 (Alice -> Bob) and Fiber 2 (Bob -> Charlie)
    distance = 10 
    delay = 50000 # 50 microseconds for 10km
    
    channel_ab = QuantumChannel("Fiber_A_to_B", length=distance, 
                                models={"delay_model": ns.components.models.FixedDelayModel(delay=delay)})
    channel_bc = QuantumChannel("Fiber_B_to_C", length=distance, 
                                models={"delay_model": ns.components.models.FixedDelayModel(delay=delay)})
    
    # 3. Connections
    # Alice to Bob
    alice.ports["out_to_bob"].connect(channel_ab.ports["send"])
    channel_ab.ports["recv"].connect(bob.ports["in_from_alice"])
    
    # Bob to Charlie
    bob.ports["out_to_charlie"].connect(channel_bc.ports["send"])
    channel_bc.ports["recv"].connect(charlie.ports["in_from_bob"])
    
    # Memory Routing
    bob.ports["in_from_alice"].forward_input(bob.qmemory.ports["qin0"])
    charlie.ports["in_from_bob"].forward_input(charlie.qmemory.ports["qin0"])

    # 4. Setup Source at Alice
    # Using a 2-qubit Bell state for practice
    my_sampler = StateSampler([ks.b00])
    source = QSource("EPR_Source", state_sampler=my_sampler, num_ports=2, status=SourceStatus.EXTERNAL)
    alice.add_subcomponent(source)
    source.ports["qout1"].forward_output(alice.ports["out_to_bob"])

    # --- EXECUTION ---
    source.trigger()
    
    # Run simulation for the first leg (A to B)
    ns.sim_run()
    
    # 5. Bob's Action (The "Middle Man")
    if bob.qmemory.peek(0)[0] is not None:
        qubit, = bob.qmemory.pop(0)
        # Apply the bit flip you've been practicing
        ns.qubits.operate(qubit, ns.X) 
        print(f"[{ns.sim_time()} ns] Bob received qubit, flipped it (X), and sent it to Charlie.")
        
        # Manually forward the qubit to the next fiber
        bob.ports["out_to_charlie"].tx_output(qubit)
    else:
        print("Error: Bob's memory is empty after first leg.")
    
    # Run simulation for the second leg (B to C)
    ns.sim_run()

    # 6. Charlie's Measurement
    if charlie.qmemory.peek(0)[0] is not None:
        qubit, = charlie.qmemory.pop(0)
        
        # Switch to X-basis as per QIA Goal 1
        ns.qubits.operate(qubit, ns.H)
        
        m, prob = ns.qubits.measure(qubit)
        print(f"[{ns.sim_time()} ns] Charlie measured in X-basis: {m}")
    else:
        print(f"[{ns.sim_time()} ns] Error: Charlie's memory is empty.")

if __name__ == "__main__":
    run_abc_bit_flip_practice()