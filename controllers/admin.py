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

##########################
## Researcher dashboard ##
##########################

def info_algorithm():
    algname = request.args(0)
    infos = matlab_wrapper.Whisperer.get_models_info()
    return dict(algname=algname, date=infos.get(algname, 'Not available'))

def update_algorithm():
    algname=request.args(0)
    schedule_model(algname=algname)
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Model creation correctly submitted</span></p>'

def upload_form():
    
    #reset tables
    #db.uplds.truncate()
    #db.owns.truncate()
    
    form = SQLFORM.factory(db.uplds, formstyle='divs', _action=URL('admin', 'upload_form'))
            
    if form.process().accepted:
        
        #renaming private algs
        if (form.vars.algorithm_sharing == 'private'):
            form.vars.algorithm_name = str(form.vars.algorithm_name) + '@user' + str(auth.user_id)
        
        #function renames in system
        rnm1a = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/' + str(form.vars.model_creator_function)
        rnm1b = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/' + "createModel_" + str(form.vars.algorithm_name) + ".m"
        rnm2a = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/' + str(form.vars.recommender_function)
        rnm2b = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/' + "onLineRecom_" + str(form.vars.algorithm_name) + ".m"
        os.rename(rnm1a,rnm1b)
        os.rename(rnm2a,rnm2b)
        
        #function renames in database
        form.vars.model_creator_function = "createModel_" + str(form.vars.algorithm_name) + ".m"
        form.vars.recommender_function = "onLineRecom_" + str(form.vars.algorithm_name) + ".m"
        
        #database insertion
        print "\nUploaded new algorithm: " + str(form.vars.algorithm_name)
        print 'Model function: ' + str(form.vars.model_creator_function)
        print 'Recommender function: ' + str(form.vars.recommender_function)
        print 'Algorithm sharing type: ' + str(form.vars.algorithm_sharing)
        db.uplds.insert(**db.uplds._filter_fields(form.vars))
        
        #change direcotry due to algorithm sharing type
        if (form.vars.algorithm_sharing == 'private'):
            dst = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/private/'
            shutil.move(rnm1b, dst)
            shutil.move(rnm2b, dst)
        if (form.vars.algorithm_sharing == 'public'):
            dst = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/'
            shutil.move(rnm1b, dst)
            shutil.move(rnm2b, dst)
        
        #setting ownership table
        iid = str(db(db.uplds.algorithm_name==str(form.vars.algorithm_name)).select(db.uplds.id))
        iiid = int(''.join(c for c in iid if c.isdigit()))
        db.owns.insert(upload=iiid, author=int(auth.user_id))

        #check tables
        #enlist = db(db.uplds).select()
        #print enlist
        #owners = db(db.owns).select()
        #print owners
        
        response.flash='record inserted'
        redirect(URL('index'))
    elif form.errors:
        response.flash="errors"
    else:
        response.flash='fill out the form'
    return dict(form=form)

def rules_en():
    return dict()

def pubalg():
    pubalg = matlab_wrapper.Whisperer.get_algnames()
    return dict(pubalg=pubalg)

def download_mc():
    whois=request.args(0)
    
    alg = (str(db(db.uplds.id==whois).select())).split('uplds.algorithm_sharing')[1]
    alg = alg.split('\n')[1]
    alg = alg.split('\r')[0]
    
    fname = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/' + "createModel_" + alg + ".m"
    print 'downloading: ' + fname
    
    #download function
      
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Operation was successful!</span></p>'
    
def download_or():
    whois=request.args(0)
    
    alg = (str(db(db.uplds.id==whois).select())).split('uplds.algorithm_sharing')[1]
    alg = alg.split('\n')[1]
    alg = alg.split('\r')[0]
    
    fname = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/' + "onLineRecom_" + alg + ".m"
    print 'downloading: ' + fname
    
    #download function
    
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Operation was successful!</span></p>'
    
def myalg():

    #extract personal upload IDs
    buff = [];
    algorithms = matlab_wrapper.Whisperer.get_algnames()
    for alg in algorithms:
	algline = str(db(db.uplds.algorithm_name==alg).select(db.uplds.id))
	algid = ''.join(i for i in algline if i.isdigit())
	
	if algid:
		checkline = str(db(db.owns.upload==int(algid)).select(db.owns.author))
		checkid = ''.join(i for i in checkline if i.isdigit())

		if (int(checkid) == int(auth.user_id)):
			buff.append(int(algid))

    #select personal uploads
    myalg = db(db.uplds.id).select()
    
    return dict(myalg=myalg, buff=buff)

def del_alg():
    whois=request.args(0)
    
    alg = (str(db(db.uplds.id==whois).select())).split('uplds.algorithm_sharing')[1]
    alg = alg.split('\n')[1]
    alg = alg.split('\r')[0]
    
    fname1 = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/' + "createModel_" + alg + ".m"
    print 'deleting: ' + fname1
    fname2 = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/' + "onLineRecom_" + alg + ".m"
    print 'deleting: ' + fname2
    
    #delete algorithm
    #db(db.uplds.id == whois).delete()
    #db(db.owns.upload == whois).delete()
    
    #destroy file
    
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Operation was successful!</span></p>'

def passage():
    whois=request.args(0)
    form = SQLFORM.factory(db.rnm, formstyle='divs', _action=URL('admin', 'passage', args=[whois]))
    
    if form.process().accepted:
    	newname = form.vars.new_name
    	alg = (str(db(db.uplds.id==whois).select())).split('uplds.algorithm_sharing')[1]
    	alg = alg.split('\n')[1]
    	alg = alg.split('\r')[0]
    	algo = []
    	algo = alg.split(',')
    
    	if (algo[4] == 'private'):
        	rows = db(db.uplds.id==whois).select()
        	row = rows[0]
        	#change name
        	algo[1] = newname + '@user' + str(auth.user_id)
        	row.update_record(algorithm_name=algo[1])
        
        	#change model function
        	oldmod = algo[2]
        	algo[2] = "createModel_" + algo[1] + ".m"
        	row.update_record(model_creator_function=algo[2]) 
        
        	#change recom function
        	oldrec = algo[3]
        	algo[3] = "onLineRecom_" + algo[1] + ".m"
        	row.update_record(recommender_function=algo[3]) 
        
        	#rename files
        	rnm1a = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/private/' + oldmod
        	rnm1b = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/private/' + algo[2]
        	rnm2a = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/private/' + oldrec
        	rnm2b = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/private/' + algo[3]
        	os.rename(rnm1a,rnm1b)
        	os.rename(rnm2a,rnm2b)
        
    	if (algo[4] == 'public'):
        	rows = db(db.uplds.id==whois).select()
        	row = rows[0]
        
        	#change name
        	algo[1] = newname
        	row.update_record(algorithm_name=algo[1])
        
        	#change model function
        	oldmod = algo[2]
        	algo[2] = "createModel_" + algo[1] + ".m"
        	row.update_record(model_creator_function=algo[2]) 
        
        	#change recom function
        	oldrec = algo[3]
        	algo[3] = "onLineRecom_" + algo[1] + ".m"
        	row.update_record(recommender_function=algo[3]) 
        
        	#rename files
        	rnm1a = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/' + oldmod
        	rnm1b = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/' + algo[2]
        	rnm2a = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/' + oldrec
        	rnm2b = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/' + algo[3]
        	os.rename(rnm1a,rnm1b)
        	os.rename(rnm2a,rnm2b)
       	
    	actual = db(db.uplds.id==whois).select()
    	#print actual
    	
        response.flash='record inserted'
        redirect(URL('index'))
        return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Operation was successful!</span></p>'

    elif form.errors:
        response.flash="errors"
    else:
        response.flash='fill out the form'
    return dict(form=form)

def change():
    whois=request.args(0)
    
    alg = (str(db(db.uplds.id==whois).select())).split('uplds.algorithm_sharing')[1]
    alg = alg.split('\n')[1]
    alg = alg.split('\r')[0]
    algo = []
    algo = alg.split(',')
    
    if (algo[4] == 'private'):
        rows = db(db.uplds.id==whois).select()
        row = rows[0]
        
        #change name
        algo[1]=algo[1].split('@user')[0]
        row.update_record(algorithm_name=algo[1])
        
        #change type
        row.update_record(algorithm_sharing='public') 
        
        #change model function
        oldmod = algo[2]
        algo[2] = algo[2].split('@user')[0] + '.m'
        row.update_record(model_creator_function=algo[2]) 
        
        #change recom function
        oldrec = algo[3]
        algo[3] = algo[3].split('@user')[0] + '.m'
        row.update_record(recommender_function=algo[3]) 
        
        #rename and move files
        rnm1a = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/private/' + oldmod
        rnm1b = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/private/' + algo[2]
        rnm2a = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/private/' + oldrec
        rnm2b = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/private/' + algo[3]
        os.rename(rnm1a,rnm1b)
        os.rename(rnm2a,rnm2b)
        
        dst = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/'
        shutil.move(rnm1b, dst)
        shutil.move(rnm2b, dst)
        
    if (algo[4] == 'public'):
        rows = db(db.uplds.id==whois).select()
        row = rows[0]
        
        #change name
        algo[1] = algo[1] + '@user' + str(auth.user_id)
        row.update_record(algorithm_name=algo[1])
        
        #change type
        row.update_record(algorithm_sharing='private') 
        
        #change model function
        oldmod = algo[2]
        pos = algo[2].rfind('.m')
        algo[2] = algo[2][:pos] + '@user' + str(auth.user_id) + algo[2][pos:]
        row.update_record(model_creator_function=algo[2]) 
        
        #change recom function
        oldrec = algo[3]
        pos = algo[3].rfind('.m')
        algo[3] = algo[3][:pos] + '@user' + str(auth.user_id) + algo[3][pos:]
        row.update_record(recommender_function=algo[3]) 

        #rename and move files
        rnm1a = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/' + oldmod
        rnm1b = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/' + algo[2]
        rnm2a = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/' + oldrec
        rnm2b = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/public/' + algo[3]
        os.rename(rnm1a,rnm1b)
        os.rename(rnm2a,rnm2b)
        
        dst = 'applications/milo/modules/algorithms/recsys_matlab_codes/algorithms/private/'
        shutil.move(rnm1b, dst)
        shutil.move(rnm2b, dst)
    
    actual = db(db.uplds.id==whois).select()
    #print actual
  
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Operation was successful!</span></p>'

def please():

    #check and store admin IDs
    admin_ids = [];
    runner = range(1,MAX_USERS)
    for count in runner:
            if (auth.has_membership('admin',count)):
                admin_ids.append(count);
    current_id = auth.user_id

    #retrieve admin emails
    mail = [];
    for i in admin_ids:
            tempo = str(db(db.auth_user.id==i).select(db.auth_user.email))
            tempo2 = str(tempo[17:])
            tempo3 = tempo2.split('\r')[0]
            mail.append(tempo3)
    
    return dict(admin_ids=admin_ids, current_id=current_id, mail=mail)


#####################
## Admin dashboard ##
#####################

def promo():
    
    #getting user IDs
    promo=[]
    runner = range(1,MAX_USERS)
    for count in runner:
    	    if (auth.has_membership('destr',count) == False):
            	if (auth.has_membership('rsc',count) == True):
                	promo.append(count)
            	if (auth.has_membership('disabled',count) == True):
            		promo.append(count)
    return dict(promo=promo)
    
def del_user():
    whois=request.args(0)
    
    #delete user    
    tempo = str(db(db.auth_user.id==whois).select(db.auth_user.email))
    tempo2 = str(tempo[17:])
    mail = tempo2.split('\r')[0]
    
    db(db.users.email == mail).delete()
    
    auth.add_membership('destr',whois)
    auth.del_membership('rsc',whois)
    auth.del_membership('admin',whois)
    
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Operation was successful!</span></p>'

def addrsc():
    whois=request.args(0)
    
    #enable rsc privileges
    auth.add_membership('rsc',whois)
    auth.del_membership('disabled',whois)
    
    return '<p class="alert congrats"><span class="txt"><span class="icon"></span>Operation was successful!</span></p>'

def rvkrsc():
    whois=request.args(0)
    
    #revoke rsc privileges
    auth.del_membership('rsc',whois)
    auth.add_membership('disabled',whois)
    
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
