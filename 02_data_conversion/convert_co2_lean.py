#!/usr/bin/env python3
"""
Convert CO2_lean_AIMD CP2K output to DeePMD-kit npy format.

Handles:
  - Split output files (aimd.out + aimd_cont.out)
  - Forces file containing both equilibration and production data
  - Restart alignment
"""

import os
import re
import numpy as np
import argparse

# Unit conversion constants
HARTREE_TO_EV = 27.211386245988
BOHR_TO_ANG = 0.529177210903
HA_BOHR_TO_EV_ANG = HARTREE_TO_EV / BOHR_TO_ANG
GPA_ANG3_TO_EV = 1.0 / 160.21766208


def parse_xyz_trajectory(filepath):
    """Parse XYZ trajectory file."""
    frames = []
    atom_names = []
    with open(filepath) as f:
        while True:
            line = f.readline()
            if not line:
                break
            natoms = int(line.strip())
            f.readline()  # comment
            frame = []
            names = []
            for _ in range(natoms):
                parts = f.readline().split()
                names.append(parts[0])
                frame.append([float(parts[1]), float(parts[2]), float(parts[3])])
            frames.append(frame)
            if not atom_names:
                atom_names = names
    return atom_names, np.array(frames)


def parse_energy_file(filepath):
    """Parse CP2K energy file."""
    steps = []
    pot_energies = []
    with open(filepath) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            steps.append(int(parts[0]))
            pot_energies.append(float(parts[4]))
    return np.array(steps), np.array(pot_energies)


def parse_forces_file(filepath, natoms):
    """Parse CP2K forces file."""
    blocks = []
    current_block = []
    in_block = False
    with open(filepath) as f:
        for line in f:
            if 'ATOMIC FORCES in' in line:
                if current_block:
                    blocks.append(current_block)
                current_block = []
                in_block = True
                continue
            if in_block and line.strip().startswith('#'):
                continue
            if in_block and 'SUM OF ATOMIC' in line:
                in_block = False
                continue
            if in_block and line.strip():
                parts = line.split()
                if len(parts) >= 6:
                    current_block.append([float(parts[3]), float(parts[4]), float(parts[5])])
    if current_block:
        blocks.append(current_block)
    # Only keep complete blocks (natoms lines)
    blocks = [b for b in blocks if len(b) == natoms]
    return np.array(blocks)


def parse_cell_lengths_from_outputs(filepaths):
    """Parse cell lengths from multiple CP2K output files."""
    cell_lengths = []
    for filepath in filepaths:
        if not os.path.exists(filepath):
            continue
        with open(filepath) as f:
            for line in f:
                if 'Cell lengths [ang]' in line and ('MD|' in line or 'MD_INI|' in line):
                    numbers = re.findall(r'[\d.]+E[+-]\d+', line)
                    if len(numbers) >= 3:
                        cell_lengths.append([float(numbers[0]), float(numbers[1]), float(numbers[2])])
    return np.array(cell_lengths)


def parse_stress_tensors_from_outputs(filepaths):
    """Parse stress tensors from multiple CP2K output files."""
    stresses = []
    for filepath in filepaths:
        if not os.path.exists(filepath):
            continue
        with open(filepath) as f:
            lines = f.readlines()
        i = 0
        while i < len(lines):
            if 'STRESS| Analytical stress tensor [GPa]' in lines[i]:
                tensor = []
                for row in range(3):
                    i += 1
                    while i < len(lines) and 'STRESS|' in lines[i]:
                        parts = lines[i].split()
                        if len(parts) >= 5 and parts[1] in ('x', 'y', 'z'):
                            tensor.append([float(parts[2]), float(parts[3]), float(parts[4])])
                            break
                        i += 1
                if len(tensor) == 3:
                    stresses.append(tensor)
            i += 1
    return np.array(stresses)


def stress_to_virial(stress_gpa, volume_ang3):
    return -stress_gpa * volume_ang3 * GPA_ANG3_TO_EV


def convert_temperature(temp_dir, output_dir, type_map, subsample=1):
    """Convert one temperature's AIMD data to DeePMD format."""
    traj_file = os.path.join(temp_dir, 'aimd-aimd.xyz-pos-1.xyz')
    ener_file = os.path.join(temp_dir, 'aimd-1.ener')
    force_file = os.path.join(temp_dir, 'forces')
    # Multiple output files
    out_files = [
        os.path.join(temp_dir, 'aimd.out'),
        os.path.join(temp_dir, 'aimd_cont.out'),
    ]

    print(f"  Parsing trajectory...")
    atom_names, coords = parse_xyz_trajectory(traj_file)
    nframes = coords.shape[0]
    natoms = coords.shape[1]
    print(f"    {nframes} frames, {natoms} atoms")

    print(f"  Parsing energies...")
    steps, pot_energies = parse_energy_file(ener_file)
    print(f"    {len(steps)} energy entries (steps {steps[0]}-{steps[-1]})")

    print(f"  Parsing forces...")
    all_forces = parse_forces_file(force_file, natoms)
    print(f"    {all_forces.shape[0]} total force blocks (incl. equilibration)")

    # The forces file contains equilibration + production forces.
    # Production starts after equilibration (5000 steps).
    # Take only the last nframes + n_extra forces.
    # n_extra accounts for restart eval entries.
    print(f"  Parsing cell lengths from output files...")
    cell_lengths = parse_cell_lengths_from_outputs(out_files)
    print(f"    {cell_lengths.shape[0]} cell entries")

    print(f"  Parsing stress tensors from output files...")
    stresses = parse_stress_tensors_from_outputs(out_files)
    print(f"    {stresses.shape[0]} stress tensors")

    # Cell/stress include initial eval + MD steps. For each output file segment,
    # there's 1 initial eval + N MD steps = N+1 entries per segment.
    # Number of restart segments from step discontinuities
    gaps = np.where(np.diff(steps) < 0)[0]
    n_segments = len(gaps) + 1
    seg_boundaries = [0] + list(gaps + 1) + [len(steps)]
    seg_sizes = [seg_boundaries[i+1] - seg_boundaries[i] for i in range(n_segments)]
    print(f"    Detected {n_segments} segments, sizes: {seg_sizes}")

    # For cell/stress: each segment has seg_size+1 entries (initial eval + steps)
    # We need to skip the first entry of each segment
    expected_cs = sum(s + 1 for s in seg_sizes)
    print(f"    Expected cell/stress entries: {expected_cs}, got cell={len(cell_lengths)}, stress={len(stresses)}")

    # Remove initial eval entry from each segment
    skip_cs = []
    pos = 0
    for s in seg_sizes:
        skip_cs.append(pos)
        pos += s + 1
    print(f"    Skipping initial eval at positions: {skip_cs}")

    keep_cs = np.ones(len(cell_lengths), dtype=bool)
    keep_cs[skip_cs] = False
    cell_lengths = cell_lengths[keep_cs]
    keep_st = np.ones(len(stresses), dtype=bool)
    keep_st[skip_cs[:len(stresses)]] = False  # stress might have fewer
    stresses = stresses[keep_st]

    # For forces: file contains equil forces + production forces + restart evals
    # We need to extract only production forces.
    # Strategy: take the last (nframes + n_segments) force blocks,
    # then remove 1 restart eval per segment
    n_prod_forces = nframes + n_segments
    forces = all_forces[-n_prod_forces:]
    # Remove restart eval (first entry of each segment)
    skip_f = []
    pos = 0
    for s in seg_sizes:
        skip_f.append(pos)
        pos += s + 1
    keep_f = np.ones(len(forces), dtype=bool)
    keep_f[skip_f] = False
    forces = forces[keep_f]

    # Verify alignment
    print(f"  After alignment: coords={nframes}, energy={len(pot_energies)}, "
          f"forces={len(forces)}, cell={len(cell_lengths)}, stress={len(stresses)}")

    min_frames = min(nframes, len(pot_energies), len(forces), len(cell_lengths), len(stresses))
    if min_frames < nframes:
        print(f"  WARNING: Trimming to {min_frames} frames (smallest dataset)")
        coords = coords[:min_frames]
        pot_energies = pot_energies[:min_frames]
        forces = forces[:min_frames]
        cell_lengths = cell_lengths[:min_frames]
        stresses = stresses[:min_frames]
        nframes = min_frames

    # Subsample
    if subsample > 1:
        indices = np.arange(0, nframes, subsample)
        coords = coords[indices]
        pot_energies = pot_energies[indices]
        forces = forces[indices]
        stresses = stresses[indices]
        cell_lengths = cell_lengths[indices]
        nframes = len(indices)
        print(f"  Subsampled to {nframes} frames (every {subsample})")

    # Unit conversions
    energies_ev = pot_energies * HARTREE_TO_EV
    forces_ev_ang = forces * HA_BOHR_TO_EV_ANG

    # Box vectors (cubic NPT_I)
    boxes = np.zeros((nframes, 9))
    for i in range(nframes):
        a, b, c = cell_lengths[i]
        boxes[i] = [a, 0, 0, 0, b, 0, 0, 0, c]

    # Virials
    volumes = cell_lengths[:, 0] * cell_lengths[:, 1] * cell_lengths[:, 2]
    virials = np.zeros((nframes, 9))
    for i in range(nframes):
        v = stress_to_virial(stresses[i], volumes[i])
        virials[i] = v.flatten()

    # Type mapping
    type_dict = {name: i for i, name in enumerate(type_map)}
    type_indices = np.array([type_dict[name] for name in atom_names])

    # Write DeePMD npy format
    os.makedirs(output_dir, exist_ok=True)
    set_dir = os.path.join(output_dir, 'set.000')
    os.makedirs(set_dir, exist_ok=True)

    with open(os.path.join(output_dir, 'type.raw'), 'w') as f:
        for t in type_indices:
            f.write(f"{t}\n")

    with open(os.path.join(output_dir, 'type_map.raw'), 'w') as f:
        for name in type_map:
            f.write(f"{name}\n")

    np.save(os.path.join(set_dir, 'box.npy'), boxes)
    np.save(os.path.join(set_dir, 'coord.npy'), coords.reshape(nframes, -1))
    np.save(os.path.join(set_dir, 'energy.npy'), energies_ev)
    np.save(os.path.join(set_dir, 'force.npy'), forces_ev_ang.reshape(nframes, -1))
    np.save(os.path.join(set_dir, 'virial.npy'), virials)

    print(f"  Written to {output_dir}")
    print(f"    type_map: {type_map}")
    print(f"    frames: {nframes}")
    print(f"    energy range: {energies_ev.min():.4f} to {energies_ev.max():.4f} eV")
    print(f"    cell range: {cell_lengths.min():.4f} to {cell_lengths.max():.4f} Ang")

    return nframes


def main():
    parser = argparse.ArgumentParser(description='Convert CO2_lean_AIMD to DeePMD format')
    parser.add_argument('--aimd-dir', default='/gs/fs/tga-harada/Moin/deepmd/CO2_lean_AIMD',
                        help='Directory containing temperature subdirectories')
    parser.add_argument('--output-dir', default='/gs/fs/tga-harada/Moin/deepmd/CO2_lean_AIMD/data',
                        help='Output directory for DeePMD data')
    parser.add_argument('--subsample', type=int, default=5,
                        help='Take every Nth frame (default: 5)')
    parser.add_argument('--temps', nargs='+', default=['600C', '700C', '800C', '900C', '1000C'],
                        help='Temperature directories to convert')
    parser.add_argument('--type-map', nargs='+', default=['B', 'O', 'Na', 'Li'],
                        help='Type map (must match DP-Gen param.json)')
    args = parser.parse_args()

    total_frames = 0
    for temp in args.temps:
        print(f"\n{'='*60}")
        print(f"Converting {temp}...")
        print(f"{'='*60}")
        temp_dir = os.path.join(args.aimd_dir, temp)
        out_dir = os.path.join(args.output_dir, temp)
        nf = convert_temperature(temp_dir, out_dir, args.type_map, subsample=args.subsample)
        total_frames += nf

    print(f"\n{'='*60}")
    print(f"DONE: {total_frames} total frames across {len(args.temps)} temperatures")
    print(f"Output: {args.output_dir}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
