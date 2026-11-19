
from sncf_project.preprocessing import get_data_and_preprocess
from sncf_project.aggregation import aggregate_by_ligne
from sncf_project.scoring import all_scores_and_sort


from sncf_project.config import cols_to_drop, columns_mapping
from sncf_project.config import file_path, start_date, end_date, aller_retour, poids_gravité

df = get_data_and_preprocess(file_path, cols_to_drop, columns_mapping)

print(df.shape)

agg_df, ligne_dict = aggregate_by_ligne(df, start_date=start_date, end_date=end_date, aller_retour=aller_retour)

print(agg_df.shape)
print(len(ligne_dict))

scores_df = all_scores_and_sort(
    agg_df, poids_gravité, sort_by="score_3", debut=start_date, fin=end_date,
)


print(scores_df.head())