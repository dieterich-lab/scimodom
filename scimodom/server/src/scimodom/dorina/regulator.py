#!/usr/bin/env python
# -*- coding: utf-8

from __future__ import unicode_literals
import os
import json
from pybedtools import BedTool
from scimodom.dorina.utils import DorinaUtils
from io import open


class Regulator(object):
    _datadir = None
    _regulators = None

    def __init__(self, name, path, custom):
        self.name = name
        self.path = path
        self.basename = os.path.splitext(path)[0]
        self.custom = custom
        self.bed = self._bed()

    @classmethod
    def init(cls, datadir):
        def parse_experiment(filename):
            """Return the the experiment annotation as a python object.

            :param str filename: path to experiment file
            :return dict: parsed experiment
            """

            with open(filename, encoding="utf-8") as fh:
                return json.load(fh)

        def parse_func(root):
            """Parse function used to initialise the regulators from the data
            directory. Gets all available regulators.  A valid regulator must
            have a JSON metadata file as well as a BED file containing the data.
            """

            regulators = {}

            for experiment in os.listdir(root):
                experiment_path = os.path.join(root, experiment)
                if not os.path.isfile(experiment_path):
                    continue

                experiment_root, experiment_ext = os.path.splitext(experiment)
                if not experiment_ext.lower() == '.json':
                    continue

                bedfile = os.path.join(root, '%s.%s' % (experiment_root, 'bed'))
                if not os.path.isfile(bedfile):
                    continue

                experiments = parse_experiment(experiment_path)
                for experiment_dict in experiments:
                    experiment_dict['file'] = experiment_path
                    regulators[experiment_dict['id']] = experiment_dict

            return regulators

        cls._datadir = datadir
        cls._regulators = DorinaUtils.walk_assembly_tree(
            os.path.join(datadir, 'regulators'),
            parse_func)

    @classmethod
    def all(cls):
        return cls._regulators

    def _bed(self):
        def by_name(rec):

            # Drop first part before underscore.
            if "_" in self.name:
                name = "_".join(self.name.split("_")[1:])
            else:
                name = self.name
            return (name + "*" in rec.name) or (name == rec.name)
        
        bt = BedTool(self.path)
        #if not self.custom and '_all' not in self.name:
        #    bt = bt.filter(by_name).saveas()

        if len(bt) > 0 and len(bt[0].fields) > 6:
            #bt = bt.bed6().saveas()
            bt = bt.cut(list(range(6))).saveas()

        return bt

    @staticmethod
    def merge(regulators):
        """Merge a list of regulators using BedTool.cat"""
        if len(regulators) > 1:
            return BedTool.cat(*regulators, postmerge=False)
        else:
            return regulators[0]

    @classmethod
    def from_name(cls, name_or_path, assembly=None):
        if os.sep in name_or_path:
            return Regulator("custom", name_or_path, True)

        if not assembly:
            raise ValueError("Must provide assembly")

        filename = None
        for species, species_dir in cls._regulators.items():
            for _assembly, assembly_dir in species_dir.items():
                if assembly == _assembly and name_or_path in assembly_dir:
                    basename = \
                    os.path.splitext(assembly_dir[name_or_path]['file'])[0]
                    filename = basename + ".bed"

        if not filename or not os.path.isfile(filename):
            raise ValueError("Could not find regulator: %s" % name_or_path)

        return Regulator(name_or_path, filename, False)

    @staticmethod
    def from_names(names, assembly):
        if names:
            return list(
                [Regulator.from_name(x, assembly).bed for x in names])
        else:
            return []
