import numpy as np
import pandas as pd
from collections import Counter

import matplotlib.pyplot as plt
from sklearn.preprocessing import scale
from sklearn.metrics import pairwise_distances
from sklearn.manifold import MDS, TSNE
from umap import UMAP
from umap.parametric_umap import ParametricUMAP

from scipy.cluster.hierarchy import dendrogram, linkage, fcluster, set_link_color_palette

### data preparation
tableau10 = {
    0: '#78B7B2',  #teal
    1: '#507AA6',  #blue
    2: '#F08E39',  # orange
    3: '#DF585C',  # red
    4: '#5BA053',  # green
    5: '#AF7BA1',  # purple
    6: '#ECC854',  # yellow
    7: '#9A7460',  # brown
    8: '#FD9EA9',  # pink
    9: '#BAB0AC'  # gray
}

df = pd.read_csv(
    './data/Primates.subsampledHumans.trimmed.padded.cleaned.seqCenteredOnSpeCenteredRef.indicVectors.deMirrored.csv',
    header=None)
df2 = pd.read_csv('./data/primates.seqId2taxon.csv', header=None, sep=';')
y_names = np.unique(df2[1])
seqid_to_taxon = dict(zip(df2[0], df2[1]))
taxon_to_label = dict(zip(y_names, list(range(len(y_names)))))

seqids = np.array(df.loc[:, 0])
taxons = np.array([seqid_to_taxon[seqid] for seqid in seqids])
taxon_to_label = dict(
    zip(np.unique(taxons), list(range(len(np.unique(taxons))))))
label_to_taxon = dict(
    zip(list(range(len(np.unique(taxons)))), np.unique(taxons)))

genuses = np.array([taxon.split(' ')[0] for taxon in taxons])
genus_to_label = dict(
    zip(np.unique(genuses), list(range(len(np.unique(genuses))))))
label_to_genus = dict(
    zip(list(range(len(np.unique(genuses)))), np.unique(genuses)))

genus_names = np.array(list(Counter(genuses).keys()))
genus_counts = np.array(list(Counter(genuses).values()))
genus_to_colorid = {}
colorid_to_genus = {}
for i, name in enumerate(genus_names[np.argsort(-genus_counts)]):
    colorid = i if i < 9 else 9
    genus_to_colorid[name] = colorid
    colorid_to_genus[colorid] = name
colorid_to_genus[9] = 'Others'

### X and y used for learning
X = np.array(df.loc[:, 1:])
y_taxon = np.array([taxon_to_label[taxon] for taxon in taxons])
y_genus = np.array([genus_to_label[genus] for genus in genuses])
y_color = np.array([genus_to_colorid[genus] for genus in genuses])


### dimensionality reduction
def plot(Y, y_color):
    plt.figure(figsize=(8, 8))
    if Y.shape[1] == 2:
        for i in range(10):
            plt.scatter(Y[y_color == i, 0],
                        Y[y_color == i, 1],
                        c=tableau10[i],
                        label=colorid_to_genus[i],
                        zorder=2 if i < 9 else 1)
    elif Y.shape[1] == 3:
        ax = plt.axes(projection='3d')
        for i in range(10):
            ax.scatter3D(Y[y_color == i, 0],
                         Y[y_color == i, 1],
                         Y[y_color == i, 2],
                         c=tableau10[i],
                         label=colorid_to_genus[i],
                         zorder=2 if i < 9 else 1)
    plt.legend()
    plt.tight_layout()
    plt.show()


def output(Y, y_color, filename=None, y_genus=None, y_taxon=None, seqids=None):
    if Y.shape[1] == 3:
        df = pd.DataFrame(Y, columns=['x', 'y', 'z'])
    elif Y.shape[1] == 2:
        df = pd.DataFrame(Y, columns=['x', 'y'])
        df['z'] = [0] * df.shape[0]

    df['class'] = y_color
    df['class_name'] = [colorid_to_genus[id] for id in y_color]
    df['color'] = [tableau10[id] for id in y_color]
    df['genus'] = [''] * df.shape[0]
    df['taxon'] = [''] * df.shape[0]
    df['seqid'] = [''] * df.shape[0]
    if y_genus is not None:
        df['genus'] = [label_to_genus[id] for id in y_genus]
    if y_taxon is not None:
        df['taxon'] = [label_to_taxon[id] for id in y_taxon]
    if seqids is not None:
        df['seqid'] = seqids

    if filename is not None:
        df.to_csv(filename)

    return df


n_components = 3
## not sure, applying scaling is a good idea
# X = scale(X)

# no aggregation
D_euclid = pairwise_distances(X, metric='euclidean')
D_euclid = (D_euclid.T + D_euclid) / 2  # to enforce D to be symmetric
Y_mds = MDS(n_components=n_components,
            dissimilarity='precomputed').fit_transform(D_euclid)
plot(Y_mds, y_color)
output(Y_mds,
       y_color,
       'mds_noaggregation.csv',
       y_genus=y_genus,
       y_taxon=y_taxon,
       seqids=seqids)

Y_umap = UMAP(n_components=n_components,
              n_neighbors=100,
              min_dist=0.5,
              metric='precomputed').fit_transform(D_euclid)
plot(Y_umap, y_color)
output(Y_umap,
       y_color,
       'umap_noaggregation.csv',
       y_genus=y_genus,
       y_taxon=y_taxon,
       seqids=seqids)

# Parameteric UMAP doesn't work on precomputed matrix (Idk why yet)
pumap = ParametricUMAP(n_components=n_components,
                       n_neighbors=100,
                       min_dist=0.5)
Y_pumap = pumap.fit_transform(X)
plot(Y_pumap, y_color)
output(Y_pumap,
       y_color,
       'pumap_noaggregation.csv',
       y_genus=y_genus,
       y_taxon=y_taxon,
       seqids=seqids)

# aggregation by taxon
df = pd.DataFrame(X)
df['y_taxon'] = y_taxon
df['y_genus'] = y_genus
df['y_color'] = y_color

df_by_taxon = df.groupby(['y_taxon'], as_index=False).mean()
y_taxon_by_taxon = np.array(df_by_taxon['y_taxon'])
y_genus_by_taxon = np.array(df_by_taxon['y_genus']).astype(int)
y_color_by_taxon = np.array(df_by_taxon['y_color']).astype(int)
X_by_taxon = np.array(
    df_by_taxon.drop(columns=['y_taxon', 'y_genus', 'y_color']))

Y_mds_by_taxon = MDS(n_components=n_components).fit_transform(X_by_taxon)
plot(Y_mds_by_taxon, y_color_by_taxon)
output(Y_mds_by_taxon,
       y_color_by_taxon,
       'mds_taxon.csv',
       y_genus=y_genus_by_taxon,
       y_taxon=y_taxon_by_taxon,
       seqids=None)

Y_umap_by_taxon = UMAP(n_components=n_components, n_neighbors=30,
                       min_dist=0.2).fit_transform(X_by_taxon)
plot(Y_umap_by_taxon, y_color_by_taxon)
output(Y_umap_by_taxon,
       y_color_by_taxon,
       'umap_taxon.csv',
       y_genus=y_genus_by_taxon,
       y_taxon=y_taxon_by_taxon,
       seqids=None)

pumap = ParametricUMAP(n_components=n_components, n_neighbors=30, min_dist=0.2)
Y_pumap_by_taxon = pumap.fit_transform(X_by_taxon)
plot(Y_pumap_by_taxon, y_color_by_taxon)
output(Y_pumap_by_taxon,
       y_color_by_taxon,
       'pumap_taxon.csv',
       y_genus=y_genus_by_taxon,
       y_taxon=y_taxon_by_taxon,
       seqids=None)

Y_pumap_by_taxon_all = pumap.transform(X)
plot(Y_pumap_by_taxon_all, y_color)
output(Y_pumap_by_taxon_all,
       y_color,
       'pumap_taxon_allpoints.csv',
       y_genus=y_genus,
       y_taxon=y_taxon,
       seqids=seqids)


# aggregation by hierachical clustering
def plot_hclust_result(X, Z_inst, Z_attr, attr_names=None):

    # plot dendrogram
    fig = plt.figure(figsize=(15, 8))

    set_link_color_palette(['#666666'])

    ax1 = fig.add_axes([0.01, 0.1, 0.18, 0.8])
    dn_inst = dendrogram(Z_inst,
                         orientation='left',
                         above_threshold_color='#666666')
    ax1.set_xticks([])
    ax1.set_yticks([])
    ax1.axis('off')

    ax2 = fig.add_axes([0.2, 0.91, 0.7, 0.02])
    dn_attr = dendrogram(Z_attr, above_threshold_color='#666666')
    ax2.set_xticks([])
    ax2.set_yticks([])
    ax2.axis('off')

    # Plot data as heatmap.
    axmatrix = fig.add_axes([0.2, 0.1, 0.7, 0.8])
    X_reorder = X[dn_inst['leaves'], :]
    X_reorder = X_reorder[:, dn_attr['leaves']]
    im = axmatrix.matshow(X_reorder,
                          aspect='auto',
                          origin='lower',
                          cmap=plt.cm.BuPu)
    axmatrix.set_xticks([])
    axmatrix.set_yticks([])
    # Plot attribute names
    if attr_names is not None:
        axmatrix.set_xticks(np.arange(len(attr_names)))
        axmatrix.xaxis.tick_bottom()
        axmatrix.set_xticklabels(np.array(attr_names)[dn_attr['leaves']])
        plt.setp(axmatrix.get_xticklabels(),
                 rotation=90,
                 ha="right",
                 rotation_mode="anchor")

    # Plot colorbar.
    axcolor = fig.add_axes([0.92, 0.1, 0.02, 0.8])
    plt.colorbar(im, cax=axcolor)
    plt.tight_layout()
    fig.show()


Z_inst = linkage(X, method='complete')
Z_attr = linkage(X.T, method='complete')

plot_hclust_result(X, Z_inst, Z_attr)

for n_clusters, n_neighbors, min_dist in zip(
    [1000, 300, 100, 50, 30, 10, 5, 3], [50, 30, 30, 10, 5, 5, 5, 3],
    [0.3, 0.2, 0.1, 0.1, 0.1, 0.01, 0.01, 0.005]):

    y_cluster = fcluster(Z_inst, n_clusters, criterion='maxclust')

    df = pd.DataFrame(X)
    df['y_cluster'] = y_cluster

    df_by_cluster = df.groupby(['y_cluster'], as_index=False).mean()
    X_by_cluster = np.array(df_by_cluster.drop(columns=['y_cluster']))

    pumap = ParametricUMAP(n_components=n_components,
                           n_neighbors=n_neighbors,
                           min_dist=min_dist)
    pumap.fit(X_by_cluster)
    Y_pumap_by_cluster_all = pumap.transform(X)
    plot(Y_pumap_by_cluster_all, y_color)

    output(Y_pumap_by_cluster_all,
           y_color,
           f'pumap_cluster{n_clusters}_allpoints.csv',
           y_genus=y_genus,
           y_taxon=y_taxon,
           seqids=seqids)

# aggregation by taxon then by clustering
n_clusters = 50
n_neighbors = 10
min_dist = 0.1

Z_inst_by_taxon = linkage(X_by_taxon, method='complete')
Z_attr_by_taxon = linkage(X_by_taxon.T, method='complete')

plot_hclust_result(X_by_taxon, Z_inst_by_taxon, Z_attr_by_taxon)

y_cluster_by_taxon = fcluster(Z_inst_by_taxon,
                              n_clusters,
                              criterion='maxclust')

df = pd.DataFrame(X_by_taxon)
df['y_cluster'] = y_cluster_by_taxon
df_by_cluster = df.groupby(['y_cluster'], as_index=False).mean()
X_by_taxon_cluster = np.array(df_by_cluster.drop(columns=['y_cluster']))

pumap = ParametricUMAP(n_components=n_components,
                       n_neighbors=n_neighbors,
                       min_dist=min_dist)
pumap.fit(X_by_taxon_cluster)

Y_pumap_by_taxon_cluster_all = pumap.transform(X)
plot(Y_pumap_by_taxon_cluster_all, y_color)

output(Y_pumap_by_taxon_cluster_all,
       y_color,
       f'pumap_taxon&cluster{n_clusters}_allpoints.csv',
       y_genus=y_genus,
       y_taxon=y_taxon,
       seqids=seqids)
