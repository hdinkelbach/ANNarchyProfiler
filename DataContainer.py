#==============================================================================
#
#     CodeGenerator.py
#
#     This file is part of ANNarchy.
#
#     Copyright (C) 2016-2019  Toni Freitag <tfreitag93@gmail.com>,
#     Helge Uelo Dinkelbach <helge.dinkelbach@gmail.com>
#
#     This program is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     ANNarchy is distributed in the hope that it will be useful,
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
#import numpy as np
#import copy

class DataContainer(object):
    """
    Contains all data of one profiling file, obtained from ANNarchy model.
    """
    def __init__(self):
        """
        Initialization.
        """
        self._keys = {}

        # performance config
        self._paradigm = ''
        self._num_threads = 0
        
        # performance data
        self._data = {}
        self._mean_values = {}
        self._std_values = {}
        self._raw_start = {}
        self._raw_data = {}

    def _convert_string_to_array(self, strng):
        """
        Converts a string containing multiple float or int values
        to an array of float values.
        """
        import re
        values = re.split('[\s]+', strng)
        ret = []
        for val in values:
            try:
                ret.append(float(val))
            except ValueError:
                continue

        return ret

#     def rescale_values(self, data):
#         """
#         Creates a rescaled copy of provided data.
#         """
#         tmp = copy.deepcopy( data )
# 
#         for i in range(len(data)):
#             tmp[i] = float(data[i]) / 1000.0 / 1000.0  # us -> s
# 
#         return tmp
# 
    def load_data(self, fname):
        """
        Load performance data from provided file.
 
        Parameters:
 
            * *fname*: absolute path and name of the file.
        """
        doc = etree.parse(str(fname))
 
        # configuration
        matches = doc.findall('config')
        for config in matches:
            childs = config.getchildren()
 
            for child in childs:
                if child.tag == "paradigm":
                    self._paradigm = child.text
 
                if child.tag == "num_threads":
                    self._num_threads = child.text
 
        # performance data
        matches = doc.findall('dataset')
        
        obj_type_values = {}
        name_values = {}
        func_values ={}
        mean_values = {}
        std_values = {}
        raw_data_values = {}
        #raw_start_values = {}
        num_tests = -1
 
        #keys = {
        #     'net': [],
        #     'pop': [],
        #     'proj': []
        # }
 
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
                      
                #else:
                    #obj_type_values[num_tests].append(obj_type)
                    #name_values[num_tests].append(name)
                    #func_values[num_tests].append(func)
                    #mean_values[num_tests].append(mean)
                    #std_values[num_tests].append(std)
                    #raw_data_values[num_tests].append(raw)
                
        self._num_tests = num_tests
        #self._obj_types = obj_type_values
        #self._names = name_values
        #self._functions = func_values
        #self._mean_values = mean_values
        #self._std_values = std_values
        #self._raw_data = raw_data_values       
                
        """childs = parameter.getchildren()
 
            obj_name = ""
            func_name = ""
            obj_type = ""
            mean_value = 0.0
            std_value = 0.0
            for child in childs:
                print(child)
                if child.tag == "obj_type":
                    obj_type = child.text
 
                if child.tag == "name":
                    obj_name = child.text
 
                if child.tag == "func":
                    func_name = child.text
 
                key = obj_name+' - '+func_name
 
                if child.tag == "mean":
                    mean_value = float(child.text)
                    if key in mean_values.keys():
                        mean_values[key].append(mean_value)
                    else:
                        mean_values[key] = [mean_value]
 
                if child.tag == "std":
                    std_value = float(child.text)
                    if key in std_values.keys():
                        std_values[key].append(std_value)
                    else:
                        std_values[key] = [std_value]
 
                if child.tag == "raw_data":
                    values = self._convert_string_to_array(child.text)
                    if key in raw_data_values.keys():
                        raw_data_values[key].append(values)
                    else:
                        raw_data_values[key] = [values]
 
                if child.tag == "raw_start":
                    values = self._convert_string_to_array(child.text)
                    if key in raw_start_values.keys():
                        raw_start_values[key].append(values)
                    else:
                        raw_start_values[key] = [values]
 
            keys[obj_type].append(key)
            keys[obj_type] = list(set(keys[obj_type])) # remove doubled entries
 
        # udpate data model
        self._keys = keys
        self._mean_values = mean_values
        self._std_values = std_values
        self._raw_data = raw_data_values
        self._raw_start = raw_start_values
        #print(self._keys)"""
        
    def num_tests(self):
        """
            Number of test-network created
        """
        return self._num_tests

    def values_by_function(self, index, obj_type, func):
        """
            Returns the values of a network filtered by function and object type
            
            params:
                * index - number of the network
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
            
            params:
                * index - number of the network
                * obJ_type - name of the object to filter
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
                                  
            #for
            #names.append(self._names[0][i]+" - "+self._functions[0][i])
            
        return names
    
    def values_each_test(self, obj_type, func, val_type):
        values = []
        
        if obj_type == "net":
            for _,value in self._data.items():
                values.append(value[obj_type][func][val_type])
        else:
            match = re.match(r"([a-z]+)([0-9]+)", obj_type, re.I).groups()
            for _,value in self._data.items():
                values.append(value[match[0]][int(match[1])][func][val_type])
            
        return values
            
#     def paradigm(self):
#         return self._paradigm
# 
#     def num_threads(self):
#         return self._num_threads
# 
#     def keys(self, type):
#         return self._keys[type]
# 
#     def num_elem(self, type):
#         return len(self._keys[type])
# 
#     def mean_value(self, type, id):
#         return np.array(self.rescale_values(self._mean_values[self._keys[type][id]]))
# 
#     def std_value(self, type, id):
#         return np.array(self.rescale_values(self._std_values[self._keys[type][id]]))
# 
#     def raw_data(self, type, id):
#         return np.array(self._raw_data[self._keys[type][id]])
# 
#     def raw_start(self, type, id):
#         return np.array(self._raw_start[self._keys[type][id]])