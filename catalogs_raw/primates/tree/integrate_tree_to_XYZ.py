''' Code by Wandrille Duchemin'''

import pandas as pd
import numpy as np
from ete3 import Tree
from collections import defaultdict



def latLong2xyz( lat, long , r=1.0 ):
    x = r * np.cos( lat ) * np.cos( long )
    y = r * np.cos( lat ) * np.sin( long )
    z = r * np.sin(lat)
    return x,y,z
    
def rescale(x , current_bounds, new_bounds):
    x_scaled = (( x - current_bounds[0] )  / ( current_bounds[1]- current_bounds[0]))
    return new_bounds[0] + x_scaled * (new_bounds[1]-new_bounds[0])

def get_pseudo_sphere_bounds( tree ):
    """
    Compute X,Y,Z bounds for re-scaling prior to projection on a pseudo-sphere
    Takes:
        - tree (ete3.Tree) : the tree structure where nodes have a .coordinates attribute
    Returns:
        (tuple) of 3 tuples of X, Y, Z bounds
    """    
    # re-scaling 

    ## finding the bound of the current projection
    x,y,z = tree.coordinates
    X_bounds = [x,x]
    Y_bounds = [y,y]
    Z_bounds = [z,z]

    for n in tree.traverse():
        x,y,z = n.coordinates

        if x < X_bounds[0]:
            X_bounds[0] = x
        elif x > X_bounds[1]:
            X_bounds[1] = x

        if y < Y_bounds[0]:
            Y_bounds[0] = y
        elif y > Y_bounds[1]:
            Y_bounds[1] = y

        if z < Z_bounds[0]:
            X_bounds[0] = z
        elif z > Z_bounds[1]:
            Z_bounds[1] = z

    return X_bounds,Y_bounds,Z_bounds

def project_to_pseudo_spherical( x,y,z, 
                            X_bounds,Y_bounds,Z_bounds,
                            long_limits = [-np.pi * 120/180 , np.pi * 120/180],
                            lat_limits = [-np.pi * 60/180 , np.pi * 60/180] ):
    """
    transforms a single point to a representation where modern points occupy the xy plane and the z-axis is used to represent time
    into a spherical representation centered on the tree root.

    we use simple inverse mercator projection to go from the xy plane to longitude latitude, hence we recommend putting limits
    on latitude to prevent extreme deformation,
    and on longitude to avoid having distance point being brought very clode on the back of the sphere.

    Takes:
        - x (float): original x-coordinate
        - y (float): original y-coordinate
        - z (float): original z-coordinate
        - X_bounds (tuple): X bounds, used for rescaling
        - Y_bounds (tuple): Y bounds, used for rescaling
        - Z_bounds (tuple): Z bounds, used for rescaling
        - long_limits = [-np.pi * 120/180 , np.pi * 120/180] : limits the longitude of the sphere we project into
        - lat_limits = [-np.pi * 60/180 , np.pi * 60/180] : limits the latitude of the sphere we project into

    Return :
        (tuple) of 3 floats, x,y,z of the input point in the pseudo-sphere projection 
    """
    lng = rescale( x , X_bounds , long_limits )
    lat = rescale( y , Y_bounds , lat_limits )
    R   = rescale( z , Z_bounds , Z_bounds )

    return latLong2xyz( lat , lng , R )


def make_pseudo_spherical( tree, X_bounds,Y_bounds,Z_bounds,
                            long_limits = [-np.pi * 120/180 , np.pi * 120/180],
                            lat_limits = [-np.pi * 60/180 , np.pi * 60/180] ):
    """
    transforms a representation where modern points occupy the xy plane and the z-axis is used to represent time
    into a spherical representation centered on the tree root.

    we use simple inverse mercator projection to go from the xy plane to longitude latitude, hence we recommend putting limits
    on latitude to prevent extreme deformation,
    and on longitude to avoid having distance point being brought very clode on the back of the sphere.

    Takes:
        - tree (ete3.Tree) : the tree structure where nodes have a .coordinates attribute
        - X_bounds (tuple): X bounds, used for rescaling
        - Y_bounds (tuple): Y bounds, used for rescaling
        - Z_bounds (tuple): Z bounds, used for rescaling
        - long_limits = [-np.pi * 120/180 , np.pi * 120/180] : limits the longitude of the sphere we project into
        - lat_limits = [-np.pi * 60/180 , np.pi * 60/180] : limits the latitude of the sphere we project into

    """

    for n in tree.traverse():
        x,y,z = n.coordinates

        lng = rescale( x , X_bounds , long_limits )
        lat = rescale( y , Y_bounds , lat_limits )
        R   = rescale( z , Z_bounds , Z_bounds )

        n.coordinates = latLong2xyz( lat , lng , R )
    
    return tree

def giveInternalNames(tree):
    """give names to internal nodes which have none"""
    i = 0
    for n in tree.traverse():
        if n.name == '' or n.name == '1': ## small limit if name is actually supposed to be 1
            n.name = "internal{}".format(i)
        i+=1
    return tree


if __name__ == "__main__":
    import sys
    


    import argparse

    parser = argparse.ArgumentParser(
            description="""Projects a tree structure in 3D from a set of coordinates of their leaves (by default 2D coordinates).""")
    parser.add_argument('-i','--inputFile', type=str, required=True,
         help='file containing x,y coordinates for each points (csv format, header expected, it is expected that the first column contains point id)')
    parser.add_argument('-t','--inputTree', type=str, required=True,
         help='tree in newick format. Leaves absent from the coordinate files will be ignored')
    parser.add_argument('-o','--outputPrefix', type=str, required=True,
         help='output file prefix for the x,y,z coordinates of points an lines')
    parser.add_argument('--z-scale', type=float, default=1.0,
             help='factor to rescale the z-axis (default:1.0)')
    parser.add_argument('--use-z-from-file', action='store_true', required=False, 
             help='uses the z-axis from the coordinate file.')
    parser.add_argument('--drag', type=float, default=0.2, 
             help='drag of internal nodes toward their parent.')
    parser.add_argument('--spherical-layout', action='store_true', required=False, 
             help='represent the tree as a sphere centered on the root. Incompatible with --use-z-from-file')
    parser.add_argument('--ignore-missing', action='store_true', required=False, 
             help='ignore points missing from the tree')
    

    ## options to add:
    ##      - input leaves height


    args = parser.parse_args()

    drag = args.drag
    if drag < 0 or drag > 1:
        print("Error: --drag must be between 0.0 and 1.0")
        exit(1)

    if args.use_z_from_file and args.spherical_layout:
        print("Warning: --spherical-layout is incompatible with --use-z-from-file and will be ignored.")

    ## reading coordinates

    XY = pd.read_csv( args.inputFile , index_col=0)

    n_coords = 2
    if args.use_z_from_file:
        n_coords += 1

    coordinates = list(XY.columns[:n_coords])
    

    if not coordinates[0] in 'xX':
        print(' -> mapped first column {} as x coordinate'.format(coordinates[0]))
    if not coordinates[1] in 'yY':
        print(' -> mapped second column {} as y coordinate'.format(coordinates[1]))
    if args.use_z_from_file:
        if not coordinates[2] in 'zZ':
            print(' -> mapped second column {} as z coordinate'.format(coordinates[2]))

    if len(XY.columns)  > n_coords:
        print('Warning: ignoring columns after the 2nd one:', XY.columns[n_coords:])

    # reading tree
    tree = Tree( args.inputTree , format = 1 )

    missing_leaves = pd.DataFrame( columns = XY.columns )

    leaf_set = set( [name for name in tree.iter_leaf_names()] )
    error = False
    for n in XY.index:
        if not n in leaf_set:
            msg = "ERROR"
            if args.ignore_missing:
                msg = "Warning"
                missing_leaves = pd.concat( [missing_leaves , XY.loc[[n],:]] )
                XY.drop( index=n,inplace=True )
            print("{}: {} is absent from the tree".format(msg,n))
            print("use the --ignore-missing option if you want to ignore this.")
            error = True
    if error and not args.ignore_missing:
        exit(1)


    ## pruning tree from leaves absent from the file
    tree.prune( XY.index , preserve_branch_length=True)

    ## giving names to all nodes in the tree where they are missing
    tree = giveInternalNames(tree)

    ## we will presume the root at height 0, and go down to the leaves from there

    for n in tree.traverse('preorder'):
        if n.up is None: # root
            n.height = 0
        else:
            n.height = n.up.height + n.dist

    ## compute the x and y of all points

    for n in tree.traverse('postorder'):
        if n.is_leaf() : # for leaves, use what's in the coordinate source file
            n.coordinates = list( XY.loc[ n.name , coordinates ] )
        else: # use average of children
            #sum
            n.coordinates = n.children[0].coordinates[:]
            for ch in n.children[1:]:
                for i in range(len( n.coordinates )):
                    n.coordinates[i] += ch.coordinates[i]
            # normalize
            for i in range(len( n.coordinates )):
                n.coordinates[i] /= len(n.children)

    # eventually apply some drag from the ancestor
    for n in tree.traverse('preorder'):
        if n.is_root() or n.is_leaf():
            continue
        n.coordinates = [n.coordinates[i]*(1-drag) + n.up.coordinates[i]*drag for i in range(len(n.coordinates))]

    if not args.use_z_from_file:
        for n in tree.traverse('postorder'):
            ## apply height as z-axis
            n.coordinates.append(n.height * args.z_scale)

        ## handling of missing leaves
        if missing_leaves.shape[0]>0:
            # assign average height as Z
            AH = 0
            N = 0
            for n in tree.iter_leaves():
                AH += n.coordinates[-1]
                N += 1

            missing_leaves["Z"] = AH/N
            coordinates.append( "Z" )

        if args.spherical_layout:
            X_bounds,Y_bounds,Z_bounds = get_pseudo_sphere_bounds( tree )
            tree = make_pseudo_spherical( tree , X_bounds,Y_bounds,Z_bounds)
            ## eventually project to pseudo-sphere

            ## handling of missing leaves
            for i,r in missing_leaves.iterrows():
                x,y,z = r.loc[ coordinates ]
                x,y,z = project_to_pseudo_spherical( x,y,z, 
                                                    X_bounds,Y_bounds,Z_bounds)
                r.loc[ coordinates ] = x,y,z


    ## output

    ### leaves
    suffix = ".leaves.csv"
    print("writing leaves coordinates in", args.outputPrefix+suffix)
    with open(args.outputPrefix+suffix , 'w') as OUT:
        print('name','x','y','z', sep=',' , file=OUT )
        for l in tree.iter_leaves():
            print(l.name , *(l.coordinates) , sep=',' , file=OUT )

        for i,r in missing_leaves.iterrows():
            x,y,z = r.loc[ coordinates ]
            print(i , x,y,z , sep=',' , file=OUT )


    ### internal nodes
    suffix = ".internal.csv"
    print("writing internal nodes coordinates in", args.outputPrefix+suffix)
    with open(args.outputPrefix+suffix , 'w') as OUT:
        print('name','x','y','z', sep=',' , file=OUT )
        i=0
        for n in tree.traverse():
            if n.is_leaf():
                continue
            print( n.name , *(n.coordinates) , sep=',' , file=OUT )
            i+=1
    ### branches
    suffix = ".branches.csv"
    print("writing branch coordinates in", args.outputPrefix+suffix)
    with open(args.outputPrefix+suffix , 'w') as OUT:
        print('name','x0','y0','z0','x1','y1','z1', sep=',' , file=OUT )
        i=0
        for n in tree.traverse():
            if n.is_root():
                continue
            print( 'branch_{}'.format(n.name) , *(n.up.coordinates), *(n.coordinates) , sep=',' , file=OUT )
            i+=1



    