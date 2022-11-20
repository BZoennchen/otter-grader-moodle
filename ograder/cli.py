import argparse
from .grade import main

def cli():
    parser = argparse.ArgumentParser(
        description='Grades a moodle assignment of otter notebooks.')
    parser.add_argument('-i', '--in', dest='src', type=str,
                        help='path to the zip file that includes all the student assignments')
    parser.add_argument('-o', '--out', dest='dest', type=str, default='assignments',
                        help='path to the directory that will be used to extract and run all assignments. This directory should not already exists.')
    parser.add_argument('-m', '--master', dest='dist', type=str, default='dist',
                        help='path to the directory of the otter master zip file, containing all the solutions and tests')
    
    args = parser.parse_args()
    main(args.src, args.dest, args.dist)
    