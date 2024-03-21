import json
import logging
from pathlib import Path
from collections import Counter
import numpy as np
import pybtex.scanner
from tqdm import tqdm
from pybtex.database import BibliographyData
from pybtex.database import parse_string as bibtex_parse_string
from unidecode import unidecode


logging.basicConfig(level=logging.INFO)


def print_info(issues_file: str):
    """
    Print basic information regarding the issues_file file.
    """
    # load issues.json
    with open(issues_file, "r") as infile:
        issues_dict = json.load(infile)

    # get total numer of issues
    logging.info(f"Total number of issues: {len(issues_dict.keys())}")

    # get total number of papers
    n_papers_per_issue = {issue_number: len(papers) for issue_number, papers in issues_dict.items()}
    n_papers = sum(n_papers_per_issue.values())
    logging.info(f"The total number of papers is: {n_papers}")

    # get all DOIs
    all_DOIs = [paper["DOI"] for papers in issues_dict.values() for paper in papers]
    # get number of papers without DOI
    n_no_DOI = len([doi for doi in all_DOIs if doi is None])
    logging.info(f"Could not find DOI for {n_no_DOI} / {n_papers} ({(n_no_DOI / n_papers) * 100:.2g}%)")

    # write papers without doi
    papers_no_DOI =[{"title": paper["title"], "link": paper["link"], "issue": int(issue)}
                    for issue, papers in issues_dict.items() for paper in papers if paper["DOI"] is None]
    with open("out/null_papers.json", "w") as outfile:
        json.dump(papers_no_DOI, outfile, indent=2)

    # check if there are duplicates
    papers_with_DOI = [doi for doi in all_DOIs if doi is not None]
    unique_DOIs, counts = np.unique(np.array(papers_with_DOI), return_counts=True)
    duplicated_DOIs = list(unique_DOIs[counts > 1])
    logging.info(f"N duplicates between papers with DOI: {len(duplicated_DOIs)}")


def remove_duplicates(issues_file: str, output_file: str = None):
    """
    Remove duplicates from the issues file (.json)
    """
    # load issues json file
    with open(issues_file, "r") as infile:
        issues_dict = json.load(infile)

    # get dois for all papers
    all_dois = [paper["DOI"] for papers in issues_dict.values() for paper in papers]

    # check if there are duplicates
    papers_with_DOI = [doi for doi in all_dois if doi is not None]
    unique_DOIs, counts = np.unique(np.array(papers_with_DOI), return_counts=True)
    duplicated_DOIs = list(unique_DOIs[counts > 1])
    logging.info(f"N duplicates between papers with DOI: {len(duplicated_DOIs)}")

    # Remove duplicates
    unique_issues_dict = {}  # init new dict
    duplicates_counter = Counter({doi: 0 for doi in duplicated_DOIs})  # init counter
    for issue, papers_list in issues_dict.items():
        unique_issues_dict[issue] = []  # init issues
        for paper in papers_list:
            # get doi
            doi = paper["DOI"]  
            # if doi in duplicates and was not added, add it
            if (doi not in duplicated_DOIs):  
                unique_issues_dict[issue].append(paper)
            else:
                if duplicates_counter[doi] == 0:
                    unique_issues_dict[issue].append(paper)
                    duplicates_counter[doi] += 1

    # sort dict
    sorted_dict = dict(sorted(unique_issues_dict.items(), key=lambda t: int(t[0]), reverse=True))

    # Write json without duplicates
    if output_file is None:
        with open(issues_file, "w") as out_file:
            json.dump(unique_issues_dict, out_file)
    else:
        with open(output_file, "w") as out_file:
            json.dump(unique_issues_dict, out_file, indent=2)


def bibtex_writer(issues_file: str):
    # load json file
    out_json_file = Path(issues_file)
    with open(out_json_file, "r") as infile:
        input_dict = json.load(infile)

    # convert each key to int
    sorted_dict = dict(sorted(input_dict.items(), key=lambda t: int(t[0]), reverse=True))

    # set up pbar file
    pbar_file = open(Path("../pbar.o"), "w")

    # iterate
    logging.info(f"Writing .bib")
    with open(f"out/mathonco_issues.bib", "w") as bib_file:
        for issue_number, papers_list in tqdm(sorted_dict.items(), file=pbar_file):
            bib_file.write(f"//MathOnco Issue {issue_number}\n")
            for paper in papers_list:
                if paper["bibtex"] is not None:
                    # parse entry
                    try:
                        parsed_bibtex = bibtex_parse_string(paper["bibtex"], "bibtex")
                    except pybtex.scanner.TokenRequired:
                        logging.info(f"Something wrong with the entry: {paper['bibtex']}")
                        continue
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
                    # format bibtex
                    formatted_bibtex = parsed_bibtex.to_string('bibtex')
                    # write to file
                    bib_file.write(formatted_bibtex)
                    bib_file.write("\n")
    
    # close pbar
    pbar_file.close()


def text_file_writer(issues_file: str = "mathonco-newsletter/issues_no_duplicates.json"):
    """
    Write column text file with all DOIs of the mathonco papers
    """
    # load json file
    out_json_file = Path(issues_file)
    with open(out_json_file, "r") as infile:
        input_dict = json.load(infile)

    # Generate dict where each DOI is coupled with the issue number
    doi_issue_number_list = [{"DOI": paper["DOI"], "Issue": int(issue_number)}
                             for issue_number, papers_list in input_dict.items()
                             for paper in papers_list if paper["DOI"] is not None]
    
    # sort list
    doi_issue_number_list.sort(key=lambda e: e["Issue"], reverse=True)
    
    # set output file
    column_file = Path("out/mathonco_DOIs.txt")
    column_file_annotated = Path("out/mathonco_DOIs_annotated.txt")

    # write text
    column_file_txt = ""
    column_file_annotated_txt = ""
    for element in doi_issue_number_list:
        column_file_txt += f"{element['DOI']}\n"
        column_file_annotated_txt += f"{element['DOI']} # Issue {element['Issue']}\n"

    # write on file
    with open(column_file, "w") as out_file:
        out_file.write(column_file_txt)
    with open(column_file_annotated, "w") as out_file:
        out_file.write(column_file_annotated_txt)


def main():
    # 1. Remove duplicates 
    remove_duplicates("out/issues.json", "out/issues_no_duplicates.json")

    # # 2. Write bibtex
    bibtex_writer("out/issues_no_duplicates.json")

    # # 3. DOI file
    # text_file_writer()


if __name__ == "__main__":
    main()
