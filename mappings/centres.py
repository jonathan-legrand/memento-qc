def fetch_centre(rsfmri, participants):
    participant_id = rsfmri.dirname.split("/")[4]
    return str(participants.loc[participants.participant_id == participant_id, "centre"].values[0]) 
