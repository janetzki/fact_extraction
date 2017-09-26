"""
Various methods for manipulation of URIs.
"""


def strip_name(uri):
    """
    Get the last part of a URI.

    :param uri: URI
    :return: last part of URI
    """
    return uri.split('/')[-1]


def convert_to_internal_wikipedia_link(uri):
    """
    Convert a URI to an internal Wikipedia link.

    :param uri: URI
    :return: internal Wikipedia link
    """
    entity_name = strip_name(uri)
    return '/wiki/' + entity_name


def convert_to_wikipedia_resource_uri(uri):
    """
    Convert a URI to a URI that points to a Wikipedia resource.

    :param uri: original URI
    :return: URI to Wikipedia resource
    """
    entity_name = strip_name(uri)
    return 'https://en.wikipedia.org/wiki/' + entity_name


def convert_to_dbpedia_resource_uri(uri):
    """
    Convert a URI to a URI that points to a DBpedia resource.

    :param uri: original URI
    :return: URI to DBpedia resource
    """
    entity_name = strip_name(uri)
    return 'http://dbpedia.org/resource/' + entity_name


def capitalize(uri):
    """
    Capitalize the first letter of the last part of a URI.

    :param uri: original URI
    :return: URI with capitalized letter
    """
    prefix, entity_name = uri.rsplit('/', 1)
    entity_name = entity_name[0].upper() + entity_name[1:]
    return prefix + '/' + entity_name


def strip_cleaned_name(uri):
    """
    Get the actual name of a resource linked by a URI.
    Example: 'http://dbpedia.org/resource/Alain_Connes' -> 'Alain Connes'

    :param uri: URI
    :return: actual name of the resource
    """
    entity_name = strip_name(uri)
    entity_name = entity_name.replace('_', ' ')
    # return clean_input(entity_name)
    return entity_name
