from countries import countrynames

response.menu = None

def amazonturk():
    #it can be logged or not logged
    if auth.is_logged_in():
        redirect(URL('survey', 'demographic', args=request.args))
    else:
        #create user, log in and reload
        last_user = db(db.auth_user.email.startswith('amazonturk')).select().last()
        if last_user is None:
            num = 0
        else:
            num = int(last_user.email[10:-10]) + 1
        #prevent double crypting
        db.auth_user.password.requires = None
        email = 'amazonturk'+str(num)+'@movish.co'
        password = 'automatic-amazonturk'
        db.auth_user.insert(password=password, email=email)
        auth.login_bare(email, password)
        redirect(URL('survey', 'amazonturk', args=request.args))

@auth.requires_login()
def demographic():
    surveyid = request.args[0]
    #check that the user is in that survey
    if not session.survey_stage:
        session.survey_stage = 1
    form=FORM(
              TABLE(
                  TR('Age',SELECT(value='23',_name='age', *range(15,100))),
                  TR('Gender',SELECT('Male', 'Female', _name='gender')),
                  TR('Education',SELECT('Primary school', 'Middle secondary school', 'High school', 'Bachelor degree', 'Master degree', 'Phd', 'Professor', _name='education', value='Bachelor degree',)),
                  TR('Nationality', SELECT(*countrynames, _name='nationality')),
                  TR('Average number of movies watched per month', SELECT(_name='number_of_movies_per_month', value='10', *(range(1,20)+['more than 20']))),
                  TR('','',INPUT(_type='submit'))
              ))
    if form.process().accepted:
        session.flash = 'form accepted'
        session.survey=surveyid
        if session.survey_stage < 2:
            session.survey_stage = 2
        print form
        redirect(URL('milo','default', 'index'))
    elif form.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill the form'
    response.view = 'survey/form.html'
    return dict(form=form)


@auth.requires_login()
def catalogue_questions():
    if session.survey_stage < 3:
        session.survey_stage = 3
    form = FORM(TABLE(
        TR("Where you looking for specific items?", SELECT('No',
                                                           'Partially',
                                                           'Yes', _name="spec_item")),
        TR("Did you looked for movies that couldn't be found?", SELECT('No', 'Yes', _name="not_found")),
        TR("If yes, which ones?"),
        TR('',INPUT(_name="title1")),
        TR('',INPUT(_name="title2")),
        TR('',INPUT(_name="title3")),
        TR("Do you think that the catalogue appers to be complete?", SELECT("Highly complete",
                                                                            "Complete enough",
                                                                            "Partially complete",
                                                                            "Incomplete")),
        TR("Check the boxes you LIKED about the graphical interface"),
        TR(TD(INPUT(_type="checkbox"), "Color Palette")),
        TR(TD(INPUT(_type="checkbox"),"Text readability")),
        TR(TD(INPUT(_type="checkbox"),"Organizzation")),
        TR(TD(INPUT(_type="checkbox"),"Orientation guidelines")),
        TR("Check the boxes you DISLIKED about the graphical interface"),
        TR(TD(INPUT(_type="checkbox"),"Color Palette")),
        TR(TD(INPUT(_type="checkbox"),"Text readability")),
        TR(TD(INPUT(_type="checkbox"),"Organizzation")),
        TR(TD(INPUT(_type="checkbox"),"Orientation guidelines")),
        TR("Did you find confusing the browsing experience through the catalogue?", SELECT('No', 'Partially', 'Yes')),
        TR('','',INPUT(_type="submit"))
        ))
    if form.process().accepted:
        session.flash = 'form accepted'
        redirect(URL('rec_movies'))
    elif form.errors:
        response.flash = 'form has errors'
    else:
        survey = db.surveys[session.survey]
        schedule_recommendation(survey.algorithm, auth.user.milo_user, survey.number_of_ratings*2)
        response.flash = 'please fill the form'
    response.view = 'survey/form.html'
    return dict(form=form)


def next_movie():
    survey = db.surveys[session.survey]
    n_rec = survey.number_of_ratings
    if not session.recommendation:
        recommendation = db(db.recommendations.iuser==auth.user.milo_user).select().last()
        rec = recommendation.rec
        session.recommendation = rec
    else:
        rec = session.recommendation
    print rec
    if session.rec_seen == None:
        session.rec_seen = list()
    while True:
        for index in rec:
            if index not in session.rec_seen and db((db.ratings.imovie==index)&(db.ratings.iuser==auth.user.milo_user)).count() == 0:
                return index
        session.recommendation = None
        schedule_recommendation(survey.algorithm, auth.user.milo_user, survey.number_of_ratings*10)
        rec = [x.id for x in db(useful_movies).select(db.movies.id, limitby=(0,1000))]

@auth.requires_login()
def rec_movies():
    if session.survey_stage < 4:
        session.survey_stage = 4
    if session.movie:
        movie_id = session.movie
    else:
        session.movie = next_movie()
        movie_id = session.movie
        session.rec_to_do = db.surveys[session.survey].number_of_ratings
    if len(request.post_vars) != 0:
        #we are in the post
        #process form
        session.rec_to_do -= 1
        if db((db.ratings.imovie==session.movie)&(db.ratings.iuser==auth.user.milo_user)).count():
            session.rec_seen.append(session.movie)
        if session.rec_to_do == 0:
            session.rec_seen = None
            redirect(URL('local_info'))
        else:
            movie_id = next_movie()
            session.movie = movie_id

    movie = db.movies[movie_id]
    comments = db(db.comments.movie==movie).select()
    cast = movie.persons_in_movies(db.persons_in_movies.role.belongs(db.roles.name=='actor')).select()
    directors = movie.persons_in_movies(db.persons_in_movies.role.belongs(db.roles.name=='director')).select()
    return dict(movie=movie, comments=comments, cast=cast, directors=directors)

@auth.requires_login()
def local_info():
    if session.survey_stage < 5:
        session.survey_stage = 5
    form = FORM(TABLE(
        TR('Where did this survey take place?', SELECT('University', 'Home', 'Work place', 'Public place', 'Other')),
        TR('Why did you accepted to take part to the survey?', SELECT('Friend request', 'Interest in movies', 'Other')),
        TR('','',INPUT(_type="submit", value="Finish"))
        ))
    if form.process().accepted:
        session.flash = 'Thank you for participating to this survey!'
        session.survey = None
        session.survey_stage = None
        redirect(URL('default', 'index'))
    elif form.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill the form'
    response.view = 'survey/form.html'
    return dict(form=form)
