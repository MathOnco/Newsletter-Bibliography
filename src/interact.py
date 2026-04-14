
from src.postprocessing import _iter_issue_entries
from src.utils import get_parsed_bibliography


def get_doi_list():
    """
    Load the bibliography in the form of a list of DOIS to be used for Scopus.
    """
    # load bibliography
    bib_content_parsed = get_parsed_bibliography()

    # init output list
    doi_list = []

    for entry in bib_content_parsed.entries:
        doi = bib_content_parsed.entries[entry].fields.get("doi")
        if doi is not None:
            doi_list.append(doi)

    # return list of DOIs
    return doi_list


def get_formatted_doi_list_for_scopus():
    """
    Load the bibliography in the form of a list of DOIS to be used for Scopus, formatted as a string.
    """
    doi_list = get_doi_list()
    doi_list_formatted = " OR ".join([f"DOI({doi})" for doi in doi_list])
    return doi_list_formatted


def main():
    print(get_formatted_doi_list_for_scopus())
