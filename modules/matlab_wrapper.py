from pymatlab.matlab import MatlabSession
import numpy
import os
import functools
import datetime
import bottleneck

here = os.path.abspath(os.path.dirname(__file__))

ALGOPATH=os.path.join(here,'algorithms')
SAVEPATH=os.path.join(here,'elaborated_models')

ALL_MATRICES = ['urm', 'icm', 'titles', 'features']

def matlab(f):
    @functools.wraps(f)
    def wrapper(self, *args, **kwds):
        self._start_matlab()
        res = f(self, *args, **kwds)
        self._close_matlab()
        return res
    return wrapper

class Whisperer(object):

    savepath = SAVEPATH
    algopath = ALGOPATH

    def _start_matlab(self):
        self.m = MatlabSession('/usr/local/MATLAB/R2011a/bin/matlab -nosplash -nodisplay')
        self.m.run("addpath(genpath('"+os.path.abspath(self.algopath)+"'))")

    def __init__(self,db,im=None):
        self.m = None
        self.db = db
        self.im = im

    def _put(self, name, value):
        self.m.putvalue(name, value)

    def _run(self, command):
        self.m.run(command)

    def _get(self, name):
        return self.m.getvalue(name)

    def _close_matlab(self):
        if self.m:
            self.m.close()
        self.m = None

    @matlab
    def create_titles_vector(self):
        db = self.db
        db_ratings = db(db.ratings).select(db.ratings.ALL, distinct=db.ratings.imovie).sort(lambda x: x.imovie)
        titles = None
        if self.im:
            titles = list()
            for x in db_ratings:
                movie = x.imovie
                titles.append(movie.title)
        if titles:
            self._run("titles = cell({},1)".format(len(titles)))
            for i, title in enumerate(titles):
                if title is None:
                    title = 'None'
                title = title.replace("'", "''")
                self._run("titles{{{0}}}='{1}'".format(i+1, title))
            self._run("save('"+os.path.join(self.savepath, 'titles')+"', 'titles')")

    @matlab
    def create_features_vector(self):
        db = self.db
        db_features = db(db.movies_features).select(db.movies_features.ALL, distinct=db.movies_features.feature).sort(lambda x: x.feature)
        features_vector = list()
        for x in db_features:
            features_vector.append(x.feature.name)
        self._run("features = cell({},1)".format(len(features_vector)))
        for i, feature in enumerate(features_vector):
            feature_escaped = feature.replace("'", "''")
            self._run("features{{{0}}}='{1}'".format(i+1, feature_escaped))
        self._run("save('"+os.path.join(self.savepath, 'features')+"', 'features')")


    @matlab
    def create_matlab_matrices(self, type=None, force=False, *args, **vars):
        c_icm = True
        c_urm = True
        urm_filepath = os.path.join(self.savepath, 'urm.mat')
        icm_filepath = os.path.join(self.savepath, 'icm.mat')
        try:
            urm_date = datetime.datetime.fromtimestamp(os.path.getctime(urm_filepath))
        except OSError:
            urm_date = None
        try:
            icm_date = datetime.datetime.fromtimestamp(os.path.getctime(icm_filepath))
        except OSError:
            icm_date = None
        if type == 'urm':
            c_icm = False
        elif type == 'icm':
            c_urm = False
        if c_urm:
            filepath = os.path.join(self.savepath, 'urm.mat')
            if not urm_date or force:
                users, movies, ratings, urm_dimensions = self._create_urm()
                self._put('urm_users', users)
                self._put('urm_movies', movies)
                self._put('urm_ratings', ratings)
                self._put('urm_dimensions', urm_dimensions)
                self._run("urm = sparse(urm_users, urm_movies, urm_ratings, urm_dimensions(1), urm_dimensions(2))")
                self._run("save('"+os.path.join(self.savepath, 'urm')+"', 'urm')")
                self._run("clear")
        if c_icm:
            filepath = os.path.join(self.savepath, 'icm.mat')
            if not icm_date or force:
                icm_items, icm_features, icm_occurrencies, icm_dimensions = self._create_icm()
                self._put('icm_items', icm_items)
                self._put('icm_features', icm_features)
                self._put('icm_occurrencies', icm_occurrencies)
                self._put('icm_dimensions', icm_dimensions)
                self._run("icm = sparse(icm_items, icm_features, icm_occurrencies, icm_dimensions(1), icm_dimensions(2))")
                self._run("save('"+os.path.join(self.savepath, 'icm')+"', 'icm')")
                self._run("clear")


    def _create_urm(self, users=None, items=None, ratings=None):
        """Return the user rating matrix"""
        db = self.db
        db_ratings = db(db.ratings).select(db.ratings.ALL, distinct=True)
        users = [float(x.iuser) for x in db_ratings]
        movies = [float(x.imovie) for x in db_ratings]
        ratings = [float(x.rating) for x in db_ratings]
        users = numpy.array(users)
        movies = numpy.array(movies)
        ratings = numpy.array(ratings)
        max_user = db.ratings.iuser.max()
        max_movies = db.ratings.imovie.max()
        dimensions = [float(db().select(max_user).first()[max_user]), float(db().select(max_movies).first()[max_movies])]
        dimensions = numpy.array(dimensions)

        return users, movies, ratings, dimensions


    def _create_icm(self, items=None, metadata=None):
        """Returns the item content matrix"""
        db = self.db
        if not items and not metadata:
            entries = db(db.movies_features).select(db.movies_features.ALL, distinct=True)

        items = [float(x.movie.id) for x in entries]
        features = [float(x.feature.id) for x in entries]
        occurrencies = [float(x.times) for x in entries]
        max_movies = db.movies_features.movie.max()
        max_features = db.movies_features.feature.max()
        dimensions = numpy.array([float(db().select(max_movies).first()[max_movies]), float(db().select(max_features).first()[max_features])])
        return numpy.array(items), numpy.array(features), numpy.array(occurrencies), dimensions

    def create_userprofile(self, user):
        db = self.db
        entries = db(db.ratings.iuser==user).select(db.ratings.ALL, cacheable=True)
        ratings = [float(x.rating) for x in entries]
        movies = [float(x.imovie) for x in entries]
        max_movies = db.ratings.imovie.max()
        dimension = [float(db().select(max_movies).first()[max_movies])]

        # up = numpy.zeros((1,self.db.query(func.max(Item.id)).one()[0]))
        # for r in ratings:
        #     up[0][r.item.id-1] = r.rating
        return numpy.array(ratings), numpy.array(movies), numpy.array(dimension)

    @matlab
    def _create_model(self, alg, param=None, *args, **kwargs):
        self._run("load('"+os.path.join(self.savepath, 'urm.mat')+"')")
        self._run("load('"+os.path.join(self.savepath, 'icm.mat')+"')")
        self._run("param = struct()")
        if param:
            for k,v in param.iteritems():
                self._run("param."+str(k)+" = "+str(v))
        self._run("["+alg+"_model] = createModel_"+alg+"(urm, icm, param)")
        self._run("save('"+os.path.join(self.savepath, alg+'_model')+"', '"+alg+"_model')")

    def create_model(self, algname='AsySVD'):
        """Create a model and saves it the ALGORITHMS/saved directory"""
        #function [model] = createModel_ALGORITHM_NAME(URM,ICM,param)
        db = self.db
        alg = self._get_model_name(algname)
        self.create_matlab_matrices(force=True)
        self._create_model(alg)


    @matlab
    def _get_rec(self, algname, user, **param):
        """Return a recommendation using the matlab engine"""
        #function [recomList] = onLineRecom_ALGORITHM_NAME (userProfile, model,param)
        ratings, movies, dimension = self.create_userprofile(user)
        alg = self._get_model_name(algname)
        self._put('ratings', ratings)
        self._put('movies', movies)
        self._put('dimension', dimension)
        self._run("up = sparse(1, movies, ratings, 1, dimension(1))")
        self._run("param = struct()")
        for k,v in param.iteritems():
            self._run("param."+str(k)+" = "+str(v))
        self._run("load('"+os.path.join(self.savepath, alg+'_model')+"', '"+alg+"_model')")
        self._run("[rec] = onLineRecom_"+algname+"(up, "+alg+"_model, param)")
        return self._get("rec")

    def get_rec(self, algname, user, max=10, **param):
        """Wrapper aroung the real recommendation getter to set parameters"""
        if algname == 'AsySVD':
            param = dict(param, userToTest=user)

        rec = self._get_rec(algname, user, **param)
        rec = numpy.squeeze(rec)
        indexes = bottleneck.argpartsort(rec, rec.size-max, axis=0)[-max:]
        rec = [(rec[index], index) for index in indexes]
        rec.sort(reverse=True)
        return rec

    @classmethod
    def get_algnames(self):
        """Return a list of algorithms in the system"""
        algs = list()
        for root, dirs, files in os.walk(self.algopath):
            for f in files:
                if f.startswith('onLineRecom'):
                    algs.append(f[12:-2])
        algs.sort()
        return algs

    @classmethod
    def _get_model_name(self, algname=None):
        for root, dirs, files in os.walk(self.algopath):
            for f in files:
                if f.startswith('onLineRecom'):
                    if f[12:-2] == algname:
                        for mf in files:
                            if mf.startswith('createModel'):
                                return mf[12:-2]

        return None


    @classmethod
    def get_models_info(self):
        """Return a dict of algorithms in which there is a model created and the time the model was created"""
        algnames = self.get_algnames()
        algs = dict()
        for root, dirs, files in os.walk(self.savepath):
            for f in files:
                for algname in algnames:
                    if f[:-10] in self._get_model_name(algname) and f[:-10]!='':
                        algo =f[:-10]
                        path = os.path.join(root, f)
                        algs[algname] = datetime.datetime.fromtimestamp(os.path.getmtime(path))
        return algs

    @classmethod
    def get_matrices_info(cls):
        matrices = dict()
        for matrice in ALL_MATRICES:
            try:
                matrices[matrice] = datetime.datetime.fromtimestamp(os.path.getmtime(os.path.join(cls.savepath, matrice+'.mat')))
            except:
                matrices[matrice] = None
        return matrices

    @classmethod
    def get_matrices_path(cls):
        matrices = dict()
        for matrice in ALL_MATRICES:
            try:
                matrices[matrice] = os.path.join(cls.savepath, matrice+'.mat')
            except:
                matrices[matrice] = None
        return matrices

    @classmethod
    def delete_matrice(cls, matrice):
        matrices_path = cls.get_matrices_path()
        os.remove(matrices_path[matrice])
