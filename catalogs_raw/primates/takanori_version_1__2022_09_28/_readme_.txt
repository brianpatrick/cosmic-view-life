naming of files:
{dimensionality reduction method}_{aggregation by}_{whether all points are projected}.csv

For example,
- pumap_noaggregation.csv: Parametric UMAP without any aggregation.
- pumap_taxon.csv: Parametric UMAP performed on data aggregated by taxons.
- pumap_cluster300_allpoints.csv: Parametric UMAP performed on data aggregated by 300 clusters. All points are projected in the same latent space.
- pumap_taxon&cluster50_allpoints.csv: Parametric UMAP performed on data aggregated by taxon then 50 clusters. . All points are projected in the same latent space.
