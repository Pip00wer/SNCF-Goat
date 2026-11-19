import pandas as pd 
import numpy as np 



"""
Fichier de scoring pour le projet SNCF.
Contient les fonctions permettant de calculer différents scores de performance des lignes.

Ces scores seront une note entre 0 et 100. 

0 : Rien ne va 
100 : Parfait, aucun retard ni annulation
"""


# Calcul du score 1 : proportion de trajets effectués sans retard supérieur à 15 minutes.
def score_1 (df) : 

    df["score_1"] =((df["nb_trajets"] - df["nb_>15min"]) / df["nb_prevues"]*100).round(3)
    
    return df


# Calcul du score 2 : pondération des retards selon leur gravité et des annulations.
def score_2 (df,poids_gravité) :
    df["nb_15-30"] = df["nb_>15min"] - df["nb_>30min"]
    df["nb_30-60"] = df["nb_>30min"] - df["nb_>60min"] 

   
    df["score_2"] = ((
        1 - ( 
            df["nb_15-30"] * poids_gravité["15_30"] +
            df["nb_30-60"] * poids_gravité["30_60"] +
            df["nb_>60min"] * poids_gravité["60"] +
            df["nb_annules"] * poids_gravité["annules"]
        )/df["nb_prevues"]
    )*100).round(3)

    return df


# Calcul du score 3 : Retard moyen relatif au temps de trajet moyen et annulation des trajets
def score_3 ( df ):

    df["score_3"] = 100*(
        (1 - (df["nb_annules"] / df["nb_prevues"]))*
        (1-(df["retard_moy_all"] / df["moy_durée"]))
    ).round(3)

    return df

def all_scores_and_sort ( df, poids_gravité, sort_by="score_1"):
    df = score_1(df)
    df = score_2(df, poids_gravité)
    df = score_3(df)
    return df.sort_values(by=sort_by, ascending=False)

