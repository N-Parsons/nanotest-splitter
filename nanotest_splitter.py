# -*- coding: utf-8 -*-

import os
import csv
import json

import click


@click.command()
@click.argument('infiles', nargs=-1,
                type=click.Path(exists=True, dir_okay=False, resolve_path=True))
@click.option('--clobber', is_flag="True",
              help="Force overwrite without confirmation")
def nanotest_split(infiles, clobber):
    # Set the write-mode based on the clobber flag state
    write_mode = "w" if clobber else "x"

    # Create a comforting progressbar
    with click.progressbar(infiles, width=0) as bar:
        for infile in bar:
            # Split the input tsv into chunks
            chunks = chunk_file(infile)

            # Get the output filepath
            _dirname = os.path.dirname(infile)
            _basename = os.path.basename(infile)
            _filename, _ = os.path.splitext(_basename)
            outpath = os.path.join(_dirname, _filename + ".json")

            # Write the chunks to file
            write_json(chunks, outpath, mode=write_mode)


def chunk_file(filename, delim="\t"):
    """Split a tsv/csv file into chunks if there are blank lines"""

    # Create some empty lists to store data in
    chunks = []
    chunk = []
    subchunk = []

    with open(filename, "r") as csvfile:
        csvreader = csv.reader(csvfile, delimiter=delim)
        for line in csvreader:
            if line == [] and subchunk == []:  # second blank line
                chunks.append(chunk)
                chunk = []
            elif line == []:                   # first blank line
                chunk.append(subchunk)
                subchunk = []
            else:                              # line contains data
                _line = list(map(from_repr, line))
                subchunk.append(_line)

    # Append anything that hasn't already been appended
    # (ie. anything not followed by a double blank line)
    if subchunk:
        chunk.append(subchunk)
    if chunk:
        chunks.append(chunk)

    return chunks


def write_json(chunks, filepath, mode="x"):
    outdict = {"point{}".format(i+1): v for i, v in enumerate(chunks)}

    try:
        with open(filepath, mode) as outfile:
            json.dump(outdict, outfile, indent=4, sort_keys=True)
    except FileExistsError:
        click.secho("\n{} already exists!".format(filepath), fg="yellow")
        if input("Do you want to overwrite it? (y/N): ").lower() == "y":
            write_json(chunks, filepath, mode="w")
        else:
            resp = input("Rename or cancel? (r/C): ")
            if resp == "r":
                new_filename = input("New filename (.json): ")
                directory = os.path.dirname(filepath)
                new_filepath = os.path.join(directory, new_filename + ".json")
                write_json(chunks, new_filepath, mode="x")
            else:
                click.secho("File not saved", fg="red")


def from_repr(s):
    """Get an int or float from its representation as a string"""
    # Strip any outside whitespace
    s = s.strip()
    # "NaN" and "inf" can be converted to floats, but we don't want this
    # because it breaks in Mathematica!
    if s.lower() in ("nan", "inf", "-inf"):
        rep = s
    else:
        try:
            rep = int(s)
        except ValueError:
            try:
                rep = float(s)
            except ValueError:
                rep = s
    return rep



if __name__ == '__main__':
    nanotest_split()