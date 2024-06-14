#!/bin/bash

# Set the Python script name
cd /nfs/alfred/code/LIHKG/LIHKG_scraper

# Set the default values for the parameters
start=2850000
stop=2900000
machine_name="g12"

# Parse the command-line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --start)
      start="$2"
      shift # past argument
      shift # past value
      ;;
    --stop)
      stop="$2"
      shift # past argument
      shift # past value
      ;;
    --machine)
      machine_name="$2"
      shift # past argument
      shift # past value
      ;;
    *)
      # Unknown option
      shift # past argument
      ;;
  esac
done

# Create and activate the virtual environment
source ~/nfs/code/nlp/bin/activate

# Run the Python script using nohup
python3 scrape_threads_mt.py --start $start --stop $stop --threads 10 --ignore_handled True > scrape_threads_mt_${start}_${stop}_${machine_name}.out 2>&1 &

# Deactivate the virtual environment
deactivate