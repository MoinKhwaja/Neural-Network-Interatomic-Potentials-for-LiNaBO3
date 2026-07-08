#!/usr/bin/env python3
"""Extract POSCAR files from post-CO2 AIMD trajectories for DP-Gen.

Takes one equilibrated snapshot per temperature, reorders atoms by species
(B, O, C, Na, Li), and writes VASP POSCAR format.
"""

import os
import re
import numpy as np


def parse_single_frame(traj_file, frame_idx):
    """Read a specific frame from XYZ trajectory."""
    with open(traj_file) as f:
        for i in range(frame_idx + 1):
            line = f.readline()
            natoms = int(line.strip())
            comment = f.readline()
            names = []
            coords = []
            for _ in range(natoms):
                parts = f.readline().split()
                names.append(parts[0])
                coords.append([float(parts[1]), float(parts[2]), float(parts[3])])
    return names, np.array(coords)


def get_cell_length(output_file, frame_idx):
    """Get cell length for a specific frame from CP2K output."""
    cell_lengths = []
    with open(output_file) as f:
        for line in f:
            if 'Cell lengths [ang]' in line and 'MD|' in line and 'MD_INI|' not in line:
                numbers = re.findall(r'[\d.]+E[+-]\d+', line)
                if len(numbers) >= 3:
                    cell_lengths.append(float(numbers[0]))
    return cell_lengths[frame_idx]


def write_poscar(filename, names, coords, cell_length, type_order):
    """Write VASP POSCAR with atoms grouped by species."""
    # Group atoms by element
    groups = {elem: [] for elem in type_order}
    for i, name in enumerate(names):
        groups[name].append(coords[i])

    counts = [len(groups[elem]) for elem in type_order]
    header = ''.join(f'{elem}{n} ' for elem, n in zip(type_order, counts)).strip()

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w') as f:
        f.write(f'{header}\n')
        f.write('1.0\n')
        f.write(f'  {cell_length:.10e}  0.0000000000e+00  0.0000000000e+00\n')
        f.write(f'  0.0000000000e+00  {cell_length:.10e}  0.0000000000e+00\n')
        f.write(f'  0.0000000000e+00  0.0000000000e+00  {cell_length:.10e}\n')
        f.write(' '.join(type_order) + '\n')
        f.write(' '.join(str(c) for c in counts) + '\n')
        f.write('Cartesian\n')
        for elem in type_order:
            for c in groups[elem]:
                f.write(f'  {c[0]:16.10f}  {c[1]:16.10f}  {c[2]:16.10f}\n')


def main():
    base = '/gs/fs/tga-harada/Moin/deepmd'
    aimd_dir = os.path.join(base, 'post_co2/aimd')
    out_dir = os.path.join(base, 'post_co2/init_structures')
    type_order = ['B', 'O', 'C', 'Na', 'Li']

    # Temperature dirs (AIMD naming) -> POSCAR naming (uppercase C)
    temps = {
        '600C': '600C',
        '700c': '700C',
        '800c': '800C',
        '900c': '900C',
        '1000c': '1000C',
    }

    for aimd_name, poscar_name in temps.items():
        traj_file = os.path.join(aimd_dir, aimd_name, 'aimd-aimd.xyz-pos-1.xyz')
        output_file = os.path.join(aimd_dir, aimd_name, 'aimd.out')

        # Count frames
        with open(traj_file) as f:
            first_line = f.readline()
            natoms = int(first_line.strip())
        nframes = sum(1 for _ in open(traj_file)) // (natoms + 2)

        # Pick frame from middle of trajectory (well equilibrated)
        frame_idx = nframes // 2
        print(f'{aimd_name}: {nframes} frames, picking frame {frame_idx}')

        names, coords = parse_single_frame(traj_file, frame_idx)
        cell = get_cell_length(output_file, frame_idx)

        poscar_path = os.path.join(out_dir, poscar_name, 'POSCAR')
        write_poscar(poscar_path, names, coords, cell, type_order)

        # Verify counts
        from collections import Counter
        c = Counter(names)
        print(f'  atoms: {dict(c)}, cell: {cell:.4f} A')
        print(f'  written: {poscar_path}')


if __name__ == '__main__':
    main()
