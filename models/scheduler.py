from importer import Importer
import json
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

from gluon.scheduler import Scheduler
myscheduler = Scheduler(db_scheduler)
