# Public release checklist

Complete these items immediately before creating the GitHub repository or Zenodo record:

- [ ] Replace the temporary author entry in `CITATION.cff` with the final ordered author list and ORCID identifiers.
- [ ] Confirm the repository owner and final repository name.
- [ ] Decide whether the inputs remain private until acceptance or are released with the first public version.
- [ ] If releasing data, copy the exact verified workbooks into `data/private/`, update the folder name/policy if desired, and review journal/licensing restrictions.
- [ ] Add the accepted-article DOI and Zenodo DOI to `CITATION.cff` and the article’s data/code statement.
- [ ] Clear generated artifacts before packaging: `find . -name "__pycache__" -type d -exec rm -rf {} +` (running the tests or notebooks locally regenerates these; they must not end up in the distributed archive).
- [ ] Run `python -m unittest discover -s tests -v`.
- [ ] Run `python run_all.py` after adding the datasets.
- [ ] Review `git status` and confirm no manuscript, SI, credentials, personal paths, temporary files, or private data were added accidentally.
- [ ] Create a versioned release, archive that release in Zenodo, and record the exact Git tag/commit in the article.

Recommended first public tag after metadata completion: `v1.0.0`.
