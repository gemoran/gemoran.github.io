# Academic website with a BibTeX-driven publication list

This is the source for [gemma-moran.com](https://gemma-moran.com), built with [Quarto](https://quarto.org/) and hosted on GitHub Pages.

It is adapted from Gang He's [Quarto Academic Website Template](https://github.com/drganghe/quarto-academic-website-template). The main change is that **the publication list is built straight from a `.bib` file**. You keep your papers in one BibTeX file, and the same file feeds both the website and a LaTeX CV. You're welcome to fork it for your own site.

## What's different from the original template

- **Publications come from `research/papers.bib`**, not from `publications.xlsx`. There's no spreadsheet to keep in sync and nothing to `pip install`: the converter uses only the Python standard library.
- **Titles keep your capitalization**, and LaTeX accents come out as Unicode.
- **Student and co-first author marks** (†, \*) come from biblatex's `author+an` annotations, so the CV uses them too.
- **One `.bib` for the site and the CV.** BibTeX and Biber silently ignore the website-only fields (`code`, `software`, …).
- **A simpler publication layout:** one entry per paper with the title, the authors, `[code]`/`[pdf]` links and the venue in italics. There are no Altmetric or Dimensions badges.
- **Each page has its own folder** (`research/`, `teaching/`, `resources/`, `cv/`). The template's posts, people and projects pages are gone.

## Project layout

| Path | What it is |
|---|---|
| `_quarto.yml` | Site settings: title, navbar, footer, which pages to build, the pre-render step |
| `index.qmd` | Home page |
| `research/papers.bib` | **Your publications. This is the only file you edit for the publication list.** |
| `research/bib_to_yml.py` | Converts `papers.bib` to `publications.yml`, automatically before each render |
| `research/publications.yml` | Generated. Don't edit it. |
| `research/pub-listing.qmd` | Publications page: sections, headings, the key to the marks |
| `research/pub-listing.ejs`, `.css` | How each paper is laid out and styled |
| `teaching/teaching.qmd`, `resources/resources.qmd` | Teaching and resources pages |
| `cv/moran_cv.tex` | LaTeX CV that reads `research/papers.bib`. The compiled PDF is linked from the site. |
| `files/images/` | Headshot and course hex stickers (`make_hex_stickers.py` draws them; it needs numpy and matplotlib) |
| `files/includes/` | Snippets included in pages |
| `_extensions/` | Icon extensions (Font Awesome, Academicons, Iconify) |
| `remove-stray-divfence.lua` | Removes stray `:::` that the publication listing leaves in the HTML |
| `CNAME` | Custom domain for GitHub Pages (see [Custom domain](#custom-domain)) |
| `docs/` | The rendered site. It's generated, but it's committed because GitHub Pages serves it. |

## Make it your own site

1. **Install** [Quarto](https://quarto.org/docs/get-started/) and Python 3.10 or newer.
2. **Fork** this repository and rename it to `your-username.github.io`.
3. **Personalize:**
   - `_quarto.yml`: title, description, navbar, footer, `site-url` and `repo-url`. **Remove or replace the `google-analytics` tracking ID**, otherwise your visits are counted on my analytics.
   - `index.qmd`: your bio, links and headshot.
   - `research/papers.bib`: your papers (see [Publications](#publications-from-a-bib-file)).
   - `research/bib_to_yml.py`: set `MY_NAME` so your name is bolded. Authors are shown as initials plus surname, so `r"G\.(?: [A-Z]\.)* Moran"` matches both "G. Moran" and "G. E. Moran".
   - `research/pub-listing.qmd`: your Google Scholar link.
   - `cv/`: your own CV, or remove the CV links from the navbar and `index.qmd` and the `cv/moran_cv.pdf` line under `resources:` in `_quarto.yml`.
   - `CNAME`: your own domain, or delete the file and its line under `resources:` to use `your-username.github.io`.
   - `teaching/` and `resources/`: your content, or remove them from the navbar.
4. **Preview** with `quarto preview`, or **build** with `quarto render`, which writes the site to `docs/`.
5. **Publish:** commit everything, including `docs/`, and push. Then in the repository's **Settings → Pages**, choose *Deploy from a branch* with branch `main` and folder `/docs`.

> The pre-render step runs `python`. If your system only has `python3`, change `python` to `python3` on the `pre-render:` line of `_quarto.yml`.

## Publications from a `.bib` file

Each time you render, `bib_to_yml.py` turns `research/papers.bib` into `research/publications.yml`, and `research/pub-listing.qmd` displays it. You only ever edit the `.bib` file.

```bibtex
@article{moran2026multi,
  title     = {Nonlinear multi-study sparse factor analysis},
  author    = {Moran, Gemma E. and Krishnan, Anandi},
  journal   = {arXiv preprint arXiv:2601.18128},
  year      = {2026},
  keywords  = {unpublished},
  author+an = {1=highlight},
  code      = {https://github.com/your-name/your-repo},
}
```

appears on the site as:

> “[Nonlinear multi-study sparse factor analysis](https://arxiv.org/abs/2601.18128)”\
> **G. E. Moran**, A. Krishnan [code]\
> *arXiv preprint arXiv:2601.18128*, 2026.

The title links to `url` if there is one, otherwise to the DOI, otherwise to the arXiv page. Papers are listed newest first within each section, using `date`, or `year` and `month`.

### Sections come from `keywords`

| `keywords` | Section on the page |
|---|---|
| `peerjournal` | Peer-reviewed Publications |
| `unpublished` | Preprints |
| `techreport` | Technical Reports |

An entry with none of these keywords is left off the page, and the render prints a warning listing it.

**To add a section** (say `keywords = {talk}` for talks), change three places:

1. `research/bib_to_yml.py`: add `"talk": "Talks"` to `KEYWORD_SECTIONS`.
2. `research/pub-listing.qmd`, front matter: add a listing whose `include: section:` matches that name exactly.
   ```yaml
     - id: talks
       contents: publications.yml
       type: custom
       page-size: 100
       sort: "date desc"
       template: pub-listing.ejs
       include:
         section: "Talks"
   ```
3. `research/pub-listing.qmd`, body: add a heading and a div whose id matches the listing's `id`.
   ```markdown
   ## Talks

   ::: {#talks}
   :::
   ```

### Marking students and co-first authors

Use biblatex's `author+an` field. Authors are numbered from 1 in the order they appear in `author`. **Use `;` between authors** and `,` between labels for the same author:

```bibtex
author+an = {1=student; 2=student; 3=highlight},
author+an = {1=first; 2=first,highlight},
```

| Label | Website | CV |
|---|---|---|
| `highlight` | Marks you. The site bolds your name by matching `MY_NAME`; this label is only checked against it. | Bold |
| `first` (or `equal`, website only) | \* | \* |
| `student` | † | † |
| `corresponding` | — | ‡ |

The script warns you if you separate authors with commas, refer to an author number that doesn't exist, or `highlight` someone who isn't you. To change the symbols, edit `ANNOTATION_MARKS` in `bib_to_yml.py` and the key near the top of `pub-listing.qmd`.

### Extra fields for links and notes

These go in the `.bib` entry like any other field (`pdf = {https://…}`). BibTeX and Biber ignore them.

| Fields | What they add |
|---|---|
| `pdf`, `preprint`, `code`, `software`, `github`, `data`, `supplemental`, `slides`, `poster`, `video`, `shareit` | A `[label]` link after the authors |
| `awards`, `mediacoverage`, `invitedpresentation` | An extra line under the entry (Markdown works) |
| `highlycited = {1}`, `hotpaper = {1}` | A badge next to the title |
| `section = {...}` | Puts the entry in that section, overriding its `keywords` |

To add a new kind of link, add the field name to `PASSTHROUGH` in `bib_to_yml.py` and to `LINKS` in `pub-listing.ejs`.

## Using the same `.bib` for a LaTeX CV

`cv/moran_cv.tex` uses biblatex with Biber and reads the same file. It splits the bibliography by the same keywords, and redefines the name format so the `author+an` labels print as bold, \*, † and ‡:

```latex
\usepackage[backend=biber, doi=false, url=false, sorting=ydnt,
            maxbibnames=99, giveninits=true]{biblatex}
\addbibresource{../research/papers.bib}

\renewcommand*{\mkbibnamefamily}[1]{%
  \ifitemannotation{highlight}{\textbf{#1}}{#1}%
  \ifitemannotation{first}{\textsuperscript{*}}{}%
  \ifitemannotation{student}{$^\dagger$}{}%
}

\nocite{*}
\printbibliography[heading=none, keyword=peerjournal]
```

`doi=false, url=false` stops biblatex printing the links that the website uses. After you recompile the CV, run `quarto render` to copy the new PDF into `docs/`. The copy happens because `cv/moran_cv.pdf` is listed under `resources:` in `_quarto.yml`.

## Custom domain

GitHub Pages finds a custom domain in a `CNAME` file in the published folder (`docs/`). A full `quarto render` empties `docs/`, so the `CNAME` file lives in the project root and is listed under `resources:` in `_quarto.yml`, which copies it in on every render.

At your domain registrar, add four `A` records for `@` pointing to `185.199.108.153`, `185.199.109.153`, `185.199.110.153` and `185.199.111.153`, and a `CNAME` record for `www` pointing to `your-username.github.io`. Then tick **Enforce HTTPS** in Settings → Pages. See GitHub's [custom domain guide](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site) for details.

## Tips

- **Hiding a page while you work on it.** The `render:` list in `_quarto.yml` builds every `.qmd` except those under `!folder/`. Comment out the page's navbar link too, and add the folder to `.gitignore` if the drafts shouldn't be in a public repository.
- **Keep `docs/` committed.** Some global `.gitignore` templates ignore `docs/`. This project's `.gitignore` ends with a block that re-includes it, and that block has to stay last.

## Credits

Adapted from the [Quarto Academic Website Template](https://github.com/drganghe/quarto-academic-website-template) by Gang He, released under the MIT License (see `LICENSE`). See also Gang He's [Quarto academic site examples and tips](https://drganghe.github.io/quarto-academic-site-examples.html).
