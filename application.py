from copy import copy
from typing import Optional, Generator
import netsquid as ns

from squidasm.sim.stack.program import Program, ProgramContext, ProgramMeta
from netqasm.sdk.classical_communication.socket import Socket
from netqasm.sdk.epr_socket import EPRSocket

class AnonymousTransmissionProgram(Program):
    def __init__(self, node_name: str, node_names: list, send_bit: bool = None, use_ec: bool = True):
        """
        Initializes the AnonymousTransmissionProgram.
        :param use_ec: Added flag to toggle Goal 4 (Repetition Code).
        """
        self.node_name = node_name
        self.send_bit = send_bit  # Truth value if node is the sender
        self.use_ec = use_ec

        node_index = node_names.index(node_name)
        self.next_node_name = node_names[node_index+1] if node_index + 1 < len(node_names) else None
        self.prev_node_name = node_names[node_index-1] if node_index - 1 >= 0 else None

        self.remote_node_names = copy(node_names)
        self.remote_node_names.pop(node_index)

        self.next_socket: Optional[Socket] = None
        self.next_epr_socket: Optional[EPRSocket] = None
        self.prev_socket: Optional[Socket] = None
        self.prev_epr_socket: Optional[EPRSocket] = None

    @property
    def meta(self) -> ProgramMeta:
        epr_node_names = [node for node in [self.next_node_name, self.prev_node_name] if node is not None]
        return ProgramMeta(
            name="anonymous_transmission_program",
            csockets=self.remote_node_names,
            epr_sockets=epr_node_names,
            max_qubits=2,
        )

    def run(self, context: ProgramContext):
        self.setup_next_and_prev_sockets(context)
        
        # Goal 5: Performance Timing
        start_time = ns.sim_time()
        
        # Goal 2: Transmit 8 bits (one byte)
        # Defining the byte 10110101 for the sender
        secret_byte = [1, 0, 1, 1, 0, 1, 0, 1] if self.send_bit is not None else [None] * 8
        final_received_byte = []

        for bit in secret_byte:
            # Goal 4: Repetition Code (n=3)
            num_reps = 3 if self.use_ec else 1
            votes = []
            
            for _ in range(num_reps):
                # Execute protocol bit-by-bit
                result = yield from self.anonymous_transmit_bit(context, bit)
                votes.append(int(result))
            
            # Goal 4: Majority Vote Logic
            # If 2 or 3 votes are 1, the logical bit is 1.
            decoded_bit = 1 if sum(votes) >= (num_reps / 2 + 0.5) else 0
            final_received_byte.append(decoded_bit)

        duration = ns.sim_time() - start_time
        print(f"Node {self.node_name} final byte: {final_received_byte}")
        
        # Goal 2 & 5: Return data for run_simulation.py averages
        return {"received_byte": final_received_byte, "duration_ns": duration}

    def anonymous_transmit_bit(self, context: ProgramContext, send_bit: bool = None) -> Generator[None, None, bool]:
        """
        Implementation of the Christandl & Wehner Protocol (ANON).
        """
        conn = context.connection

        # 1. Access the qubit from the GHZ distribution
        q = conn.get_qubit() 

        # 2. Protocol Step: If sender and bit=1, apply Phase Flip (Z gate)
        if send_bit == 1:
            q.Z()

        # 3. Protocol Step: Rotate to X-basis and Measure
        # Goal 5: 0.5% gate error applies to this H gate
        q.H()
        m = q.measure()
        yield from conn.flush()
        m_val = int(m)

        # 4. Broadcast local measurement bit (d_i)
        self.broadcast_message(context, str(m_val))

        # 5. Collect broadcasted bits from all other 3 nodes
        all_bits = [m_val]
        for remote_node in self.remote_node_names:
            socket = context.csockets[remote_node]
            msg = yield from socket.recv()
            all_bits.append(int(msg))

        # 6. Parity Reconstruction: Bit = sum(d_i) mod 2
        # This is the "Dining Cryptographers" logic adapted for GHZ
        return sum(all_bits) % 2 == 1

    def broadcast_message(self, context: ProgramContext, message: str):
        for remote_node_name in self.remote_node_names:
            socket = context.csockets[remote_node_name]
            socket.send(message)

    def setup_next_and_prev_sockets(self, context: ProgramContext):
        if self.next_node_name:
            self.next_socket = context.csockets[self.next_node_name]
            self.next_epr_socket = context.epr_sockets[self.next_node_name]
        if self.prev_node_name:
            self.prev_socket = context.csockets[self.prev_node_name]
            self.prev_epr_socket = context.epr_sockets[self.prev_node_name]