# MathOnco References 
> A collection of the references collected on [This Week in Mathematical Oncology](https://thisweekmathonco.substack.com/) 

## Setup
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

- `requirements.txt` -> Dependencies for the code

## Resources
- `res/MathOncoBibliography.bib` -> All MathOnco papers. 

## Follow the blog
Stay updated on conferences, jobs, papers and preprints in Mathematical Oncology following [This Week in Mathematical Oncology](https://thisweekmathonco.substack.com/)
