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

def plot_transient_results(data, plots_dir):
    """
    Generates and saves a plot for each variable present in the raw transient data.
    data[:, 0] is assumed to be the Time axis.
    """
    if data.shape[0] == 0 or data.shape[1] < 2:
        print("  -> Não há variáveis suficientes para plotar (apenas o tempo foi salvo).")
        return
        
    times = data[:, 0]
    
    # Nomes baseados nas variáveis definidas no solvers.yml
    # O Elmer frequentemente adiciona "Eddy Current Power" e "Magnetic Energy" no final.
    labels = {
        1: "Current Density (Mean Z)",
        2: "Potential (Volume Integral)",
        3: "Potential (Surface Integral)",
        4: "Eddy Current Power",
        5: "Electromagnetic Field Energy"
    }

    for i in range(1, data.shape[1]):
        plt.figure(figsize=(10, 6))
        plt.plot(times, data[:, i], marker='o', linestyle='-', color='tab:blue')
        
        var_name = labels.get(i, f"Variable {i}")
        plt.title(f"Transient Simulation: {var_name} over Time")
        plt.xlabel("Time (s)")
        plt.ylabel(var_name)
        plt.grid(True, linestyle='--', alpha=0.7)
        plt.tight_layout()
        
        plot_path = os.path.join(plots_dir, f"transient_var_{i}.png")
        plt.savefig(plot_path)
        plt.close()

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