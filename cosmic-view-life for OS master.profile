{
  "assets": [
    "base_blank",
    "${USER_ASSETS}/cosmic_life/birds/UMAP_v2/branches_anas",
    "${USER_ASSETS}/cosmic_life/birds/UMAP_v2/branches_columba",
    "${USER_ASSETS}/cosmic_life/birds/UMAP_v2/clades",
    "${USER_ASSETS}/cosmic_life/birds/UMAP_v2/consensus_species",
    "${USER_ASSETS}/cosmic_life/birds/UMAP_v2/sequence_lineage",
    "${USER_ASSETS}/cosmic_life/birds/UMAP_v2/sequences",
    "${USER_ASSETS}/cosmic_life/birds/UMAP_v2/taxon",
    "${USER_ASSETS}/cosmic_life/human_origins/human_origins",
    "${USER_ASSETS}/cosmic_life/human_origins/human_origins_regions",
    "${USER_ASSETS}/cosmic_life/primates/MDS_v1/consensus_species",
    "${USER_ASSETS}/cosmic_life/primates/MDS_v1/sequence_lineage",
    "${USER_ASSETS}/cosmic_life/primates/MDS_v1/sequences",
    "${USER_ASSETS}/cosmic_life/primates/tree/primates_branches",
    "${USER_ASSETS}/cosmic_life/primates/tree/primates_interpolated",
    "${USER_ASSETS}/cosmic_life/primates/tree/primates_leaves"
  ],
  "camera": {
    "aim": "",
    "anchor": "Root",
    "frame": "",
    "position": {
      "x": 100000.0,
      "y": 100000.0,
      "z": 100000.0
    },
    "type": "setNavigationState"
  },
  "delta_times": [
    1.0,
    5.0,
    30.0,
    60.0,
    300.0,
    1800.0,
    3600.0,
    43200.0,
    86400.0,
    604800.0,
    1209600.0,
    2592000.0,
    5184000.0,
    7776000.0,
    15552000.0,
    31536000.0,
    63072000.0,
    157680000.0,
    315360000.0,
    630720000.0
  ],
  "mark_nodes": [
    "Earth",
    "Mars",
    "Moon",
    "Sun",
    "Venus",
    "ISS"
  ],
  "meta": {
    "author": "OpenSpace Team",
    "description": "Default OpenSpace Profile. Adds Earth satellites not contained in other profiles",
    "license": "MIT License",
    "name": "Default",
    "url": "https://www.openspaceproject.com",
    "version": "1.0"
  },
  "properties": [
    {
      "name": "Scene.primates_tree_branches.Renderable.Enabled",
      "type": "setPropertyValueSingle",
      "value": "true"
    },
    {
      "name": "Scene.primates_tree_leaves.Renderable.Enabled",
      "type": "setPropertyValueSingle",
      "value": "true"
    }
  ],
  "time": {
    "is_paused": false,
    "type": "relative",
    "value": "-1d"
  },
  "version": {
    "major": 1,
    "minor": 3
  }
}