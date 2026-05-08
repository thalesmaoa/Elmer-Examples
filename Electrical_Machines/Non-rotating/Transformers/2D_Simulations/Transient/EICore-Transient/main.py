# main.py
"""
Main script for the 2D E-I Core Transformer Simulation.

This script orchestrates the entire simulation process:
1. Sets up the simulation environment and parameters.
2. Converts the mesh file to Elmer's format.
3. Builds the Solver Input File (SIF) using pyelmer.
4. Plots the B-H curve of the magnetic material.
5. Iterates through a range of currents, running the Elmer solver for each.
6. Parses the results from each simulation run.
7. Plots the final results (Inductance, Flux, Energy vs. Current).
"""
import os
import numpy as np
from dotenv import load_dotenv
import glob
from PIL import Image

# Carrega as variáveis de ambiente a partir do arquivo stack.env (se ele existir)
load_dotenv("stack.env")

# Import custom modules from the 'src' directory
from src.simulation_utils import run_elmer_grid, run_elmer_solver, parse_scalar_results
from src.sif_builder import setup_simulation_sif
from src.plotting import plot_bh_curve, plot_transient_results, plot_flux_line, run_paraview_script

def main():
    """Main function to run the entire simulation workflow."""
    
    # --- Leitura das flags de execução ---
    run_mesh = os.getenv("RUN_MESH", "1") == "1"
    run_sif = os.getenv("RUN_SIF", "1") == "1"
    run_solver = os.getenv("RUN_SOLVER", "1") == "1"
    run_post = os.getenv("RUN_POST", "1") == "1"

    # --- 1. Simulation Setup and Parameters ---
    print("--- Setting up simulation environment ---")

    # Define paths
    mesh_filepath = os.path.abspath("mesh/EIcoreR00.unv")
    sim_dir = os.path.abspath("./sim")
    plots_dir = os.path.join(sim_dir, "plots")
    
    # Create simulation and plot directories if they don't exist
    os.makedirs(plots_dir, exist_ok=True)
    
    # Create result directories required by Elmer solvers
    for sub in ["paraview", "scalar", "plot"]:
        os.makedirs(os.path.join(sim_dir, "result", sub), exist_ok=True)

    # Define physical group IDs from the mesh file
    # These IDs link mesh regions to physical properties.
    physical_ids = {
        "air": 1,
        "iron": 2,
        "coil_a_minus": 3,
        "coil_a_plus": 4,
        "coil_b_minus": 5,
        "coil_b_plus": 6,
        "zerobound": 19,
    }

    # Coil and simulation parameters
    N_turns = int(os.getenv("N_TURNS", "217"))  # Number of turns in the coil
    core_depth = float(os.getenv("CORE_DEPTH", "70e-3"))  # Depth of the 2D model in meters

    # Define the peak current for the transient simulation (amplitude da senoide)
    peak_current = float(os.getenv("CURRENT", "0.5"))
    coil_area = float(os.getenv("COIL_AREA", "1.225e-3")) # Área transversal da bobina em m2 (ex: 1225 mm2)

    # --- 2. Mesh Conversion ---
    print("\n--- Converting mesh file ---")
    mesh_basename = os.path.splitext(os.path.basename(mesh_filepath))[0]
    mesh_dir = os.path.dirname(mesh_filepath)
    meshout_dir = os.path.join(mesh_dir, mesh_basename)
    
    if run_mesh:
        run_elmer_grid(
            mesh_dir=mesh_dir,
            mesh_filepath=mesh_filepath,
            meshout_dir=meshout_dir
        )
        print(f"  -> Mesh converted successfully to '{meshout_dir}'")
    else:
        print("  -> Pular etapa: Conversão da malha.")

    # --- 3. SIF Building ---
    print("\n--- Building Solver Input File (SIF) ---")
    # Sempre carregamos a estrutura base do SIF na memória para uso nas etapas seguintes
    sim, bf_a_plus, bf_a_minus, iron_material = setup_simulation_sif(
        mesh_basename=mesh_basename,
        physical_ids=physical_ids,
        core_depth=core_depth,
        N_turns=N_turns
    )
    
    # Calcula a densidade de corrente de pico (J = N*I / Area) em A/m2
    J_peak = (N_turns * peak_current) / coil_area
    bf_a_plus.data["Current Density"] = f'Variable time\n  Real MATC "{J_peak} * sin(2 * pi * 60 * tx)"'
    bf_a_minus.data["Current Density"] = f'Variable time\n  Real MATC "{-J_peak} * sin(2 * pi * 60 * tx)"'
    # NI_peak = N_turns * peak_current
    # bf_a_plus.data["Current Density"] = f'Variable time\n  Real MATC "{NI_peak} * sin(2 * pi * 60 * tx)"'
    # bf_a_minus.data["Current Density"] = f'Variable time\n  Real MATC "{-NI_peak} * sin(2 * pi * 60 * tx)"'

    if run_sif:
        # sim.write_startinfo(sim_dir) # Não é mais necessário com a alteração em run_elmer_solver
        sim.write_sif(sim_dir)
        print("  -> SIF structure created and saved.")
    else:
        print("  -> Pular etapa: Escrita do SIF base.")

    # --- 5. Simulation Execution ---
    print(f"\n--- Starting transient simulation for Peak Current = {peak_current:.3f} A ---")
    
    pv_script = os.path.abspath("export_view.py")
    run_pv = os.path.exists(pv_script)

    if run_solver:
        # Run solver exactly once in the main directory
        run_elmer_solver(sim_dir)
        
        scalar_filepath = os.path.join(sim_dir, "result", "scalar", "integrais_bobina.dat")
        if os.path.exists(scalar_filepath):
            print(f"  -> Transient results successfully generated at {scalar_filepath}")
            
        # After simulation, generate the ParaView screenshot for the final moment
        if run_pv:
            pvd_path = os.path.join(sim_dir, "result", "paraview", "results.pvd")
            frame_path = os.path.join(plots_dir, "cena_paraview_final.png")
            run_paraview_script(
                script_path=pv_script,
                pvd_input_path=pvd_path,
                png_output_path=frame_path
            )
    else:
        print("  -> Pular etapa: Solver.")

    # --- 6. Plotting Final Results ---
    if run_post:
        scalar_filepath = os.path.join(sim_dir, "result", "scalar", "integrais_bobina.dat")
        if os.path.exists(scalar_filepath):
            print("\n--- Plotting transient simulation results ---")
            data = np.loadtxt(scalar_filepath, ndmin=2)
            # Passa os dados brutos para plotar variável por variável
            plot_transient_results(data, plots_dir)
            print(f"  -> All result plots saved to '{plots_dir}'")
        else:
            print(f"  -> AVISO: {scalar_filepath} não encontrado. Execute o solver primeiro para plotar os dados.")

        print("\n--- Plotting flux line (final timestep) ---")
        flux_line_filepath = os.path.join(sim_dir, "result", "plot", "linha_fluxo.dat")
        if os.path.exists(flux_line_filepath):
            plot_flux_line(flux_line_filepath, plots_dir)
            
        print("\n  -> Dica: Para ver e exportar a animação dos campos magnéticos ao longo do tempo,\n           abra o arquivo 'sim/result/paraview/results.pvd' no seu ParaView Desktop!")
    else:
        print("\n  -> Pular etapa: Pós-processamento e gráficos.")

    print("\n--- Simulation finished successfully! ---")

if __name__ == "__main__":
    main()
