import netsquid as ns
from netsquid.nodes import Node
from netsquid.components import QuantumChannel, QSource, SourceStatus, QuantumMemory
from netsquid.qubits.state_sampler import StateSampler
import netsquid.qubits.ketstates as ks
from netsquid.components.models.qerrormodels import FibreLossModel
from netsquid.components.models import FixedDelayModel

def run_20km_network(num_runs=10):
    success_count = 0
    
    for i in range(num_runs):
        ns.sim_reset()
        
        # 1. Define Nodes
        alice = Node("Alice", port_names=["out_to_bob"])
        bob = Node("Bob", port_names=["in_from_alice", "in_from_charlie"], 
                   qmemory=QuantumMemory("BobMemory", num_positions=2))
        charlie = Node("Charlie", port_names=["out_to_bob"])
        
        # 2. Setup Models
        # 0.2 dB/km is the standard loss for telecom fiber
        loss_model = FibreLossModel(p_loss_init=0, p_loss_length=0.2)
        delay_model = FixedDelayModel(delay=5000) # 5000ns per km
        
        # 3. Setup Sources
        sampler = StateSampler([ks.b00])
        source_AB = QSource("Source_AB", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
        source_BC = QSource("Source_BC", state_sampler=sampler, num_ports=2, status=SourceStatus.EXTERNAL)
        alice.add_subcomponent(source_AB)
        charlie.add_subcomponent(source_BC)
        
        # 4. Setup Channels with Loss and Delay
        channel_AB = QuantumChannel("Fiber_AB", length=10, 
                                    models={"delay_model": delay_model, "loss_model": loss_model})
        channel_BC = QuantumChannel("Fiber_BC", length=10, 
                                    models={"delay_model": delay_model, "loss_model": loss_model})
        
        # 5. Connections
        source_AB.ports["qout1"].forward_output(alice.ports["out_to_bob"])
        alice.ports["out_to_bob"].connect(channel_AB.ports["send"])
        channel_AB.ports["recv"].connect(bob.ports["in_from_alice"])
        bob.ports["in_from_alice"].forward_input(bob.qmemory.ports["qin0"])
        
        source_BC.ports["qout1"].forward_output(charlie.ports["out_to_bob"])
        charlie.ports["out_to_bob"].connect(channel_BC.ports["send"])
        channel_BC.ports["recv"].connect(bob.ports["in_from_charlie"])
        bob.ports["in_from_charlie"].forward_input(bob.qmemory.ports["qin1"])
        
        # 6. Execute
        source_AB.trigger()
        source_BC.trigger()
        ns.sim_run()

        # 7. Check if both qubits survived the 10km trek
        q0 = bob.qmemory.peek(0)[0]
        q1 = bob.qmemory.peek(1)[0]
        
        if q0 is not None and q1 is not None:
            success_count += 1

    print(f"--- Simulation Results ({num_runs} runs) ---")
    print(f"Successes: {success_count} / {num_runs}")
    print(f"Success Rate: {(success_count/num_runs)*100}%")
    print(f"Final Latency: {ns.sim_time()} ns")

if __name__ == "__main__":
    run_20km_network(num_runs=20)