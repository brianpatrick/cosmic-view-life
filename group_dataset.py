#!/bin/env python

"""
group_dataset.py

This script takes a CSV file with points and groups them by a label column. It calculates
the centroid of each group and creates a new CSV file with the centroids. The new CSV file
can be used to create labels in OpenSpace, or place images, models, or whatever.
"""

import argparse
import pandas as pd
import os
import math
import sys

parser = argparse.ArgumentParser(description="Group dataset by column.")
parser.add_argument("-i", "--input_csv_file", help="Input CSV file.", 
                    required=True)
parser.add_argument("-c", "--column", help="Column to group by.",
                    required=True)
args = parser.parse_args()



# Get the input CSV file and the column to group by.
input_csv_file = args.input_csv_file
label_column = args.column
# Check if the input CSV file exists.
if not os.path.exists(input_csv_file):
    print("Input CSV file does not exist.")
    sys.exit(1)

# Read the input CSV file into a pandas dataframe.

input_points_df = pd.read_csv(input_csv_file)

# First we want to figure out the unique values in the label column. These
# are the groups we want to create labels for. Ignore NaN values in the label
# column.
groups = input_points_df[label_column].unique()
groups = [x for x in groups if str(x) != "nan"]

# Now we want to make a new empty dataframe with the same columns as the
# points_df. This new dataframe will contain the centroids of the
# groups.
centroids_df = pd.DataFrame(columns=input_points_df.columns)

# Iterate over the groups and calculate the centroid of each group.
for group in groups:
    # Get the rows that belong to this group.
    group_rows = input_points_df[input_points_df[label_column] == group]
    # Calculate the centroid of the group.
    centroid = {}
    centroid["x"] = group_rows["x"].mean()
    centroid["y"] = group_rows["y"].mean()
    centroid["z"] = group_rows["z"].mean()

    # dump the number of points and the centroid.
    #print("Group: " + group + " number of points: " + str(len(group_rows)))
    #print("Group: " + group + " centroid before placing on sphere: " + str(centroid))

    # The points all have the same radius from the origin, but the centroid
    # may be placed inside the sphere. We need to move the centroid to the
    # surface of the sphere. We can do this by normalizing the centroid vector
    # and then multiplying by the radius of the sphere.
    # First let's normalize the centroid vector.
    centroid_radius = math.sqrt(centroid["x"]**2 + centroid["y"]**2 + centroid["z"]**2)
    centroid["x"] = centroid["x"] / centroid_radius
    centroid["y"] = centroid["y"] / centroid_radius
    centroid["z"] = centroid["z"] / centroid_radius

    # Dump normalized centroid for debugging.
    #print("Group: " + group + " centroid normalized: " + str(centroid))

    # Now multiply by the radius of the sphere. Get the first point in the group.
    first_point = group_rows.iloc[0]
    sphere_radius = math.sqrt(first_point["x"]**2 + first_point["y"]**2 + first_point["z"]**2)
    # Print the radius for debugging.
    #print("Group: " + group + " sphere radius: " + str(sphere_radius))
    centroid["x"] = centroid["x"] * sphere_radius
    centroid["y"] = centroid["y"] * sphere_radius
    centroid["z"] = centroid["z"] * sphere_radius

    # Dump the centroid and its radius (to double check).
    #print("Group: " + group + " centroid on sphere: " + str(centroid))
    #print("Group: " + group + " centroid radius: " + str(math.sqrt(centroid["x"]**2 + centroid["y"]**2 + centroid["z"]**2)))

    # If the number if points is more than 1, add the number of points to the group
    # name.
    if len(group_rows) > 1:
        group = group + " (" + str(len(group_rows)) + ")"

    # Add the group name to the centroid.
    centroid[label_column] = group

    # If x is non nan, add the centroid to the new dataframe.
    if not math.isnan(centroid["x"]):
        centroids_df.loc[len(centroids_df)] = centroid

# Now we want to write the centroids to a new CSV file. The name of the new
# CSV file will be the same as the input CSV file, but with the column name
# appended to the end. For example, if the input CSV file is points.csv and
# the column name is group, the new CSV file will be points_group.csv.
output_csv_file = os.path.splitext(input_csv_file)[0] + "_by_" + label_column + ".csv"
# Check if the output CSV file already exists. If it does, ask the user if
# they want to overwrite it.
if os.path.exists(output_csv_file):
    print("Output CSV file already exists. Overwrite? (y/n)")
    answer = input()
    if answer != "y":
        print("Exiting.")
        sys.exit(0)
# Write the centroids to the new CSV file.
centroids_df.to_csv(output_csv_file, index=False)



