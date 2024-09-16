
def extract_info(fpath):
    """
    Evil hacking to get information from the path
    of imaging files in memento structure
    """

    month = fpath.__str__().split("/")[-2]
    subject_id = fpath.__str__().split("/")[-3][4:]
    
    # The centre is meant to be in the tsv file
    centre = fpath.__str__().split("/")[-4]

    return centre, month, subject_id