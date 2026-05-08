# 2D E-I Core Transformer Simulation with Elmer FEM

This project demonstrates how to set up and run a 2D magnetostatic simulation of an E-I core transformer using Elmer FEM, controlled by a Python script.

The simulation calculates the inductance, magnetic flux, and magnetic energy for a range of excitation currents, and plots the results, including the material's B-H curve.

## Project Structure

```
.
├── README.md
├── main.py                 # Main script to run the simulation
├── mesh/
│   └── EIcoreR00.unv       # Mesh file in Universal format
├── src/
│   ├── __init__.py
│   ├── sif_builder.py      # Module to build the Elmer SIF (Solver Input File)
│   ├── plotting.py         # Module for plotting results
│   └── simulation_utils.py # Utility functions for running Elmer and parsing results
└── sim/                    # Directory for simulation output (created automatically)
    ├── plots/              # Output plots
    └── ...
```

## How to Run

1.  **Prerequisites:**
    *   Python 3.x
    *   Elmer FEM (with `ElmerGrid` and `ElmerSolver` in the system's PATH)
    *   Python libraries: `numpy`, `matplotlib`, `pyelmer`, `python-dotenv`

2.  **Install the dependencies:**
    Navigate to the project's root directory and install the required Python libraries using pip:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Execute the simulation:**
    Navigate to the project's root directory and run the main script:
    ```bash
    python main.py
    ```
