# create zip file of the files *.txt in gtfs folder
from zipfile import ZipFile, ZIP_DEFLATED
import os
import glob

with ZipFile("gtfs.zip", "w", compression=ZIP_DEFLATED, compresslevel=6) as zipf:
    # Get all .txt filesn in gtfs directory
    files = glob.glob("gtfs/*.txt")
    for file in files:
        # Add file to the zip file
        zipf.write(file, os.path.basename(file))
    print("Created gtfs.zip containing all .txt files.")