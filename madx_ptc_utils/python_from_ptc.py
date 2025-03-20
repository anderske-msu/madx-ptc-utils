from os.path import join
import typing
import pathlib
import numpy as np
import sympy as sp


def __load_exponent_data(
    folder: str, exponent_variable: str, target_variable: str, dtype: type
):
    """Loads the exponent data from the PTC map."""

    pth = join(folder, exponent_variable + "_" + target_variable + ".txt")

    return np.loadtxt(pth).astype(dtype)


def python_from_ptc(
    folder: typing.Union[str, pathlib.PosixPath],
    int_type: type = np.int32,
    float_type: type = np.float64,
) -> typing.Callable:
    """Reads in the PTC map from `create-ptc-files` and returns it as a python function.

    Inputs:
        folder: str
            Folder where ptc data is located.

        int_type: type, optional
            Integer type to use for the ptc data. Default is np.int32.

        float_type: type, optional
            Float type to use for the ptc data. Default is np.float64.

    Returns:
        new_variables: Callable
            A list of python functions that take in (x, px, y, py) and
            return (x', px', y', py').
    """

    ptc_dim = 2 * len(np.loadtxt(join(folder, "linear_tunes.txt")).astype(float_type))
    variable_strings = ("x", "px", "y", "py", "z", "pz")  # Names of variables
    exponent_names = ("xexp", "pxexp", "yexp", "pyexp", "zexp", "pzexp")  # Terms in PTC

    variable_strings = variable_strings[:ptc_dim]
    exponent_names = exponent_names[:ptc_dim]
    vars_ = [sp.symbols(vi, real=True) for vi in variable_strings]
    vmap = []  # one turn maps for each variable

    for vstr in variable_strings:  # Loops through each variable's saved ptc map
        # load ptc data from files
        coeff = __load_exponent_data(folder, "coeff", vstr, float_type)
        exponent_lists = [
            __load_exponent_data(folder, exp_name, vstr, int_type)
            for exp_name in exponent_names
        ]

        vmap.append(
            sum(
                [
                    cn * sp.prod([vi**ei for vi, ei in zip(vars_, exps)])
                    for cn, *exps in zip(coeff, *exponent_lists)
                ]
            )
        )

    fmap = sp.lambdify(vars_, vmap, "numpy")

    return fmap
