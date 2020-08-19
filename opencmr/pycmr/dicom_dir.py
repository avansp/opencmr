# -*- coding: utf-8 -*-
"""Managing DICOM directory structure.

"""
import os
import logging
from .dicom_ext import read_dicom

__date__ = "19 August 2020"
__author__ = "Avan Suinesiaputra"

logger = logging.getLogger("opencmr.DicomDir")


class DicomDir:

	SERIES_TAGS = ['SeriesInstanceUID', 'SeriesNumber', 'SeriesDescription', 'ProtocolName', 'SequenceName']
	STUDY_TAGS = ['StudyInstanceUID', 'StudyDescription', 'PatientID', 'StudyDate', 'StudyTime', 'Modality']
	IMAGE_TAGS = [
		'SOPInstanceUID', 'AcquisitionTime',
		'Rows', 'Columns', 'TriggerTime',
		'SliceLocation', 'SliceThickness',
		'PixelRepresentation', 'PixelSpacing',
		'ImageOrientationPatient', 'ImagePositionPatient',
		'SmallestImagePixelValue', 'LargestImagePixelValue'
	]

	def __init__(self, folder):
		assert os.path.isdir(folder), logger.error(f"Directory '{folder}' does not exist")

		# initialise the dicom directory dictionary
		self.dcmdir = {'RootFolder': folder}
		self.scan()

	def scan(self, folder=None):
		"""
		Scan a folder to update the self.dcmdir structure.
		Default folder is self.dcmdir['RootFolder']
		"""

		if folder is None:
			folder = self.dcmdir['RootFolder']

		# generate all files from the given folder
		all_files = []
		for root, subFolders, files in os.walk(folder):
			if len(files) > 0:
				all_files += [os.path.join(root, f) for f in files]

		logger.debug(f"Scan {folder}. Found {len(all_files)} files.")

		# collect necessary tags for all files
		TAGS = self.SERIES_TAGS + self.STUDY_TAGS + self.IMAGE_TAGS
		all_tags = []
		for f in all_files:
			# read as dicom
			dcm = read_dicom(f)

			if dcm is None:
				logger.debug(f"{f.replace(self.dcmdir['RootFolder'], '')} is not a DICOM file.")
				continue

			# new tag
			new_tag = {tag: getattr(dcm, tag) if hasattr(dcm, tag) else None for tag in TAGS}
			new_tag['Filename'] = f.replace(self.dcmdir['RootFolder'],'')

			# second attempt for ImageOrientationPatient & ImagePositionPatient
			for tt, old_tt in [('ImageOrientationPatient', 'ImageOrientation'), ('ImagePositionPatient', 'ImagePosition')]:
				if new_tag[tt] is None:
					new_tag[tt] = getattr(dcm, old_tt) if hasattr(dcm, old_tt) else None

			# append
			all_tags.append(new_tag)

		# we can check now if there are multiple studies / patients
		assert len(set([t['StudyInstanceUID'] for t in all_tags])) == 1, logger.error("There are multiple studies in this folder.")
		assert len(set([t['PatientID'] for t in all_tags])) == 1, logger.error("There are multiple studies in this folder.")

		# build the dicom directory
		self.dcmdir['RootFolder'] = folder
		self.dcmdir.update({t: all_tags[0][t] for t in self.STUDY_TAGS})
		self.dcmdir['Series'] = []

		# scan series: identify with couple of (SeriesInstanceUID, SeriesNumber)
		series = set([(t['SeriesInstanceUID'], t['SeriesNumber']) for t in all_tags])
		logger.debug(f"Found {len(series)} series")
		for ser_uid, ser_num in series:
			# find items with this series
			ser_items = [t for t in all_tags if t['SeriesInstanceUID'] == ser_uid and t['SeriesNumber'] == ser_num]

			# build new series
			new_series = {t: ser_items[0][t] for t in self.SERIES_TAGS}
			new_series['Images'] = [{img_tag: ss[img_tag] for img_tag in ['Filename'] + self.IMAGE_TAGS} for ss in ser_items]

			# append
			self.dcmdir['Series'].append(new_series)

		# info
		logger.info(f"Scanned {self.dcmdir['RootFolder']}")
		logger.info(f"Patient ID = {self.dcmdir['PatientID']}")
		logger.info(f"Number of series = {len(self.dcmdir['Series'])}")
		for i, s in enumerate(self.dcmdir['Series']):
			logger.info(f"[{i:2d}]: SeriesNumber {s['SeriesNumber']}: {len(s['Images'])} image{'s' if len(s['Images'])>1 else ''}")

	def __repr__(self):
		msg = f"RootFolder: {self.dcmdir['RootFolder']}"
		if len(self.dcmdir) == 1:
			msg += f"\nDirectory is still empty. Call scan() method to create a DICOM directory."
			return msg

		for s in self.STUDY_TAGS:
			msg += f"\n{s}: {self.dcmdir[s]}"

		msg += f"\nContains {len(self.dcmdir['Series'])} series:"
		for s in self.dcmdir['Series']:
			msg += f"\n  Series {s['SeriesNumber']}: {len(s['Images'])} image{'s' if len(s['Images'])>1 else ''}"

		return msg

