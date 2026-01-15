import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel, QSource, SourceStatus, QuantumMemory
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks
from netsquid.components.models import DepolarNoiseModel

def run_abcd_noisy_chain():
    ns.sim_reset()
    
    # 1. Define 4 Nodes
    nodes = {
        "A": Node("Alice", port_names=["out_B"]),
        "B": Node("Bob", port_names=["in_A", "out_C"], qmemory=QuantumMemory("B_Mem", num_positions=1)),
        "C": Node("Charlie", port_names=["in_B", "out_D"], qmemory=QuantumMemory("C_Mem", num_positions=1)),
        "D": Node("David", port_names=["in_C"], qmemory=QuantumMemory("D_Mem", num_positions=1))
    }
    
    # 2. Setup Noise Model (Challenge Spec: Fidelity 0.97)
    # 0.97 fidelity corresponds to roughly 0.03 depolarization rate
    noise_model = DepolarNoiseModel(depolar_rate=0.03)
    for n in ["B", "C", "D"]:
        nodes[n].qmemory.models["quantum_noise_model"] = noise_model

    # 3. Setup Fibers (10km each)
    delay = 50000 # 50us for 10km
    def create_channel(name):
        return QuantumChannel(name, length=10, 
                              models={"delay_model": ns.components.models.FixedDelayModel(delay=delay)})

    ch_ab = create_channel("Ch_AB")
    ch_bc = create_channel("Ch_BC")
    ch_cd = create_channel("Ch_CD")

    # 4. Connections
    nodes["A"].ports["out_B"].connect(ch_ab.ports["send"])
    ch_ab.ports["recv"].connect(nodes["B"].ports["in_A"])
    
    nodes["B"].ports["out_C"].connect(ch_bc.ports["send"])
    ch_bc.ports["recv"].connect(nodes["C"].ports["in_B"])
    
    nodes["C"].ports["out_D"].connect(ch_cd.ports["send"])
    ch_cd.ports["recv"].connect(nodes["D"].ports["in_C"])

    # Memory Routing
    nodes["B"].ports["in_A"].forward_input(nodes["B"].qmemory.ports["qin0"])
    nodes["C"].ports["in_B"].forward_input(nodes["C"].qmemory.ports["qin0"])
    nodes["D"].ports["in_C"].forward_input(nodes["D"].qmemory.ports["qin0"])

    # 5. Source at Alice
    source = QSource("GHZ_Source", state_sampler=StateSampler([ks.b00]), num_ports=2, status=SourceStatus.EXTERNAL)
    nodes["A"].add_subcomponent(source)
    source.ports["qout1"].forward_output(nodes["A"].ports["out_B"])

    # --- EXECUTION ---
    source.trigger()
    
    # Step-by-Step Forwarding
    for current, next_node, out_port in [("B", "C", "out_C"), ("C", "D", "out_D")]:
        ns.sim_run()
        if nodes[current].qmemory.peek(0)[0] is not None:
            q, = nodes[current].qmemory.pop(0)
            print(f"[{ns.sim_time()} ns] Node {current} forwarding qubit...")
            nodes[current].ports[out_port].tx_output(q)

    ns.sim_run()

    # 6. Final Measurement at David
    if nodes["D"].qmemory.peek(0)[0] is not None:
        q, = nodes["D"].qmemory.pop(0)
        ns.qubits.operate(q, ns.H) # X-basis
        m, _ = ns.qubits.measure(q)
        print(f"[{ns.sim_time()} ns] David measured final bit: {m}")
    else:
        print("Transmission Failed.")

if __name__ == "__main__":
    run_abcd_noisy_chain()