import matlab_wrapper
import cStringIO
import csv
import os
import shutil

MAX_USERS = 100

@auth.requires_membership('rsc')
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

@auth.requires_membership('admin')    
def indexplus():
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

def upload_form():
    
    form = SQLFORM.factory(db.uplds, formstyle='divs', _action=URL('admin', 'upload_form'))
            
    if form.process().accepted:
        
        #function renames in system
        rnm1a = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/' + form.vars.model_creator_function
        rnm1b = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/' + "createModel_" + form.vars.algorithm_identifier_name + ".m"
        rnm2a = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/' + form.vars.recommender_function
        rnm2b = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/' + "onLineRecom_" + form.vars.algorithm_identifier_name + ".m"
        os.rename(rnm1a,rnm1b)
        os.rename(rnm2a,rnm2b)
        
        #function renames in database
        form.vars.model_creator_function = "createModel_" + form.vars.algorithm_identifier_name + ".m"
        form.vars.recommender_function = "onLineRecom_" + form.vars.algorithm_identifier_name + ".m"
        form.vars.author = auth.user_id
        
        #control insertion
        print "\nUploaded new algorithm: " + form.vars.algorithm_identifier_name
        print 'Model function: ' + form.vars.model_creator_function
        print 'Recommender function: ' + form.vars.recommender_function
        print 'Algorithm family: ' + form.vars.algorithm_family    
        print 'Author ID: ' + str(auth.user_id)
        db.uplds.insert(**db.uplds._filter_fields(form.vars))
                
        #whole upload list
        enlist = db(db.uplds).select()
        #print enlist
    
        #change direcotry due to alg_type
        if (form.vars.algorithm_family == 'collaborative(latent-factors)'):
            os.mkdir('applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/collaborative/latentFactors/' + form.vars.algorithm_identifier_name)
            dst = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/collaborative/latentFactors/' + form.vars.algorithm_identifier_name
            shutil.move(rnm1b, dst)
            shutil.move(rnm2b, dst)
        
        elif (form.vars.algorithm_family == 'collaborative(neighborhood-based)'):
            os.mkdir('applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/collaborative/neighborhoodBased/' + form.vars.algorithm_identifier_name)
            dst = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/collaborative/neighborhoodBased/' + form.vars.algorithm_identifier_name
            shutil.move(rnm1b, dst)
            shutil.move(rnm2b, dst)
        
        elif (form.vars.algorithm_family == 'content-based'):
            os.mkdir('applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/content-based/' + form.vars.algorithm_identifier_name)
            dst = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/content-based/' + form.vars.algorithm_identifier_name
            shutil.move(rnm1b, dst)
            shutil.move(rnm2b, dst)
        
        elif (form.vars.algorithm_family == 'non-personalized'):
            os.mkdir('applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/non-personalized/' + form.vars.algorithm_identifier_name)
            dst = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/non-personalized/' + form.vars.algorithm_identifier_name
            shutil.move(rnm1b, dst)
            shutil.move(rnm2b, dst)
        
        else:
            print 'error. algorithm family is not valid'
        
        response.flash='record inserted'
        redirect(URL('index'))
    elif form.errors:
        response.flash="errors"
    else:
        response.flash='fill out the form'
    return dict(form=form)

def promo():
    
    #getting researchers' ID
    promo=[]
    runner = range(1,MAX_USERS)
    for count in runner:
            if (auth.has_membership('rsc',count) == True):
                promo.append(count)
    return dict(promo=promo)

def addrsc():
    whois=request.args(0)
    
    #grant rsc privileges
    auth.add_membership('rsc',whois)
    
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Operation was successful!</span></p>'

def rvkrsc():
    whois=request.args(0)
    
    #revoke rsc privileges
    auth.del_membership('rsc',whois)
    
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Operation was successful!</span></p>'

def addadm():
    whois=request.args(0)
    
    #grant admin privileges
    auth.add_membership('admin',whois)
    
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Operation was successful!</span></p>'

def rvkadm():
    whois=request.args(0)
    
    #revoke admin privileges
    auth.del_membership('admin',whois)
    
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Operation was successful!</span></p>'

def please():
    print 'banana1'
    #check and store admin IDs
    admin_ids = [];
    for count2 in runner2:
            if (auth.has_membership('admin',count)):
                admin_ids.append(count);
    current_id = auth.user_id
    
    print 'banana2'
    #retrieve admin emails
    mail = [];
    for i in admin_ids:
            tempo = str(db(db.auth_user.id==i).select(db.auth_user.email))
            tempo2 = str(tempo[17:])
            tempo3 = tempo2.split('\r')[0]
            mail.append(tempo3)
            
    print 'banana3'
    
    return dict(admin_ids=admin_ids, current_id=current_id, mail=mail)

def rules_en():
    return dict()
    
def rules_it():
    return dict()

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
                user_id = db[auth.settings.table_user_name].insert(email=email)
            else:
                user_id = db_email.id
            db.surveys_users.insert(survey=survey_id, iuser=db[auth.settings.table_user_name][user_id].milo_user)
        schedule_start_survey(survey_id)
        response.flash="ok"
        redirect(URL('index'))
    elif form.errors:
        response.flash="errors"
    else:
        response.flash='fill out the form'
    return dict(form=form)

def download_survey_results():
    survey = db.surveys[request.args[0]]
    survey_users_ids = db(db.surveys_users.survey==survey)._select(db.surveys_users.id)
    questions_ids = db(db.answers_to_surveys.survey_user.belongs(survey_users_ids))._select(db.answers_to_surveys.question,  distinct=True)
    questions = db(db.questions.id.belongs(questions_ids)).select(db.questions.ALL)
    answers_to_survey = db(db.answers_to_surveys.survey_user.belongs(survey_users_ids)).select(db.answers_to_surveys.ALL, orderby=db.answers_to_surveys.survey_user|db.answers_to_surveys.question, groupby=db.answers_to_surveys.survey_user|db.answers_to_surveys.id)
    stream=cStringIO.StringIO()
    cvs_writer = csv.writer(stream)
    users = set([x.survey_user for x in answers_to_survey])
    users = list(users)
    users.sort()
    cvs_writer.writerow(['survey_user']+[x.text for x in questions])

    question_id_mapping = dict()
    counter = 0
    for x in questions:
        question_id_mapping[x.id]=counter
        counter+=1
    for user in users:
        res = [None]*counter
        for id_question in [x.id for x in questions]:
            if res[question_id_mapping[id_question]] is None:
                for answer_to_survey in answers_to_survey:
                    if answer_to_survey.survey_user == user:
                        if answer_to_survey.question == id_question:
                            res[question_id_mapping[id_question]]=answer_to_survey.answer.text
        res.insert(0, user)
        cvs_writer.writerow(res)
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename={}.csv'.format('movish-survey-'+str(survey.id))
    return stream.getvalue()

def delete_survey():
    del db.surveys[request.args[0]]
    response.view = 'admin/surveys.html'
    return surveys()

def get_popular_movies():
    schedule_popular_movies()
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Movies retrieval scheduled in the system</span></p>'

def update_all_movies():
    schedule_all_movies()
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Movies retrieval scheduled in the system</span></p>'

def bisect():
    completed_n = db_scheduler(db_scheduler.scheduler_task.status=="COMPLETED").count()
    failed_n = db_scheduler(db_scheduler.scheduler_task.status=="FAILED").count()
    faileds = db_scheduler(db_scheduler.scheduler_run.status=="FAILED").select(orderby=~db_scheduler.scheduler_run.id, limitby=(0,10), cacheable=True)
    return dict(completed_n=completed_n, failed_n=failed_n, faileds=faileds)

def remove_adult_movies():
    schedule_remove_adult_movies()
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>All movies with Adult genre will be deleted from the dataset shortly</span></p>'
