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
from src.plotting import plot_bh_curve, plot_simulation_results, plot_flux_line, run_paraview_script

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

    # Define the range of currents to simulate
    env_current = os.getenv("CURRENT")
    if env_current is not None:
        # Se a variável CURRENT for informada, o loop rodará apenas para este valor
        currents = [float(env_current)]
    else:
        currents = np.unique(np.concatenate((np.linspace(0, 0.2, 10), np.linspace(0.2, 2, 20))))

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
    
    # Atualiza o SIF base com a corrente inicial através das Body Forces
    NI_initial = N_turns * currents[0]
    bf_a_plus.data["Current Density"] = f"-distribute {NI_initial:.6f}"
    bf_a_minus.data["Current Density"] = f"-distribute {-NI_initial:.6f}"

    if run_sif:
        # sim.write_startinfo(sim_dir) # Não é mais necessário com a alteração em run_elmer_solver
        sim.write_sif(sim_dir)
        print("  -> SIF structure created and saved.")
    else:
        print("  -> Pular etapa: Escrita do SIF base.")

    # --- 5. Simulation Loop ---
    print("\n--- Starting simulation loop over currents ---")
    
    # Lists to store results
    inductances, fluxes, energies = [], [], []

    summary_filepath = os.path.join(sim_dir, "result", "scalar", "results_summary.txt")

    pv_script = os.path.abspath("export_view.py")
    run_pv = os.path.exists(pv_script)

    if run_solver:
        for I in currents:
            print(f"\n--- Simulating for Current = {I:.3f} A ---")
            
            # Se for uma única corrente, executa direto na pasta raiz 'sim' para aproveitar o SIF base
            if len(currents) == 1:
                current_sim_dir = sim_dir
            else:
                # Create a dedicated directory for this simulation run
                current_sim_dir = os.path.join(sim_dir, f"I_{I:.3f}A")
                os.makedirs(current_sim_dir, exist_ok=True)
                for sub in ["result/paraview", "result/scalar", "result/plot"]:
                    os.makedirs(os.path.join(current_sim_dir, sub), exist_ok=True)

            # Só sobrescreve o SIF aqui se RUN_SIF estiver ativado
            if run_sif:
                # Update the current density in the body forces for this simulation run
                NI = N_turns * I
                bf_a_plus.data["Current Density"] = f"-distribute {NI:.6f}"
                bf_a_minus.data["Current Density"] = f"-distribute {-NI:.6f}"
                sim.write_sif(current_sim_dir)
                
            # Run solver in the specific directory
            run_elmer_solver(current_sim_dir)
            
            # Update scalar file path for parsing
            scalar_filepath_current = os.path.join(current_sim_dir, "result", "scalar", "integrais_bobina.dat")

            try:
                flux_val, Wj, L = parse_scalar_results(scalar_filepath_current, N_turns, core_depth, I)
                print(f"  -> Inductance L calculated: {L:.6e} H")
                inductances.append(L); fluxes.append(flux_val); energies.append(Wj)
            except (FileNotFoundError, IndexError) as e:
                print(f"\n  -> FAILURE: Could not parse results for I={I:.3f}A. Check 'sim/elmersolver.log'. Error: {e}")
                inductances.append(np.nan); fluxes.append(np.nan); energies.append(np.nan)
                
            # After simulation, generate the ParaView view and save the frame
            if run_pv:
                pvd_path = os.path.join(current_sim_dir, "result", "paraview", "results.pvd")
                frame_path = os.path.join(plots_dir, f"frame_I_{I:.3f}A.png")
                run_paraview_script(
                    script_path=pv_script,
                    pvd_input_path=pvd_path,
                    png_output_path=frame_path
                )

        if currents[0] == 0.0 and len(inductances) > 1:
            inductances[0] = next((val for val in inductances[1:] if not np.isnan(val)), 0)
            
        # Salva o estado dos escalares para o pós-processamento independente
        np.savetxt(summary_filepath, np.column_stack((currents, inductances, fluxes, energies)), 
                   header="Current(A) Inductance(H) Flux(Vs) Energy(J)")
    else:
        print("  -> Pular etapa: Solver.")

    # --- 6. Plotting Final Results ---
    if run_post:
        print("\n--- Plotting material properties ---")
        plot_bh_curve(iron_material, plots_dir)

        if os.path.exists(summary_filepath):
            print("\n--- Plotting simulation results ---")
            data = np.loadtxt(summary_filepath, ndmin=2)
            plot_simulation_results(data[:, 0], data[:, 1], data[:, 2], data[:, 3], plots_dir, N_turns)
            print(f"  -> All result plots saved to '{plots_dir}'")
        else:
            print(f"  -> AVISO: {summary_filepath} não encontrado. Execute o solver primeiro para plotar os dados.")

        print("\n--- Plotting flux line for each simulation run ---")
        sim_subdirs = sorted(glob.glob(os.path.join(sim_dir, "I_*A")))
        if not sim_subdirs:
            # Fallback para o modo de execução única (usa a pasta raiz sim)
            sim_subdirs = [sim_dir]

        for current_sim_dir in sim_subdirs:
            flux_line_filepath = os.path.join(current_sim_dir, "result", "plot", "linha_fluxo.dat")
            if os.path.exists(flux_line_filepath):
                plot_flux_line(flux_line_filepath, current_sim_dir)

        # Buscar frames para a animação independentemente de termos rodado o solver ou não (caso já existam na pasta)
        frames_paths = sorted(glob.glob(os.path.join(plots_dir, "frame_I_*.png")))
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
    else:
        print("\n  -> Pular etapa: Pós-processamento e gráficos.")

    print("\n--- Simulation finished successfully! ---")

if __name__ == "__main__":
    main()
