import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel, QSource, SourceStatus, QuantumMemory
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks

def run_10km_bit_flip_practice():
    ns.sim_reset()
    
    # 1. Define Nodes
    # Bob needs a quantum memory to store the incoming qubit
    alice = Node("Alice", port_names=["out_to_bob"])
    bob = Node("Bob", port_names=["in_from_alice"], 
               qmemory=QuantumMemory("BobMemory", num_positions=1))
    
    # 2. Setup Source at Alice
    # We use ks.b00 which is |00> + |11>. Alice keeps one, sends the other.
    my_sampler = StateSampler([ks.b00])
    source = QSource("EPR_Source", state_sampler=my_sampler,
                     num_ports=2, status=SourceStatus.EXTERNAL)
    alice.add_subcomponent(source)
    
    # 3. Setup Fiber (10km)
    # 200,000 km/s in fiber means 10km takes 50,000 ns
    distance = 10 
    delay_model = ns.components.models.FixedDelayModel(delay=50000)
    channel = QuantumChannel("Fiber_to_Bob", length=distance, models={"delay_model": delay_model})
    
    # 4. Physical Connections
    source.ports["qout1"].forward_output(alice.ports["out_to_bob"])
    alice.ports["out_to_bob"].connect(channel.ports["send"])
    channel.ports["recv"].connect(bob.ports["in_from_alice"])
    
    # Route the fiber output into Bob's memory slot 0
    bob.ports["in_from_alice"].forward_input(bob.qmemory.ports["qin0"])
    
    # --- EXECUTION ---
    
    # Trigger the source to create the qubits
    source.trigger()
    
    # Run the simulation so the qubit actually travels the 10km
    ns.sim_run()

    print(f"Simulation Time after travel: {ns.sim_time()} ns")

    # 5. The Bit Flip Practice
    # Peek to see if it arrived
    if bob.qmemory.peek(0)[0] is not None:
        # Pop the qubit out of memory to work on it
        qubit, = bob.qmemory.pop(0)
        
        # Before the flip, if we measured, it would likely be 0 (from the b00 state)
        # Now we apply the Pauli X gate (The Bit Flip)
        ns.qubits.operate(qubit, ns.X)
        print("ACTION: Bob applied an X gate (Physical Bit Flip).")

        # 6. Measurement
        # This converts the quantum state into a classical bit (0 or 1)
        m, prob = ns.qubits.measure(qubit)
        print(f"RESULT: Measured bit at Bob is {m}")
        
        if m == 1:
            print("SUCCESS: The bit flip was recorded correctly.")
    else:
        print("ERROR: Bob's memory is empty. Check connections or timing.")

if __name__ == "__main__":
    run_10km_bit_flip_practice()