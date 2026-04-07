import pandas as pd
import numpy as np
import ast
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.stem.porter import PorterStemmer
import pickle

movies = pd.read_csv('tmdb_5000_movies.csv')
credits = pd.read_csv('tmdb_5000_credits.csv')
movies = movies.merge(credits, on='title')

'''
we will be using :
genre,id,title,overview,cast,crew
'''
movies = movies[['movie_id', 'title', 'overview', 'genres', 'keywords', 'cast', 'crew']]
movies.dropna(inplace=True)
#checking for duplicate data

#print(movies.duplicated().sum()) # no duplicate movies found

#print(movies.iloc[0].genres)
# [{"id": 28, "name": "Action"}, {"id": 12, "name": "Adventure"}, {"id": 14, "name": "Fantasy"}, {"id": 878, "name": "Science Fiction"}]
#we want in this format:
#   ['Action','Adventure','Fantasy','Science Fiction']
#we will be creating a helper function 'convert()'

def convert(obj):
    L = []
    for i in ast.literal_eval(obj):
        L.append(i['name'])
    return L

def convert3(obj):
    L = []
    counter = 0
    for i in ast.literal_eval(obj):
        if counter != 3:
            L.append(i['name'])
            counter += 1
        else:
            break
    return L

def fetch_director(obj):
    L = []
    for i in ast.literal_eval(obj):
        if i['job'] == 'Director':
            L.append(i['name'])
            break
    return L

movies['genres'] = movies['genres'].apply(convert)
movies['keywords'] = movies['keywords'].apply(convert)
movies['cast'] = movies['cast'].apply(convert3)
movies['crew'] = movies['crew'].apply(fetch_director)
movies['overview'] = movies['overview'].apply(lambda x: x.split())
# now we will be concatinating the lists to have one big list.
# then this list will be converted into a string, so a big paragraph will be formed which will be our tags col
# a transformatio on the last 4 col will be applied --> transformation: all the space between the words are to be removed.
'''
this is impt because if the words are kept different then each word is a different entity so 2 tags pointing the same thing
eg: sam worthigton, is to be converted to 'samwothigton'
now the prob arises when there's another name 'sam mendes' so even it will have 2 tags 'sam' 'mendes'
i wanted to watch 'Sam Wothigton' movie but recommender might get confuse between the two.
therefore by removing the spaces 'samwothigton' will now be one single entity.
'''
movies['genres'] = movies['genres'].apply(lambda x: [i.replace(" ", "") for i in x])
movies['keywords'] = movies['keywords'].apply(lambda x: [i.replace(" ", "") for i in x])
movies['cast'] = movies['cast'].apply(lambda x: [i.replace(" ", "") for i in x])
movies['crew'] = movies['crew'].apply(lambda x: [i.replace(" ", "") for i in x])

movies['tag'] = movies['overview'] + movies['genres'] + movies['keywords'] + movies['cast'] + movies['crew']
new_df = movies[['movie_id', 'title', 'tag']].copy()
new_df['tag'] = new_df['tag'].apply(lambda x: " ".join(x))
new_df['tag'] = new_df['tag'].apply(lambda x: x.lower())

ps = PorterStemmer()
def stem(text):
    y = []
    for i in text.split():
        y.append(ps.stem(i))
    return " ".join(y)

new_df['tag'] = new_df['tag'].apply(stem)

cv = CountVectorizer(max_features=5000, stop_words='english')
vectors = cv.fit_transform(new_df['tag']).toarray()
# TEXT VECTORISATION
# now we have to calculate the similarity score b/w the 2 movie tags
'''
one way to do is to compare/count the number of same words ---but not the best way
that's why we need text vectorisation.
-- converting every movie's tag into vector so now every movie is a vector
-- so when recommending movies the vectors near to the selected vector movie will be recommended
-- technique we will be using: BAG OF WORDS (SIMPLEST)
-- Other techniques are: TF IDF, WORD TO VEC
-- we do not consider stop words in text vectorisation
-- here scikit learn will be used as it has countvectoriser
'''

similarity = cosine_similarity(vectors)
#print(similarity)
#its shape is 4806,4806
#we have to find the index of the movie int he data now through this index we will enter into similarity matrix
#to know the index of a movie:
#print(new_df[new_df['title'] == 'Batman Begins'].index[0])
#SINCE WE ARE FACING THE ISSUE OF LARGER FILE SIZE WE WILL BE ONLY TOP 10 SIMILAR MOVIE

# Save only top 10 similar movies per movie to reduce file size
#KNN (K-NEAREST NEIGHBOURS)
top_k = 10
similarity_dict = {}

for idx in range(len(similarity)):
    sim_scores = list(enumerate(similarity[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_k+1]
    similarity_dict[idx] = [(i[0], np.float32(i[1])) for i in sim_scores]
'''
we have to sort the array but while sortiing the array we are loosing the index value
sorted(similarity[0],reverse = True)
to prevent that from happening we will use 'enumerate' in the form of a list
therefore, sorted(list(enumerate(similarity[0])),reverse = True)     now sorting is done, but based on index pos i.ewe are getting the last movie as first pos^n. To solve this:
sorted(list(enumerate(similarity[0])),reverse = True,key = lambda x:x[1])
to decide how many movies to be recommended, use:
sorted(list(enumerate(similarity[0])),reverse = True,key = lambda x:x[1])[1:6]
'''
# Building genre-to-index map
movie_genre = {}
for idx, row in movies.reset_index(drop=True).iterrows():
    for genre in row['genres']:
        movie_genre.setdefault(genre, []).append(idx)

pickle.dump(new_df.to_dict(), open('movies_dict.pkl', 'wb'))
pickle.dump(similarity_dict, open('similarity.pkl', 'wb'))
pickle.dump(movie_genre, open('genre_map.pkl', 'wb'))

print("✅ Backend processing complete. Files saved.")