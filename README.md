# MathOnco References 
> A collection of the references collected on [This Week in Mathematical Oncology](https://thisweekmathonco.substack.com/) 

## Access the collection
Everything is in the `res` folder! 
- `res/MathOncoBibliography.bib` -> All MathOnco papers.
- `res/single_issues/*.bib` -> MathOnco papers divided per issue
- `res/single_years/*.bib` -> MathOnco papers divided per year 

## Follow the blog
Stay updated on conferences, jobs, papers and preprints in Mathematical Oncology following [This Week in Mathematical Oncology](https://thisweekmathonco.substack.com/)

## Code 
In case you want to generate the `bib` files on your own.

### Setup
Add a config file:
```bash
touch config.json
```
Add your email to the config file:
```json
{
    "email": "youremail@example.xy"
}
```

## Code
- `src/scraper.py` -> Scrape the papers from MathOnco issues. Try running 
    ```python
    python3 src/scraper.py --help
    ```

- `src/postprocessing.py` -> Clean references, produce `.bib` file

- `src/utils.py` -> functions to split and reorganize the references

- `requirements.txt` -> Dependencies for the code
