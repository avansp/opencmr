# -*- coding: utf-8 -*-
"""Managing cardiac MRI study.

This module contains a single class CMRStudy to manage/extract a cardiac MR study.
"""
import pydicom as dicom
import os
import json
from .dicom_ext import read_dicom


class CMRStudy:
    """
    Read/manage/store a cardiac MRI study.

    Attributes:
        - source: the DICOM folder
    """

    STUDY_TAGS = ['StudyInstanceUID',
                  'StudyDescription',
                  'StudyDate',
                  'StudyTime',
                  'PatientID',
                  'Manufacturer']

    SERIES_TAGS = ['SeriesDescription',
                   'ProtocolName',
                   'SequenceName']

    INSTANCE_TAGS = ['AcquisitionTime',
                     'Rows',
                     'Columns',
                     'TriggerTime',
                     'SliceLocation',
                     'SliceThickness',
                     'PixelRepresentation',
                     'PixelSpacing',
                     'ImageOrientation',
                     'ImageOrientationPatient',
                     'ImagePosition',
                     'ImagePositionPatient']

    # --- CONSTRUCTOR ---
    def __init__(self,
                 _source='',
                 _study_instance_uid=None,
                 _dcmdir=None):
        """
        Create an empty object.
        To read a folder, use CMRStudy().from_folder(...)
        To read from a JSON file, use CMRStudy().from_file(...)
        """
        if _dcmdir is None:
            _dcmdir = dict()

        self.source = _source
        self.study_instance_uid = _study_instance_uid
        self.dcmdir = _dcmdir

    # --- CONSTRUCTOR: FROM A FOLDER ---
    @classmethod
    def from_folder(cls, folder_name, verbose=True):
        """
        Static constructor of a CMRStudy object.

        :param folder_name: a folder that contains a CMR study. It must contain 1 study.
        :param verbose: set false if you want quite construction.
        :return: a CMRStudy object
        """

        # check folder_name
        if not os.path.isdir(folder_name):
            raise ValueError('{} is not a folder'.format(folder_name))

        # collect all files from the given folder
        all_files = []
        for root, subFolders, files in os.walk(folder_name):
            if len(files) > 0:
                all_files += [os.path.join(root, f) for f in files]
        if verbose:
            print('Found {} files inside {} folder'.format(len(all_files), folder_name))

        # process all files
        study_iuid = None
        dd = dict()
        for f in all_files:
            # read as dicom
            dcm = read_dicom(f)
            if dcm is None:
                continue

            # add a study
            if study_iuid is None:
                study_iuid = dcm.StudyInstanceUID
                if verbose:
                    print('Study Instance UID = {} ()'.format(study_iuid, dcm.StudyDescription))

                # add study into dd
                for t in cls.STUDY_TAGS:
                    dd[t] = cls.get_tag(dcm, t)

                dd['Series'] = {}

            assert study_iuid == dcm.StudyInstanceUID, "Found 2 StudyInstanceUID. The folder must contain 1 study."

            # add a series
            series_iuid = dcm.SeriesInstanceUID
            if series_iuid not in dd['Series']:
                dd['Series'][series_iuid] = {s: cls.get_tag(dcm, s) for s in cls.SERIES_TAGS}
                dd['Series'][series_iuid]['Instances'] = {}
                if verbose:
                    print('Found new series: {} ({})'.format(series_iuid, dcm.SeriesDescription))

            # add new instance
            sop_iuid = dcm.SOPInstanceUID
            assert sop_iuid not in dd['Series'][series_iuid]['Instances'], "Duplicate SOPInstanceUID is found!!"

            new_instance = {s: cls.get_tag(dcm, s) for s in cls.INSTANCE_TAGS}
            new_instance['Filename'] = f.replace(os.path.join(folder_name, ''), '')

            dd['Series'][series_iuid]['Instances'][dcm.SOPInstanceUID] = new_instance

        # create & return instance
        return cls(_source=folder_name, _study_instance_uid=study_iuid, _dcmdir=dd)

    # --- CONSTRUCTOR: FROM A FILE ---
    @classmethod
    def from_file(cls, file_name):
        dd = cls

        return dd

    # --- GET A TAG VALUE ---
    @staticmethod
    def get_tag(dcm, tag_name):
        """
        Safely get a DICOM tag value.

        :param dcm: a DICOM structure return from pydicom.read
        :param tag_name: a DICOM tag
        :return: DICOM tag's value
        """

        if tag_name in dcm:
            val = dcm.get(tag_name)
            if type(val) == bytes:
                val = val.decode().split('\\')
            elif type(val) == dicom.multival.MultiValue:
                val = list(map(float, val))
            elif type(val) == dicom.valuerep.DSfloat:
                val = float(val)
        else:
            val = None

        return val

    def is_empty(self):
        return len(self.dcmdir)==0

    def __repr__(self):
        if self.is_empty():
            return "An empty CMRStudy"

        message = "CMRStudy from: {}\n".format(self.source)
        for t in self.STUDY_TAGS:
            message += "{}: {}\n".format(t, self.dcmdir[t])

        message += "Series:\n"
        for i, s in enumerate(self.dcmdir['Series']):
            message += "{:3d}. SeriesInstanceUID: {}\n".format(i+1, s)
            message += "     SeriesDescription: {}\n".format(self.dcmdir['Series'][s]['SeriesDescription'])
            message += "     Number of images: {}\n".format(len(self.dcmdir['Series'][s]['Instances']))

        return message
