# 🌐 Quantum Internet Alliance (QIA) - Foundation Challenge 2025
### **Project: Anonymous Transmission Protocol (Logic Verification)**

## 📖 Overview
This repository contains my progress on the **QIA Foundation Challenge**. Due to temporary server availability issues with the NetSquid/SquidASM backends, I have developed a **"Digital Twin"** simulation using **Qiskit** to verify the underlying quantum networking logic.

The goal is to send a message across a 4-node network (Alice, Bob, Charlie, and David) so that the message is received, but the sender remains anonymous.

## 🛠 Features
* **Goal 1 (The Anonymous Bit):** Uses a 4-qubit GHZ state to transmit a single bit via phase-encoding.
* **Goal 2 (The Anonymous Byte):** An automated loop that converts ASCII characters into 8 quantum rounds, reconstructing the message at the receiver's end.
* **Hybrid Logic:** Combines quantum gate operations with classical binary-to-decimal reconstruction.



## 📐 The Math & Logic
This implementation follows the **Tier 4 (Advanced)** curriculum structure of my **"Quantum for All" (QAMP)** project:

1. **State Prep:** Create entanglement using Hadamard and CNOT gates: 
   $$\ket{\Psi}_{GHZ} = \frac{1}{\sqrt{2}} (\ket{0000} + \ket{1111})$$
2. **Encoding:** Alice applies a $Z$ gate to flip the phase if her bit is $1$. The rule is:
   $Z\ket{0} = \ket{0}$ and $Z\ket{1} = -\ket{1}$
3. **Transformation:** All nodes apply a Hadamard ($H$) gate to rotate to the $X$-basis before measurement.
4. **Parity:** The receiver calculates the XOR sum of measurements to extract the bit $b$: 
   $$b = m_A \oplus m_B \oplus m_C \oplus m_D$$

## 🚀 How to use `QIAPractice1.ipynb`
1. Open the file in **Google Colab**.
2. Run the first cell to install `qiskit` and `qiskit-aer`.
3. The simulation demonstrates the transmission of the character `'a'` anonymously across the four nodes.

## 🎓 QAMP Integration
This work supports my **Master Schedule** goal of mastering Dirac Notation and Tensor Products to represent multi-node systems. It serves as the Tier 4 capstone for the **Quantum Internet** module.

---
**Author:** Noor  
*Qiskit Advocate | QAMP Mentor | Systems Analyst*
