from scheduler import Scheduler
from importer import Importer
import json
import datetime
matlab_wrapper = local_import('matlab_wrapper')

db_scheduler = DAL('postgres://milo:milosecret@localhost/milo-scheduler')
 
def create_model(*args, **vars):
    w = matlab_wrapper.Whisperer(db)
    w.create_model()

def create_metadata(*args, **vars):
    metadata = local_import('metadata')
    generator = metadata.MetadataGenerator(db, im)
    generator.create_metadata()
    return

def create_features_titles(*args, **kwargs):
    w = matlab_wrapper.Whisperer(db, im)
    w.create_titles_and_features_vector()

def import_movies():
    i = Importer(db, im)
    i.import_movies_from_imdb()

def import_or_update_movie(*args, **kwargs):
    i = Importer(db, im)
    i.import_or_update_movie(*args, **kwargs)

def import_posters():
    i = Importer(db, im)
    i.import_posters()
    
milo_scheduler = Scheduler(db_scheduler, dict(
    create_model=create_model,
    create_metadata=create_metadata,
    create_features_titles=create_features_titles,
    import_or_update_movie=import_or_update_movie
    ))

def schedule_movie(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        status='QUEUED',
        application_name='milo',
        task_name='schedule_movie',
        function_name='import_or_update_movie',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        enabled=True,
        start_time = request.now,
        stop_time = request.now+datetime.timedelta(days=10),
        repeats = 1,
        timeout = 3600,
    )

#import datetime    
#db_scheduler.scheduler_task.insert(
#        application_name='milo',
#        function_name='create_urm',
#        enabled=True,
#        start_time=request.now,
#        stop_time = request.now+datetime.timedelta(days=1)
#        )
