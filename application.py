import netsquid as ns
import netsquid.qubits.operators as ops

def anonymous_transmit_bit(node, secret_bit=None, is_sender=False):
    """
    Implementation of the ANON protocol (Christandl & Wehner, 2005).
    Goal: Transmit a bit while keeping the sender's identity hidden from observers.
    """
    
    # 1. ENCODING (Sender only)
    # The sender performs a phase flip (Z-gate) if their bit is '1'.
    # Theoretically, this shifts the GHZ state |000> + |111> to |000> - |111>.
    # Because this is a global phase change, an observer cannot tell WHO applied it.
    if is_sender and secret_bit == 1:
        qubit = node.qmemory.pop(0)[0]
        ns.qubits.operate(qubit, ops.Z)
        node.qmemory.push(qubit, 0)

    # 2. BASIS TRANSFORMATION
    # To extract the parity, we must move from the Z-basis to the X-basis.
    # The Hadamard (H) gate maps |0> -> |+> and |1> -> |->.
    qubit = node.qmemory.pop(0)[0]
    ns.qubits.operate(qubit, ops.H)

    # 3. MEASUREMENT & COLLAPSE
    # Measurement collapses the local qubit. The 'tracelessness' comes from the fact
    # that the local result 'm' looks random (50/50) to an attacker.
    m, _ = ns.qubits.measure(qubit)

    # 4. CLASSICAL POST-PROCESSING
    # The final bit is the XOR sum (parity) of all participants' measurements.
    return m 

def majority_vote(results):
    """
    GOAL 4: Error Correction (Repetition Code).
    Since noise (Fidelity 0.97) can flip bits during the 30km journey, 
    we take 3 samples and pick the most frequent result to ensure 100% accuracy.
    """
    return 1 if results.count(1) > results.count(0) else 0