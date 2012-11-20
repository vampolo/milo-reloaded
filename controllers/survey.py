from countries import countrynames

response.menu = None

@auth.requires_login()
def _form_in_db(form, survey):
    for k,v in form.vars.iteritems():
        question = db(db.questions.text==k).select(db.questions.ALL).first()
        if question is None:
            question = db.questions.insert(text=k)
        answer = db(db.answers.text==v).select(db.answers.ALL).first()
        if answer is None:
            answer = db.answers.insert(text=v)

        db.commit()

        survey_user = db((db.surveys_users.survey==survey)&
                         (db.surveys_users.iuser==auth.user.milo_user)).select(
                             db.surveys_users.ALL).first()

        if survey_user is None:
            raise ValueError('survey_user cannot be None. It means that user is not allowed'
                             ' for this survey')

        answ_surv = db((db.answers_to_surveys.question==question)&
                       (db.answers_to_surveys.survey_user==survey_user)).select(
                           db.answers_to_surveys.ALL).first()
        if answ_surv is None:
            db.answers_to_surveys.insert(survey_user=survey_user,
                                         question=question,
                                         answer=answer
                )
        else:
            answ_surv.answer=answer
            answ_surv.update_record()

        db.commit()



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
        user = db.auth_user.insert(password=password, email=email)
        auth.login_bare(email, password)
        survey = request.args[0]
        db.surveys_users.insert(survey=survey, iuser=auth.user.milo_user)
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
        _form_in_db(form, surveyid)
        redirect(URL('milo','default', 'index', vars={'ord': 'popular'}))
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
                                                                            "Incomplete",
                                                                            _name="catalogue_complete")),
        TR("Check the boxes you LIKED about the graphical interface"),
        TR(TD(INPUT(_type="checkbox", _name='color_palette'), "Color Palette")),
        TR(TD(INPUT(_type="checkbox", _name='text_readability'),"Text readability")),
        TR(TD(INPUT(_type="checkbox", _name='organizzation'),"Organizzation")),
        TR(TD(INPUT(_type="checkbox", _name='orientation_guidelines'),"Orientation guidelines")),
        TR("Check the boxes you DISLIKED about the graphical interface"),
        TR(TD(INPUT(_type="checkbox", _name='color_palette_dislike'),"Color Palette")),
        TR(TD(INPUT(_type="checkbox", _name='text_readability_dislike'),"Text readability")),
        TR(TD(INPUT(_type="checkbox", _name='organizzation_dislike'),"Organizzation")),
        TR(TD(INPUT(_type="checkbox", _name='orientation_guidelines'),"Orientation guidelines")),
        TR("Did you find confusing the browsing experience through the catalogue?", SELECT('No', 'Partially', 'Yes', _name='confusing_browser_experience')),
        TR('','',INPUT(_type="submit"))
        ))
    if form.process().accepted:
        session.flash = 'form accepted'
        _form_in_db(form, session.survey)
        survey = db.surveys[session.survey]
        redirect(URL(survey.type))
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
        if recommendation is not None:
            #there is no ready recommendation for this user
            rec = recommendation.rec
            session.recommendation = rec
        else:
            rec = list()
    else:
        rec = session.recommendation
    if session.rec_seen == None:
        session.rec_seen = list()
    while True:
        for index in rec:
            if index not in session.rec_seen and db((db.ratings.imovie==index)&(db.ratings.iuser==auth.user.milo_user)).count() == 0:
                return index
        session.recommendation = None
        schedule_recommendation(survey.algorithm, auth.user.milo_user, survey.number_of_ratings*10)
        return None

@auth.requires_login()
def algorithm_performance():
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
def algorithm_strenght():
    if session.survey_stage < 4:
        session.survey_stage = 4
    survey = db.surveys[session.survey]
    rec = db((db.recommendations.iuser==auth.user.milo_user)&
                (db.recommendations.algorithm==survey.algorithm)
                ).select(db.recommendations.ALL).last()
    if rec is None:
        schedule_recommendation(survey.algorithm, auth.user.milo_user, survey.number_of_ratings*2)
        import time
        time.sleep(5)
        #reload the page, algorithm not ready
        redirect(URL('algorithm_strenght'))
    movies = db(db.movies.id.belongs(rec.movies)).select(limitby=(0, survey.number_of_ratings))
    movies_num = len(movies)
    movies_select = range(movies_num+1)
    form = FORM(TABLE(
        TR('How many movies in this list have you ever watched?', SELECT(*movies_select, _name='num_watched')),
        TR('How many movies in this list have you never heard of?', SELECT(*movies_select, _name='num_heard_of')),
        TR('How many movies in this list do you like?', SELECT(*movies_select, _name='num_like')),
        TR('How many movies in this list do you hate?', SELECT(*movies_select, _name='num_hate')),
        TR('From 1 to 5 how interesting did you find the given recommendations?', SELECT(*range(6), _name='1_to_5_interesting')),
        TR('How many movies in this list will you likely watch in the future?', SELECT(*movies_select, _name='num_like_to_watch')),
        TR('','',INPUT(_type="submit", value="Finish"))
        ))
    if form.process().accepted:
        _form_in_db(form, session.survey)
        session.rec_seen = None
        redirect(URL('local_info'))
    elif form.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill the form'
    return dict(list_movies=movies, form=form)

@auth.requires_login()
def local_info():
    if session.survey_stage < 5:
        session.survey_stage = 5
    form = FORM(TABLE(
        TR('Where did this survey take place?', SELECT('University', 'Home', 'Work place', 'Public place', 'Other', _name='survey_take_place')),
        TR('Why did you accepted to take part to the survey?', SELECT('Friend request', 'Interest in movies', 'Amazon Turk', 'Other', _name='why_survey')),
        TR('','',INPUT(_type="submit", value="Finish"))
        ))
    if form.process().accepted:
        _form_in_db(form, session.survey)
        session.flash = 'Thank you for participating to this survey!'
        session.survey = None
        session.survey_stage = None
        redirect(URL('end_survey'))
    elif form.errors:
        response.flash = 'form has errors'
    else:
        response.flash = 'please fill the form'
    response.view = 'survey/form.html'
    return dict(form=form)

@auth.requires_login()
def end_survey():
    if request.post:
        redirect(URL('default', 'index'))
    return dict()
