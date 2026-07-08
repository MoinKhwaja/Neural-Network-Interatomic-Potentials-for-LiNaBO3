#!/usr/bin/env python3
"""
Convert CP2K AIMD output to DeePMD-kit npy format.

Reads:
  - Coordinates from aimd-aimd.xyz-pos-1.xyz
  - Energies from aimd-1.ener (Hartree)
  - Forces from forces file (Hartree/Bohr)
  - Cell lengths from aimd.out (Angstrom, NPT_I isotropic)
  - Stress tensors from aimd.out (GPa)

Writes DeePMD npy format with proper unit conversions:
  - Energies in eV
  - Forces in eV/Angstrom
  - Coordinates in Angstrom
  - Box vectors in Angstrom
  - Virials in eV
"""

import os
import re
import numpy as np
import argparse

# Unit conversion constants
HARTREE_TO_EV = 27.211386245988
BOHR_TO_ANG = 0.529177210903
HA_BOHR_TO_EV_ANG = HARTREE_TO_EV / BOHR_TO_ANG  # ~51.422 eV/Ang
GPA_ANG3_TO_EV = 1.0 / 160.21766208  # GPa * Ang^3 -> eV


def parse_xyz_trajectory(filepath):
    """Parse XYZ trajectory file. Returns atom_names, coords (nframes, natoms, 3) in Angstrom."""
    frames = []
    atom_names = []
    with open(filepath) as f:
        while True:
            line = f.readline()
            if not line:
                break
            natoms = int(line.strip())
            f.readline()  # comment line
            frame = []
            names = []
            for _ in range(natoms):
                parts = f.readline().split()
                names.append(parts[0])
                frame.append([float(parts[1]), float(parts[2]), float(parts[3])])
            frames.append(frame)
            if not atom_names:
                atom_names = names
    coords = np.array(frames)  # (nframes, natoms, 3)
    return atom_names, coords


def parse_energy_file(filepath):
    """Parse CP2K energy file. Returns step numbers and potential energies in Hartree."""
    steps = []
    pot_energies = []
    with open(filepath) as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            parts = line.split()
            steps.append(int(parts[0]))
            pot_energies.append(float(parts[4]))  # Pot. energy column
    return np.array(steps), np.array(pot_energies)


def parse_forces_file(filepath, natoms):
    """Parse CP2K forces file. Returns forces (nblocks, natoms, 3) in Hartree/Bohr."""
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
    forces = np.array(blocks)  # (nblocks, natoms, 3)
    return forces


def parse_cell_lengths_from_output(filepath):
    """Parse cell lengths from CP2K output. Returns (n, 3) array in Angstrom."""
    cell_lengths = []
    with open(filepath) as f:
        for line in f:
            if 'Cell lengths [ang]' in line and ('MD|' in line or 'MD_INI|' in line):
                # Extract the 3 cell lengths
                numbers = re.findall(r'[\d.]+E[+-]\d+', line)
                if len(numbers) >= 3:
                    cell_lengths.append([float(numbers[0]), float(numbers[1]), float(numbers[2])])
    return np.array(cell_lengths)


def parse_stress_tensors_from_output(filepath):
    """Parse analytical stress tensors from CP2K output. Returns (n, 3, 3) in GPa."""
    stresses = []
    with open(filepath) as f:
        lines = f.readlines()

    i = 0
    while i < len(lines):
        if 'STRESS| Analytical stress tensor [GPa]' in lines[i]:
            # Next 3 lines are x, y, z rows (skip header row)
            tensor = []
            for row in range(3):
                i += 1
                while i < len(lines) and 'STRESS|' in lines[i]:
                    parts = lines[i].split()
                    # Format: STRESS| x/y/z  val1  val2  val3
                    if len(parts) >= 5 and parts[1] in ('x', 'y', 'z'):
                        tensor.append([float(parts[2]), float(parts[3]), float(parts[4])])
                        break
                    i += 1
            if len(tensor) == 3:
                stresses.append(tensor)
        i += 1
    return np.array(stresses)


def make_type_raw(atom_names, type_map):
    """Create type indices from atom names and type_map."""
    type_dict = {name: i for i, name in enumerate(type_map)}
    return np.array([type_dict[name] for name in atom_names])


def stress_to_virial(stress_gpa, volume_ang3):
    """Convert stress tensor (GPa) to virial (eV).
    virial = -stress * volume (with sign convention for DeePMD-kit).
    """
    # virial_eV = -stress_GPa * volume_Ang3 * GPA_ANG3_TO_EV
    return -stress_gpa * volume_ang3 * GPA_ANG3_TO_EV


def convert_temperature(temp_dir, output_dir, subsample=1):
    """Convert one temperature's AIMD data to DeePMD format."""
    traj_file = os.path.join(temp_dir, 'aimd-aimd.xyz-pos-1.xyz')
    ener_file = os.path.join(temp_dir, 'aimd-1.ener')
    force_file = os.path.join(temp_dir, 'forces')
    output_file = os.path.join(temp_dir, 'aimd.out')

    print(f"  Parsing trajectory...")
    atom_names, coords = parse_xyz_trajectory(traj_file)
    nframes = coords.shape[0]
    natoms = coords.shape[1]
    print(f"    {nframes} frames, {natoms} atoms")

    print(f"  Parsing energies...")
    steps, pot_energies = parse_energy_file(ener_file)
    print(f"    {len(steps)} energy entries (steps {steps[0]}-{steps[-1]})")

    print(f"  Parsing forces...")
    forces = parse_forces_file(force_file, natoms)
    print(f"    {forces.shape[0]} force blocks")

    print(f"  Parsing cell lengths...")
    cell_lengths = parse_cell_lengths_from_output(output_file)
    print(f"    {cell_lengths.shape[0]} cell entries")

    print(f"  Parsing stress tensors...")
    stresses = parse_stress_tensors_from_output(output_file)
    print(f"    {stresses.shape[0]} stress tensors")

    # Alignment: each restart adds 1 extra evaluation entry to forces, stress, cell
    # but NOT to trajectory/energy. Detect restart boundaries from energy steps
    # (where step number decreases) and remove the corresponding restart entries.
    n_extra = forces.shape[0] - nframes
    if n_extra > 0:
        # Find restart boundaries in energy steps (where step[i+1] < step[i])
        gaps = np.where(np.diff(steps) < 0)[0]
        n_segments = len(gaps) + 1
        print(f"    Detected {n_segments} segments ({n_extra} restart evaluations to skip)")

        # Compute segment sizes from energy data
        seg_boundaries = [0] + list(gaps + 1) + [nframes]
        seg_sizes = [seg_boundaries[i+1] - seg_boundaries[i] for i in range(n_segments)]

        # Restart eval entries in forces/stress/cell are at the start of each segment
        # Position of restart eval for segment j = sum(seg_sizes[0:j]) + j
        skip_indices = []
        cumpos = 0
        for j in range(n_segments):
            skip_indices.append(cumpos)
            cumpos += seg_sizes[j] + 1  # +1 for the restart eval entry
        print(f"    Skipping restart eval entries at positions: {skip_indices}")

        keep_mask = np.ones(forces.shape[0], dtype=bool)
        keep_mask[skip_indices] = False
        forces = forces[keep_mask]
        stresses = stresses[keep_mask]
        cell_lengths = cell_lengths[keep_mask]

    # Verify alignment
    assert coords.shape[0] == len(pot_energies) == forces.shape[0] == stresses.shape[0] == cell_lengths.shape[0], \
        f"Data size mismatch: coords={coords.shape[0]}, energy={len(pot_energies)}, " \
        f"forces={forces.shape[0]}, stress={stresses.shape[0]}, cell={cell_lengths.shape[0]}"

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

    # Build box vectors (cubic cells for NPT_I)
    # box = [ax, ay, az, bx, by, bz, cx, cy, cz] per frame
    boxes = np.zeros((nframes, 9))
    for i in range(nframes):
        a, b, c = cell_lengths[i]
        boxes[i] = [a, 0, 0, 0, b, 0, 0, 0, c]

    # Compute volumes and virials
    volumes = cell_lengths[:, 0] * cell_lengths[:, 1] * cell_lengths[:, 2]
    virials = np.zeros((nframes, 9))
    for i in range(nframes):
        v = stress_to_virial(stresses[i], volumes[i])
        # Flatten 3x3 to 9 in row-major order: xx, xy, xz, yx, yy, yz, zx, zy, zz
        virials[i] = v.flatten()

    # Create type_map and type indices
    unique_elements = []
    seen = set()
    for name in atom_names:
        if name not in seen:
            unique_elements.append(name)
            seen.add(name)
    type_map = unique_elements  # B, O, Li, Na
    type_indices = make_type_raw(atom_names, type_map)

    # Write DeePMD npy format
    os.makedirs(output_dir, exist_ok=True)
    set_dir = os.path.join(output_dir, 'set.000')
    os.makedirs(set_dir, exist_ok=True)

    # type.raw
    with open(os.path.join(output_dir, 'type.raw'), 'w') as f:
        for t in type_indices:
            f.write(f"{t}\n")

    # type_map.raw
    with open(os.path.join(output_dir, 'type_map.raw'), 'w') as f:
        for name in type_map:
            f.write(f"{name}\n")

    # npy files
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
    parser = argparse.ArgumentParser(description='Convert CP2K AIMD to DeePMD format')
    parser.add_argument('--aimd-dir', default='/gs/fs/tga-harada/Moin/deepmd/AIMD',
                        help='Directory containing temperature subdirectories')
    parser.add_argument('--output-dir', default='/gs/fs/tga-harada/Moin/deepmd/data',
                        help='Output directory for DeePMD data')
    parser.add_argument('--subsample', type=int, default=5,
                        help='Take every Nth frame (default: 5)')
    parser.add_argument('--temps', nargs='+', default=['600C', '700C', '800C', '900C', '1000C'],
                        help='Temperature directories to convert')
    args = parser.parse_args()

    total_frames = 0
    for temp in args.temps:
        print(f"\n{'='*60}")
        print(f"Converting {temp}...")
        print(f"{'='*60}")
        temp_dir = os.path.join(args.aimd_dir, temp)
        out_dir = os.path.join(args.output_dir, temp)
        nf = convert_temperature(temp_dir, out_dir, subsample=args.subsample)
        total_frames += nf

    print(f"\n{'='*60}")
    print(f"DONE: {total_frames} total frames across {len(args.temps)} temperatures")
    print(f"Output: {args.output_dir}")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
