import netsquid as ns
from netsquid.nodes import Node, Network
from netsquid.components import QuantumChannel

def run_10km_test():
    # 1. Setup the Hardware
    network = Network("10km_Link")
    alice = Node("Alice", port_names=["out_to_bob"])
    bob = Node("Bob", port_names=["in_from_alice"])
    
    # 2. Create the Fiber (10km)
    distance = 10 # km
    # Light in fiber delay (approx 5 microseconds per km)
    channel = QuantumChannel("Fiber_Alice_to_Bob", length=distance, models={"delay_model": None})
    
    # 3. Connect Alice's port to the Channel, and Channel to Bob's port
    # Alice [out] -> [in] Channel [out] -> [in] Bob
    alice.ports["out_to_bob"].connect(channel.ports["send"])
    channel.ports["recv"].connect(bob.ports["in_from_alice"])
    
    # 4. Add to network
    network.add_nodes([alice, bob])
    
    print(f"Network built successfully in Codespaces!")
    print(f"Connection: Alice -> {distance}km Fiber -> Bob")

if __name__ == "__main__":
    run_10km_test()