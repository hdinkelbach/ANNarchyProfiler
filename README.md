# ANNarchyProfiler

A profiling extension for the ANNarchy simulation environment, which is available on github (https://github.com/ANNarchy/ANNarchy) or bitbucket (https://bitbucket.org/annarchy/annarchy).

## Dependencies

The ANNarchyProfiler requires the following packages:

* PyQt5
* lxml

## Usage

The tool serves as an offline analysis tool to determine the fraction of time required by single population or projections. The required profiling data, stored as *.xml files, can be obtained 

* either by the profiler itself via the Start -> Run measurement dialog
* on command line: python YourScript.py --profile

## TODO
 - [X] reloading data
 - [X] calculate bottom of bars as sum of previos bars
 - [X] calculate overhead as step - sum(operations)
 - [X] log mode for y axis
 - [X] y label (computation time per step [ms] or computation time per step [ms, log-scale] or percentage)
 - [ ] missing values = 0.0
 - [X] summary for population
 - [X] plot all mean values as line plot (spikes are standard deviation)
 - [X] line plot with log scale
 - [X] mutual exclusion normalisation and log scale
 - [X] check box speed up (single thread / multi thread)
 - [X] grid for line plots
 - [X] Save function for current plot
 - [X] x label (number of measurements)
 - [X] calculate speed up based on mean values
 - [X] raw data plot