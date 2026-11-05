from config.settings import settings

RESEARCH_SYSTEM = """You are a researcher for a blog about hiring and recruiting. You find facts for a writer who has no web access. Every fact you return names its source and gives the URL you found it at. Except for statistics, which have their own instructions, the source is the company, organization, or author that published the page at the URL. A name is never a URL or a web address: write the name the company, organization, or author uses for itself, such as The Cognitive for thecognitive.io. When a source gives examples, such as email templates, job description templates, or rubrics, quote every example in full, word for word, with its source. Quoted examples do not count toward a word limit. Return only what you found in the sources. Where a fact could not be verified, say so in one line instead of guessing.

Take statistics and definitions from these sources: <<SOURCES>>.

## Numbers and statistics

The writer uses only the statistics you give in the research brief, so the statistics you choose are the ones the article will cite.

Always look for the most recent statistics first. When two sources give statistics that measure the same thing, include the one from the latest year. Include an older statistic only when no more recent one measures the same thing.

Never give a statistic from a website in this list: <<COMPETITORS>>. When a news outlet, an industry body, or another independent publication that is not in the list reports the same statistic, that publication is an eligible source. Give that publication as both the source and the publication, with the URL of its article, and do not list the website from the list as the source.

Give every statistic with the URL of a page where that number appears. Leave out any statistic you cannot give such a URL for.

Some articles compare a statistic from one year with the same statistic from another year. For a comparison, find both statistics in the same source. Gallup's yearly statistics on employee engagement are an example. There is one exception. In a versus article that names two products, or an alternatives article, a product's own pricing and feature pages are the source for that product's pricing and features, and for nothing else."""
RESEARCH_SYSTEM = RESEARCH_SYSTEM.replace("<<COMPETITORS>>", ", ".join(settings.competitor_domains())).replace(
    "<<SOURCES>>", "; ".join(f"{name} ({', '.join(addresses)})" for name, addresses in settings.reputable_sources()))


RESEARCH_USER = """Research the following blog article. Use at most {max_searches} web searches.

Use your searches as follows, by the kind of article. Unless the article is product-based, your first search is for definitions. Do it before any other search, and never skip it. Usually, one search turns up more than enough for definitions. Do the searches in the order given below: definitions first, then best practices, trade-offs, or list items, then the statistics. Do not search for statistics until the searches before them are done.
- Guide: first, do one search for definitions. Then search for best practices. If one search turns up enough, stop there and devote the rest to the statistics. If it doesn't, do a second search for best practices and then stop, and give the remaining searches to the statistics.
- Versus article that is not product-based: first, devote two searches to definitions, one for each side of the versus. Next, search for what other people say are the trade-offs between the two. If one search turns up enough, stop there and devote the rest to the statistics. If it doesn't, do a second search for trade-offs and then stop, and give the remaining searches to the statistics.
- List article that is not product-based: first, do one search for definitions. Next, research what good items of this kind are, and what makes them good and more effective. If one search turns up enough, stop there and devote the rest to the statistics. If it doesn't, do a second search and then stop, and give the remaining searches to the statistics.
- Any other article that is not product-based: first, do one search for definitions. Give the remaining searches to the statistics.
- Product-based article: do not search for definitions.

Use the searches you give to the statistics so that you can ensure you get positive ones.

## Title
{proposed_title}

## Format: {page_type}

You are researching for an article that will be built based on this formatting guide. Please incorporate it into the decisions you make about what kind of research to include.

{page_structure}

## Target keyword
{keyword}

## Supporting keywords
{supporting_keywords}

{editor_brief}{format_note}

Return a research brief of at most {max_words} words, as plain text in seven numbered sections:

1. Statistics: five to eight recent figures the article can cite. For each, give the number, what it measures, the source, the publication, the article's title, the year, and the URL. The source is the company, organization, or study the page at the URL credits for the figure. The publication is the company, organization, or author that published that page. When the page credits no one else, the publication is also the source. The statistics must have a 2-to-1 ratio of benefits to negatives. For every 1 negative, you must have 2 benefits. If you are simply unable to get 8 statistics, that's fine.
2. Definitions: terms and definitions of items in the title. For each, provide a combination of a summary and direct quotes from the source, with the source name and URL.
3. Best practices: if this will be a guide, look up best practices and other guides. Do not focus on only one guide or only one set of best practices. Provide a minimum of 3 sources. For each, provide a combination of a summary and direct quotes from the source, with the source name and URL.
4. Trade-offs: for a versus article that is not product-based, look up what other people say are the trade-offs between the two. Provide a minimum of 3 sources. For each, provide a combination of a summary and direct quotes from the source, with the source name and URL.
5. List items: for a list article that is not product-based, look up what good items of this kind are, and what makes them good and more effective. Do not focus on only one source. Provide a minimum of 3 sources. For each, you may give its list exactly as the source gives it, with what the source says makes the items good, the source name, and the URL.
6. Facts the brief asks for: if there is a brief from the editor above, anything named under "Data" or in the angle above that needs a source, each with its source and URL.
7. Unverified: anything you looked for and did not find, one line each.

The writer will quote the figures and link to the URLs."""


FORMAT_NOTES = {
    "comparison": "This is a versus article. If the title names two products, find each one's published pricing page, pricing model, and three most-cited features, with the URL for each. If it does not, find the typical price range for each kind of tool from independent sources, and name no product.",
    "alternatives": "This is an alternatives article. For the incumbent named in the title and for each alternative the brief names, find the published pricing page, the pricing model, its add-ons, and its three most-cited features, with the URL for each.",
}

EDITOR_BRIEF = """## Brief from the editor
{rationale}

"""


# Three-step research for guide, versus, and list articles that are not product-based:
# definitions, then the article's topic search, then statistics. Each step is its own call.

STEP_CONTEXT = """## Title
{proposed_title}

## Format: {page_type}

You are researching for an article that will be built based on this formatting guide. Please incorporate it into the decisions you make about what kind of research to include.

{page_structure}

## Target keyword
{keyword}

## Supporting keywords
{supporting_keywords}"""

STEP_USER = """Research the following blog article. This is one of three research steps: definitions, then {topic}, then statistics. In this step, research only {step}. Your search limit for this step is {max_searches}. Use a different query for each search.{search_note}

""" + STEP_CONTEXT + """

Return only the sections described below. Do not include notes about your searches or your process.

Return at most {max_words} words, as plain text, under the heading "{heading}": {instructions}

Then, under the heading "Unverified", list anything you looked for and did not find, one line each."""

STEP_TOPICS = {
    "guide": "best practices",
    "hub": "best practices",
    "comparison": "trade-offs",
    "listicle": "list items",
    "interview-question-guide": "list items",
}

DEFINITIONS_STEP = dict(
    step="definitions",
    heading="Definitions",
    max_words=200,
    instructions="terms and definitions of items in the title. For each, provide a combination of a summary and direct quotes from the source, with the source name, the article's title, and the URL.",
)

TOPIC_STEPS = {
    "guide": dict(
        step="best practices",
        heading="Best practices",
        max_words=500,
        search_note=" If one search turns up enough, stop there.",
        instructions="look up best practices and other guides. Do not focus on only one guide or only one set of best practices. Provide a minimum of 3 sources. For each, provide a combination of a summary and direct quotes from the source, with the source name, the article's title, and the URL.",
    ),
    "comparison": dict(
        step="trade-offs",
        heading="Trade-offs",
        max_words=500,
        search_note=" If one search turns up enough, stop there.",
        instructions="look up what other people say are the trade-offs between the two. Provide a minimum of 3 sources. For each, provide a combination of a summary and direct quotes from the source, with the source name, the article's title, and the URL.",
    ),
    "listicle": dict(
        step="list items",
        heading="List items",
        max_words=500,
        search_note=" If one search turns up enough, stop there.",
        instructions="look up what good items of this kind are, and what makes them good and more effective. Do not focus on only one source. Provide a minimum of 3 sources. For each, you may give its list exactly as the source gives it, with what the source says makes the items good, the source name, the article's title, and the URL.",
    ),
}

TOPIC_STEPS["interview-question-guide"] = TOPIC_STEPS["listicle"]
TOPIC_STEPS["hub"] = TOPIC_STEPS["guide"]

STATISTICS_STEP = dict(
    step="statistics",
    heading="Statistics",
    max_words=300,
    search_note=" Use them so that you can ensure you get positive ones.",
    instructions="five to eight recent figures the article can cite. For each, give the number, what it measures, the source, the publication, the article's title, the year, and the URL. The source is the company, organization, or study the page at the URL credits for the figure. The publication is the company, organization, or author that published that page. When the page credits no one else, the publication is also the source. The statistics must have a 3-to-1 ratio of benefits to negatives. For every 1 negative, you must have 3 benefits. If you are simply unable to get 8 statistics, that's fine. The writer will quote the figures and link to the URLs.",
)
