from scheduler import Scheduler
from importer import Importer
import json
import datetime
import matlab_wrapper

db_scheduler = DAL('postgres://milo:milosecret@localhost/milo-scheduler')

whisperer = matlab_wrapper.Whisperer(db, im)
 
def create_model(*args, **vars):
    w = matlab_wrapper.Whisperer(db,im)
    w.create_model(*args, **vars)

def import_or_update_movie(*args, **kwargs):
    i = Importer(db, im)
    i.import_or_update_movie(*args, **kwargs)

def import_popular_movies(*args, **kwargs):
    i = Importer(db, im)
    i.get_popular_movies(schedule_movie, *args, **kwargs)
    
def create_features_vector(*args, **kwargs):
    w = matlab_wrapper.Whisperer(db, im)
    w.create_features_vector(*args, **kwargs)

def create_titles_vector(*args, **kwargs):
    w = matlab_wrapper.Whisperer(db, im)
    w.create_titles_vector(*args, **kwargs)

def create_matlab_matrices(*args, **kwargs):
    w = matlab_wrapper.Whisperer(db, im)
    w.create_matlab_matrices(*args, **kwargs)

def update_all_movies(*args, **kwargs):
    movies = db(db.movies).select(db.movies.ALL, cacheable=True)
    for movie in movies:
        schedule_movie(movie.id, reviews=True)

def start_survey(surveyid):
    def send_mail():
        l= ['vincenzo.ampolo@gmail.com']
        mail.send(to=l,
          subject='hello',
          # If reply_to is omitted, then mail.settings.sender is used
          reply_to='noreply@noreply',
          message='hi there')
    survey = db.survey[surveyid]
    create_model(survey.algorithm)
    send_email()

milo_scheduler = Scheduler(db_scheduler, dict(
    create_model=create_model,
    create_features_vector=create_features_vector,
    create_titles_vector=create_titles_vector,
    import_or_update_movie=import_or_update_movie,
    create_matlab_matrices=create_matlab_matrices,
    import_popular_movies=import_popular_movies,
    update_all_movies=update_all_movies
    ))

def schedule_movie(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        application_name='milo',
        task_name='schedule_movie',
        function_name='import_or_update_movie',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600,
    )
    db_scheduler.commit()

def schedule_model(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        application_name='milo',
        task_name='schedule_model',
        function_name='create_model',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600*24*7,
    )
    db_scheduler.commit()

def schedule_create_features_vector(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        application_name='milo',
        task_name='schedule_create_features_vector',
        function_name='create_features_vector',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600*24*7,
    )
    db_scheduler.commit()
    
def schedule_create_titles_vector(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        application_name='milo',
        task_name='schedule_create_titles_vector',
        function_name='create_titles_vector',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600*24*7,
    )
    db_scheduler.commit()
    
def schedule_create_matlab_matrices(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        application_name='milo',
        task_name='schedule_create_matlab_matrices',
        function_name='create_matlab_matrices',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600*24*7,
    )
    db_scheduler.commit()

def schedule_popular_movies(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        application_name='milo',
        task_name='schedule_popular_movies',
        function_name='import_popular_movies',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600,
    )
    db_scheduler.commit()

def schedule_all_movies(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        application_name='milo',
        task_name='schedule_all_movies',
        function_name='update_all_movies',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600*24*7,
    )
    db_scheduler.commit()

def schedule_start_survey(surveyid):
    db_scheduler.scheduler_task.insert(
        application_name='milo',
        task_name='schedule_start_survey',
        function_name='start_survey',
        args=json.dumps([surveyid]),
        timeout = 3600*24*7,
    )
    db_scheduler.commit() 
