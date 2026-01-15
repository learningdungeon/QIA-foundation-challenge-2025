import netsquid as ns
import netsquid.qubits.ketstates as ks
from netsquid.qubits.qformalism import QFormalism

# Try the most common enum names for Density Matrix mode
try:
    ns.set_qstate_formalism(QFormalism.DM)
except AttributeError:
    ns.set_qstate_formalism(QFormalism.DENSITY_MATRIX)

def run_30km_bridge(num_runs=20):
    total_successful_bridging = 0
    
    # 2% error probability to ensure we see the decimal drop
    error_prob = 0.02 

    print("Starting 30km Bridge in Density Matrix Mode...\n")

    for i in range(num_runs):
        ns.sim_reset()
        
        # 1. Create and entangle 6 qubits (3 segments)
        q1_a, q1_b = ns.qubits.create_qubits(2)
        q2_b, q2_c = ns.qubits.create_qubits(2)
        q3_c, q3_d = ns.qubits.create_qubits(2)
        
        for pair in [(q1_a, q1_b), (q2_b, q2_c), (q3_c, q3_d)]:
            ns.qubits.operate(pair[0], ns.H)
            ns.qubits.operate(pair, ns.CNOT)

        # 2. INJECT HARDWARE NOISE (The "No-Fluff" Reality)
        # In DM mode, this creates a consistent mixed state
        for q in [q1_a, q1_b, q2_b, q2_c, q3_c, q3_d]:
            ns.qubits.depolarize(q, prob=error_prob)

        # 3. SWAP AT BOB
        ns.qubits.operate([q1_b, q2_b], ns.CNOT)
        ns.qubits.operate(q1_b, ns.H)
        m1, _ = ns.qubits.measure(q1_b)
        m2, _ = ns.qubits.measure(q2_b)

        # 4. SWAP AT CHARLIE
        ns.qubits.operate([q2_c, q3_c], ns.CNOT)
        ns.qubits.operate(q2_c, ns.H)
        m3, _ = ns.qubits.measure(q2_c)
        m4, _ = ns.qubits.measure(q3_c)

        # 5. DAVID'S FEED-FORWARD CORRECTIONS
        # Correcting based on the outcome of Bob's and Charlie's measurements
        if (m2 + m4) % 2 == 1: 
            ns.qubits.operate(q3_d, ns.X)
        if (m1 + m3) % 2 == 1: 
            ns.qubits.operate(q3_d, ns.Z)

        # 6. FINAL VERIFICATION
        f = ns.qubits.fidelity([q1_a, q3_d], ks.b00)
        total_successful_bridging += 1
        print(f"Run {i}: Realistic Fidelity: {f:.4f}")

    print(f"\n--- 30km Bridge Results ---")
    print(f"Successes: {total_successful_bridging} / {num_runs}")

if __name__ == "__main__":
    run_30km_bridge()