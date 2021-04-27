#!/usr/bin/env python


import numpy as np
import pycuda.driver as cuda
from pycuda.compiler import SourceModule
from pycuda.tools import dtype_to_ctype, context_dependent_memoize

"""
This file contains functions to get prepared cuda functions for parray.py.
All functions here should not be used directly.
"""


def _get_type(dtype):
    return dtype.type if isinstance(dtype, np.dtype) else dtype


@context_dependent_memoize
def get_fill_function(dtype, pitch = True):
    type_dst = dtype_to_ctype(dtype)
    name = "fill"

    if pitch:
        func = SourceModule(
            fill_pitch_template % {
                    "name": name,
                    "type_dst": type_dst
            }, options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPi'+np.dtype(dtype).char)
        #    [np.int32, np.int32, np.intp, np.int32, _get_type(dtype)])
    else:
        func = SourceModule(
                fill_nonpitch_template % {
                    "name": name,
                    "type_dst": type_dst
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iP'+np.dtype(dtype).char)#[np.int32, np.intp, _get_type(dtype)])
    return func


@context_dependent_memoize
def get_astype_function(dtype_dest, dtype_src, pitch = True):
    type_dest = dtype_to_ctype(dtype_dest)
    type_src = dtype_to_ctype(dtype_src)
    name = "astype"
    operation = ""

    if pitch:
        func = SourceModule(
                pitch_template % {
                    "name": name,
                    "dest_type": type_dest,
                    "src_type": type_src,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi')
        #        [np.int32, np.int32, np.intp, np.int32, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_template % {
                    "name": name,
                    "dest_type": type_dest,
                    "src_type": type_src,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPi')#[np.intp, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_realimag_function(dtype, real = True, pitch = True):
    type_src = dtype_to_ctype(dtype)

    if dtype == np.complex64:
        type_dest = "float"
        if real:
            operation = "pycuda::real"
            name = "real"
        else:
            operation = "pycuda::imag"
            name = "imag"
    elif dtype == np.complex128:
        type_dest = "double"
        if real:
            operation = "pycuda::real"
            name = "real"
        else:
            operation = "pycuda::imag"
            name = "imag"
    else:
        raise TypeError("only support complex inputs are "
                        "numpy.complex64 or numpy.complex128")

    if pitch:
        func = SourceModule(
                pitch_template % {
                    "name": name,
                    "dest_type": type_dest,
                    "src_type": type_src,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi')
        #        [np.int32, np.int32, np.intp, np.int32, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_template % {
                    "name": name,
                    "dest_type": type_dest,
                    "src_type": type_src,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPi')#[np.intp, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_abs_function(dtype, pitch = True):
    type_src = dtype_to_ctype(dtype)
    if dtype == np.complex128:
        operation = "pycuda::abs"
        type_dest = "double"
    elif dtype == np.complex64:
        operation = "pycuda::abs"
        type_dest = "float"
    elif dtype == np.float64:
        operation = "fabs"
        type_dest = "double"
    elif dtype == np.float32:
        operation = "fabsf"
        type_dest = "float"
    else:
        operation = "abs"
        type_dest = dtype_to_ctype(dtype)
    name = "abs_function"

    if pitch:
        func = SourceModule(
                pitch_template % {
                    "name": name,
                    "dest_type": type_dest,
                    "src_type": type_src,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi')
        #        [np.int32, np.int32, np.intp, np.int32, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_template % {
                    "name": name,
                    "dest_type": type_dest,
                    "src_type": type_src,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPi')#[np.intp, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_angle_function(dtypein, dtypeout, pitch = True):
    type_src = dtype_to_ctype(dtypein)
    type_dest = dtype_to_ctype(dtypeout)
    name = "angle_function"
    if dtypeout == np.float32:
        fletter = "f"
    else:
        fletter = ""

    if pitch:
        func = SourceModule(
                pitch_angle_template % {
                    "name": name,
                    "dest_type": type_dest,
                    "src_type": type_src,
                    "fletter": fletter,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi')
        #        [np.int32, np.int32, np.intp, np.int32, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_angle_template % {
                    "name": name,
                    "dest_type": type_dest,
                    "src_type": type_src,
                    "fletter": fletter,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPi')#[np.intp, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_conj_function(dtype, pitch = True):
    type_src = dtype_to_ctype(dtype)
    if dtype == np.complex128:
        operation = "pycuda::conj"
    elif dtype == np.complex64:
        operation = "pycuda::conj"
    else:
        raise TypeError("Only complex arrays are allowed "
                        "to perform conjugation")
    name = "conj"

    if pitch:
        func = SourceModule(
                pitch_template % {
                    "name": name,
                    "dest_type": type_src,
                    "src_type": type_src,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi')
        #        [np.int32, np.int32, np.intp, np.int32, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_template % {
                    "name": name,
                    "dest_type": type_src,
                    "src_type": type_src,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPi')#[np.intp, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_resize_function(dtype):
    type_src = dtype_to_ctype(dtype)
    name = "resize"
    func = SourceModule(
            reshape_template % {
                "name": name,
                "dest_type": type_src,
                "src_type": type_src,
                "operation": "",
            },
            options=["--ptxas-options=-v"]).get_function(name)
    func.prepare('iiiiPiPi')#[np.int32, np.int32, np.int32, np.int32,
    #              np.intp, np.int32, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_transpose_function(dtype, conj = False):
    src_type = dtype_to_ctype(dtype)
    name = "trans"
    operation = ""

    if conj:
        if dtype == np.complex128:
            operation = "pycuda::conj"
        elif dtype == np.complex64:
            operation = "pycuda::conj"

    func = SourceModule(
            transpose_template % {
                "name": name,
                "type": src_type,
                "operation": operation
            },
            options=["--ptxas-options=-v"]).get_function(name)
    func.prepare('iiPiPi')#[np.int32, np.int32, np.intp,
    #              np.int32, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_addarray_function(left_dtype, right_dtype,
                          rslt_dtype, pitch = True):
    type_left = dtype_to_ctype(left_dtype)
    type_right = dtype_to_ctype(right_dtype)
    type_rslt = dtype_to_ctype(rslt_dtype)

    name = "addarray"
    operation = "+"

    if pitch:
        func = SourceModule(
                pitch_array_op_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPiPi')#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_array_op_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPPi')#[np.intp, np.intp, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_addscalar_function(src_type, dest_type, pitch = True):
    type_src = dtype_to_ctype(src_type)
    type_dest = dtype_to_ctype(dest_type)
    name = "addscalar"
    operation = "+"

    if pitch:
        func = SourceModule(
                pitch_left_scalar_op_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi'+np.dtype(dest_type).char)#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, _get_type(dest_type)])
    else:
        func = SourceModule(
                non_pitch_left_scalar_op_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PP'+np.dtype(dest_type).char+'i')#[np.intp, np.intp, _get_type(dest_type), np.int32])
    return func

@context_dependent_memoize
def get_powarray_function(left_dtype, right_dtype,
                          rslt_dtype, pitch = True):
    type_left = dtype_to_ctype(left_dtype)
    type_right = dtype_to_ctype(right_dtype)
    type_rslt = dtype_to_ctype(rslt_dtype)

    name = "powarray"
    operation = "pow"

    if pitch:
        func = SourceModule(
                pitch_array_func_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                    "fletter": 'f' if left_dtype == np.float32 else '',
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPiPi')#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_array_func_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                    "fletter": 'f' if left_dtype == np.float32 else ''
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPPi')#[np.intp, np.intp, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_powscalar_function(src_type, dest_type, pitch = True):
    type_src = dtype_to_ctype(src_type)
    type_dest = dtype_to_ctype(dest_type)
    name = "powscalar"
    operation = "pow"

    if pitch:
        func = SourceModule(
                pitch_left_scalar_func_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                    "fletter": 'f' if src_type == np.float32 else '',
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi'+np.dtype(dest_type).char)#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, _get_type(dest_type)])
    else:
        func = SourceModule(
                non_pitch_left_scalar_func_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                    "fletter": 'f' if src_type == np.float32 else '',
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PP'+np.dtype(dest_type).char+'i')#[np.intp, np.intp, _get_type(dest_type), np.int32])
    return func


@context_dependent_memoize
def get_subarray_function(left_dtype, right_dtype, rslt_dtype, pitch = True):
    type_left = dtype_to_ctype(left_dtype)
    type_right = dtype_to_ctype(right_dtype)
    type_rslt = dtype_to_ctype(rslt_dtype)
    name = "subdarray"
    operation = "-"

    if pitch:
        func = SourceModule(
                pitch_array_op_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPiPi')#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_array_op_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPPi')#[np.intp, np.intp, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_subscalar_function(src_type, dest_type, pitch = True):
    type_src = dtype_to_ctype(src_type)
    type_dest = dtype_to_ctype(dest_type)

    name = "subscalar"
    operation = "-"

    if pitch:
        func = SourceModule(
                pitch_left_scalar_op_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi'+np.dtype(dest_type).char)#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, _get_type(dest_type)])
    else:
        func = SourceModule(
                non_pitch_left_scalar_op_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PP'+np.dtype(dest_type).char+'i')#[np.intp, np.intp, _get_type(dest_type), np.int32])
    return func


@context_dependent_memoize
def get_scalarsub_function(src_type, dest_type, pitch = True):
    type_src = dtype_to_ctype(src_type)
    type_dest = dtype_to_ctype(dest_type)

    name = "scalarsub"
    operation = "-"

    if pitch:
        func = SourceModule(
                pitch_right_scalar_op_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi'+np.dtype(dest_type).char)#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, _get_type(dest_type)])
    else:
        func = SourceModule(
                non_pitch_right_scalar_op_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PP'+np.dtype(dest_type).char+'i')#[np.intp, np.intp, _get_type(dest_type), np.int32])
    return func


@context_dependent_memoize
def get_mularray_function(left_dtype, right_dtype, rslt_dtype, pitch = True):
    type_left = dtype_to_ctype(left_dtype)
    type_right = dtype_to_ctype(right_dtype)
    type_rslt = dtype_to_ctype(rslt_dtype)

    name = "mularray"
    operation = "*"

    if pitch:
        func = SourceModule(
                pitch_array_op_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPiPi')#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_array_op_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPPi')#[np.intp, np.intp, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_mulscalar_function(src_type, dest_type, pitch = True):
    type_src = dtype_to_ctype(src_type)
    type_dest = dtype_to_ctype(dest_type)

    name = "mulscalar"
    operation = "*"

    if pitch:
        func = SourceModule(
                pitch_left_scalar_op_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi'+np.dtype(dest_type).char)#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, _get_type(dest_type)])
    else:
        func = SourceModule(
                non_pitch_left_scalar_op_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PP'+np.dtype(dest_type).char+'i')#[np.intp, np.intp, _get_type(dest_type), np.int32])
    return func


@context_dependent_memoize
def get_divarray_function(left_dtype, right_dtype, rslt_dtype, pitch = True):
    type_left = dtype_to_ctype(left_dtype)
    type_right = dtype_to_ctype(right_dtype)
    type_rslt = dtype_to_ctype(rslt_dtype)

    name = "divarray"
    operation = "/"

    if pitch:
        func = SourceModule(
                pitch_array_op_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPiPi')#[np.int32, np.int32, np.intp, np.int32,
        #             np.intp, np.int32, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_array_op_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPPi')#[np.intp, np.intp, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_divscalar_function(src_type, dest_type, pitch = True):
    type_src = dtype_to_ctype(src_type)
    type_dest = dtype_to_ctype(dest_type)

    name = "divscalar"
    operation = "/"

    if pitch:
        func = SourceModule(
                pitch_left_scalar_op_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi'+np.dtype(dest_type).char)#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, _get_type(dest_type)])
    else:
        func = SourceModule(
                non_pitch_left_scalar_op_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PP'+np.dtype(dest_type).char+'i')#[np.intp, np.intp, _get_type(dest_type), np.int32])
    return func


@context_dependent_memoize
def get_scalardiv_function(src_type, dest_type, pitch = True):
    type_src = dtype_to_ctype(src_type)
    type_dest = dtype_to_ctype(dest_type)

    name = "scalardiv"
    operation = "/"

    if pitch:
        func = SourceModule(
                pitch_right_scalar_op_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi'+np.dtype(dest_type).char)#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, _get_type(dest_type)])
    else:
        func = SourceModule(
                non_pitch_right_scalar_op_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PP'+np.dtype(dest_type).char+'i')#[np.intp, np.intp, _get_type(dest_type), np.int32])
    return func


@context_dependent_memoize
def get_complex_function(real_type, imag_type, result_type, pitch = True):
    type_real = dtype_to_ctype(real_type)
    type_imag = dtype_to_ctype(imag_type)
    type_result = dtype_to_ctype(result_type)

    name = "makecomplex"

    if pitch:
        func = SourceModule(
                pitch_complex_template % {
                    "name": name,
                    "real_type": type_real,
                    "imag_type": type_imag,
                    "result_type": type_result
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPPi')#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_complex_template % {
                    "name": name,
                    "real_type": type_real,
                    "imag_type": type_imag,
                    "result_type": type_result
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPPi')#[np.intp, np.intp, np.intp, np.int32])
    return func

@context_dependent_memoize
def get_complex_from_amp_function(in_type, result_type, pitch = True):
    type_in = dtype_to_ctype(in_type)
    type_result = dtype_to_ctype(result_type)

    name = "makecomplex_amp_phase"

    if pitch:
        func = SourceModule(
                pitch_complex_amp_template % {
                    "name": name,
                    "in_type": type_in,
                    "result_type": type_result,
                    "fletter": 'f' if in_type == np.float32 else ''
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPPi')#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_complex_amp_template % {
                    "name": name,
                    "in_type": type_in,
                    "result_type": type_result,
                    "fletter": 'f' if in_type == np.float32 else ''
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPPi')#[np.intp, np.intp, np.intp, np.int32])
    return func

@context_dependent_memoize
def get_bsxfun_function(array_type, vector_type, result_type,
                        operator, direction, order, pitch = True):
    type_array = dtype_to_ctype(array_type)
    type_vector = dtype_to_ctype(vector_type)
    type_result = dtype_to_ctype(result_type)

    name = "bsxfun"

    possibles = globals().copy()
    possibles.update(locals())
#    method = possibles.get(method_name)
    if pitch:
        func = SourceModule(
                possibles.get("pitch_bsxfun_"+order+"_"+direction+"_template") % {
                    "name": name,
                    "array_type": type_array,
                    "vector_type": type_vector,
                    "result_type": type_result,
                    "operator": operator
               },
               options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PiPPiii')
    else:
        raise NotImplementedError

    return func

@context_dependent_memoize
def get_maxarray_function(left_dtype, right_dtype,
                          rslt_dtype, pitch = True):
    type_left = dtype_to_ctype(left_dtype)
    type_right = dtype_to_ctype(right_dtype)
    type_rslt = dtype_to_ctype(rslt_dtype)

    name = "maxarray"
    if left_dtype == np.int32 or right_dtype == np.int32:
        operation = "max"
    else:
        operation = "fmax"

    if pitch:
        func = SourceModule(
                pitch_array_func_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                    "fletter": 'f' if left_dtype == np.float32 else '',
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPiPi')#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_array_func_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                    "fletter": 'f' if left_dtype == np.float32 else ''
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPPi')#[np.intp, np.intp, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_maxscalar_function(src_type, dest_type, pitch = True):
    type_src = dtype_to_ctype(src_type)
    type_dest = dtype_to_ctype(dest_type)
    name = "maxscalar"
    if src_type == np.int32:
        operation = "max"
    else:
        operation = "fmax"

    if pitch:
        func = SourceModule(
                pitch_left_scalar_func_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                    "fletter": 'f' if src_type == np.float32 else '',
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi'+np.dtype(dest_type).char)#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, _get_type(dest_type)])
    else:
        func = SourceModule(
                non_pitch_left_scalar_func_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                    "fletter": 'f' if src_type == np.float32 else '',
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PP'+np.dtype(dest_type).char+'i')#[np.intp, np.intp, _get_type(dest_type), np.int32])
    return func

@context_dependent_memoize
def get_minarray_function(left_dtype, right_dtype,
                          rslt_dtype, pitch = True):
    type_left = dtype_to_ctype(left_dtype)
    type_right = dtype_to_ctype(right_dtype)
    type_rslt = dtype_to_ctype(rslt_dtype)

    name = "minarray"
    if left_dtype == np.int32 or right_dtype == np.int32:
        operation = "min"
    else:
        operation = "fmin"

    if pitch:
        func = SourceModule(
                pitch_array_func_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                    "fletter": 'f' if left_dtype == np.float32 else '',
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPiPi')#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, np.intp, np.int32])
    else:
        func = SourceModule(
                non_pitch_array_func_template % {
                    "name": name,
                    "dest_type": type_rslt,
                    "left_type": type_left,
                    "right_type": type_right,
                    "operation": operation,
                    "fletter": 'f' if left_dtype == np.float32 else ''
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPPi')#[np.intp, np.intp, np.intp, np.int32])
    return func


@context_dependent_memoize
def get_minscalar_function(src_type, dest_type, pitch = True):
    type_src = dtype_to_ctype(src_type)
    type_dest = dtype_to_ctype(dest_type)
    name = "minscalar"
    if src_type == np.int32:
        operation = "min"
    else:
        operation = "fmin"

    if pitch:
        func = SourceModule(
                pitch_left_scalar_func_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                    "fletter": 'f' if src_type == np.float32 else '',
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi'+np.dtype(dest_type).char)#[np.int32, np.int32, np.intp, np.int32,
        #              np.intp, np.int32, _get_type(dest_type)])
    else:
        func = SourceModule(
                non_pitch_left_scalar_func_template % {
                    "name": name,
                    "src_type": type_src,
                    "dest_type": type_dest,
                    "operation": operation,
                    "fletter": 'f' if src_type == np.float32 else '',
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PP'+np.dtype(dest_type).char+'i')#[np.intp, np.intp, _get_type(dest_type), np.int32])
    return func


@context_dependent_memoize
def get_array_operator_function(src_type, dest_type, operator_name, pitch = True):
    type_src = dtype_to_ctype(src_type)
    type_dest = dtype_to_ctype(dest_type)
    name = "array_"+operator_name
    if src_type in [np.complex128, np.complex64]:
        operation = "pycuda::"+operator_name
    else:
        operation = operaotr_name

    if pitch:
        func = SourceModule(
                pitch_template % {
                    "name": name,
                    "dest_type": type_dest,
                    "src_type": type_src,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('iiPiPi')
    else:
        func = SourceModule(
                non_pitch_template % {
                    "name": name,
                    "dest_type": type_dest,
                    "src_type": type_src,
                    "operation": operation,
                },
                options=["--ptxas-options=-v"]).get_function(name)
        func.prepare('PPi')
    return func


"""templates"""

pycuda_complex_header = """
#include <pycuda-complex.hpp>
extern "C++" {
namespace pycuda{

template <class _Tp1, class _Tp2>
__device__ inline complex<double> operator+(
    const complex<_Tp1>& __z1, const complex<_Tp2>& __z2)
{return complex<double>(__z1._M_re + __z2._M_re, __z1._M_im + __z2._M_im);}

template <class _Tp1, class _Tp2>
__device__ inline complex<double> operator-(
    const complex<_Tp1>& __z1, const complex<_Tp2>& __z2)
{return complex<double>(__z1._M_re - __z2._M_re, __z1._M_im - __z2._M_im);}

template <class _Tp1, class _Tp2>
__device__ inline complex<double> operator*(
    const complex<_Tp1>& __z1, const complex<_Tp2>& __z2)
{return complex<double>(\
    __z1._M_re * __z2._M_re - __z1._M_im * __z2._M_im,\
    __z1._M_re * __z2._M_im + __z1._M_im * __z2._M_re);}

template <class _Tp1, class _Tp2>
__device__ inline complex<double> operator/(
    const complex<_Tp1>& __z1, const complex<_Tp2>& __z2)
{
    double c = __z2._M_re;
    double d = __z2._M_im;
    double nom = __z2._M_re*__z2._M_re+__z2._M_im*__z2._M_im;
    return complex<double>((__z1._M_re*__z2._M_re+__z1._M_im*__z2._M_im)/nom,\
                           (__z1._M_im*__z2._M_re-__z1._M_re*__z2._M_im)/nom);
}

template <class _Tp1, class _Tp2>
__device__ inline complex<double> operator+(
    const complex<_Tp1>& __z, const _Tp2& __x)
{return complex<double>(__z._M_re + __x, __z._M_im);}

template <class _Tp1, class _Tp2>
__device__ inline complex<double> operator+(
    const _Tp1& __x, const complex<_Tp2>& __z)
{return complex<double>(__z._M_re + __x, __z._M_im);}

template <class _Tp1, class _Tp2>
__device__ inline complex<double> operator-(
    const complex<_Tp1>& __z, const _Tp2& __x)
{return complex<double>(__z._M_re - __x, __z._M_im);}

template <class _Tp1, class _Tp2>
__device__ inline complex<double> operator-(
    const _Tp1& __x, const complex<_Tp2>& __z)
{return complex<double>(__x - __z._M_re, -__z._M_im);}

template <class _Tp1, class _Tp2>
__device__ inline complex<double> operator*(
    const complex<_Tp1>& __z, const _Tp2& __x)
{return complex<double>(__z._M_re * __x, __z._M_im * __x);}

template <class _Tp1, class _Tp2>
__device__ inline complex<double> operator*(
    const _Tp1& __x, const complex<_Tp2>& __z)
{return complex<double>(__z._M_re * __x, __z._M_im * __x);}

template <class _Tp1, class _Tp2>
__device__ inline complex<double> operator/(
    const complex<_Tp1>& __z, const _Tp2& __x)
{return complex<double>(__z._M_re / __x, __z._M_im / __x);}

template <class _Tp1, class _Tp2>
__device__ inline complex<double> operator/(
    const _Tp1& __x, const complex<_Tp2>& __z)
{
    double nom = __z._M_re*__z._M_re+__z._M_im*__z._M_im;
    return complex<double>(__x*__z._M_re/nom, -__x*__z._M_im/nom);
}


}
}

"""



pitch_complex_template = """
#include <pycuda-complex.hpp>

__global__ void
%(name)s(const int M, const int N, %(result_type)s *odata,
         const int ldo, const %(real_type)s *real,
         const %(imag_type)s *imag, const int ldi)
{
    //M is the number of rows, N is the number of columns
    const int tid = threadIdx.x;
    const int sid = threadIdx.y + blockDim.y * blockIdx.x;
    const int total = gridDim.x * blockDim.y;

    int m, n, idx;
    %(result_type)s tmp;
    int segment_per_row = ((N - 1) >> 5) + 1;
    int total_segments = M * segment_per_row;

    for(int i = sid; i < total_segments; i+=total)
    {
        m = i / segment_per_row;
        n = i %% segment_per_row;
        idx = (n<<5) + tid;
        if(idx < N)
        {
            tmp = %(result_type)s(real[m*ldi+idx], imag[m*ldi+idx]);
            odata[m * ldo + idx] = (tmp);
        }
    }
}

"""


non_pitch_complex_template = """
#include <pycuda-complex.hpp>

__global__ void
%(name)s(%(result_type)s *odata, const %(real_type)s *real,
         const %(imag_type)s *imag, const int N)
{
    const int totalthreads = blockDim.x * gridDim.x;
    const int tid = blockIdx.x * blockDim.x + threadIdx.x;

    %(result_type)s tmp;

    for (int i = tid; i < N; i += totalthreads)
    {
        tmp = %(result_type)s(real[i], imag[i]);
        odata[i] = (tmp);
    }
}

"""

pitch_complex_amp_template = """
#include <pycuda-complex.hpp>

__global__ void
%(name)s(const int M, const int N, %(result_type)s *odata,
         const int ldo, const %(in_type)s *amp,
         const %(in_type)s *phase, const int ldi)
{
    //M is the number of rows, N is the number of columns
    const int tid = threadIdx.x;
    const int sid = threadIdx.y + blockDim.y * blockIdx.x;
    const int total = gridDim.x * blockDim.y;

    int m, n, idx;
    %(result_type)s tmp;
    int segment_per_row = ((N - 1) >> 5) + 1;
    int total_segments = M * segment_per_row;
    %(in_type)s c,s, a;

    for(int i = sid; i < total_segments; i+=total)
    {
        m = i / segment_per_row;
        n = i %% segment_per_row;
        idx = (n<<5) + tid;
        if(idx < N)
        {
            sincos%(fletter)s(phase[m*ldi+idx], &s, &c);
            a = amp[m*ldi+idx];
            tmp = %(result_type)s(a*c, a*s);
            odata[m * ldo + idx] = (tmp);
        }
    }
}

"""


non_pitch_complex_amp_template = """
#include <pycuda-complex.hpp>

__global__ void
%(name)s(%(result_type)s *odata, const %(in_type)s *amp,
         const %(in_type)s *phase, const int N)
{
    const int totalthreads = blockDim.x * gridDim.x;
    const int tid = blockIdx.x * blockDim.x + threadIdx.x;

    %(result_type)s tmp;
    %(in_type)s c,s, a;

    for (int i = tid; i < N; i += totalthreads)
    {
        sincos%(fletter)s(phase[i], &s, &c);
        a = amp[i];
        tmp = %(result_type)s(a*c, a*s);
        odata[i] = (tmp);
    }
}

"""

transpose_template = """
#include <pycuda-complex.hpp>
#define TILE_DIM 32
#define BLOCK_ROWS 8

#define tile(r, c) (tile[(r)*(TILE_DIM+1) + (c)])

__global__ void
%(name)s(const int M, const int N, %(type)s *odata,
         const int ldo, const %(type)s *idata, const int ldi)
{
    extern __shared__ %(type)s tile[];

    int xIndex, yIndex, index_in, index_out;
    int MM = ((M-1) >> 5) + 1;
    int NN = ((N-1) >> 5) + 1;

    for(int i = blockIdx.x; i < MM * NN; i += gridDim.x)
    {
        xIndex = (i %% NN) * TILE_DIM + threadIdx.x;
        yIndex = (i / NN) * TILE_DIM + threadIdx.y;
        index_in = xIndex + ldi * yIndex;
        if(xIndex < N)
        {
            #pragma unroll
            for(int j = 0; j < TILE_DIM; j+=BLOCK_ROWS)
            {
                if(yIndex + j < M)
                {
                    tile(threadIdx.y+j, threadIdx.x) = \
                        (idata[index_in+j*ldi]);
                }
            }
        }
        __syncthreads();

        xIndex = (i / NN) * TILE_DIM + threadIdx.x;
        yIndex = (i %% NN) * TILE_DIM + threadIdx.y;
        index_out = xIndex + ldo * yIndex;

        if(xIndex < M)
        {
            #pragma unroll
            for(int j = 0; j < TILE_DIM; j+=BLOCK_ROWS)
            {
                if(yIndex + j < N)
                {
                    odata[index_out+j*ldo] = \
                        %(operation)s(tile(threadIdx.x, threadIdx.y+j));
                }
            }
        }
        __syncthreads();
    }
}

"""

pitch_angle_template = """
#include <pycuda-complex.hpp>

__global__ void
%(name)s(const int M, const int N, %(dest_type)s *dest,
         const int ld_dest, const %(src_type)s *src, const int ld_src)
{
    //M is the number of rows, N is the number of columns
    const int tid = threadIdx.x;
    const int sid = threadIdx.y + blockDim.y * blockIdx.x;
    const int total = gridDim.x * blockDim.y;

    int m, n, idx;
    %(src_type)s tmp;
    int segment_per_row = ((N - 1) >> 5) + 1;
    int total_segments = M * segment_per_row;
    for(int i = sid; i < total_segments; i+=total)
    {
        m = i / segment_per_row;
        n = i %% segment_per_row;
        idx = (n<<5) + tid;
        if(idx < N)
        {
            tmp = src[m * ld_src + idx];
            dest[m * ld_dest + idx] = atan2%(fletter)s(pycuda::imag(tmp), pycuda::real(tmp));
        }
    }
}

"""
"""
launching MULTIPROCESSOR_COUNT*6 blocks of (32,8,1),
M: number of rows, N: number of columns,
ld: leading dimension entries(aasumed to be row major)
"""

non_pitch_angle_template = """
#include <pycuda-complex.hpp>

__global__ void
%(name)s (%(dest_type)s *dest, const %(src_type)s *src, const int N)
{
    const int totalthreads = blockDim.x * gridDim.x;
    const int tid = blockIdx.x * blockDim.x + threadIdx.x;
    %(src_type)s tmp;
    for (int i = tid; i < N; i += totalthreads)
    {
        tmp = src[i];
        dest[i] =  atan2%(fletter)s(pycuda::imag(tmp), pycuda::real(tmp));
    }
}

"""
""" launching MULTIPROCESSOR_COUNT*6 blocks of (256,1,1), N = totalsize"""


pitch_template = """
#include <pycuda-complex.hpp>

__global__ void
%(name)s(const int M, const int N, %(dest_type)s *dest,
         const int ld_dest, const %(src_type)s *src, const int ld_src)
{
    //M is the number of rows, N is the number of columns
    const int tid = threadIdx.x;
    const int sid = threadIdx.y + blockDim.y * blockIdx.x;
    const int total = gridDim.x * blockDim.y;

    int m, n, idx;
    %(src_type)s tmp;
    int segment_per_row = ((N - 1) >> 5) + 1;
    int total_segments = M * segment_per_row;
    for(int i = sid; i < total_segments; i+=total)
    {
        m = i / segment_per_row;
        n = i %% segment_per_row;
        idx = (n<<5) + tid;
        if(idx < N)
        {
            tmp = src[m * ld_src + idx];
            dest[m * ld_dest + idx] = %(operation)s (tmp);
        }
    }
}

"""
"""
launching MULTIPROCESSOR_COUNT*6 blocks of (32,8,1),
M: number of rows, N: number of columns,
ld: leading dimension entries(aasumed to be row major)
"""


non_pitch_template = """
#include <pycuda-complex.hpp>

__global__ void
%(name)s (%(dest_type)s *dest, const %(src_type)s *src, const int N)
{
    const int totalthreads = blockDim.x * gridDim.x;
    const int tid = blockIdx.x * blockDim.x + threadIdx.x;
    %(src_type)s tmp;
    for (int i = tid; i < N; i += totalthreads)
    {
        tmp = src[i];
        dest[i] =  %(operation)s (tmp);
    }
}

"""
""" launching MULTIPROCESSOR_COUNT*6 blocks of (256,1,1), N = totalsize"""


reshape_template = """
#include <pycuda-complex.hpp>
#include <cuComplex.h>
__global__ void
%(name)s(const int Msrc, const int Nsrc, const int Mdest,
         const int Ndest, %(dest_type)s *dest, const int ld_dest,
         const %(src_type)s *src, const int ld_src)
{
    const int totalthreads = blockDim.x * gridDim.x;
    const int tid = blockIdx.x * blockDim.x + threadIdx.x;
    %(src_type)s tmp;
    for (int i = tid; i < Nsrc * Msrc; i += totalthreads)
    {
        tmp = src[i / Nsrc * ld_src + i %% Nsrc];
        dest[i / Ndest * ld_dest + i %% Ndest] = %(operation)s (tmp);
    }
}

"""
"""
launching MULTIPROCESSOR_COUNT*6 blocks of (256,1,1),
M: number of rows, N: number of columns,
ld: leading dimension entries(aasumed to be row major)
"""

irregular_pitch_template = """
#include <pycuda-complex.hpp>

__global__ void
%(name)s(const int M, const int N, %(dest_type)s *dest,
         const int ld_dest, const %(src_type)s *src, const int ld_src)
{
    const int totalthreads = blockDim.x * gridDim.x;
    const int tid = blockIdx.x * blockDim.x + threadIdx.x;

    %(src_type)s tmp;
    int m,n;
    for (int i = tid; i < N * M; i += totalthreads)
    {
        m = i / N;
        n = i %% N;
        tmp = src[m * ld_src + n];
        dest[m * ld_dest + n] =  %(operation)s (tmp);
    }
}

"""
"""
launching MULTIPROCESSOR_COUNT*6 blocks of (256,1,1),
M: number of rows, N: number of columns,
ld: leading dimension entries(aasumed to be row major)
"""


pitch_array_op_template = pycuda_complex_header + """
__global__ void
%(name)s(const int M, const int N, %(dest_type)s *dest,
         const int ld_dest, const %(left_type)s *left,
         const int ld_left, const %(right_type)s *right,
         const int ld_right)
{
    //M is the number of rows, N is the number of columns
    const int tid = threadIdx.x;
    const int sid = threadIdx.y + blockDim.y * blockIdx.x;
    const int total = gridDim.x * blockDim.y;

    int m, n, idx;
    %(left_type)s tmp_left;
    %(right_type)s tmp_right;
    int segment_per_row = ((N - 1) >> 5) + 1;
    int total_segments = M * segment_per_row;

    for(int i = sid; i < total_segments; i+=total)
    {
        m = i / segment_per_row;
        n = i %% segment_per_row;
        idx = (n<<5) + tid;
        if(idx < N)
        {
            tmp_left = left[m * ld_left + idx];
            tmp_right = right[m * ld_right + idx];
            dest[m * ld_dest + idx] = (tmp_left) %(operation)s (tmp_right);
        }
    }
}

"""

non_pitch_array_op_template = pycuda_complex_header + """
__global__ void
%(name)s(%(dest_type)s *dest, const %(left_type)s *left,
         const %(right_type)s *right, const int N)
{
    const int totalthreads = blockDim.x * gridDim.x;
    const int tid = blockIdx.x * blockDim.x + threadIdx.x;

    %(left_type)s tmp_left;
    %(right_type)s tmp_right;

    for (int i = tid; i < N; i += totalthreads)
    {
        tmp_left = left[i];
        tmp_right = right[i];
        dest[i] =  (tmp_left) %(operation)s (tmp_right);
    }
}

"""

pitch_left_scalar_op_template = pycuda_complex_header + """
__global__ void
%(name)s(const int M, const int N, %(dest_type)s *dest,
         const int ld_dest, const %(src_type)s *left,
         const int ld_left, const %(dest_type)s right)
{
    //M is the number of rows, N is the number of columns
    const int tid = threadIdx.x;
    const int sid = threadIdx.y + blockDim.y * blockIdx.x;
    const int total = gridDim.x * blockDim.y;
    int m, n, idx;
    %(src_type)s tmp_left;
    int segment_per_row = ((N - 1) >> 5) + 1;
    int total_segments = M * segment_per_row;

    for(int i = sid; i < total_segments; i+=total)
    {
        m = i / segment_per_row;
        n = i %% segment_per_row;
        idx = (n<<5) + tid;
        if(idx < N)
        {
            tmp_left = left[m * ld_left + idx];
            dest[m * ld_dest + idx] = (tmp_left) %(operation)s (right);
        }
    }
}

"""

non_pitch_left_scalar_op_template = pycuda_complex_header + """
__global__ void
%(name)s(%(dest_type)s *dest, const %(src_type)s *left,
         const %(dest_type)s right, const int N)
{
    const int totalthreads = blockDim.x * gridDim.x;
    const int tid = blockIdx.x * blockDim.x + threadIdx.x;

    %(src_type)s tmp_left;
    for (int i = tid; i < N; i += totalthreads)
    {
        tmp_left = left[i];
        dest[i] =  (tmp_left) %(operation)s (right);
    }
}

"""

pitch_right_scalar_op_template = pycuda_complex_header + """
__global__ void
%(name)s(const int M, const int N, %(dest_type)s *dest,
         const int ld_dest, const %(src_type)s *left,
         const int ld_left, const %(dest_type)s right)
{
    //M is the number of rows, N is the number of columns
    const int tid = threadIdx.x;
    const int sid = threadIdx.y + blockDim.y * blockIdx.x;
    const int total = gridDim.x * blockDim.y;

    int m, n, idx;
    %(src_type)s tmp_left;
    int segment_per_row = ((N - 1) >> 5) + 1;
    int total_segments = M * segment_per_row;

    for(int i = sid; i < total_segments; i+=total)
    {
        m = i / segment_per_row;
        n = i %% segment_per_row;
        idx = (n<<5) + tid;
        if(idx < N)
        {
            tmp_left = left[m * ld_left + idx];
            dest[m * ld_dest + idx] = (right) %(operation)s (tmp_left);
        }
    }
}

"""

non_pitch_right_scalar_op_template = pycuda_complex_header + """
__global__ void
%(name)s(%(dest_type)s *dest, const %(dest_type)s *left,
         const %(src_type)s right, const int N)
{
    const int totalthreads = blockDim.x * gridDim.x;
    const int tid = blockIdx.x * blockDim.x + threadIdx.x;

    %(src_type)s tmp_left;
    for (int i = tid; i < N; i += totalthreads)
    {
        tmp_left = left[i];
        dest[i] =  (right) %(operation)s (tmp_left);
    }
}

"""

fill_pitch_template = """
#include <pycuda-complex.hpp>

__global__ void
%(name)s(const int M, const int N, %(type_dst)s *dst,
         const int ld_dst, %(type_dst)s value)
{
    //M is the number of rows, N is the number of columns
    const int tid = threadIdx.x;
    const int sid = threadIdx.y + blockDim.y * blockIdx.x;
    const int total = gridDim.x * blockDim.y;

    int m, n;
    int segment_per_row = ((N - 1) >> 5) + 1;
    int total_segments = M * segment_per_row;
    for(int i = sid; i < total_segments; i+=total)
    {
        m = i / segment_per_row;
        n = i %% segment_per_row;
        dst[m * ld_dst + (n<<5) + tid] = value;
     }
}

"""

"""
launching MULTIPROCESSOR_COUNT*6 blocks of (32,8,1),
M: number of rows, N: number of columns,
ld: leading dimension entries(aasumed to be row major)
"""

fill_nonpitch_template = """
#include <pycuda-complex.hpp>

__global__ void
%(name)s(const int M,  %(type_dst)s *dst, %(type_dst)s value)
{
    //M is the number of rows, N is the number of columns
    const int tid = threadIdx.x + blockDim.x * blockIdx.x;
    const int total = gridDim.x * blockDim.x;

    for(int i = tid; i < M; i+=total)
    {
        dst[i] = value;
    }
}

"""


pitch_array_func_template = pycuda_complex_header + """
__global__ void
%(name)s(const int M, const int N, %(dest_type)s *dest,
         const int ld_dest, const %(left_type)s *left,
         const int ld_left, const %(right_type)s *right,
         const int ld_right)
{
    //M is the number of rows, N is the number of columns
    const int tid = threadIdx.x;
    const int sid = threadIdx.y + blockDim.y * blockIdx.x;
    const int total = gridDim.x * blockDim.y;

    int m, n, idx;
    %(left_type)s tmp_left;
    %(right_type)s tmp_right;
    int segment_per_row = ((N - 1) >> 5) + 1;
    int total_segments = M * segment_per_row;

    for(int i = sid; i < total_segments; i+=total)
    {
        m = i / segment_per_row;
        n = i %% segment_per_row;
        idx = (n<<5) + tid;
        if(idx < N)
        {
            tmp_left = left[m * ld_left + idx];
            tmp_right = right[m * ld_right + idx];
            dest[m * ld_dest + idx] = %(operation)s%(fletter)s((tmp_left) , (tmp_right));
        }
    }
}

"""

non_pitch_array_func_template = pycuda_complex_header + """
__global__ void
%(name)s(%(dest_type)s *dest, const %(left_type)s *left,
         const %(right_type)s *right, const int N)
{
    const int totalthreads = blockDim.x * gridDim.x;
    const int tid = blockIdx.x * blockDim.x + threadIdx.x;

    %(left_type)s tmp_left;
    %(right_type)s tmp_right;

    for (int i = tid; i < N; i += totalthreads)
    {
        tmp_left = left[i];
        tmp_right = right[i];
        dest[i] = %(operation)s%(fletter)s((tmp_left) , (tmp_right));
    }
}

"""


pitch_left_scalar_func_template = pycuda_complex_header + """
__global__ void
%(name)s(const int M, const int N, %(dest_type)s *dest,
         const int ld_dest, const %(src_type)s *left,
         const int ld_left, const %(dest_type)s right)
{
    //M is the number of rows, N is the number of columns
    const int tid = threadIdx.x;
    const int sid = threadIdx.y + blockDim.y * blockIdx.x;
    const int total = gridDim.x * blockDim.y;
    int m, n, idx;
    %(src_type)s tmp_left;
    int segment_per_row = ((N - 1) >> 5) + 1;
    int total_segments = M * segment_per_row;

    for(int i = sid; i < total_segments; i+=total)
    {
        m = i / segment_per_row;
        n = i %% segment_per_row;
        idx = (n<<5) + tid;
        if(idx < N)
        {
            tmp_left = left[m * ld_left + idx];
            dest[m * ld_dest + idx] = %(operation)s%(fletter)s((tmp_left) , (right));
        }
    }
}

"""

non_pitch_left_scalar_func_template = pycuda_complex_header + """
__global__ void
%(name)s(%(dest_type)s *dest, const %(src_type)s *left,
         const %(dest_type)s right, const int N)
{
    const int totalthreads = blockDim.x * gridDim.x;
    const int tid = blockIdx.x * blockDim.x + threadIdx.x;

    %(src_type)s tmp_left;
    for (int i = tid; i < N; i += totalthreads)
    {
        tmp_left = left[i];
        dest[i] = %(operation)s%(fletter)s((tmp_left) , (right));
    }
}

"""

pitch_right_scalar_func_template = pycuda_complex_header + """
__global__ void
%(name)s(const int M, const int N, %(dest_type)s *dest,
         const int ld_dest, const %(src_type)s *left,
         const int ld_left, const %(dest_type)s right)
{
    //M is the number of rows, N is the number of columns
    const int tid = threadIdx.x;
    const int sid = threadIdx.y + blockDim.y * blockIdx.x;
    const int total = gridDim.x * blockDim.y;

    int m, n, idx;
    %(src_type)s tmp_left;
    int segment_per_row = ((N - 1) >> 5) + 1;
    int total_segments = M * segment_per_row;

    for(int i = sid; i < total_segments; i+=total)
    {
        m = i / segment_per_row;
        n = i %% segment_per_row;
        idx = (n<<5) + tid;
        if(idx < N)
        {
            tmp_left = left[m * ld_left + idx];
            dest[m * ld_dest + idx] = %(operation)s%(fletter)s((right) , (tmp_left));
        }
    }
}

"""

non_pitch_right_scalar_func_template = pycuda_complex_header + """
__global__ void
%(name)s(%(dest_type)s *dest, const %(dest_type)s *left,
         const %(src_type)s right, const int N)
{
    const int totalthreads = blockDim.x * gridDim.x;
    const int tid = blockIdx.x * blockDim.x + threadIdx.x;

    %(src_type)s tmp_left;
    for (int i = tid; i < N; i += totalthreads)
    {
        tmp_left = left[i];
        dest[i] = %(operation)s%(fletter)s((right) , (tmp_left));
    }
}

"""


pitch_bsxfun_right_row_template = pycuda_complex_header + """
__global__ void
%(name)s(%(array_type)s *array, int array_ld, %(vector_type)s *vector,
         %(result_type)s *result, int result_ld, int M, int N)
{
    // M: number of rows, N: number of cols
    const int tidx = threadIdx.x;
    const int tidy = threadIdx.y;
    const int bidx = blockIdx.x;
    const int bidy = blockIdx.y;
    const int dimy = blockDim.y;

    int col = bidx *32 + tidx;
    extern __shared__ %(vector_type)s v[];
    __syncthreads();

    if(tidy == 0)
    {
        if(col < N)
        {
            v[tidx] = vector[col];
        }
    }

    __syncthreads();

    if(col < N)
    {
        for(int i = tidy + bidy*32; i < min(M, (bidy+1)*32); i += dimy)
        {
            result[i*result_ld+col] = array[i*array_ld+col] %(operator)s v[tidx];
        }
    }
}

"""


pitch_bsxfun_left_row_template = pycuda_complex_header + """
__global__ void
%(name)s(%(array_type)s *array, int array_ld, %(vector_type)s *vector,
         %(result_type)s *result, int result_ld, int M, int N)
{
    // M: number of rows, N: number of cols
    const int tidx = threadIdx.x;
    const int tidy = threadIdx.y;
    const int bidx = blockIdx.x;
    const int bidy = blockIdx.y;
    const int dimy = blockDim.y;

    int col = bidx *32 + tidx;
    extern __shared__ %(vector_type)s v[];
    __syncthreads();

    if(tidy == 0)
    {
        if(col < N)
        {
            v[tidx] = vector[col];
        }
    }

    __syncthreads();

    if(col < N)
    {
        for(int i = tidy + bidy*32; i < min(M, (bidy+1)*32); i += dimy)
        {
            result[i*result_ld+col] = v[tidx] %(operator)s array[i*array_ld+col];
        }
    }
}

"""

pitch_bsxfun_right_col_template = pycuda_complex_header + """
__global__ void
%(name)s(%(array_type)s *array, int array_ld, %(vector_type)s *vector,
         %(result_type)s *result, int result_ld, int M, int N)
{
    // M: number of rows, N: number of cols
    const int tidx = threadIdx.x;
    const int tidy = threadIdx.y;
    const int bidx = blockIdx.x;
    const int bidy = blockIdx.y;
    const int dimy = blockDim.y;

    int col = bidy *32 + tidx; // actually row
    extern __shared__ %(vector_type)s v[];
    __syncthreads();

    if(tidy == 0)
    {
        if(col < M)
        {
            v[tidx] = vector[col];
        }
    }

    __syncthreads();

    col = bidx*32 + tidx;
    int a = tidy;
    if(col < N)
    {
        for(int i = tidy + bidy*32; i < min(M, (bidy+1)*32); i += dimy, a+= dimy)
        {
            result[i*result_ld+col] = array[i*array_ld+col] %(operator)s v[a];
        }
    }
}

"""


pitch_bsxfun_left_col_template = pycuda_complex_header + """
__global__ void
%(name)s(%(array_type)s *array, int array_ld, %(vector_type)s *vector,
         %(result_type)s *result, int result_ld, int M, int N)
{
    // M: number of rows, N: number of cols
    const int tidx = threadIdx.x;
    const int tidy = threadIdx.y;
    const int bidx = blockIdx.x;
    const int bidy = blockIdx.y;
    const int dimy = blockDim.y;

    int col = bidy *32 + tidx; // actually row
    extern __shared__ %(vector_type)s v[];
    __syncthreads();

    if(tidy == 0)
    {
        if(col < M)
        {
            v[tidx] = vector[col];
        }
    }

    __syncthreads();

    col = bidx*32 + tidx;
    int a = tidy;
    if(col < N)
    {
        for(int i = tidy + bidy*32; i < min(M, (bidy+1)*32); i += dimy, a+= dimy)
        {
            result[i*result_ld+col] = v[a] %(operator)s array[i*array_ld+col] ;
        }
    }
}

"""
