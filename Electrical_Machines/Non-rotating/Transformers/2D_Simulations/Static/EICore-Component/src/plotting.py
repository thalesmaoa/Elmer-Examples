# src/plotting.py
"""
Module for creating and saving all plots related to the simulation.
"""
import os
import numpy as np
import matplotlib.pyplot as plt

def plot_bh_curve(material, plots_dir):
    """
    Extracts the B-H curve data from a pyelmer material object and plots it.

    Args:
        material (pyelmer.Material): The material object (e.g., iron).
        plots_dir (str): The directory where the plots will be saved.
    """
    if "H-B Curve" not in material.data:
        print("  -> No B-H curve data found in the material.")
        return

    hb_data, col1, col2 = material.data["H-B Curve"], [], []

    if isinstance(hb_data, (list, tuple)):
        for item in hb_data:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                try:
                    col1.append(float(item[0])); col2.append(float(item[1]))
                except (ValueError, TypeError): continue
    else:
        for line in str(hb_data).splitlines():
            parts = line.replace(',', ' ').strip().split()
            if len(parts) >= 2:
                try:
                    col1.append(float(parts[0])); col2.append(float(parts[1]))
                except ValueError: continue
    
    if not (col1 and col2):
        print("  -> Failed to parse B-H curve data.")
        return

    B_vals, H_vals = (col1, col2) if max(col1) < max(col2) else (col2, col1)
    
    # --- Plot 1: Linear Scale ---
    plt.figure(figsize=(8, 6))
    plt.plot(H_vals, B_vals, marker='.', linestyle='-', color='k', label=f'Material ({material.name})')
    plt.title("Material B-H Curve"); plt.xlabel("Magnetic Field Strength H (A/m)"); plt.ylabel("Magnetic Flux Density B (T)")
    plt.grid(True, linestyle='--', alpha=0.7); plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "material_BH_curve_linear.png")); plt.close()

    # --- Plot 2: Logarithmic H-axis Scale ---
    plt.figure(figsize=(8, 6))
    plt.plot(H_vals, B_vals, marker='.', linestyle='-', color='k', label=f'Material ({material.name})')
    plt.title("Material B-H Curve (Logarithmic H-axis)"); plt.xlabel("Magnetic Field Strength H (A/m)"); plt.ylabel("Magnetic Flux Density B (T)")
    plt.xscale('log'); plt.grid(True, which="both", linestyle='--', alpha=0.7); plt.legend(); plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "material_BH_curve_log.png")); plt.close()
    
    print(f"  -> Material B-H curve plots saved to '{plots_dir}'.")

def plot_simulation_results(currents, inductances, fluxes, energies, plots_dir, N_turns):
    """
    Generates and saves plots from the simulation results.
    """
    # --- Inductance vs. Current ---
    plt.figure(figsize=(8, 6))
    plt.plot(currents, inductances, marker='o', linestyle='-', color='b')
    plt.title("Inductance vs. Current"); plt.xlabel("Coil Current (A)"); plt.ylabel("Inductance (H)")
    plt.grid(True, linestyle='--', alpha=0.7); plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "inductance_vs_current.png")); plt.close()

    # --- Flux vs. Current ---
    plt.figure(figsize=(8, 6))
    plt.plot(currents, fluxes, marker='o', linestyle='-', color='r')
    plt.title("Magnetic Flux vs. Current"); plt.xlabel("Coil Current (A)"); plt.ylabel("Magnetic Flux (V.s or Wb)")
    plt.grid(True, linestyle='--', alpha=0.7); plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "flux_vs_current.png")); plt.close()

    # --- Energy vs. Current ---
    plt.figure(figsize=(8, 6))
    plt.plot(currents, energies, marker='o', linestyle='-', color='g')
    plt.title("Magnetic Energy vs. Current"); plt.xlabel("Coil Current (A)"); plt.ylabel("Magnetic Energy (J)")
    plt.grid(True, linestyle='--', alpha=0.7); plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "energy_vs_current.png")); plt.close()

    # --- Combined Inductance and Flux vs. Current ---
    fig, ax1 = plt.subplots(figsize=(8, 6))
    color1 = 'b'
    ax1.set_xlabel("Coil Current (A)")
    ax1.set_ylabel("Inductance (H)", color=color1)
    ax1.plot(currents, inductances, marker='o', linestyle='-', color=color1, label='Inductance')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, linestyle='--', alpha=0.7)

    ax2 = ax1.twinx()
    color2 = 'r'
    ax2.set_ylabel("Magnetic Flux (V.s)", color=color2)
    ax2.plot(currents, fluxes, marker='s', linestyle='--', color=color2, label='Flux')
    ax2.tick_params(axis='y', labelcolor=color2)

    plt.title("Inductance and Flux vs. Current")
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper left')
    fig.tight_layout()
    plt.savefig(os.path.join(plots_dir, "inductance_and_flux_vs_current.png")); plt.close()
    
    # --- Combined Inductance and Relative Permeability vs. Current ---
    # This is an estimation of the effective permeability of the core.
    peak_mu_r_assumed = 4138
    max_inductance = np.nanmax(inductances)
    if max_inductance > 0:
        # mu_r = L * (l_e / (N^2 * A_e * mu_0))
        # We define a factor K = (peak_mu_r * N^2) / max_L
        geometric_factor_K = peak_mu_r_assumed / max_inductance
        mu_r_values = [L * geometric_factor_K for L in inductances]
    else:
        mu_r_values = [0] * len(inductances)

    fig, ax1 = plt.subplots(figsize=(8, 6))
    color1 = 'b'
    ax1.set_xlabel("Coil Current (A)")
    ax1.set_ylabel("Inductance (H)", color=color1)
    ax1.plot(currents, inductances, marker='o', linestyle='-', color=color1, label='Inductance')
    ax1.tick_params(axis='y', labelcolor=color1)
    ax1.grid(True, linestyle='--', alpha=0.7)

    ax2 = ax1.twinx()
    color2 = 'g'
    ax2.set_ylabel("Effective Relative Permeability ($\mu_r$)", color=color2)
    ax2.plot(currents, mu_r_values, marker='^', linestyle='--', color=color2, label='Est. $\mu_r$')
    ax2.tick_params(axis='y', labelcolor=color2)
    
    ax2.axhline(y=peak_mu_r_assumed, color='k', linestyle=':', linewidth=2, label=f'Assumed Peak $\mu_r$')
    
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax2.legend(lines + lines2, labels + labels2, loc='upper right')

    plt.title("Inductance and Estimated Permeability vs. Current")
    fig.tight_layout()
    plt.savefig(os.path.join(plots_dir, "inductance_and_permeability_vs_current.png")); plt.close()

def plot_flux_line(filepath, plots_dir):
    """
    Plots the normal magnetic flux density (By) along the defined line.
    """
    if not os.path.exists(filepath):
        print(f"  -> File not found: {filepath}")
        return

    try:
        data = np.loadtxt(filepath)
        if len(data) == 0:
            return
            
        # Extract X coordinate (column 4 -> index 3) and Nodal By (column 9 -> index 8)
        x_coords = data[:, 3]
        # By_vals = data[:, 8]
        By_vals = data[:, 17]
        
        # Sort by X coordinate so the line plots correctly sequentially
        sort_idx = np.argsort(x_coords)
        x_coords = x_coords[sort_idx]
        By_vals = By_vals[sort_idx]

        plt.figure(figsize=(10, 6))
        plt.plot(x_coords, By_vals, linestyle='-', color='purple', linewidth=2)
        plt.title("Densidade de Fluxo Magnético Normal ($B_y$)")
        plt.xlabel("Coordenada X (m)")
        plt.ylabel("Densidade de Fluxo Normal $B_y$ (T)")
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        plot_path = os.path.join(plots_dir, "normal_flux_density_By.png")
        plt.savefig(plot_path)
        plt.close()
        
        print(f"  -> Gráfico de densidade de fluxo na linha salvo em '{plot_path}'.")
    except Exception as e:
        print(f"  -> Erro ao plotar a linha de fluxo: {e}")

def run_paraview_script(script_path, pvd_input_path, png_output_path):
    """
    Executa um script de estado do ParaView para exportar uma cena customizada.
    Lê o executável/comando do ParaView a partir da variável de ambiente PVBATCH_CMD.

    Args:
        script_path (str): Path to the ParaView python script.
        pvd_input_path (str): Path to the .pvd file to be loaded by the script.
        png_output_path (str): Path where the output screenshot will be saved.
    """
    import subprocess
    import shlex
    
    if not os.path.exists(script_path):
        print(f"  -> Script do ParaView não encontrado: {script_path}\n     Crie-o no ParaView indo em File -> Save State -> (*.py)")
        return
        
    pvbatch_cmd = os.environ.get("PVBATCH_CMD", "pvbatch")
    cmd_args = shlex.split(pvbatch_cmd) + [script_path, os.path.abspath(pvd_input_path), os.path.abspath(png_output_path)]
    
    try:
        result = subprocess.run(cmd_args, check=True, capture_output=True, text=True)
        print(f"  -> Vista exportada perfeitamente pelo script ParaView para '{png_output_path}'!")
    except FileNotFoundError:
        print(f"  -> ERRO: O comando '{cmd_args[0]}' não foi encontrado. Verifique sua instalação ou seu arquivo 'stack.env'.")
    except subprocess.CalledProcessError as e:
        print(f"  -> Erro na execução do pvbatch: {e}\n     STDOUT: {e.stdout}\n     STDERR: {e.stderr}")