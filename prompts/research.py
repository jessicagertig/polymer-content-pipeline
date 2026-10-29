RESEARCH_SYSTEM = """You are a researcher for a blog about hiring and recruiting. You find facts for a writer who has no web access. Every fact you return names its source and gives the URL you found it at. Return only what you found in the sources. Where a fact could not be verified, say so in one line instead of guessing."""


RESEARCH_USER = """Research the following blog post. Use at most {max_searches} web searches.

## Title
{proposed_title}

## Format: {page_type}

## Target keyword
{keyword}

## Brief from the editor
{rationale}

{format_note}

Return a research brief of at most {max_words} words, as plain text in four numbered sections:

1. Statistics: five to eight recent figures the post can cite. For each, give the number, what it measures, the source name, the year, and the URL.
2. Definitions: the standard definition of the post's subject and of any term the brief uses, each with its source and URL.
3. Facts the brief asks for: anything named under "Data" or in the angle above that needs a source, each with its source and URL.
4. Unverified: anything you looked for and did not find, one line each.

The writer will quote the figures and link to the URLs."""


FORMAT_NOTES = {
    "comparison": "This is a versus post. For each product named in the title, find its published pricing page, its pricing model, and its three most-cited features, with the URL for each.",
    "alternatives": "This is an alternatives post. For the incumbent named in the title and for each alternative the brief names, find the published pricing page, the pricing model, its add-ons, and its three most-cited features, with the URL for each.",
    "listicle": "This is a list post. Find a source for every item the brief names, and figures that show why the subject matters.",
}
