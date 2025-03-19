#! /usr/bin/env python3

import re
import pathlib
import argparse
import subprocess
import numpy as np
from cpymad.madx import Madx

# * Functions


def get_transformation(M: np.ndarray, unitary: bool = False) -> tuple:
    eig, U = np.linalg.eig(M)

    tunes = np.angle(eig[::2]) / 2 / np.pi

    if unitary:
        u, _, v = np.linalg.svd(U)
        U = u @ v

    return tunes, U


def main() -> None:
    # * Variables
    parser = argparse.ArgumentParser(
        prog="Python-PTC", description="Create PTC files from a MAD-X file."
    )
    parser.add_argument("madx_file", type=pathlib.Path, help="The MAD-X file to use.")
    parser.add_argument("--ptc-dim", type=int, help="Dimension of PTC map.", default=4)
    parser.add_argument("--ptc-order", type=int, help="Order of PTC map.", default=10)
    parser.add_argument(
        "--sequence_index", type=int, help="Index of sequence in MAD-X file.", default=0
    )
    args = parser.parse_args()

    source_file = args.madx_file
    lattice_name = source_file.name.split(".")[0]
    ptc_dim = args.ptc_dim
    ptc_order = args.ptc_order
    sequence_index = args.sequence_index

    # Check if arguments are valid
    if ptc_order > 9 and ptc_dim == 6:
        raise Exception(
            "PTC order cannot be greater than 9 for 6-D PTC maps. Please use a lower order."
        )

    if ptc_dim == 4 and ptc_order > 19:
        raise Exception(
            "PTC order cannot be greater than 19 for 4-D PTC maps. Please use a lower order."
        )

    # Folder where ptc data is saved
    output_folder = (pathlib.Path("./out") / lattice_name).absolute()

    filename = pathlib.Path("./fort.18").absolute()  # PTC output file
    inputs = ["", "", "", "", "", ""]  # List of strings to name PTC files

    ptc_output_filename = output_folder / "ptc_"  # Folder to store PTC files
    variable_strings = ("x", "px", "y", "py", "z", "pz")  # Names of variables
    terms = ("coeff", "xexp", "pxexp", "yexp", "pyexp", "zexp", "pzexp")  # Terms in PTC

    # Limit to PTC dimension
    variable_strings = variable_strings[:ptc_dim]
    terms = terms[: ptc_dim + 1]
    # inputs doesn't need to be shortened because it is zipped with variable_strings and
    # looped over so indexes that are larger than the length of variable_strings are
    # ignored.

    # Data Types
    float_type = np.float64
    int_type = np.int32
    complex_type = np.complex128

    # Lists for PTC Data
    ptc_filenames = ["" for _ in variable_strings]
    coeff = [[] for _ in ptc_filenames]
    exps = [[[] for _ in ptc_filenames] for _ in ptc_filenames]

    # Array for Linear Map
    linear_matrix = np.zeros((ptc_dim, ptc_dim), dtype=complex_type)

    # ! DO NOT CHANGE BELOW THIS LINE !
    regex = r"-?[\d.]+(?:[Ee][+-]?\d+)?"  # Regex for reading numbers from fort.18
    # Number of numbers on first line of fort.18
    if ptc_dim == 4:
        numbers_first_line_length = 7
    elif ptc_dim == 6:
        numbers_first_line_length = 9
        # TODO Use this for 6-D PTC maps
    else:
        raise Exception("PTC dimension should be 4 or 6.")
    # ! END OF DO NOT CHANGE !

    # * Main Code

    # Importing madx file

    print(f"Importing madx file: {source_file}")
    print(f"Lattice: {lattice_name}")

    with Madx() as madx:
        madx.option(echo=False)
        madx.call(file=source_file.as_posix(), chdir=False)

        sequence = list(madx.sequence.keys())[sequence_index]

        print(f"Sequence: {sequence}")

        # PTC Commands

        madx.use(sequence=sequence)
        madx.command.ptc_create_universe()
        madx.command.ptc_create_layout(model=1, method=2, exact=True, nst=40)
        madx.command.ptc_normal(icase=ptc_dim, no=ptc_order)
        madx.command.ptc_end()

    # Reading PTC File

    i = -1  # index for inputs
    for line in open(filename):
        li = line.strip()
        starts_with_etall = li.startswith("etall")

        if starts_with_etall:
            i += 1
        if not li.startswith("*") and not starts_with_etall:
            inputs[i] += li + "\n"

    # Saving PTC File
    output_folder.mkdir(parents=True, exist_ok=True)

    for i, (txt, variable) in enumerate(zip(inputs, variable_strings)):
        fn = ptc_output_filename.as_posix() + variable + ".txt"
        ptc_filenames[i] = fn
        with open(fn, "w") as f:
            f.write(txt)

    # Saving for numpy imports

    for i, fn in enumerate(ptc_filenames):
        first_line = True

        for line in open(fn):
            li = line.strip()

            if not li.startswith("I") and li:
                # Not a title line and not empty
                numbers = re.findall(regex, li)

                if first_line and len(numbers) == 1:
                    break

                if first_line:
                    order = int_type(numbers[2])
                    len_difference = numbers_first_line_length - len(numbers)
                    ei = []

                    if len_difference == 1:
                        # ! These statements are for 4-D PTC maps
                        # px or py got grouped with x/y coefficients

                        if len(numbers[-1]) == 3:
                            # py got grouped

                            ei.append(numbers[-3])
                            ei.append(numbers[-2])
                            ei.append(numbers[-1][0])
                            ei.append(numbers[-1][1:])

                        elif len(numbers[-3]) == 3:
                            # px got grouped

                            ei.append(numbers[-3][0])
                            ei.append(numbers[-3][1:])
                            ei.append(numbers[-2])
                            ei.append(numbers[-1])

                        else:
                            raise Exception(
                                f"Unknown error in reading fort.18; Numbers: {numbers}"
                            )

                    elif len_difference == 2:
                        # px and py got grouped

                        ei.append(numbers[-2][0])
                        ei.append(numbers[-2][1:])
                        ei.append(numbers[-1][0])
                        ei.append(numbers[-1][1:])

                    elif len_difference == 0:
                        # Line of nummbers was read normally
                        # Works for any dmension
                        ei = numbers[-ptc_dim:]

                    else:
                        raise Exception(
                            f"Unknown error in reading fort.18; Numbers: {numbers}"
                        )

                    first_line = False

                    ei = np.array(ei).astype(int_type)

                    if np.sum(ei) != order:
                        raise Exception(
                            f"Error Reading Exponents: Order is {order} but exponents are of order {np.sum(ei)}."
                        )

                    for j, eji in enumerate(ei):
                        exps[j][i].append(eji)

                else:
                    coeff[i].append(numbers[0])

                    first_line = True

    for vi, variable in enumerate(variable_strings):
        for term in terms:
            fn = output_folder / (term + "_" + variable + ".txt")

            if term == "coeff":
                temp = np.array(coeff[vi]).astype(float_type)
            elif term == "xexp":
                temp = np.array(exps[0][vi]).astype(int_type)
            elif term == "pxexp":
                temp = np.array(exps[1][vi]).astype(int_type)
            elif term == "yexp":
                temp = np.array(exps[2][vi]).astype(int_type)
            elif term == "pyexp":
                temp = np.array(exps[3][vi]).astype(int_type)
            elif term == "zexp":
                temp = np.array(exps[4][vi]).astype(int_type)
            elif term == "pzexp":
                temp = np.array(exps[5][vi]).astype(int_type)

            np.savetxt(fn, temp)

    np.savetxt(output_folder / "ptc_order.txt", np.array([ptc_order]).astype(int_type))

    # Normalizing Data

    for row in range(ptc_dim):
        cn = np.array(coeff[row]).astype(float_type)
        exponents = np.array(
            [np.array(exps[dim][row]).astype(int_type) for dim in range(ptc_dim)]
        )

        order = np.sum(exponents, axis=0)

        linear_terms = order == 1

        coefficients = [
            np.sum(exponents[dim][linear_terms] * cn[linear_terms])
            for dim in range(ptc_dim)
        ]

        for dim in range(ptc_dim):
            linear_matrix[row, dim] = coefficients[dim]

    linear_tunes, U = get_transformation(linear_matrix, unitary=False)

    # Saving Transformation Data
    np.savetxt(output_folder / "U.txt", U)
    np.savetxt(output_folder / "linear_tunes.txt", linear_tunes)

    # Remove temporary files
    fort_18 = filename.as_posix()
    internal_mag_pot = (filename.parent / "internal_mag_pot.txt").as_posix()

    command = ["rm", fort_18, internal_mag_pot]
    subprocess.run(command, check=True)

    command = ["rm"]
    for variable in variable_strings:
        command.append((output_folder / f"ptc_{variable}.txt").as_posix())

    subprocess.run(command, check=True)

    print(f'PTC files created successfully at "{output_folder}"')

    return None


if __name__ == "__main__":
    main()
