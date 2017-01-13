import re


def strip_name(uri):
    return uri.split('/')[-1]


def convert_to_internal_wikipedia_link(uri):
    entity_name = strip_name(uri)
    return '/wiki/' + entity_name


def convert_to_wikipedia_uri(uri):
    entity_name = strip_name(uri)
    return 'https://en.wikipedia.org/wiki/' + entity_name


def strip_cleaned_name(uri):
    """
    http://dbpedia.org/resource/Alain_Connes -> 'Alain Connes'
    """
    entity_name = strip_name(uri)
    entity_name = entity_name.replace('_', ' ')
    return clean_input(entity_name)


def clean_input(input):
    """
    Sanitize text - remove multiple new lines and spaces - get rid of non ascii chars
    and citations - strip words from punctuation signs - returns sanitized string
    """
    input = re.sub('\n+', " ", input)
    input = re.sub(' +', " ", input)

    # get rid of non-ascii characters
    input = re.sub(r'[^\x00-\x7f]', r'', input)

    # get rid of citations
    input = re.sub(r'\[\d+\]', r'', input)
    cleanInput = []
    input = input.split(' ')
    for item in input:
        # item = item.strip('?!;,')
        if len(item) > 1 or (item.lower() == 'a' or item == 'I'):
            cleanInput.append(item)
    return ' '.join(cleanInput).encode('utf-8')
