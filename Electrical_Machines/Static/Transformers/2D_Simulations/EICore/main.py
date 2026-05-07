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
from PIL import Image

# Carrega as variáveis de ambiente a partir do arquivo stack.env (se ele existir)
load_dotenv("stack.env")

# Import custom modules from the 'src' directory
from src.simulation_utils import run_elmer_grid, run_elmer_solver, parse_scalar_results
from src.sif_builder import setup_simulation_sif
from src.plotting import plot_bh_curve, plot_simulation_results, plot_flux_line, run_paraview_script

def main():
    """Main function to run the entire simulation workflow."""
    
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
    N_turns = 217  # Number of turns in the coil
    core_depth = 70e-3  # Depth of the 2D model in meters

    # --- 2. Mesh Conversion ---
    print("\n--- Converting mesh file ---")
    mesh_basename = os.path.splitext(os.path.basename(mesh_filepath))[0]
    mesh_dir = os.path.dirname(mesh_filepath)
    meshout_dir = os.path.join(mesh_dir, mesh_basename)
    
    run_elmer_grid(
        mesh_dir=mesh_dir,
        mesh_filepath=mesh_filepath,
        meshout_dir=meshout_dir
    )
    print(f"  -> Mesh converted successfully to '{meshout_dir}'")

    # --- 3. SIF Building ---
    print("\n--- Building Solver Input File (SIF) ---")
    sim, bf_a_plus, bf_a_minus, iron_material = setup_simulation_sif(
        mesh_basename=mesh_basename,
        physical_ids=physical_ids
    )
    sim.write_startinfo(sim_dir)
    sim.write_sif(sim_dir)
    print("  -> SIF structure created.")

    # --- 4. Plot Material B-H Curve ---
    print("\n--- Plotting material properties ---")
    plot_bh_curve(iron_material, plots_dir)

    # --- 5. Simulation Loop ---
    print("\n--- Starting simulation loop over currents ---")
    
    # Define the range of currents to simulate
    currents = np.unique(np.concatenate((np.linspace(0, 0.2, 10), np.linspace(0.2, 2, 20))))
    # currents = [0.53]
    
    # Lists to store results
    inductances, fluxes, energies = [], [], []

    scalar_filepath = os.path.join(sim_dir, "result", "scalar", "integrais_bobina.dat")

    pv_script = os.path.abspath("export_view.py")
    run_pv = os.path.exists(pv_script)
    frames_paths = []

    for I in currents:
        print(f"\n--- Simulating for Current = {I:.3f} A ---")
        
        NI = N_turns * I
        bf_a_plus.data["Current Density"] = f"-distribute {NI:.6f}"
        bf_a_minus.data["Current Density"] = f"-distribute {-NI:.6f}"
        
        sim.write_sif(sim_dir)
        run_elmer_solver(sim_dir)
        
        try:
            flux_val, Wj, L = parse_scalar_results(scalar_filepath, N_turns, core_depth, I)
            print(f"  -> Inductance L calculated: {L:.6e} H")
            inductances.append(L); fluxes.append(flux_val); energies.append(Wj)
        except (FileNotFoundError, IndexError) as e:
            print(f"\n  -> FAILURE: Could not parse results for I={I:.3f}A. Check 'sim/elmersolver.log'. Error: {e}")
            inductances.append(np.nan); fluxes.append(np.nan); energies.append(np.nan)
            
        # Após a simulação, gera a vista no ParaView e guarda o frame
        if run_pv:
            run_paraview_script(pv_script)
            default_pv_out = os.path.join(plots_dir, "cena_paraview.png")
            frame_path = os.path.join(plots_dir, f"frame_I_{I:.3f}A.png")
            if os.path.exists(default_pv_out):
                os.replace(default_pv_out, frame_path)  # Renomeia a imagem
                frames_paths.append(frame_path)

    if currents[0] == 0.0 and len(inductances) > 1:
        inductances[0] = next((val for val in inductances[1:] if not np.isnan(val)), 0)

    # --- 6. Plotting Final Results ---
    print("\n--- Plotting simulation results ---")
    plot_simulation_results(currents, inductances, fluxes, energies, plots_dir, N_turns)
    print(f"  -> All result plots saved to '{plots_dir}'")

    print("\n--- Plotting flux line ---")
    flux_line_filepath = os.path.join(sim_dir, "result", "plot", "linha_fluxo.dat")
    plot_flux_line(flux_line_filepath, plots_dir)

    if frames_paths:
        print("\n--- Generating Animation (GIF) ---")
        try:
            frames = [Image.open(f) for f in frames_paths]
            
            # Adiciona os frames em ordem decrescente (do penúltimo ao segundo) para o efeito de pulso
            pulsing_frames = frames + frames[-2:0:-1]
            
            gif_path = os.path.join(plots_dir, "animacao_campo.gif")
            # duration = tempo por frame em ms (150ms = ~6.6 FPS)
            pulsing_frames[0].save(gif_path, format='GIF', append_images=pulsing_frames[1:], save_all=True, duration=150, loop=0)
            print(f"  -> Animação GIF gerada perfeitamente em '{gif_path}'!")
        except Exception as e:
            print(f"  -> Erro ao gerar o GIF: {e}")

    print("\n--- Simulation finished successfully! ---")

if __name__ == "__main__":
    main()
