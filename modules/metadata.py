import nltk
from nltk.corpus import brown
brown_tagged = brown.tagged_sents()
tagger = nltk.UnigramTagger(brown_tagged)


def tag(text):
        '''return a list of (keyword, type, occurrences) after tagging the text
        '''
        def accumulate(l):
            for x in set(l):
                counter = 0
                for y in l:
                    if x[0] == y[0]:
                        counter += 1
                else:
                    yield x[0], x[1], counter

        tagged = [(x[0], 'NP' if x[1].find('NP') >= 0 else 'NN' if x[1].startswith('NN') else 'VV') for x in tagger.tag(text.split()) if x[1] is not None and (x[1].startswith('N') or x[1].startswith('V'))]
        
        return list((accumulate(tagged)))


class MetadataGenerator(object):
    def __init__(self, db, im):
        self.db = db
        self.im = im
    
    def _add_feature(self, movie, feature):
        '''adds a feature which is a tuple (keyword, type, occurrencies) to db
        '''
        db_f = self.db.features.update_or_insert(name=feature[0], type=feature[1])
        if not db_f:
            db_f = self.db(self.db.features.name == feature[0]).select().first()
        self.db.movies_features.update_or_insert(movie = movie, feature=db_f, times=feature[2])
        self.db.commit()

    
    def create_metadata(self):
        db = self.db
        im = self.im
        items = db(db.movies.id.belongs(db(db.ratings)._select(db.ratings.imovie, distinct=True))).select(db.movies.ALL, distinct=True)
        for movie in items:
            m = im.get_movie(movie.imdb_id)
            features = []
            plot = m.get('plot')
            if plot:
                plot = plot[0]
                tagged = tag(plot)
                for fea_tag in tagged:
                    self._add_feature(movie, fea_tag)                
            im.update(m, 'keywords')
            keywords = m.get('keywords')
            if keywords:
                for keyword in keywords:
                    self._add_feature(movie, (keyword, 'keyword', 1))
            