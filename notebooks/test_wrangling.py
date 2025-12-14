import polars as pl

df = pl.read_csv("../data/NAMO_2025_09.csv")

print(df.head())

df.columns

len(df)
