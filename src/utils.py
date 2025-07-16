import numpy as np
import pandas as pd
from pathlib import Path

def split_bib_per_issue(bib_file_txt = Path("res/MathOncoBibliograpy.bib")):
    """
    Split a bib file into separate issues
    """
    # generate output folder
    output_folder = bib_file_txt.parent / "single_issues"
    output_folder.mkdir(exist_ok=True)

    # read the bib file
    with open(bib_file_txt, "r") as f:
        bib_content = f.read()

    # split the bib file into separate issues
    issues = bib_content.split("//MathOnco Issue ")[1:]

    # get issue number
    issue_numbers = [issue.split("\n")[0] for issue in issues]
    issue_numbers = [int(n) for n in issue_numbers]

    # re-add the comment at the beginning of each issue
    issues = [f"//MathOnco Issue {issue}" for issue in issues]

    # write each issue to a separate file
    for issue, issue_number in zip(issues, issue_numbers):
        with open(output_folder / f"issue_{issue_number}.bib", "w") as f:
            f.write(issue)
    print(f"Split {len(issues)} issues into {output_folder}")


def split_single_bib_files_per_year(bib_file_txt = Path("res/MathOncoBibliograpy.bib")):
    """
    Split a bib file into separate years
    """
    # generate output folder
    output_folder = bib_file_txt.parent / "single_years"
    output_folder.mkdir(exist_ok=True)

    # read the bib file
    with open(bib_file_txt, "r") as f:
        bib_content = f.read()

    # split the bib file into separate issues
    issues = bib_content.split("//MathOnco Issue ")[1:][::-1]

    # get issue number
    issue_numbers = [issue.split("\n")[0] for issue in issues]
    issue_numbers = np.array([int(n) for n in issue_numbers], dtype=int)

    # re-add the comment at the beginning of each issue
    issues = [f"//MathOnco Issue {issue}" for issue in issues]

    # set up range of issues per year
    issues_per_year = {
        2017: [1, 2],
        2018: [3, 47],
        2019: [48, 95],
        2020: [96, 143],
        2021: [144, 190],
        2022: [191, 237],
        2023: [238, 279],
        2024: [280, 315],
        2025: [316, issue_numbers[-1]],
    }

    for year, issues_range in issues_per_year.items():
        # get index where the issues start and end
        start_range = np.nonzero(issue_numbers == issues_range[0])[0][0]
        stop_range = np.nonzero(issue_numbers == issues_range[1])[0][0]
        # get the issues for the year
        issues_for_year = issues[start_range : stop_range + 1]

        # write each issue to a separate file
        with open(output_folder / f"issues_in_year_{year}.bib", "w") as f:
            f.write("\n".join(issues_for_year))


def count_n_papers_per_year(single_years_folder = Path("res/single_years")):
    """
    Count the number of papers per year
    """
    n_papers_per_year = []
    for year_file in single_years_folder.glob("*.bib"):
        with open(year_file, "r") as f:
            # read the file 
            bib_content = f.read()
        # count the number of papers
        n_papers = bib_content.count("@article")
        n_papers_per_year.append({"Year": year_file.stem.split("_")[-1], "n_papers": n_papers})

    # save the results as csv
    pandas_df = pd.DataFrame(n_papers_per_year)
    pandas_df.to_csv("out/n_papers_per_year.csv", index=False)


if __name__ == "__main__":
    split_bib_per_issue()
    split_single_bib_files_per_year()
    count_n_papers_per_year()