import json

def schedule_movie(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        function_name='import_or_update_movie',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600,
    )
    db_scheduler.commit()

def schedule_model(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        function_name='create_model',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600*24*7,
        group_name = 'model'
    )
    db_scheduler.commit()

def schedule_create_features_vector(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        function_name='create_features_vector',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600*24*7,
    )
    db_scheduler.commit()

def schedule_create_titles_vector(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        function_name='create_titles_vector',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600*24*7,
    )
    db_scheduler.commit()

def schedule_create_matlab_matrices(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        function_name='create_matlab_matrices',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600*24*7,
    )
    db_scheduler.commit()

def schedule_popular_movies(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        function_name='import_popular_movies',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600,
    )
    db_scheduler.commit()

def schedule_all_movies(*args, **kwargs):
    db_scheduler.scheduler_task.insert(
        function_name='update_all_movies',
        args=json.dumps(args),
        vars=json.dumps(kwargs),
        timeout = 3600*24*7,
    )
    db_scheduler.commit()

def schedule_start_survey(surveyid):
    db_scheduler.scheduler_task.insert(
        function_name='start_survey',
        args=json.dumps([surveyid]),
        timeout = 3600*24*7,
    )
    db_scheduler.commit()

def schedule_recommendation(algorithm, userid, num_rec=10):
    db_scheduler.scheduler_task.insert(
        function_name='do_recommendation',
        args=json.dumps([algorithm, userid, num_rec]),
        group_name = 'recommendation',
        timeout = 3600*24
        )
    db_scheduler.commit()

def schedule_remove_adult_movies():
    db_scheduler.scheduler_task.insert(
        function_name='remove_adult_movies',
        timeout = 3600*24
        )
    db_scheduler.commit()
