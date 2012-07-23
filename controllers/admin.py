# coding: utf8
# try something like

import matlab_wrapper

def index():
    algorithms = matlab_wrapper.Whisperer.get_algnames()
    matrices = matlab_wrapper.Whisperer.get_matrices_info()
    return dict(message="hello from admin.py", algorithms=algorithms, matrices_info=matrices)

def info_algorithm():
    print request.args, request.vars
    algname = request.args(0)
    return dict(algname=algname)
    