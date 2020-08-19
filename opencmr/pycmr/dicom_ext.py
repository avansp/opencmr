"""Because some dicom files cannot be read, except if you use use_force = TRUE"""

import pydicom


def read_dicom(dcm_file):
    """ Safely read dicom file.

    :param dcm_file: a DICOM file
    :return: a pydicom.dataset.FileDataset or None
    """

    # read the dicom file with force
    dcm = pydicom.read_file(dcm_file, force=True)

    # if the file is read by force, you cannot get pixel_array because there is no TransferSyntaxUID.
    # we need to add it manually, and there is a workaround from StackOverflow:
    # https://stackoverflow.com/questions/44492420/pydicom-dataset-object-has-no-attribute-transfersyntaxuid

    if "TransferSyntaxUID" not in dcm.file_meta:
        dcm.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian  # default syntax

    if len(dcm) <= 1:
        dcm = None

    return dcm

