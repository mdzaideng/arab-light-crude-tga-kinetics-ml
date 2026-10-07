# Release checklist

Status at v1.0.1: repository public, Zenodo archiving enabled, citation metadata and licences complete. Experimental and cleaned datasets are provided only as the article's Supplementary Material and can be verified with the SHA-256 values listed in data/README.md.

Use these items before each new release:

- [ ] Replace the temporary author entry in `CITATION.cff` with the final ordered author list and ORCID identifiers.
- [ ] Confirm the repository owner and final repository name.
- [ ] Confirm no dataset workbook is committed (`data/private/` holds only `.gitkeep`).
- [ ] Add the article DOI to `CITATION.cff` once published.
- [ ] Clear generated artifacts before packaging: `find . -name "__pycache__" -type d -exec rm -rf {} +` (running the tests or notebooks locally regenerates these; they must not end up in the distributed archive).
- [ ] On a machine with Times New Roman, run `python render_publication_figures.py` (workbooks in `data/private/`); confirm `figures/RENDER_LOG.json` names Times New Roman.
- [ ] Run `python -m unittest discover -s tests -v`. All tests, including the font test, must pass.
- [ ] Run `python run_all.py` locally with the Supplementary Material workbooks in `data/private/` (do not commit them).
- [ ] Review `git status` and confirm no manuscript, SI, credentials, personal paths, temporary files, or private data were added accidentally.
- [ ] Create a versioned release, archive that release in Zenodo, and record the exact Git tag/commit in the article.

Recommended first public tag after metadata completion: `v1.0.0`.
