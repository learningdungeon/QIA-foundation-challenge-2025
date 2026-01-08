
#  QIA Foundation Challenge 2025: Anonymous Transmission Protocol

## Overview

This repository contains my progress and final submission for the **QIA Foundation Challenge 2025**. The project implements a protocol for sending a message across a 4-node network (Alice, Bob, Charlie, and David) such that the message is received, but the sender remains anonymous.

Due to technical issues of NetSquid backend access, I developed a **"Digital Twin"** simulation using **Qiskit** to verify the underlying quantum networking logic alongside the official **SquidASM** implementation.

## Research Foundation

The logic implemented here is based on the protocol described in the foundational paper:

> **"Quantum Anonymous Transmissions"**
>  > *Authors: Matthias Christandl and Stephanie Wehner* > *Reference: arXiv:quant-ph/0409201v2 (Protocol definition, Page 10)*

### The Math & Logic

This implementation follows the Tier 4 (Advanced) curriculum structure of my **"Quantum for All" (QAMP)** project:

* **State Prep:** Create entanglement using Hadamard and CNOT gates to form a 4-qubit GHZ state:

* **Encoding:** The anonymous sender applies a  gate to flip the phase if their secret bit is . Logic:  and .
* **Transformation:** All nodes apply a Hadamard () gate to rotate to the -basis before measurement.
* **Parity:** The receiver calculates the XOR sum of measurements to extract the bit :


## Features & Goals Completed:

* **Goal 1 (The Anonymous Bit):** core logic implementation in `application.py`.
* **Goal 2 (The Anonymous Byte):** An automated loop that converts ASCII characters into 8 quantum rounds, reconstructing the message at the receiver's end.
* **Goal 3:** Average success probability and transmission speed metrics.
* **Goal 4 (Error Correction):** Integrated **3-bit Repetition Code** to mitigate noise in near-term quantum hardware.
* **Goal 5 (Noisy Network):** Hardware-realistic `config.yaml` with 10km node spacing,  coherence times of 0.5s, and 0.5% gate-level depolarizing noise.

## How to use QIAPractice1.ipynb (Digital Twin)

1. Open the file in **Google Colab**.
2. Run the first cell to install `qiskit` and `qiskit-aer`.
3. The simulation demonstrates the transmission of the character **'a'** anonymously across the four nodes, verifying the parity logic used in the main application.

## QAMP Integration

This work supports my **Master Schedule** goal of mastering Dirac Notation and Tensor Products to represent multi-node systems. It serves as the Tier 4 capstone for the **Quantum Internet** module.

---

### License

This project is licensed under the **MIT License**.

**Author:** Noor Ul Ain Faisal

*IBM Qiskit Advocate | Friend of OQI.CERN | GRSS QUEST | Quantum Curriculum Developer | Quantum Learner*

