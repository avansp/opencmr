# -*- coding: utf-8 -*-
"""Managing cardiac MRI directory structure.

This module contains a single class CMRDir to manage/extract cardiac MR
directory structure. The directory should contains a cardiac MRI study.
"""
import pydicom as dicom
import os
import json
from .dicom_ext import read_dicom

__date__ = "15 January 2018"
__author__ = "Avan Suinesiaputra"


class CMRDir:
    """Managing cardiac MRI directory structure.

    Constants:
       STUDY_TAGS: list of DICOM header tags on a study level.
       SERIES_TAGS: list of DICOM header tags on a series level.
       INSTANCE_TAGS: list of DICOM header tags on an instance level.

    Attributes:
       studyName: name of a study
       dicomDir: the directory structure
    """

    STUDY_TAGS = ['StudyInstanceUID',
                  'StudyDescription',
                  'StudyDate',
                  'StudyTime',
                  'PatientID',
                  'Manufacturer']

    SERIES_TAGS = ['SeriesInstanceUID',
                   'SeriesDescription',
                   'ProtocolName',
                   'SequenceName']

    INSTANCE_TAGS = ['SOPInstanceUID',
                     'AcquisitionTime',
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

    # ---- CONSTRUCTOR ----
    def __init__(self, study_name=None):
        """Constructor."""
        self.source = ""
        self.studyName = study_name
        self.dicomDir = dict()

    # ---- PRINT OUT THE SUMMARY ----
    def __str__(self):
        """Default printing this object."""
        s = self.studyName + ' ({} studies):\n'.format(len(self.dicomDir.keys()))
        for studyIUID in self.dicomDir.keys():
            for t in self.STUDY_TAGS:
                if t in self.dicomDir[studyIUID]:
                    s = s + '  {}: {}\n'.format(t, self.dicomDir[studyIUID][t])
            s = s + '  {} ({} series):\n'.format(studyIUID, len(self.dicomDir[studyIUID].keys()))
            for seriesIUID in self.get_series_uids(studyIUID):
                s = s + '    {}: {} files\n'.format(
                    seriesIUID,
                    len(self.get_filenames(studyIUID, seriesIUID))
                )
                for t in self.SERIES_TAGS:
                    if t in self.dicomDir[studyIUID][seriesIUID]:
                        s = s + '      {}: {}\n'.format(t, self.dicomDir[studyIUID][seriesIUID][t])

        return (s)

    # ---- READ FROM FOLDER
    @classmethod
    def from_folder(cls, dicomFolder, studyName=None, quiet=True):
        """Read DICOM directory structure from a cardiac MRI folder."""
        # read dicomFolder
        if not os.path.isdir(dicomFolder):
            raise ValueError('Not a folder')

        # assign study name
        D = cls(studyName) if studyName is not None else cls(os.path.basename(dicomFolder))
        D.source = dicomFolder

        # generate all files from the given folder
        allFiles = []
        for root, subFolders, files in os.walk(dicomFolder):
            if len(files) > 0:
                allFiles += [os.path.join(root, f) for f in files]

        print(len(allFiles))

        for f in allFiles:
            # read as dicom
            dcm = read_dicom(f)

            if dcm is None:
                if not quiet:
                    print('Cannot open file {} as a DICOM'.format(f))
                continue

            # add study
            studyIUID = dcm.StudyInstanceUID
            if studyIUID not in D.dicomDir:
                D.dicomDir[studyIUID] = {s: cls.get_tag(dcm, s) for s in D.STUDY_TAGS}

            # add series
            seriesIUID = dcm.SeriesInstanceUID
            if seriesIUID not in D.dicomDir[studyIUID]:
                D.dicomDir[studyIUID][seriesIUID] = {s: cls.get_tag(dcm, s) for s in D.SERIES_TAGS}

            # add new instance
            newInstance = {s: cls.get_tag(dcm, s) for s in D.INSTANCE_TAGS}
            newInstance['Filename'] = f.replace(os.path.join(dicomFolder, ''), '')
            D.dicomDir[studyIUID][seriesIUID][dcm.SOPInstanceUID] = newInstance

        return D

    # ---- GET A TAG ----
    @classmethod
    def get_tag(cls, dcm, tagName):
        """Safely get a DICOM tag value."""
        if tagName in dcm:
            val = dcm.get(tagName)
            if type(val) == bytes:
                val = val.decode().split('\\')
            elif type(val) == dicom.multival.MultiValue:
                val = list(map(float, val))
            elif type(val) == dicom.valuerep.DSfloat:
                val = float(val)
        else:
            val = None

        return val

    # ---- CHECK EMPTY ----
    def is_empty(self):
        """True if the directory is empty."""

        return len(self.dicomDir)==0

    # ---- GET LIST OF STUDY INSTANCE UIDS
    def get_study_uids(self):
        """Return a list of StudyInstanceUIDs."""
        return list(self.dicomDir.keys())

    # ---- GET LIST OF SERIES INSTANCE UIDS
    def get_series_uids(self, studyUID):
        """Return a list of SeriesInstanceUIDs."""
        return list(set.difference(set(self.dicomDir[studyUID].keys()), set(self.STUDY_TAGS)))

    # ---- GET LIST OF SOP INSTANCE UIDS
    def get_sop_uids(self, studyUID, seriesUID):
        """Return a list of SOPInstanceUIDs."""
        return list(set.difference(set(self.dicomDir[studyUID][seriesUID].keys()), set(self.SERIES_TAGS)))

    # ---- GET LIST OF FILENAMES FROM A STUDY, SERIES, OPTIONALLY FRAME
    def get_filenames(self, studyUID, seriesUID, frame=None):
        """Return list of filenames from a given study and series UIDs.

        Input: studyUID is the Study Instance Unique ID
               seriesUID is the Series Instance Unique ID
               frame is the frame number, which is ordered based on TriggerTime from the middle slice.
        """
        files = [self.dicomDir[studyUID][seriesUID][s]['Filename'] for s in self.get_sop_uids(studyUID, seriesUID)]

        if frame is None:
            return files
        else:

            return files

    # --- GET LIST OF ALL FILENAMES
    def get_all_filenames(self):
        """Return list of all filenames"""
        return [self.dicomDir[studyUID][seriesUID][s]['Filename']
                for studyUID in self.get_study_uids()
                for seriesUID in self.get_series_uids(studyUID)
                for s in self.get_sop_uids(studyUID, seriesUID)]

    # ---- GET LIST OF X FROM A STUDY, SERIES
    def get_something_from_series(self, studyUID, seriesUID, something):
        """Return a list of something from a given study and series UIDs."""
        return [self.dicomDir[studyUID][seriesUID][s][something] for s in self.get_sop_uids(studyUID, seriesUID)]

    # --- GET PATIENT ID
    def get_patient_id(self, studyUID=None):
        if studyUID is None:
            ids = list(self.dicomDir.keys())
            if len(ids) == 0:
                return None
            studyUID = ids[0]

        return self.dicomDir[studyUID]['PatientID']

    # ---- SAVE
    def save(self, filename):
        """Save DICOM directory structure to a file."""
        with open(filename, 'w') as f:
            json.dump({
                'source': self.source,
                'studyName': self.studyName,
                'dicomDir': self.dicomDir
            }, f)
        f.close()

    # ---- READ FROM FILE
    @classmethod
    def from_file(cls, filename):
        """Read DICOM directory from a JSON file."""
        with open(filename, 'r') as f:
            D = json.load(f)
        f.close()

        # construct
        new_dir = cls(D['studyName'])
        new_dir.source = D['source']
        new_dir.dicomDir = D['dicomDir']

        return new_dir