from lxml import etree
import lxml.html
import os
import time
import urllib2
import urllib
import datetime
import time
import re
from lxml.html import parse
from metadata import MetadataGenerator

HERE = os.path.abspath(os.path.dirname(__file__))

MOVIE_IMAGES_PATH = os.path.join(HERE, '..','static','images','movies')
R_MOVIES_IMAGES_PATH = os.path.join('images', 'movies')
COVERS_PATH = os.path.join(MOVIE_IMAGES_PATH, 'covers')
POSTERS_PATH = os.path.join(MOVIE_IMAGES_PATH, 'posters')
R_POSTERS_PATH = os.path.join(R_MOVIES_IMAGES_PATH, 'posters')
UNKNOWN_POSTER_PATH = os.path.join('images', 'unknown_poster.jpg')
MOVIES_IN_THEATERS_URL="http://www.imdb.com/movies-in-theaters/"
COMING_SOON_URL="http://www.imdb.com/movies-coming-soon/"


IMDB_REVIEW_URL = 'http://www.imdb.com/title/tt{}/reviews'

userid_regxp = re.compile('.*/ur(\d+)/.*')
user_regxp = re.compile('^([\w\s-]+)(\((.*)\))?')
rate_regxp = re.compile('(\d*)\/(\d*)')
reviews_regxp = re.compile('^\n(\d*) reviews.*')

def review_url(id):
    if id is not None:
        return IMDB_REVIEW_URL.format(id)
    return None


IMDB_MOVIE_URL = 'http://www.imdb.com/title/tt{}/'

def movie_url(id):
    if id is not None:
        return IMDB_MOVIE_URL.format(id)
    return None

def _get_movies_ids_in_page(url):
       imdb_ids = list()
       page = urllib2.urlopen(url)
       data = lxml.html.parse(page)
       for a_tag in data.xpath("//h4[@itemprop='name']/a"):
           imdb_ids.append(a_tag.attrib.get('href')[9:-1])
       return imdb_ids
   
def get_movies_in_theaters():
    return _get_movies_ids_in_page(MOVIES_IN_THEATERS_URL)
   
def get_movies_coming_soon(period=None):
    url = COMING_SOON_URL
    if period:
        url+=period.strftime("%Y-%m")
    return _get_movies_ids_in_page(url)

def parse_review_url(url):
    i = 0
    users = {}
    return_rates = list()
    while True:
        if i > 0 and i > reviews_num/10:
            return (users, return_rates)
        ret_url = url+'?'+urllib.urlencode({'start':i*10})
        counter = 1
        while True:
            try:
                counter += 1
                tree = lxml.html.parse(ret_url)
                break
            except IOError:
                if counter >=10:
                    break
                time.sleep(100)
        if i == 0:
            try:
                td_review = tree.xpath('//div[@id="pagecontent"]//table/tr/td[@align="right"]')[0]
            except:
                return (users, return_rates)
            reviews_match = reviews_regxp.match(td_review.text)
            if reviews_match:
                reviews_num = int(reviews_match.group(1))
            else:
                reviews_num = 1
        try:
            contents = tree.xpath('//div[@id="tn15content"]//hr')
        except:
            continue
        for rev in contents[:-1]:
            p_rev = rev.getnext()
            rates = p_rev.xpath('img[@alt]')
            for r in rates:
                rate_match = rate_regxp.match(r.get('alt'))
                rate = float(rate_match.group(1))/float(rate_match.group(2))
                user = p_rev.xpath('a')[0]
                userid_rgxp = userid_regxp.match(user.get('href'))
                userid = int(userid_rgxp.group(1))
                try:
                    username_and_mail_rgxp = user_regxp.match(user.text)
                    username = username_and_mail_rgxp.group(1).rstrip()
                    email = username_and_mail_rgxp.group(3)
                except:
                    username = userid
                    email = None
                if userid not in users:
                    users[userid]=dict(username=username, email=email, imdb_id=userid)
                if rate:
                    return_rates.append((userid,rate))
        i += 1



class MediaRetriever(object):
    
    def __init__(self, movie_title, movie_imdb_id=None, tor=True):
        self.movie_title = movie_title
        self.movie_imdb_id = movie_imdb_id
        if not self.movie_imdb_id:
            self._guess_imdb_id()
        if tor:
            proxy = urllib2.ProxyHandler({'http': '127.0.0.1:8118'})
            self.opener = urllib2.build_opener(proxy)
        else:
            self.opener = urllib2.build_opener()
        self.opener.addheaders = [ ('User-Agent', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/12.04 Chromium/18.0.1025.168 Chrome/18.0.1025.168 Safari/535.19' )]

    def __create_request(self, url, params=None):
        req = urllib2.Request(url, params)
        return self.opener.open(req)

    def _guess_imdb_id(self):
        movie = self.movie_title
        first_page = parse(self.__create_request('http://www.imdb.com/find?', urllib.urlencode({'s':'tt', 'q':movie.encode('utf-8')})))
        second_page_url = first_page.xpath('//tr/td[3]/a')[0].attrib.get('href')
        self.movie_imdb_id = second_page_url[9:-1]

    def get_trailer(self):
        movie_title = self.movie_title
        counter = 1
        while True:
            try:
                page_search_list = parse(urllib2.urlopen('http://www.youtube.com/results?'+urllib.urlencode({'search_query': movie_title.encode('utf-8')+' trailer'})))
                break
            except urllib2.HTTPError:
                if counter >= 10:
                    return None
                counter += 1
                time.sleep(counter**2)
        try:
            movie_trailer = page_search_list.xpath("//ol[@id='search-results']//a")[0].attrib.get('href')
        except IndexError:
            trailer_source = None
        else:
            trailer_source = 'http://www.youtube.com'+movie_trailer
        return trailer_source

    def get_poster(self, download=True, force=False):
        imdb_id = self.movie_imdb_id
        genre = list()
        
        if self.has_poster() and not force:
            return os.path.join(R_POSTERS_PATH, str(imdb_id)+'.jpg')
        
        second_page = parse(self.__create_request(movie_url(imdb_id)))
        if second_page:
            try:
                poster_page_url = second_page.xpath("//td[@id='img_primary']/a")[0].attrib.get('href')
            except IndexError:
                poster_page_url = None
                poster_url = None
            if poster_page_url is not None:
                poster_page = parse(self.__create_request('http://www.imdb.com'+poster_page_url))
                try:
                    poster_url = poster_page.xpath("//div[@id='photo-container']/div[@id='canvas']//img[@id='primary-img']")[0].attrib.get('src')
                except IndexError:
                    poster_url = None
            if poster_url and download:
                print poster_url
                try:
                    f = self.__create_request(poster_url)
                except:
                    pass
                else:
                    path = os.path.join(POSTERS_PATH, str(imdb_id)+'.jpg')
                    with open(path, 'w') as local:
                        local.write(f.read())
                    poster_url = os.path.join(R_POSTERS_PATH, str(imdb_id)+'.jpg')
        
        if poster_url is None:
            poster_url = UNKNOWN_POSTER_PATH
        return poster_url

    def has_poster(self):
        imdb_id = self.movie_imdb_id
        return os.path.exists(os.path.join(POSTERS_PATH, str(imdb_id)+'.jpg'))

    
    
    
#    pprint(get_movies_in_theaters())
#    pprint(get_movies_coming_soon())
#    periods = list()
#    for x in range(1, 10):
#        periods.append(datetime.date(year=2012, month=x, day=1))
#    for period in periods:
#        pprint(get_movies_coming_soon(period))
#    
#pprint(get_info(get_top250_movies()))




class Importer(object):

    def __init__(self, db, im):
        self.db = db
        self.im = im
        
    def _add_user(self, user):
        self.db.users.update_or_insert(name=user.get('username'), imdb_id=user.get('imdb_id'), email=user.get('email'))

    def _add_movie(self, imdb_id):
        self.db.movies.update_or_insert(imdb_id=imdb_id)
    
    def _add_rating(self, user_imdb_id, movie_imdb_id, rating):
        db = self.db
        user = db(db.users.imdb_id==user_imdb_id).select().first()
        movie = db(db.movies.imdb_id==movie_imdb_id).select().first()
        db.ratings.update_or_insert(iuser=user, imovie=movie, rating=rating)

    def import_movies_from_imdb(self):
        '''
        Based on movie.imdb_id import a movie using imdbpy
        '''
        db = self.db
        im = self.im
        movies_with_ratings = db(db.ratings)._select(db.ratings.imovie, distinct=db.ratings.imovie)
        movies = db(db.movies.id.belongs(movies_with_ratings)&(db.movies.updated==None)).select()
        for movie in movies:
            print 'importing ', movie.title
            self._update_movie(movie)

    def import_posters(self, download=True, noposter=True):
        db = self.db
        query=(db.movies.id.belongs(db(db.ratings)._select(db.ratings.imovie, distinct=db.ratings.imovie)))
        if noposter:
            query &= (db.movies.poster==None)|(db.movies.poster.startswith('http'))
        for movie in db(query).select():
            mr = MediaRetriever(movie.title, movie.imdb_id)
            if not mr.has_poster():
                print 'processing ', movie.title 
                poster_url = mr.get_poster(download)
                print 'poster url ', poster_url
                movie.update_record(poster = poster_url)
                db.commit()

    def _get_canonical_name(self, name):
        splitted_name = name.split(' ')
        first_name = splitted_name[0].strip()
        last_name = ' '.join(splitted_name[1:]).strip()
        return dict(first_name=first_name, last_name=last_name)
    
    def get_info(self, movie_id):
        im = self.im
        movie = im.get_movie(movie_id)
        plot = movie.get('plot')
        title = movie.get('title')
        year = movie.get('year')
        genres = movie.get('genres',[])
        cast = list()
        for p in movie.get('cast', []):
            c_name = self._get_canonical_name(p.get('name'))
            c_name['role'] = 'actor'
            cast.append(c_name)
        for p in movie.get('director', []):
            d_name = self._get_canonical_name(p.get('name'))
            d_name['role'] = 'director'
            cast.append(d_name)
        return dict(title=title, plot=plot, year=year, genres=genres, cast=cast)
    
    def get_popular_movies(self, schedule_movie, *args, **kwargs):
        im = self.im
        for movie in im.get_top250_movies():
            schedule_movie(imdb_id=movie.getID(), reviews=True)
        for imdb_id in get_movies_in_theaters():
            schedule_movie(imdb_id=imdb_id, reviews=True)
        
        for year in range(2000, 2013):
            for month in range(01, 13):
                period = datetime.date(year=year, month=month, day=1)    
                for imdb_id in get_movies_coming_soon(period):
                    schedule_movie(imdb_id=imdb_id, reviews=True)
            
        return 
    
    def import_or_update_movie(self, id=None, imdb_id=None, reviews=False, metadata=True, *args, **kwargs):
        '''Given a milo id or imdb id import that movie into the database
        '''
        db = self.db
        if id:
            movie = db.movies[int(id)]
        elif imdb_id:
            movie = db(db.movies.imdb_id==imdb_id).select().first() or db.movies.insert(imdb_id=imdb_id)
        else:
            raise ValueError('you may specify id or imdb_id')
        self._update_movie(movie)
        if reviews:
            self._parse_reviews(movie)
        if metadata:
            self._add_metadata(movie)
        return True
    
    def _add_metadata(self, movie):
        generator = MetadataGenerator(self.db, self.im)
        generator.create_metadata(movie)
    
    def _update_movie(self, movie):
        '''Given a movie database instance, update it with data from imdb
        '''
        db = self.db
        im = self.im
        url = movie_url(movie.imdb_id)
        tree = lxml.html.parse(url)
        tree_counter = 1
        while True:
            try:
                h1_title = tree.xpath('//h1[@itemprop="name"]')
                break
            except AssertionError:
                tree_counter +=1
                if tree_counter > 10:
                    continue
                time.sleep(tree_counter**2)
        if not h1_title:
            #cannot retrieve movie title
            return
        title = h1_title[0].text.strip()
        imdb_movie = im.get_movie(movie.imdb_id)
        if title==imdb_movie.get('title'):
            mr = MediaRetriever(title, movie.imdb_id)
            info = self.get_info(movie.imdb_id)
            plot = info.get('plot')
            if plot:
                plot = plot[0].encode('utf-8')
            year = info.get('year')
         
            poster_url = mr.get_poster()
            
            movie.update_record(title = title,
                                plot = plot,
                                poster = poster_url,
                                trailer = mr.get_trailer(),
                                year = year,
                                updated = datetime.datetime.now()
                                )
            #do genre
            for genre in info.get('genres', []):
                genre_id = db.genres.update_or_insert(name=genre) or db(db.genres.name==genre).select(db.genres.id).first()
                db.movies_genres.update_or_insert(movie=movie, genre=genre_id)
                
            #do cast
            for person in info.get('cast'):
                first_name = person.get('first_name')
                last_name = person.get('last_name')
                role = person.get('role')
                person_id = db.persons.update_or_insert(first_name=first_name,
                                                        last_name=last_name
                                                        )
                if not person_id:
                    person_id = db((db.persons.first_name==first_name)&(db.persons.last_name==last_name)).select(db.persons.id).first()
                
                role_id = db.roles.update_or_insert(name=role)
                if not role_id:
                    role_id = db(db.roles.name==role).select(db.roles.id).first()
                db.persons_in_movies.update_or_insert(movie=movie, person=person_id, role=role_id)
            
            db.commit()
            
    
    def _parse_reviews(self, movie):
        '''Given a movie instance add reviews to database if the don't exist
        '''
        db = self.db
        im = self.im
        url = review_url(movie.imdb_id)
        (users, ratings) = parse_review_url(url)
        for user_imdb_id, user in users.iteritems():
            self._add_user(user)
        for (user_imdb_id, rating) in ratings:
            self._add_rating(user_imdb_id, movie.imdb_id, rating)
        db.commit()
        return True
        
