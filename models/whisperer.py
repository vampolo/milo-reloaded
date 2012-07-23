from scheduler import Scheduler
from importer import Importer
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

def import_posters():
    i = Importer(db, im)
    i.import_posters()
    
milo_scheduler = Scheduler(db_scheduler, dict(
    create_model=create_model,
    create_metadata=create_metadata,
    create_features_titles=create_features_titles
    ))

#import datetime    
#db_scheduler.scheduler_task.insert(
#        application_name='milo',
#        function_name='create_urm',
#        enabled=True,
#        start_time=request.now,
#        stop_time = request.now+datetime.timedelta(days=1)
#        )
