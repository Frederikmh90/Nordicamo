import polars as pl
import pandas as pd
import numpy as np
from sentence_transformers import SentenceTransformer
import umap.umap_ as umap
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import hdbscan
import plotly.express as px
import os
from scipy import stats
import matplotlib.pyplot as plt
from datetime import datetime

###############################
# CONFIGURATION PARAMETERS
###############################

# Data selection
DATA_PATH = "../data/bookchapter_data.csv"
SAMPLE_SIZE = 1000  # Set to None to use all data
LOAD_SAVED_EMBEDDINGS = False  # Set to True to load previously saved embeddings

# Country and time filters
COUNTRIES = ["denmark", "sweden", "finland"]  # Set to specific countries or keep all
START_DATE = "2010-01-01"  # Set to None to include all data from the beginning
END_DATE = None  # Set to None to include all data until the end

# Embedding model
# Options: 'nomic', 'e5', 'bge'
MODEL_TYPE = "bge"

# Model configurations for different types
MODEL_CONFIGS = {
    "nomic": {
        "name": "nomic-ai/nomic-embed-text-v2-moe",
        "prompt_prefix": "search_document: ",
        "normalize": False,
    },
    "e5": {
        "name": "intfloat/multilingual-e5-base",
        "prompt_prefix": "",
        "normalize": True,
    },
    "bge": {
        "name": "BAAI/bge-m3",
        "prompt_prefix": "Represent this document for retrieval: ",
        "normalize": True,
    },
}

BATCH_SIZE = 16

# Dimensionality reduction
# Options: 'umap', 'tsne', 'pca'
PROJECTION_TECHNIQUE = "umap"

# UMAP parameters
UMAP_PARAMS = {
    "n_neighbors": 30,  # Higher for more global structure (try 15-100)
    "min_dist": 0.05,  # Lower for tighter clusters (try 0.01-0.5)
    "metric": "cosine",  # Options: 'cosine', 'euclidean', 'correlation'
    "random_state": 42,
}

# t-SNE parameters
TSNE_PARAMS = {
    "perplexity": 30,  # Balance between local and global structure (try 5-50)
    "n_iter": 1000,  # More iterations for better convergence
    "metric": "cosine",  # Options: 'cosine', 'euclidean'
    "random_state": 42,
}

# PCA parameters
PCA_PARAMS = {"n_components": 2, "random_state": 42}

# Clustering parameters
CLUSTER_MIN_SIZE = 10
CLUSTER_MIN_SAMPLES = 5

# Visualization
TITLE_PREFIX = "News Embedding Space"
SHOW_DOMAIN_LABELS = True

# Language-specific processing
EMBED_BY_LANGUAGE = False  # Set to True to embed each language separately
LANGUAGE_ALIGNMENT = True  # Attempt to align embeddings when EMBED_BY_LANGUAGE is True

###############################
# DATA LOADING AND FILTERING
###############################

# 1. Load and filter data
print("Loading and filtering data...")
df = pl.read_csv(DATA_PATH)

# Sample if specified
if SAMPLE_SIZE is not None:
    df = df.sample(SAMPLE_SIZE, seed=42)

# Apply country filter if specified
if COUNTRIES and not (
    len(COUNTRIES) == 3 and set(COUNTRIES) == set(["denmark", "sweden", "finland"])
):
    df = df.filter(pl.col("country").is_in(COUNTRIES))
    country_str = ", ".join(COUNTRIES)
    print(f"Filtered to countries: {country_str}")

# Apply date filters if specified
if START_DATE or END_DATE:
    df = df.with_columns(pl.col("date").str.to_datetime())

    filters = []
    if START_DATE:
        start_date = pl.lit(START_DATE).str.to_datetime()
        filters.append(pl.col("date") >= start_date)
        print(f"Filtered to dates after: {START_DATE}")

    if END_DATE:
        end_date = pl.lit(END_DATE).str.to_datetime()
        filters.append(pl.col("date") <= end_date)
        print(f"Filtered to dates before: {END_DATE}")

    if filters:
        combined_filter = filters[0]
        for f in filters[1:]:
            combined_filter = combined_filter & f
        df = df.filter(combined_filter)

# Filter to only rows with non-empty content
filtered_df = df.filter(
    df["content"].is_not_null() & (df["content"].str.strip_chars().str.len_chars() > 0)
)
print(f"After all filtering: {len(filtered_df)} documents")

# Create output directory
os.makedirs("../reports/embedding_space", exist_ok=True)

# Get model configuration before language processing
if MODEL_TYPE not in MODEL_CONFIGS:
    raise ValueError(
        f"Unknown model type: {MODEL_TYPE}. Choose from: {list(MODEL_CONFIGS.keys())}"
    )

model_config = MODEL_CONFIGS[MODEL_TYPE]
model_name = model_config["name"]
prompt_prefix = model_config["prompt_prefix"]
normalize = model_config["normalize"]

# Create embeddings file name based on model type and parameters
embeddings_file = f"../reports/embedding_space/document_embeddings_{MODEL_TYPE}_{SAMPLE_SIZE or 'full'}.npy"

# Load the model now so it's available for both embedding approaches
model = SentenceTransformer(model_name, trust_remote_code=True)
print(f"Loaded model: {model_name}")
print(f"Prompt prefix: {prompt_prefix or 'None'}")
print(f"Normalizing embeddings: {normalize}")

###############################
# LANGUAGE FILTERING
###############################

# Save the full filtered dataset for visualization
full_filtered_df = filtered_df.clone()

# Process by language if specified
embeddings_all = None
if EMBED_BY_LANGUAGE:
    print("\nProcessing languages separately:")
    language_map = {"denmark": "Danish", "sweden": "Swedish", "finland": "Finnish"}
    all_embeddings = []

    # Process each language
    for country, language in language_map.items():
        if country in COUNTRIES or (
            COUNTRIES
            and len(COUNTRIES) == 3
            and set(COUNTRIES) == set(["denmark", "sweden", "finland"])
        ):
            # Filter to only this country
            lang_df = full_filtered_df.filter(pl.col("country") == country)
            lang_texts = lang_df["content"].to_list()

            if not lang_texts:
                print(f"  - {language}: No texts found, skipping...")
                continue

            print(f"  - {language}: Processing {len(lang_texts)} texts...")

            # Create embeddings file name based on model type and language
            lang_embeddings_file = f"../reports/embedding_space/document_embeddings_{MODEL_TYPE}_{country}_{SAMPLE_SIZE or 'full'}.npy"

            if LOAD_SAVED_EMBEDDINGS and os.path.exists(lang_embeddings_file):
                print(f"    Loading saved {language} embeddings...")
                lang_embeddings = np.load(lang_embeddings_file)
                if len(lang_embeddings) != len(lang_texts):
                    print(
                        f"    WARNING: Saved embeddings count ({len(lang_embeddings)}) doesn't match filtered {language} texts ({len(lang_texts)})"
                    )
                    lang_embeddings = None
            else:
                lang_embeddings = None

            if lang_embeddings is None:
                print(f"    Generating {language} embeddings using {model_name}...")

                # Process texts according to model requirements
                if prompt_prefix:
                    processed_texts = [f"{prompt_prefix}{text}" for text in lang_texts]
                else:
                    processed_texts = lang_texts

                # Encode texts
                lang_embeddings = model.encode(
                    processed_texts,
                    show_progress_bar=True,
                    batch_size=BATCH_SIZE,
                    normalize_embeddings=normalize,
                )
                # Save language-specific embeddings
                np.save(lang_embeddings_file, lang_embeddings)

            # Store language ID with each embedding
            lang_id = list(language_map.keys()).index(country)
            lang_embeddings_with_id = [(lang_id, emb) for emb in lang_embeddings]
            all_embeddings.extend(lang_embeddings_with_id)

        # Sort by language ID to maintain order
        all_embeddings.sort(key=lambda x: x[0])

        # Extract just the embeddings and convert back to numpy array
        embeddings_all = np.array([emb for _, emb in all_embeddings])

        # Update filtered_df to match our new combined dataset
        # We'll keep track of which language each embedding belongs to in the clustering phase
        lang_countries = []
        for lang_id, _ in all_embeddings:
            lang_country = list(language_map.keys())[lang_id]
            lang_countries.append(lang_country)

        # Use embeddings_all for further processing
        filtered_df = full_filtered_df.filter(pl.col("country").is_in(lang_countries))
        print(f"Combined embeddings: {embeddings_all.shape}")

###############################
# EMBEDDING GENERATION
###############################

# 2. Generate or load embeddings
if not EMBED_BY_LANGUAGE:  # Only do this if we're not processing by language
    if LOAD_SAVED_EMBEDDINGS and os.path.exists(embeddings_file):
        print(f"Loading saved embeddings for {model_name}...")
        embeddings = np.load(embeddings_file)
        if len(embeddings) != len(filtered_df):
            print(
                f"WARNING: Number of saved embeddings ({len(embeddings)}) doesn't match filtered data ({len(filtered_df)})."
            )
            print("Regenerating embeddings...")
            LOAD_SAVED_EMBEDDINGS = False

    if not LOAD_SAVED_EMBEDDINGS:
        texts = filtered_df["content"].to_list()
        print(f"Generating embeddings using {model_name}...")

        # Process texts according to model requirements
        if prompt_prefix:
            processed_texts = [f"{prompt_prefix}{text}" for text in texts]
        else:
            processed_texts = texts

        # Encode texts
        embeddings = model.encode(
            processed_texts,
            show_progress_bar=True,
            batch_size=BATCH_SIZE,
            normalize_embeddings=normalize,
        )
        # Save for future use
        np.save(embeddings_file, embeddings)
        print(f"Saved embeddings for {model_name} to {embeddings_file}")
else:
    # Use the pre-computed embeddings from the language processing section
    embeddings = embeddings_all

###############################
# OUTLIER DETECTION
###############################

# 3. Detect outliers in embedding space
print("Detecting outliers...")

# Method 1: Statistical outlier detection (Z-score based)
mean_embedding = np.mean(embeddings, axis=0)
distances = np.linalg.norm(embeddings - mean_embedding, axis=1)
z_scores = stats.zscore(distances)
outliers_z = np.abs(z_scores) > 3
print(
    f"Z-score method identified {np.sum(outliers_z)} outliers out of {len(embeddings)} embeddings"
)

# Method 2: IQR-based outlier detection
q1, q3 = np.percentile(distances, [25, 75])
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr
outliers_iqr = (distances < lower_bound) | (distances > upper_bound)
print(
    f"IQR method identified {np.sum(outliers_iqr)} outliers out of {len(embeddings)} embeddings"
)

# Create non-outlier mask (combining both methods)
non_outliers = ~(outliers_z | outliers_iqr)

# Ensure we have at least some non-outliers to work with
if np.sum(non_outliers) < 10:
    print(
        "Warning: Very few non-outliers detected. Using all points for model fitting."
    )
    non_outliers = np.ones(len(embeddings), dtype=bool)

###############################
# DIMENSIONALITY REDUCTION
###############################

# 4. Reduce dimensionality based on selected technique
print(f"Reducing dimensions using {PROJECTION_TECHNIQUE.upper()}...")

# Common data structures to store projections
embedding_2d_all = None  # All data
embedding_2d_clean = None  # Using model fit on clean data
embedding_2d_robust = None  # Using robust parameters

if PROJECTION_TECHNIQUE == "umap":
    # Version 1: All points with standard parameters
    reducer_all = umap.UMAP(
        n_neighbors=15, min_dist=0.1, metric="cosine", random_state=42
    )
    embedding_2d_all = reducer_all.fit_transform(embeddings)

    # Version 2: Without outliers for better model fitting
    reducer_clean = umap.UMAP(
        n_neighbors=15, min_dist=0.1, metric="cosine", random_state=42
    )
    embedding_2d_clean_model = reducer_clean.fit_transform(embeddings[non_outliers])

    # Now transform all points using the cleaner model
    embedding_2d_clean = np.zeros((len(embeddings), 2))
    embedding_2d_clean[non_outliers] = embedding_2d_clean_model
    # Project outliers separately
    if np.sum(~non_outliers) > 0:
        try:
            embedding_2d_clean[~non_outliers] = reducer_clean.transform(
                embeddings[~non_outliers]
            )
        except Exception as e:
            print(f"Warning: Error projecting outliers: {e}")
            embedding_2d_clean[~non_outliers] = embedding_2d_all[~non_outliers]

    # Version 3: Use parameter tuning for robustness
    reducer_robust = umap.UMAP(**UMAP_PARAMS)
    embedding_2d_robust = reducer_robust.fit_transform(embeddings)

    # Save UMAP model for future use
    try:
        import joblib

        umap_model_file = f"../reports/embedding_space/umap_reducer_{MODEL_TYPE}.joblib"
        joblib.dump(reducer_robust, umap_model_file)
        print(f"Saved UMAP reducer model to {umap_model_file}")
    except ImportError:
        print("Could not save UMAP reducer (joblib not available)")

elif PROJECTION_TECHNIQUE == "tsne":
    # t-SNE often gives better local structure for text data
    print("Using t-SNE (this may take a while)...")

    # Version 1: All points with standard parameters
    tsne_standard = TSNE(n_components=2, random_state=42)
    embedding_2d_all = tsne_standard.fit_transform(embeddings)

    # Version 2: Run on non-outliers with standard parameters
    tsne_clean = TSNE(n_components=2, random_state=42)
    embedding_2d_clean = tsne_clean.fit_transform(embeddings)

    # Version 3: With custom parameters for robustness
    tsne_robust = TSNE(**TSNE_PARAMS)
    embedding_2d_robust = tsne_robust.fit_transform(embeddings)

elif PROJECTION_TECHNIQUE == "pca":
    # PCA is faster but may capture less semantic structure
    print("Using PCA (faster but may be less semantically meaningful)...")

    # Version 1: Standard PCA
    pca_standard = PCA(n_components=2, random_state=42)
    embedding_2d_all = pca_standard.fit_transform(embeddings)

    # For PCA, outlier handling doesn't really make sense since it's a linear method
    embedding_2d_clean = embedding_2d_all.copy()

    # Version 3: With any custom parameters
    pca_robust = PCA(**PCA_PARAMS)
    embedding_2d_robust = pca_robust.fit_transform(embeddings)

else:
    raise ValueError(f"Unknown projection technique: {PROJECTION_TECHNIQUE}")

###############################
# CLUSTERING
###############################

# 5. Clustering (HDBSCAN)
print("Clustering with HDBSCAN...")
clusterer = hdbscan.HDBSCAN(
    min_cluster_size=CLUSTER_MIN_SIZE,
    min_samples=CLUSTER_MIN_SAMPLES,
    metric="euclidean",
)
labels = clusterer.fit_predict(embedding_2d_robust)

###############################
# VISUALIZATION
###############################

# 6. Prepare DataFrames and visualize
print("Creating visualizations...")

# Create technique-specific suffix for filenames
technique_suffix = f"{MODEL_TYPE}_{PROJECTION_TECHNIQUE.lower()}"
if EMBED_BY_LANGUAGE:
    technique_suffix += "_multilingual"
if COUNTRIES and not (
    len(COUNTRIES) == 3 and set(COUNTRIES) == set(["denmark", "sweden", "finland"])
):
    technique_suffix += f"_{'-'.join(COUNTRIES)}"
if START_DATE:
    technique_suffix += f"_from{START_DATE.replace('-', '')}"
if END_DATE:
    technique_suffix += f"_to{END_DATE.replace('-', '')}"

# Create main DataFrame for visualization
df_vis = pd.DataFrame(
    {
        "x": embedding_2d_robust[:, 0],
        "y": embedding_2d_robust[:, 1],
        "label": labels,
        "domain": filtered_df["domain"].to_list(),
        "country": filtered_df["country"].to_list(),
        "is_outlier": ~non_outliers,
    }
)

# Add date information if available
if "date" in filtered_df.columns:
    df_vis["date"] = filtered_df["date"].to_list()

# Create title with selected parameters
title_suffix = f"({MODEL_TYPE.upper()}, {PROJECTION_TECHNIQUE.upper()}"
if EMBED_BY_LANGUAGE:
    title_suffix += ", Multi-lingual"
if COUNTRIES and not (
    len(COUNTRIES) == 3 and set(COUNTRIES) == set(["denmark", "sweden", "finland"])
):
    title_suffix += f", Countries: {', '.join(COUNTRIES)}"
if START_DATE or END_DATE:
    date_range = []
    if START_DATE:
        date_range.append(f"From: {START_DATE}")
    if END_DATE:
        date_range.append(f"To: {END_DATE}")
    title_suffix += f", {' '.join(date_range)}"
title_suffix += ")"

# Visualization 1: Robust visualization with outliers marked
fig1 = px.scatter(
    df_vis,
    x="x",
    y="y",
    color="label",
    symbol="is_outlier",
    hover_data=["domain", "country"] + (["date"] if "date" in df_vis.columns else []),
    title=f"{TITLE_PREFIX} - Outliers Marked {title_suffix}",
    width=1200,
    height=800,
)

# Visualization 2: Filtered view (outliers removed)
fig2 = px.scatter(
    df_vis[~df_vis["is_outlier"]],
    x="x",
    y="y",
    color="label",
    hover_data=["domain", "country"] + (["date"] if "date" in df_vis.columns else []),
    title=f"{TITLE_PREFIX} - Outliers Removed {title_suffix}",
    width=1200,
    height=800,
)

# Visualization 3: Country-based view
fig3 = px.scatter(
    df_vis[~df_vis["is_outlier"]],
    x="x",
    y="y",
    color="country",
    hover_data=["domain", "label"] + (["date"] if "date" in df_vis.columns else []),
    title=f"{TITLE_PREFIX} by Country {title_suffix}",
    width=1200,
    height=800,
)

# Add domain labels if specified
if SHOW_DOMAIN_LABELS:
    # Calculate mean positions for domains (excluding outliers)
    mean_positions = (
        df_vis[~df_vis["is_outlier"]].groupby("domain")[["x", "y"]].mean().reset_index()
    )

    # Add labels to all three visualizations
    for _, row in mean_positions.iterrows():
        for fig in [fig1, fig2, fig3]:
            fig.add_annotation(
                x=row["x"],
                y=row["y"],
                text=row["domain"],
                showarrow=False,
                font=dict(size=10, color="black"),
                opacity=0.7,
            )

# Save visualizations with technique-specific filenames
fig1.write_html(
    f"../reports/embedding_space/news_embedding_space_with_outliers_{technique_suffix}.html"
)
fig2.write_html(
    f"../reports/embedding_space/news_embedding_space_no_outliers_{technique_suffix}.html"
)
fig3.write_html(
    f"../reports/embedding_space/news_embedding_space_by_country_{technique_suffix}.html"
)

# Save the data
df_vis.to_csv(
    f"../reports/embedding_space/news_embedding_space_{technique_suffix}.csv",
    index=False,
)

# Information about what was saved
print("\nCreated visualizations:")
print(
    f"1. With outliers marked: news_embedding_space_with_outliers_{technique_suffix}.html"
)
print(
    f"2. With outliers removed: news_embedding_space_no_outliers_{technique_suffix}.html"
)
print(f"3. Colored by country: news_embedding_space_by_country_{technique_suffix}.html")
print(f"All saved to ../reports/embedding_space/")

# Configuration summary
print("\nUsed configuration:")
print(f"- Model: {model_name}")
print(f"- Embed by language: {EMBED_BY_LANGUAGE}")
print(f"- Projection Technique: {PROJECTION_TECHNIQUE}")
print(f"- Sample Size: {SAMPLE_SIZE if SAMPLE_SIZE else 'All data'}")
if PROJECTION_TECHNIQUE == "umap":
    print(
        f"- UMAP Parameters: n_neighbors={UMAP_PARAMS['n_neighbors']}, min_dist={UMAP_PARAMS['min_dist']}, metric={UMAP_PARAMS['metric']}"
    )
elif PROJECTION_TECHNIQUE == "tsne":
    print(
        f"- t-SNE Parameters: perplexity={TSNE_PARAMS['perplexity']}, n_iter={TSNE_PARAMS['n_iter']}, metric={TSNE_PARAMS['metric']}"
    )
print(f"- Countries: {', '.join(COUNTRIES) if COUNTRIES else 'All'}")
print(f"- Date Range: {START_DATE or 'earliest'} to {END_DATE or 'latest'}")

print(
    "\nTo experiment with different settings, edit the configuration parameters at the top of the script."
)
