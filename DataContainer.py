# ==============================================================================
#
#     DataContainer.py
#
#     This file is part of ANNarchyProfiler.
#
#     Copyright (C) 2016-2019  Toni Freitag <tfreitag93@gmail.com>,
#     Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     ANNarchyProfiler is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# ==============================================================================
from lxml import etree
from numpy import zeros, mean, std
import re


class DataContainer(object):
    """
    Contains all data of one profiling file, obtained from ANNarchy model.
    """
    def __init__(self):
        """
        Initialization.
        """

        # performance config
        self._paradigm = ''
        self._num_threads = 0
        self._rank = ''
        self._num_tests = 0
        
        # performance data
        # [obj_type][name][func]
        self._data = {}

    def _convert_string_to_array(self, strng):
        """
        Converts a string containing multiple float or int values
        to an array of float values.
        
        Arguments:
            * strng -- string to be converted to an array
        """
        values = re.split(r'[\s]+', strng)
        ret = []
        for val in values:
            try:
                ret.append(float(val))
            except ValueError:
                continue

        return ret

    def load_data(self, fname):
        """
        Load performance data from provided file. Returns true if successful else false.
 
        Arguments:

            * fname -- absolute path and name of the file.
        """
        doc = etree.parse(str(fname))
 
        # save configuration from
        config_nodes = doc.findall('config')
        if config_nodes == []:
            print("No configuration entries in XML ...")

        for config in config_nodes:
            children = config.getchildren()
 
            for child in children:
                if child.tag == "paradigm":
                    self._paradigm = child.text
 
                if child.tag == "num_threads":
                    self._num_threads = int(child.text)
                    
                if child.tag == "rank":
                    self._rank = child.text
        
        # Configuration validation
        if self._paradigm == '':
            return False
        if self._paradigm == "openmp" and self._num_threads == 0:
            return False
        if self._paradigm == "cuda":
            self._num_threads = 32

        # Scan performance data
        matches = doc.findall('dataset')
        
        self._data = {}
        num_tests = -1
 
        for dataset in matches:
            obj_type = dataset.find("obj_type").text
            name = dataset.find("name").text
            func = dataset.find("func").text
            mean = float(dataset.find("mean").text)
            std = float(dataset.find("std").text)
            raw = self._convert_string_to_array(dataset.find("raw_data").text)
            
            if obj_type == "net" and func == "global_op": # Check for first element of network
                num_tests += 1
                self._data[num_tests] = {"net" : {}, "pop" : {}, "proj" : {}}
            
            if not name in self._data[num_tests][obj_type]:
                self._data[num_tests][obj_type][name] = {}
            self._data[num_tests][obj_type][name][func] = {"mean" : mean, "std" : std, "raw" :  raw}
                
        self._num_tests = num_tests + 1

        return True
    
    def num_threads(self):
        """
        Return Number of threads
        """
        return self._num_threads
    
    def paradigm(self):
        """
        Return paradigm
        """
        return self._paradigm
    
    def key(self):
        """
        Return unique key for this container consists of paradigm, rank and number of threads
        """
        return self._paradigm + self._rank + "-" + str(self._num_threads)
    
    def num_tests(self):
        """
        Return Number of measurements
        """
        return self._num_tests

    def values_by_function(self, index, obj_type, func):
        """
        Returns the values of a network filtered by function and object type
            
        Arguments:
            * index - number of the measurement
            * obj_type - name of the object (net/pop/proj)
            * func - name of the function to filter
        """
        values = {}
        for key, value in self._data[index][obj_type].items():
            if func in value:
                values[key] = value[func]
        return values
    
    def values_by_type(self, index, obj_type):
        """
        Returns the values of a network filtered by object type
            
        Arguments:
            * index -- number of the measurement
            * obj_type -- name of the object to filter
        """
        return self._data[index][obj_type]
    
    def unique_function_names(self, obj_type):
        """
        Return the names of all defined functions for a object type
        """
        names = []
        if len(self._data.keys()) == 0:
            # HD: 13th Oct 2019:
            #   An unitialized DataContainer was called, this could be a
            #   result of: ProfilerWindow.current_data()
            return names

        for name, name_val in self._data[0][obj_type].items():
            for func_name in name_val:
                names.append(name + " - " + func_name)
            
        return names
    
    def values_each_test(self, obj_type, name, func, val_type):
        """
        Filter values by object type, function and values type
        
        Arguments:
            * obj_type -- Network(net), Projection(proj) or Population(pop)
            * name -- name of the object
            * func -- name of function to filter
            * val_type -- mean, std or raw data
        """
        values = []
        
        #if obj_type == "net":
        for _, value in self._data.items():
            values.append(value[obj_type][name][func][val_type])
        #else:
            #match = re.match(r"([a-z]+)([0-9]+)", obj_type, re.I).groups()
            #for _, value in self._data.items():
                #values.append(value[match[0]][int(match[1])][func][val_type])
            
        return values
    
    def recalc_mean_values(self, obj_type, name, func, factor):
        """
        Filter values by object type, function and recalculate the mean values.
        
        Arguments:
            * obj_type -- Network(net), Projection(proj) or Population(pop)
            * func -- name of function to filter
            * factor -- 
        """
        
        mean_values = self.values_each_test(obj_type, name, func, "mean")
        std_values = self.values_each_test(obj_type, name, func, "std")
        raw_data = self.values_each_test(obj_type, name, func, "raw")

        # result container
        new_mean = zeros(len(mean_values))
        new_std = zeros(len(std_values))

        # for each trial
        for i in range(len(mean_values)):
            without_outlier = []

            # remove outlier iteratively
            for n in range(len(raw_data[i])):
                if raw_data[i][n] <= (mean_values[i] + factor * std_values[i]) and raw_data[i][n] >= (mean_values[i] - factor * std_values[i]):
                    without_outlier.append(raw_data[i][n])

            # store result
            new_mean[i] = mean(without_outlier)
            new_std[i] = std(without_outlier)

            # debug
            #print(mean(without_outlier), std(without_outlier), mean(raw_data[i]), std(raw_data[i]))

        return new_mean, new_std
