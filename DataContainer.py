#==============================================================================
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
#==============================================================================
from lxml import etree
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
        
        # performance data
        self._data = {}

    def _convert_string_to_array(self, strng):
        """
        Converts a string containing multiple float or int values
        to an array of float values.
        
        Parameter:
            * strng -- string to be converted to an array
        """
        values = re.split('[\s]+', strng)
        ret = []
        for val in values:
            try:
                ret.append(float(val))
            except ValueError:
                continue

        return ret

    def load_data(self, fname):
        """
        Load performance data from provided file.
 
        Parameter:
            * fname -- absolute path and name of the file.
        """
        doc = etree.parse(str(fname))
 
        # save configuration from
        matches = doc.findall('config')
        for config in matches:
            childs = config.getchildren()
 
            for child in childs:
                if child.tag == "paradigm":
                    self._paradigm = child.text
 
                if child.tag == "num_threads":
                    self._num_threads = int(child.text)
 
 
        # performance data
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
            
            if obj_type == "net":
                if func == "neur_step": # Check for first element of network
                    num_tests += 1
                    self._data[num_tests] = {"net" : {}, "pop" : {}, "proj" : {}}
                self._data[num_tests][obj_type][func] = {"mean" : mean, "std" : std, "raw" :  raw}
            
            elif obj_type == "pop" or obj_type == "proj":
                num = int(re.findall("\d+", name)[0])
                if not self._data[num_tests][obj_type].has_key(num):
                    self._data[num_tests][obj_type][num] = {}
                self._data[num_tests][obj_type][num][func] = {"mean" : mean, "std" : std, "raw" :  raw}
                
        self._num_tests = num_tests
    
    def num_threads(self):
        """
        Return Number of threads
        """
        return self._num_threads
    
    def num_tests(self):
        """
        Return Number of measurements
        """
        return self._num_tests

    def values_by_function(self, index, obj_type, func):
        """
        Returns the values of a network filtered by function and object type
            
        Parameter:
            * index - number of the measurement
            * obj_type - name of the object (net/pop/proj)
            * func - name of the function to filter
        """
        if obj_type == "net":
            return self._data[index][obj_type][func]
        else:
            values = {}
            for key,value in self._data[index][obj_type].items():
                values[key] = value[func]
        return values
    
    def values_by_type(self, index, obj_type):
        """
        Returns the values of a network filtered by object type
            
        Parameter:
            * index -- number of the measurement
            * obj_type -- name of the object to filter
        """
        return self._data[index][obj_type]
    
    def unique_function_names(self):
        """
        Return the names of all defined functions
        """
        names = []

        for func in self._data[0]["net"]:
            names.append("net - " + func)
            
        for nr,values in self._data[0]["pop"].items():
            for func in values:
                names.append("pop" + str(nr) + " - " + func)
        
        for nr,values in self._data[0]["proj"].items():
            for func in values:
                names.append("proj" + str(nr) + " - " + func)
            
        return names
    
    def values_each_test(self, obj_type, func, val_type):
        """
        Filter values by object type, function and values type
        
        Parameter:
            * obj_type -- Network(net), Projection(proj) or Population(pop)
            * func -- name of function to filter
            * val_type -- mean, std or raw data
        """
        values = []
        
        if obj_type == "net":
            for _,value in self._data.items():
                values.append(value[obj_type][func][val_type])
        else:
            match = re.match(r"([a-z]+)([0-9]+)", obj_type, re.I).groups()
            for _,value in self._data.items():
                values.append(value[match[0]][int(match[1])][func][val_type])
            
        return values