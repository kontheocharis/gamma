
def get_key_from_value_in_dict(val: int, dictionary: dict):
    '''To get key from value (input) in a dictionary.'''

    for key, value in dictionary.items():

        if val == value:
            return key

    return 'Key doesnt exist.'
