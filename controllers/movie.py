def show():
    movie_id = request.args[0]
    movie = db.movies[movie_id]
    comments = db(db.comments.movie==movie).select()
    cast = movie.persons_in_movies(db.persons_in_movies.role.belongs(db.roles.name=='actor')).select()
    directors = movie.persons_in_movies(db.persons_in_movies.role.belongs(db.roles.name=='director')).select()
    if session.orientation:
        session.orientation[movie.title] = URL(r=request, args=request.args, vars=request.vars)
    return dict(movie=movie, comments=comments, cast=cast, directors=directors)
