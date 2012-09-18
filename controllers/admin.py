# coding: utf8
# try something like

import matlab_wrapper

@auth.requires_membership('admin')
def index():
    algorithms = matlab_wrapper.Whisperer.get_algnames()
    matrices = matlab_wrapper.Whisperer.get_matrices_info()
    l = list()
    l.append(db(db.users).count())
    l.append(db(useful_movies).count())
    l.append(db(db.movies).count())
    l.append(db(db.ratings).count())
    l.append(db_scheduler(db_scheduler.scheduler_worker).count())
    l.append(db_scheduler((db_scheduler.scheduler_task.status=="QUEUED")|(db_scheduler.scheduler_task.status=="ASSIGNED")).count())
    workers = db_scheduler(db_scheduler.scheduler_run.status=='RUNNING').select()
    return dict(algorithms=algorithms, matrices_info=matrices, info=l, workers=workers)

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
    if matrice == 'titles':
        schedule_create_titles_vector()
    if matrice == 'features':
        schedule_create_features_vector()
    if matrice == 'urm':
        schedule_create_matlab_matrices(type='urm', force=True)
    if matrice == 'icm':
        schedule_create_matlab_matrices(type='icm', force=True)
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Matrice creation correctly submitted</span></p>'

def delete_matrice():
    matrice = request.args(0)
    matlab_wrapper.Whisperer.delete_matrice(matrice)
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>The matrice has been deleted</span>' +str(A("Refresh page", _title="Matrices", target="content", callback=URL("matrices")))+'</p>'

def surveys():
    surveys = db(db.surveys).select()
    return dict(surveys=surveys)

def create_survey():
    form = SQLFORM.factory(db.surveys, Field('users_or_emails', 'text'), formstyle='divs', _action=URL('admin', 'create_survey'))
    if form.process().accepted:
        survey_id = db.surveys.insert(**db.surveys._filter_fields(form.vars))
        for email in form.vars.users_or_emails.split(','):
            email = email.strip()
            if len(email) == 0:
                continue
            db_email = db(db.users.email==email).select().first()
            if not db_email:
                db_email = db(db[auth.settings.table_user_name].email==email).select().first()
            if not db_email:
                user_id = db[auth.settings.table_user_name].insert(email)
            db.surverys_users.insert(survey=survey_id, iuser=db[auth.settings.table_user_name][user_id].milo_user)
            schedule_start_survey(survey_id)
        response.flash="ok"
        redirect(URL('index'))
    elif form.errors:
        response.flash="errors"
    else:
        response.flash='fill out the form'
    return dict(form=form)

def get_popular_movies():
    schedule_popular_movies()
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Movies retrieval scheduled in the system</span></p>'

def update_all_movies():
    schedule_all_movies()
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Movies retrieval scheduled in the system</span></p>'

