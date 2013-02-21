# -*- coding: utf-8 -*-

#########################################################################
## This scaffolding model makes your app work on Google App Engine too
## File is released under public domain and you can use without limitations
#########################################################################

## if SSL/HTTPS is properly configured and you want all HTTP requests to
## be redirected to HTTPS, uncomment the line below:
# request.requires_https()

if not request.env.web2py_runtime_gae:
    ## if NOT running on Google App Engine use SQLite or other DB
    db = DAL(db_string)
else:
    ## connect to Google BigTable (optional 'google:datastore://namespace')
    db = DAL('google:datastore')
    ## store sessions and tickets there
    session.connect(request, response, db = db)
    ## or store session in Memcache, Redis, etc.
    ## from gluon.contrib.memdb import MEMDB
    ## from google.appengine.api.memcache import Client
    ## session.connect(request, response, db = MEMDB(Client()))

## by default give a view/generic.extension to all actions from localhost
## none otherwise. a pattern can be 'controller/function.extension'
response.generic_patterns = ['*'] if request.is_local else []
## (optional) optimize handling of static files
# response.optimize_css = 'concat,minify,inline'
# response.optimize_js = 'concat,minify,inline'

#########################################################################
## Here is sample code if you need for
## - email capabilities
## - authentication (registration, login, logout, ... )
## - authorization (role based authorization)
## - services (xml, csv, json, xmlrpc, jsonrpc, amf, rss)
## - old style crud actions
## (more options discussed in gluon/tools.py)
#########################################################################

from gluon.tools import Auth, Crud, Service, PluginManager, prettydate
auth = Auth(db, hmac_key=Auth.get_or_create_key())
crud, service, plugins = Crud(db), Service(), PluginManager()


db.define_table('users',
        Field('name'),
        Field('email'),
        Field('imdb_id', 'integer'),
        Field('webuser', 'boolean')
        )

auth.settings.extra_fields[auth.settings.table_user_name] = [
        Field('milo_user', db.users, requires = IS_IN_DB(db,'users.id',db.users._format),
            unique=True, notnull=False, writable=False, readable=False, default=lambda: db.users.insert(webuser=True))]


## create all tables needed by auth if not custom tables
auth.define_tables()

research_group = auth.add_group(role = 'Researchers')
auth.del_group(research_group)
#auth.add_membership(research_group)

## configure email
mail=auth.settings.mailer
mail.settings.server = 'smtp.gmail.com:587'
mail.settings.sender = 'movish@movish.com'
mail.settings.login = mail_string
#mail.settings.login = None

## configure auth policy
auth.settings.registration_requires_verification = False
auth.settings.registration_requires_approval = False
auth.settings.reset_password_requires_verification = True

## if you need to use OpenID, Facebook, MySpace, Twitter, Linkedin, etc.
## register with janrain.com, write your domain:api_key in private/janrain.key
from gluon.contrib.login_methods.rpx_account import use_janrain
use_janrain(auth,filename='private/janrain.key')

#########################################################################
## Define your tables below (or better in another model file) for example
##
## >>> db.define_table('mytable',Field('myfield','string'))
##
## Fields can be 'string','text','password','integer','double','boolean'
##       'date','time','datetime','blob','upload', 'reference TABLENAME'
## There is an implicit 'id integer autoincrement' field
## Consult manual for more options, validators, etc.
##
## More API examples for controllers:
##
## >>> db.mytable.insert(myfield='value')
## >>> rows=db(db.mytable.myfield=='value').select(db.mytable.ALL)
## >>> for row in rows: print row.id, row.myfield
#########################################################################

import imdb

#imdb_connection_str = 'postgres://imdb:imdbsecret@localhost/imdb'
#
#imsql = imdb.IMDb('sql', uri=imdb_connection_str)

im = imdb.IMDb()
#let's use TOR
im.set_proxy('http://localhost:8118/')

db.define_table('genres',
        Field('name')
        )

db.define_table('persons',
        Field('first_name'),
        Field('last_name'),
        Field('birth', 'datetime')
        )

db.define_table('movies',
        Field('imdb_id', 'integer'),
        Field('title'),
        Field('poster', 'text'),
        Field('trailer', 'text'),
        Field('plot', 'text'),
        Field('year'),
        Field('updated', 'datetime')
        )

db.define_table('movies_genres',
        Field('movie', db.movies, requires=IS_IN_DB(db, 'movies.id', db.movies._format)),
        Field('genre', db.genres, requires=IS_IN_DB(db, 'movies.id', db.movies._format))
        )

db.define_table('ratings',
        Field('iuser', db.users, requires = IS_IN_DB(db,'users.id',db.users._format)),
        Field('imovie', db.movies, requires = IS_IN_DB(db,'movies.id',db.movies._format)),
        Field('rating', 'double')
        )

db.define_table('comments',
        Field('movie', db.movies, requires = IS_IN_DB(db, 'movies.id', db.movies._format)),
        Field('title'),
        Field('text', 'text'),
        Field('rating', db.ratings, requires = IS_IN_DB(db, 'ratings.id', db.ratings._format)),
        Field('timestamp', 'datetime'),
        )

db.define_table('roles',
        Field('name')
        )

db.define_table('persons_in_movies',
        Field('movie', db.movies, requires = IS_IN_DB(db, 'movies.id', db.movies._format)),
        Field('person', db.persons, requires = IS_IN_DB(db, 'persons.id', db.persons._format)),
        Field('role', db.roles, requires = IS_IN_DB(db, 'roles.id', db.roles._format))
        )


movies_with_ratings = (db.movies.id.belongs(db(db.ratings)._select(db.ratings.imovie, distinct=db.ratings.imovie)))
movies_with_titles = ~(db.movies.title==None)
with_poster = ~(db.movies.poster=='images/unknown_poster.jpg')
with_year = ~(db.movies.year==None)
adult_movies = db.movies.id.belongs(db(db.movies_genres.genre.belongs(db(db.genres.name=='Adult')._select(db.genres.id)))._select(db.movies_genres.movie))
useful_movies = movies_with_ratings&movies_with_titles&with_poster&with_year

#for x in db(db.ratings).select(db.ratings.ALL):
#    for y in db(db.ratings.id>x.id).select(db.ratings.ALL):
#        if y.iuser == x.iuser and y.imovie == x.imovie:
#            y.delete_record()
#    db.commit()

#run only once
#db.executesql('CREATE UNIQUE INDEX iuser_imovie ON ratings (iuser,imovie);')


db.define_table('features',
        Field('name'),
        Field('type')
        )

db.define_table('movies_features',
        Field('movie', db.movies, requires = IS_IN_DB(db,'movies.id',db.movies._format)),
        Field('feature', db.features, requires = IS_IN_DB(db,'features.id',db.features._format)),
        Field('times', 'integer')
        )

from matlab_wrapper import Whisperer

db.define_table('surveys',
                Field('name'),
                Field('algorithm', requires=IS_IN_SET(Whisperer.get_algnames())),
                Field('number_of_ratings', 'integer'),
                Field('scale', 'integer', requires=IS_IN_SET([1, 5, 10, 20]), default=5),
                Field('number_of_free_ratings', 'integer', default=5),
                Field('type', 'string', requires = IS_IN_SET(['algorithm_performance', 'algorithm_strenght']), default='algorithm_performance')
                )
                
db.define_table('uplds',
                Field('algorithm_identifier_name', requires=IS_NOT_EMPTY()),
                Field('author'),
                Field('model_creator_function', 'upload', uploadfolder='applications/milo/modules/algorithms/recsys_matlab_codes/algorithms',requires = IS_UPLOAD_FILENAME(extension='m')),
                Field('recommender_function', 'upload',uploadfolder='applications/milo/modules/algorithms/recsys_matlab_codes/algorithms',requires = IS_UPLOAD_FILENAME(extension='m')),
                Field('algorithm_family', 'string', requires = IS_IN_SET(['collaborative(latent-factors)', 'collaborative(neighborhood-based)','content-based','non-personalized']))
                )
                
db.uplds.algorithm_identifier_name.requires = IS_NOT_IN_DB(db, 'uplds.algorithm_identifier_name')

db.define_table('surveys_users',
                Field('survey', db.surveys, requires=IS_IN_DB(db, 'surveys.id', db.surveys._format)),
                Field('iuser', db.users, requires=IS_IN_DB(db, 'users.id', db.users._format)),
                )


db.define_table('questions',
                Field('text', 'text')
                )

db.define_table('answers',
                Field('text', 'text')
                )

db.define_table('answers_to_surveys',
                Field('survey_user', db.surveys_users),
                Field('question', db.questions),
                Field('answer', db.answers)
                )

db.define_table('recommendations',
                Field('iuser', 'reference users'),
                Field('movies', 'list:reference movies'),
                Field('algorithm'),
                Field('timestamp', 'datetime', default=request.now)
                )
