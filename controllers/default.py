# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a samples controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################

ITEMS_PER_PAGE = 15

def _render_to_index(query):
    if request.post_vars.free_rating == 'end':
        redirect(URL('survey', 'catalogue_questions'))
    response.view = 'default/index.html'
    page = 0 if not request.args(0) else int(request.args(0))
    list_movies = db(query).select(db.movies.ALL, orderby=~(db.movies.year)|~(db.movies.updated), limitby=(page*ITEMS_PER_PAGE,page*ITEMS_PER_PAGE+ITEMS_PER_PAGE), cache=(cache.disk, 3600))
    max_items = db(query).count()
    return dict(list_movies = list_movies, slider_movies = list_movies, page = page, max_items=max_items, items_per_page=ITEMS_PER_PAGE)

def index():
    query = useful_movies
    return _render_to_index(query)

def search():
    term = request.vars.get('s')
    genres = request.vars.getlist('genres')
    query = db.movies.id>0
    if term:
        query &= db.movies.title.contains(term)
    if genres:
        query &= db.movies.id.belongs(db(db.movies_genres.genre.belongs(genres))._select(db.movies_genres.movie))
    return _render_to_index(query)

def user():
    """
    exposes:
    http://..../[app]/default/user/login
    http://..../[app]/default/user/logout
    http://..../[app]/default/user/register
    http://..../[app]/default/user/profile
    http://..../[app]/default/user/retrieve_password
    http://..../[app]/default/user/change_password
    use @auth.requires_login()
        @auth.requires_membership('group name')
        @auth.requires_permission('read','table name',record_id)
    to decorate functions that need access control
    """
    return dict(form=auth())


def download():
    """
    allows downloading of uploaded files
    http://..../[app]/default/download/[filename]
    """
    return response.download(request,db)


def call():
    """
    exposes services. for example:
    http://..../[app]/default/call/jsonrpc
    decorate with @services.jsonrpc the functions to expose
    supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
    """
    return service()


@auth.requires_signature()
def data():
    """
    http://..../[app]/default/data/tables
    http://..../[app]/default/data/create/[table]
    http://..../[app]/default/data/read/[table]/[id]
    http://..../[app]/default/data/update/[table]/[id]
    http://..../[app]/default/data/delete/[table]/[id]
    http://..../[app]/default/data/select/[table]
    http://..../[app]/default/data/search/[table]
    but URLs must be signed, i.e. linked with
      A('table',_href=URL('data/tables',user_signature=True))
    or with the signed load operator
      LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
    """
    return dict(form=crud())
