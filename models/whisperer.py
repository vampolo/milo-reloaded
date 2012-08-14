from scheduler import Scheduler
from importer import Importer
import json
import datetime
import matlab_wrapper

db_scheduler = DAL('postgres://milo:milosecret@localhost/milo-scheduler')
 
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
    

milo_scheduler = Scheduler(db_scheduler, dict(
    create_model=create_model,
    create_features_vector=create_features_vector,
    create_titles_vector=create_titles_vector,
    import_or_update_movie=import_or_update_movie,
    create_matlab_matrices=create_matlab_matrices
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
