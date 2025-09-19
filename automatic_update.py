# This file automatically updates the bibliography thanks to GitHub Actions
import requests
from bs4 import BeautifulSoup
import pybtex.scanner
from src.scraper import get_publications_from_issue, enrich_publications
from pybtex.database import BibliographyData
from pybtex.database import parse_string as bibtex_parse_string
from unidecode import unidecode


### --- Read Latest Issue Number --- ###
with open("res/MathOncoBibliography.bib", "r") as f:
    latest_issue = f.readline().strip()
latest_issue_number = int(latest_issue.split(" ")[-1])

### --- Iterate on issues until you find the last --- ###

while True:
    ### --- Check if new issue exists --- ###
    new_issue_number = latest_issue_number + 1
    new_issue_url = f"https://thisweekmathonco.substack.com/p/this-week-in-mathonco-{new_issue_number}"
    response = requests.get(new_issue_url, headers={'User-Agent': 'Mozilla/5.0'})
    # if status code is 404, exit the loop. Else, raise for status and go on
    if response.status_code == 404:
        print(f"No new issue found. Latest issue is {new_issue_number - 1}.")
        break
    else:
        response.raise_for_status()
    latest_issue_number = new_issue_number
    print(f"New issue found: {new_issue_number}")

    ### --- If new issue exist, extract publications --- ###
    mathonco_issue_html = response.text                             # get html
    html_soup = BeautifulSoup(mathonco_issue_html, 'html.parser')   # parse html
    new_issue_dict = get_publications_from_issue(html_soup, new_issue_number)
    new_issue_dict = enrich_publications(new_issue_dict, new_issue_number)

    ### --- Create string with formatted bibliography --- ###
    formatted_bib = f"//MathOnco Issue {new_issue_number}\n"
    for pub in new_issue_dict[new_issue_number]:
        # get bibtex
        pub_bib = pub.get("bibtex")

        # parse
        try:
            parsed_bibtex = bibtex_parse_string(pub_bib, "bibtex")
        except pybtex.scanner.TokenRequired:
            print(f"Something wrong with the entry: {pub_bib}")
            raise pybtex.scanner.TokenRequired
        # get bibtex label and entry
        bib_label, bib_entry = list(parsed_bibtex.entries.items())[0]
        
        # create label in the format surnameYEARfirstword, where:
        # - surname is the surname of the first author
        # - YEAR is the year of the paper
        # - first word is the first word of the title

        # get surname
        authors_list = list(bib_entry.persons.values())
        if len(authors_list) == 0:
            continue
        first_author_surname = authors_list[0][0].last_names[0]
        first_author_surname = first_author_surname.lower()
        first_author_surname = unidecode(first_author_surname)
        # get year
        year = bib_entry.fields["year"]
        # get first_word
        first_word, _ = bib_entry.fields["title"].split(" ", 1)
        if len(first_word) <= 3:
            word_1, word_2, _ = bib_entry.fields["title"].split(" ", 2)
            first_word = f"{word_1}{word_2}"
        first_word = first_word.lower()
                    
        # set label of the bibtex
        parsed_bibtex = BibliographyData({
            f"{first_author_surname}{year}{first_word}": bib_entry
        })

        # add formatted bib
        formatted_bib += parsed_bibtex.to_string('bibtex')
        formatted_bib += "\n"

    ### --- Write formatted bibliography to file --- ###
    # write single issue to file
    single_issue_file = f"res/single_issues/issue_{new_issue_number}.bib"
    with open(single_issue_file, "w") as f:
        f.write(formatted_bib)

    # prepend complete file
    with open("res/MathOncoBibliography.bib", "r") as f:
        big_bib = f.read()
    with open("res/MathOncoBibliography.bib", "w") as f:
        f.write(formatted_bib)
        f.write(big_bib)
