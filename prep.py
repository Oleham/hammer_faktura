"""
module Prep contains helper functions to prepare datasets for entry into the database.
"""

def fromXTRF(jobber):
    """
    Prepares a set of jobs from XTRF for entry into the database.
    """
    
    fliste = []
    for jobb in jobber:

        id = jobb["overview"]["idNumber"]

        bsk = []
        bsk.append(jobb["overview"]["type"])
        bsk.append(jobb["overview"]["sourceLanguage"]["name"])
        bsk.append(jobb["overview"]["targetLanguages"][0]["name"])

        beskrivelse = " ".join(bsk)

        dato = jobb["overview"]["deliveryDate"] / 1000

        value = jobb["overview"]["jobValue"]["value"]

        fliste.append({
            "dato": dato,
            "id": id,
            "beskrivelse": beskrivelse,
            "netto": value,
        })

    return fliste