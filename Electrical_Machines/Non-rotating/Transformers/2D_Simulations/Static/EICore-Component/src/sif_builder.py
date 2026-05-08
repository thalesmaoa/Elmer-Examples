# src/sif_builder.py
"""
Module to construct the Elmer Solver Input File (SIF) using the pyelmer library.
"""
from pyelmer import elmer

def setup_simulation_sif(mesh_basename, physical_ids, core_depth=70e-3, N_turns=217):
    """
    Sets up the entire simulation structure for Elmer.

    This function defines all the necessary components for the SIF file:
    - Simulation settings, materials, solvers, equations, bodies, and boundaries.

    Args:
        mesh_basename (str): The base name of the mesh directory (without extension).
        physical_ids (dict): A dictionary mapping physical names to their integer IDs.
        core_depth (float): Depth of the 2D model in meters.
        N_turns (int): Number of turns in the coil.

    Returns:
        tuple: (sim, bf_a_plus, bf_a_minus, iron)
    """
    # --- Simulation Setup ---
    sim = elmer.load_simulation("2D_steady")
    sim.header["Mesh DB"] = f'"." "../mesh/{mesh_basename}"'
    
    # Opcional: injetar a profundidade do modelo na seção de Simulação global
    # sim.data["Model Depth"] = core_depth

    # --- Materials ---
    air = elmer.load_material("air", sim)
    iron = elmer.load_material("iron", sim)

    # --- Solvers ---
    solver_magnetic = elmer.load_solver("MgDyn2D", sim)
    solver_magnetic_post = elmer.load_solver("MgDynPost", sim)
    solver_magnetic_paraview = elmer.load_solver("ResultOutput", sim)
    solver_saveline = elmer.load_solver("SaveLine", sim)
    
    solver_magnetic_savescalars = elmer.load_solver("SaveScalars", sim)
    solver_magnetic_savescalars.data.update({
        "Filename": '"result/scalar/integrais_bobina.dat"'
    })

    # --- Equation ---
    eqn = elmer.Equation(sim, "main", [
        solver_magnetic,
        solver_magnetic_post,
        solver_magnetic_paraview,
        solver_saveline,
        solver_magnetic_savescalars,
    ])

    # --- Body Forces ---
    # The "-distribute" keyword tells Elmer to distribute the total Ampere-turns (NI)
    # evenly over the body's cross-section.
    bf_a_plus = elmer.BodyForce(sim, "Circuit_a_plus", {"Current Density": "Real 0.0"})
    bf_a_minus = elmer.BodyForce(sim, "Circuit_a_minus", {"Current Density": "Real 0.0"})

    # --- Bodies ---
    # A Body connects a geometric region (by ID) to its properties.
    bdy_air = elmer.Body(sim, "Air", [physical_ids["air"]])
    bdy_air.material = air
    bdy_air.equation = eqn

    bdy_iron = elmer.Body(sim, "iron", [physical_ids["iron"]])
    bdy_iron.material = iron
    bdy_iron.equation = eqn

    # Coil bodies are modeled as air with a current source
    bdy_coil_a_minus = elmer.Body(sim, "coil_a_minus_Faces", [physical_ids["coil_a_minus"]])
    bdy_coil_a_minus.material = air
    bdy_coil_a_minus.equation = eqn
    bdy_coil_a_minus.body_force = bf_a_minus

    bdy_coil_a_plus = elmer.Body(sim, "coil_a_plus_Faces", [physical_ids["coil_a_plus"]])
    bdy_coil_a_plus.material = air
    bdy_coil_a_plus.equation = eqn
    bdy_coil_a_plus.body_force = bf_a_plus
    # Add settings to this body to enable the SaveScalars calculations
    bdy_coil_a_plus.data.update({
        "Integral Area": "Logical True",
        "Integral Potencial": "Logical True"
    })
    
    # Unused coil bodies for this simulation (must be assigned to a Body to avoid Segmentation fault)
    bdy_coil_b_minus = elmer.Body(sim, "coil_b_minus_Faces", [physical_ids["coil_b_minus"]])
    bdy_coil_b_minus.material = air
    bdy_coil_b_minus.equation = eqn

    bdy_coil_b_plus = elmer.Body(sim, "coil_b_plus_Faces", [physical_ids["coil_b_plus"]])
    bdy_coil_b_plus.material = air
    bdy_coil_b_plus.equation = eqn

    # --- Boundaries ---
    # Set the magnetic vector potential 'A' to zero at the outer boundary.
    bndry_zero = elmer.Boundary(sim, "zero", [physical_ids["zerobound"]])
    bndry_zero.data.update({"Potential": 0.0})
    # comp = elmer.

    # --- Components ---
    component_circuit_a = elmer.Component(sim, "Circuit A")
    component_circuit_a.master_bodies = [bdy_coil_a_plus, bdy_coil_a_minus]
    component_circuit_a.data["Coil Type"] = "stranded"
    component_circuit_a.data["Number of Turns"] = f"Real {float(N_turns)}"

    solver_magnetic_post.data["Calculate Flux Linkage"] = "Logical True"
    solver_magnetic_post.data["Calculate Joule Heating"] = "Logical True"
    solver_magnetic_post.data["Potential Variable"] = 'String "Potential"'
    solver_magnetic_post.data["Impose Body Force Current"] = "Logical True"
    solver_magnetic_post.data["Calculate Magnetic Vector Potential"] = "Logical True"
    
    return sim, bf_a_plus, bf_a_minus, iron
