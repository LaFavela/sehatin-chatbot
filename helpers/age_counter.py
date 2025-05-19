from datetime import datetime

def age_counter(birthdate):
    """
    Calculate age based on the given ISO 8601 birthdate.

    :param birthdate: Birthdate in ISO 8601 format (e.g., "1981-02-12T00:00:00.000000Z")
    :return: Age in years
    """
    birth_date = datetime.strptime(birthdate, '%Y-%m-%dT%H:%M:%S.%fZ')
    today = datetime.utcnow()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age