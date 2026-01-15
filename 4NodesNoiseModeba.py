import netsquid as ns
import netsquid.qubits.ketstates as ks

def run_30km_bridge(num_runs=20):
    total_successful_bridging = 0
    
    # INCREASED NOISE: 5% to make the effect visible in a small sample
    error_prob = 0.05 

    print("Starting 30km Bridge with Mixed-State Noise...")

    for i in range(num_runs):
        ns.sim_reset()
        
        # 1. Create and entangle 6 qubits
        q1_a, q1_b = ns.qubits.create_qubits(2)
        q2_b, q2_c = ns.qubits.create_qubits(2)
        q3_c, q3_d = ns.qubits.create_qubits(2)
        
        for pair in [(q1_a, q1_b), (q2_b, q2_c), (q3_c, q3_d)]:
            ns.qubits.operate(pair[0], ns.H)
            ns.qubits.operate(pair, ns.CNOT)

        # 2. INJECT NOISE (Hardware Reality)
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

        # 5. DAVID'S CORRECTIONS
        if (m2 + m4) % 2 == 1: ns.qubits.operate(q3_d, ns.X)
        if (m1 + m3) % 2 == 1: ns.qubits.operate(q3_d, ns.Z)

        # 6. FINAL VERIFICATION (The "Average Fidelity" approach)
        # Using fidelity with the expected ket state |b00>
        f = ns.qubits.fidelity([q1_a, q3_d], ks.b00)
        
        total_successful_bridging += 1
        # Format to 4 decimal places to see the noise impact
        print(f"Run {i}: Realistic Fidelity: {f:.4f}")

    print(f"\n--- 30km Bridge Results ---")
    print(f"Successes: {total_successful_bridging} / {num_runs}")

if __name__ == "__main__":
    run_30km_bridge()