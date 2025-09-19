"""
Scrape MathOnco Newsletter. Get json file containing papers for each issue.
"""
import re
import json
import argparse
import logging
from pathlib import Path
from difflib import SequenceMatcher
import requests
from tqdm import tqdm
from bs4 import BeautifulSoup
from crossref.restful import Works, Etiquette
from habanero import cn


# config logger
logging.basicConfig(level=logging.INFO)

# get etiquette for CrossRef
config = {
    "email": "franco.pradelli94@gmail.com"
}
my_etiquette = Etiquette('Newsletter Bibliography Scraper', '1.0', '...', config["email"])


def cli():
    """
    CLI for the program
    """
    parser = argparse.ArgumentParser(description="MathOnco Issue Scraper. \
                                                  Get the DOI and other info from a MathOnco Issue.")
    # add mutually exclusive group for input
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument("--url", "-u",
                             type=str,
                             help="URL of a MathOnco issue")
    input_group.add_argument("--directory", "-d",
                             type=str,
                             help="Directory containing HTML files")
    input_group.add_argument("--file", "-f",
                             type=str,
                             help="HTML file of a mathonco issue")
    
    # add flag for output format
    parser.add_argument("--output_format",
                        type=str,
                        help="Output format for the scraped papers (you can choose among those supported by CrossRef API https://api.crossref.org/v1/styles)")

    return parser.parse_args()


def get_issue_number(input_issue: str) -> int:
    """
    Get the issue number for the given html name or URL
    """
    # init issue number
    issue_number = None
    # create list of possible formats
    possible_formats = [
        "issue-",
        "this-week-in-mathonco-",
        "this-week-in-math-onco-"
    ]
    # check the name format
    for name_format in possible_formats:
        if name_format in input_issue:
            issue_number_text = re.search(rf'{name_format}\d+', str(input_issue)).group()
            issue_number = issue_number_text.split("-")[-1]
    
    # log
    logging.info(f"Parsed MathOnco Issue ({input_issue}): {issue_number}")
    # return it as int
    return int(issue_number)


def get_publications_from_issue(soup: BeautifulSoup, issue_number: int) -> dict:
    """
    Get publications from the MathOnco issue and return them as dict.

    :param soup: parsed html of the MathOnco issue.
    """
    # The Mathonco issue formatting changes at issue number 140. Thus, different rules are used 
    # depending on the issue number.
    if issue_number < 141:
        # visually inspecting the document, I found out that the interesting sections are under the
        # the h3 tag. You can check it yourself doing:
        # > for section in soup.find_all('h3'):
        # >     print(section.find('strong'))

        # Thus, filter the '#MathOnco Publications'
        publications_header = '#MathOnco Publications'
        section_publications = [section for section in soup.find_all('h3')
                               if publications_header in str(section)]
        if len(section_publications) == 1:
            section_publications = section_publications[0]
        else:
            section_publications = None
        
        # now, we need to get all the links and titles contained in that section. These are not formatted as
        # children but as brother elements in the documents with the tag 'a'. This, we need to get all the 
        # 'a' elements between the '#MathOnco Publications' section and the following.

        # get following section
        if section_publications is None:
            following_section = None
        else:
            following_section = section_publications.find_next('h3')
    else:
        # visually inspecting the document, I noticed that the different sections are divided by a banner.
        # There is a banner for publications, a banner for preprints, etc.
        # All the banner are under the tag 'source' and the link to the banner image is the field 'srcset'.
        # Thus, knowing the name of the image of the publications section and of the preprint sections,
        # we can identify the papers contained in between.
        # Sometimes there are no preprints. Thus, we iterate over the other sections in order to find the follwoing one.
        publications_banner_name = "fabab95d-eefe-45a0-b47e-77fc63cde5de_1024x250.png"
        preprints_banner_name = "58c80455-f0b6-43db-830a-0f73b96ead1e_1024x250.png"
        in_the_news_banner_name = "2F104440ac-3cbf-4dd2-bf8b-a4f8b11035f5_1024x250.png"
        featured_artwork_banner_name = "2F0feba771-e36d-4595-9841-f9ee8872be92_1024x250.jpeg"
        resources_banner_name = "2F1717140c-562f-4f59-8459-4c2c1a1caa48_1024x250.png"
        section_publications = None
        following_section = None
        for image in soup.find_all("source"):
            srcset = image.get('srcset')
            # get publication section
            if publications_banner_name in srcset:
                section_publications = image
            # get following section
            if preprints_banner_name in srcset:
                following_section = image
            elif in_the_news_banner_name in srcset:
                following_section = image
            elif featured_artwork_banner_name in srcset:
                following_section = image
            elif resources_banner_name in srcset:
                following_section = image
            # when you found both, break
            if (section_publications is not None) and (following_section is not None):
                break
    
    if (section_publications is None) or (following_section is None):
        logging.info(f"Found no papers section")
        issue_dict = {issue_number: []}
    else:
        # get all tags 'a' following the publications section
        all_next_a = section_publications.find_all_next('a')
        
        # get all tags 'a' before the following section
        all_prevous_a = following_section.find_all_previous('a')

        # get common elements
        intersection = list(set(all_next_a).intersection(all_prevous_a))

        # Again, visually inspecting the result I found out that not all common elements are papers.
        # papers can be selected just filtering out the elements conaining the 'class'
        publications = [element for element in intersection
                        if ('class' not in element.attrs.keys())]
        
        # store paper link and title in a dict
        issue_dict = {issue_number: [{"title": p.text, "link": p.get('href')} for p in publications]}

        # log
        logging.info(f"Found {len(issue_dict[issue_number])} papers")

    # return dict
    return issue_dict


def get_doi(title: str, crossref: Works = None) -> str:
    """
    Get DOI for publication given its title
    """
    # Define function to format titles for comparison
    format_title = lambda s: s.replace(" ", "").lower()

    # Format title eliminating spaces and uppercases
    formatted_title = format_title(title)

    # log
    logging.info(f"Retriving doi for paper: {title}")

    # Init CrossRef if necessary
    works = Works(etiquette=my_etiquette) if crossref is None else crossref

    # Iterate on the first N results
    search_limit = 100
    for i, element in enumerate(works.query(bibliographic=title).select('title', 'DOI')):
        # format title
        try:
            formatted_element_title = format_title(element["title"][0])
        except KeyError:
            logging.warning(f"Title not found in {element}")
            continue
        # check the sequence
        sm = SequenceMatcher(None, formatted_element_title, formatted_title)
        # if the similarity ratio is above 95%, get the DOI
        if sm.ratio() > 0.90:
            # if the title match, return DOI
            logging.info(f"Found DOI: {element['DOI']}")
            return element["DOI"]
        # Else return none
        if i > search_limit:
            logging.info(f"doi not found")
            return None
    

def get_formatted_citation(doi: str, citation_format: str = "bibtex") -> str:
    """
    Given the DOI, get the citation formatted in the given style (see supported formats here: https://api.crossref.org/v1/styles).
    Default is bibtex.
    """
    # use content negotiation from habanero to get bibtex
    if doi[0] == "/":
        current_doi = doi[1:]
    else:
        current_doi = doi
    bibtex = cn.content_negotiation(ids=current_doi, format=citation_format)
    return bibtex


def enrich_publications(issue_dict: dict, issue_number: int, citation_format: str = "bibtex") -> dict:
    """
    Enrich issue dict with DOI and BibTex
    """
    new_issue_dict = {issue_number: []}  # define new dict

    for article_dict in issue_dict[issue_number]:
        article_dict["DOI"] = get_doi(article_dict["title"])  # add DOI to each publication
        if article_dict["DOI"] is None:
            article_dict[citation_format] = None
        else:
            article_dict[citation_format] = get_formatted_citation(article_dict["DOI"], citation_format)
        new_issue_dict[issue_number].append(article_dict)  # append publication to the new dict

    return new_issue_dict


def main():
    # set some macros
    out_json_file = Path("out/issues.json")
    out_json_file.parent.mkdir(parents=True, exist_ok=True)

    # get cli
    args = cli()
    input_url = args.url

    # build input list given the user input
    if args.url is not None:
        # if the input is an URL; use requests to get the html text
        response = requests.get(input_url)
        if response.raise_for_status() is None:
            mathonco_issue_html = response.text
            # create a list of a single element
            mathonco_html_list = [mathonco_issue_html]
        else:
            response.raise_for_status()
            return 1
    elif args.directory is not None:
        # if the input is a directory, use athlib to create a generator of html files
        input_directory = Path(args.directory)
        mathonco_html_list = list(input_directory.glob("*.html"))
    elif args.file is not None:
        # if the input is a single html file, convert it to path
        mathonco_html_list = [Path(args.f)]
    else:
        logging.error("User input not recognized.")
        return 1

    # get the issues already parsed
    if out_json_file.exists():
        with open(out_json_file, "r") as infile:
            output_dict = json.load(infile)
            collected_issue_numbers = list(output_dict.keys())
    else:
        output_dict = {}
        collected_issue_numbers = []

    # set up pbar
    pbar_file = open("./pbar.o", "w")

    # iterate on the issues
    for issue in tqdm(mathonco_html_list, file=pbar_file):
        # make soup
        if isinstance(issue, Path):
            # if path, read it and make soup
            with open(issue, "r") as html_file:
                current_soup = BeautifulSoup(html_file, 'html.parser')
            # get issue number
            issue_number = get_issue_number(str(issue))
        else:
            # else, just make soup
            current_soup = BeautifulSoup(issue, 'html.parser')
            # get issue number
            issue_number = get_issue_number(args.url)

        # if number already done, skip
        if (str(issue_number) in collected_issue_numbers) or (issue_number in collected_issue_numbers):
            logging.info(f"Number already present in issues.json")
            continue

        # get issue dict containing the publications for the issue
        issue_dict = get_publications_from_issue(current_soup, issue_number)
        # enrich with DOI and formatted cit
        if args.output_format is None:
            issue_dict = enrich_publications(issue_dict, issue_number)
        else:
            issue_dict = enrich_publications(issue_dict, issue_number, citation_format=args.output_format)

        # extend output_dict
        if len(issue_dict[issue_number]) == 0:
            logging.warning(f"No papers found for issue {issue_number}")
        else:
            output_dict.update(issue_dict)

    # close pbar file
    pbar_file.close()

    # sort output dict
    sorted_dict = dict(sorted(output_dict.items(), key=lambda t: int(t[0]), reverse=True))

    # write
    with open(out_json_file, "w") as outfile:
        json.dump(sorted_dict, outfile, indent=2)


if __name__ == "__main__":
    main()
