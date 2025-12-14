# import packages
import polars as pl
import pandas as pd
import numpy as np
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import os
import nltk
from nltk.corpus import stopwords
from bertopic import BERTopic
from sklearn.feature_extraction.text import CountVectorizer

path_01 = "../data/bookchapter_data.csv"
path_savemodel = "../models/model_da_16may25"

# read and transform data
df = pl.read_csv(path_01, infer_schema=0, try_parse_dates=True)
df = df.filter(pl.col("country") == "denmark")
df = df.sample(5000)

text_art = df.select(pl.col("content").cast(pl.Utf8)).to_series().to_list()

# Download the stopwords data (you only need to do this once)
nltk.download("stopwords")
danish_stopwords = set(stopwords.words("danish"))

# You can add any additional stopwords to this list if needed
additional_stopwords = set(["og", "eller", "men"])  # Example of additional words
my_list_of_stopwords = list(danish_stopwords.union(additional_stopwords))

# Create the vectorizer with Danish stopwords
vec_model = CountVectorizer(stop_words=my_list_of_stopwords)

# model traning
sm_da = SentenceTransformer("KennethTM/MiniLM-L6-danish-encoder")  # , device="cuda")
model = BERTopic(embedding_model=sm_da, vectorizer_model=vec_model, verbose=True)
print("transformer model succesfully loaded")
# With probabilities
topics, probs = model.fit_transform(text_art)

# Save model
model.save(path_savemodel)
