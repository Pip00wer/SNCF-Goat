

"""
Fichier de prétraitement pour le projet SNCF.
Contient les fonctions permettant de charger, nettoyer et préparer les données pour l'analyse.
"""


import pandas as pd 
import numpy as np 



def get_data(file_path):
    return pd.read_csv(file_path, sep=';')


def drop_columns(df, cols_to_drop):
    return df.drop(columns=cols_to_drop)


def rename_columns(df, columns_mapping):
    return df.rename(columns=columns_mapping)


def uniforme_gare(df):
    df["départ"] = df["départ"].str.strip().str.upper()
    df["arrivée"] = df["arrivée"].str.strip().str.upper()
    return df

def get_data_and_preprocess(filepath, cols_to_drop, columns_mapping):
    df = get_data(filepath)
    df = drop_columns(df,cols_to_drop)
    df = rename_columns(df, columns_mapping)
    df = uniforme_gare(df)
    df["mois"] = pd.to_datetime(df["date"], format="%Y-%m")
    df["nb_trajets"] = df["nb_prevues"] - df["nb_annules"]
    return df