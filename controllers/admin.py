# coding: utf8
# try something like

import matlab_wrapper

def index():
    algorithms = matlab_wrapper.Whisperer.get_algnames()
    matrices = matlab_wrapper.Whisperer.get_matrices_info()
    return dict(message="hello from admin.py", algorithms=algorithms, matrices_info=matrices)

def info_algorithm():
    algname = request.args(0)
    infos = matlab_wrapper.Whisperer.get_models_info()        
    return dict(algname=algname, date=infos.get(algname, 'Not available'))
    
def update_algorithm():
    algname=request.args(0)
    schedule_model(algname=algname)
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Model creation correctly submitted</span></p>'
    
def matrices():
    matrices = matlab_wrapper.Whisperer.get_matrices_info()
    return dict(matrices=matrices)
    
def download_matrice():
    matrices = matlab_wrapper.Whisperer.get_matrices_path()
    matrice = request.args(0)    
    response.headers['Content-Disposition'] = 'attachment; filename={}.mat'.format(matrice)
    return response.stream(matrices[matrice])

def make_matrice():
    matrice = request.args(0)
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Matrice creation correctly submitted</span></p>'

def delete_matrice():
    matrice = request.args(0)
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>The matrice has been deleted</span></p>'
