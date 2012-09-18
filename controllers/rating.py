from collections import namedtuple

legend5 = {
    1:'Worst',
    2:'Bad',
    3:'Ok',
    4:'Good',
    5:'Best'
}

legend2 = {
    1:'Worst',
    2:'Best',
    }

Rating = namedtuple('Rating', ['movie', 'rate', 'mode'])

RATING_MODE = 5

@auth.requires_login()
def index():
    rating_mode = RATING_MODE
    movie_id = request.args[0]
    query = (db.ratings.iuser==auth.user.milo_user)&(db.ratings.imovie==movie_id)
    entries = db(query).select(cacheable=True)
    if len(entries) == 1:
        rating = entries.first().rating * float(rating_mode)
    elif len(entries) > 1:
        raise EnvironmentError('Multiple entries in db')
    else:
        rating=None
    return dict(id=movie_id, legend=legend5, rating=rating)

@auth.requires_login()
def rate():
    if 'rate' not in request.post_vars:
        db((db.ratings.iuser==auth.user.milo_user)&(db.ratings.imovie==request.post_vars['movie'])).delete()
        return dict()
    rating = Rating(**request.post_vars)
    rating_db = db((db.ratings.iuser==auth.user.milo_user)&
        (db.ratings.imovie==rating.movie)).select()
    if len(rating_db) == 0:
        db.ratings.insert(iuser=auth.user.milo_user,
                          imovie=rating.movie,
                          rating=float(rating.rate)/float(rating.mode)
                          )
    elif len(rating_db) == 1:
        rating_db = rating_db.first()
        rating_db.rating=float(rating.rate)/float(rating.mode)
        rating_db.update_record()
    else:
        raise EnvironmentError('Multiple entries in db')
    return dict()
