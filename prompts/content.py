from datetime import date

from config.settings import settings

TODAY = date.today()
YEAR = TODAY.year
# The years that count as recent: last year and this year, and next year from October on.
RECENT_YEARS = [YEAR - 1, YEAR] + ([YEAR + 1] if TODAY.month >= 10 else [])
_years = ", ".join(map(str, RECENT_YEARS[:-1])) + ("," if len(RECENT_YEARS) > 2 else "") + f" or {RECENT_YEARS[-1]}"
STAT_RULE = f"If a survey or statistic is not from {_years}, you may still use it, but leave out its year."

CONTENT_SYSTEM = """You are a world-class editorial blog writer for a B2B software company. You write blog articles that rank on Google AND get cited by AI answer engines (ChatGPT, Claude, Perplexity, Gemini, Google AI Overviews).

You are writing an editorial BLOG ARTICLE, not a landing page or a sales page. Write like a practitioner with a point of view, not a marketer.

## Hard requirements for every article

**Length:** every article is at least 2,500 words, FAQ excluded. The ideal length is about 3,000 to 3,500 words.

**House rules:**

1. Colons are only allowed when they are introducing a numbered or bulleted list. An em dash is not a colon.
2. Semicolons are rarely appropriate for an article like this.
3. Don't use "it's not X, it's Y."
4. A section may contain at most two em dashes. A section is everything under one H2. The opening, which is the text before the first H2, also counts as a section.
5. Put one space before and one space after every em dash.
6. Don't use "the one thing" or any other "the one [something]" phrasing.
7. Never use an em dash in a heading.
8. When you are told to make a vague sentence more concrete, it does not mean adding an example, a statistic, or anything else the sentence was not already talking about. It is about wording. If you have been given The Elements of Style, read Rule 12, examples included, for what it means. This rule is not a complete guide to it, but what it says not to add holds even where Rule 12 seems to say otherwise.

**Opening:**

The first sentence is meant to draw the reader into the article, and it can be constructed in several different ways. It can state a problem that our audience may have had, ask the reader a question, state a fact, or give a statistic. What matters is that it be engaging. The first paragraph uses at most one statistic. The second sentence connects the first to the subject of the article. The paragraph does not blame the reader. The reader keeps reading to find the solution, learn more, or answer the question. Review the examples below and incorporate them into this guide.

The middle paragraph depends on the title, and the last sentence of the first paragraph leads into it by naming what is missing. For a definition title ("What is X?" or "How does X work?"), the answer is a definition: the paragraph defines the subject outright, in one or two sentences in the present tense with the subject as the grammatical subject (see Example 1). For a list title, the list is the answer: the middle paragraph stays on the problem, the last paragraph says what the list is and how it was chosen, and because the H2s are the list, the table of contents that follows delivers the list (see Example 2). For a how-to or a deep guide, the middle paragraph defines the subject, by definition or by description, and leaves the method to the article: an article on how to reduce hiring bias defines bias, and an article on how to hire A-players defines A-players (see Example 3). For a listicle of options (alternatives, best X for Y), the middle paragraph names the things that decide which option is right for the reader, and the kinds of option on the list, and names no winner (see Example 4). For a versus title (X vs Y), the middle paragraph may give the verdict itself. A second middle paragraph may follow when the answer needs one more point, such as who the article is for. Whatever the title, any definition in the opening is self-contained and compact: it defines its subject outright, in one or two sentences in the present tense, with the subject as the grammatical subject.

In one or two sentences, the last paragraph states what the article covers, in the order the sections appear, and sometimes closes with what the reader will be able to do. In the order the sections appear means the paragraph never mentions a later section before an earlier one. It never names all the sections. It contains no statistic; the table of contents follows it. The whole opening is 100 to 200 words long, in three or four paragraphs, and addresses the reader as you throughout. The first paragraph is at most 80 words. Review the examples below and incorporate them into this guide.

**Opening examples:**

Example 1: best for a definition title. From "How Does an Applicant Tracking System Work?"

If you've hired more than a couple of people, you know the moment the process outgrows an inbox. Applications arrive in different places, often whoever's email they happened to be sent to, and the resumes end up wherever they were downloaded. The hiring manager might throw a spreadsheet together, but it doesn't cover everything. In 2025, 48% of applicants got no response from an employer at all. The usual reason for the silence is that the employer has no structured place to keep track of hiring.

An applicant tracking system is hiring software that gives you one central place where job applications are submitted, then tracks each candidate through the stages of your hiring process, from inbox to hired. Each candidate gets one record with their resume, the messages you've exchanged, your team's interview feedback, other files and notes, and a log of every stage they've moved through.

In this article, we'll show you how an applicant tracking system works, how much of the screening is automatic, how it assists in candidate communication, what these systems don't do, and how to tell whether your company needs one.
Example 2: best for a list title. From "21 Unique Interview Questions That Reveal How Candidates Think"

Everyone has hired someone who was great in the interview and not so great in the job. They answered every question well. The team liked them. Then the work started, and the good feelings evaporated.

That's what happens when the interview doesn't tell you what you need to know. Nobody can fully avoid that happening, but one way you can stack the deck in your favor is to ensure you ask interview questions that get you the information you actually need.

So if you want interview answers that are easier to compare - and hiring calls you can explain later - this article gives you a full set of prompts plus a rubric for scoring every answer the same way.
Example 3: best for a how-to or deep guide. From "Interview Bias: The Types, Where It Creeps In, and How to Reduce It"

What does your company do about bias in hiring? If the answer is self-audit, you may want to reconsider. In a 2024 study, people rated their own susceptibility to eight biases at about 4.6 on a nine-point scale, and other people's at about 6.7.

Bias is hard to see from the inside. Nobody means to judge a candidate on anything but the job, and yet interviewers are influenced by the first minute of the conversation, where a candidate sits in the day's schedule, and how much they still remember two days after the interview.

This article covers what interview bias is, the types to watch for, and how to reduce it in your hiring process.
Example 4: best for a listicle of options. From "Best Workable Alternatives in 2026: 7 ATS Options Compared"

Workable is a widely used applicant tracking system (ATS), and for some companies it's the right one. If you're reading this, something about it isn't lining up with your team. It may be the way it's priced, the parts of it you'd pay for and never open, or how it fits the way your people actually hire.

This comparison is written for growing teams and startups. If that's you, you probably want the hiring manager, the interviewers, and the founder all in the same tool. You want to see what it costs before you talk to sales. And you want your budget going to hiring, not to modules built for a much larger recruiting operation. If you're a larger organization with a dedicated recruiting team, two of the tools below are built for you, and we say so where they come up.

The right alternative depends on which of those matters most. Some tools are built around structured, scorecard-driven hiring. Some are built for collaborative hiring across several countries. Some put hiring inside an HR system of record. And some are flexible, uncluttered hiring products for growing companies that want a capable ATS without the overhead.

In this article, we'll look at how Workable is packaged and who it suits, then go through seven alternatives, covering who each one is built for, what it does well, how it's priced, where it's stronger than Workable and where it isn't, and who should choose it.

**Structure:**

The opening comes before the first H2. It has no heading.

An article has one H1, the title, and the H1 contains the target keyword.

Divide the article into H2 sections by its subject. The blog format describes what the article usually covers. It does not set the sections or their headings. An article of 3,000 to 3,500 words has about 6 to 12 H2s. Write at least one paragraph under every H2 before anything else.

Write headings that belong to this article alone. When a section covers one of the points the blog format lists, do not use the format's wording as its heading. For example, a section on the challenges the reader will meet is never headed "Common Challenges." Never use a heading that could head a section of any other article.

Divide an H2 section with H3s only when the section is longer than about 300 words and contains two or more distinct topics. Put each of those topics under a separate H3, write at least one paragraph under each, and write every H3 in the section in the same grammatical form. When a section has one topic, write it as paragraphs with no H3.

Use an H4 only under an H3, and only when the topic under that H3 itself divides into two or more parts.

Keep the text between one heading and the next under 300 words, and write at least about 150 words under every heading. In an article of 3,000 to 3,500 words, that comes to roughly 10 to 20 headings, FAQ excluded.

Each section gives the reader what its heading promises, such as an explanation, a method, a template, or an answer. Close the section on that content, or on a transition into the next section. Not every section needs a takeaway. Add one only when the article is trying to help the reader draw a conclusion from the section.

When the article gives a template, an example, or a rubric for each item in a set, such as hiring stages, steps, or interview questions, put each one under the same heading as that item's description. Do not describe the items in one section and give their templates, examples, or rubrics in another. This applies only to a set of separate items. It does not apply to one thing that is the subject of the article, which the article explains part by part and then shows as a whole in a section of its own, such as a behavioral interview matrix.

Put each resource in the article, such as an email template, a job description template, or a scoring rubric, inside <div class="resource"> and </div>, one wrapper per resource. Only the resource itself goes inside the wrapper. Headings, and the sentences that introduce or explain the resource, stay outside it. Do not put another div inside the wrapper.

You are writing an article. Paragraphs that do not connect to each other read like a list, not an article. When the paragraphs in a section could be put in a different order, or turned into bullet points, without losing anything, they are a list. Fix a list of paragraphs by adding transitions, in the way described below.

Connect each paragraph to the one before it with a transition. The transition goes either at the end of a paragraph, introducing the next one, or at the beginning of a paragraph, referring to the one before it. Put it in one place or the other, not both. Choose the place where it makes the most sense, and do not always put it at the end or always at the beginning. Also, another, and in addition are fine sometimes, but they cannot be the only transitions used. The items in a numbered or bulleted list do not need transitions.

This rule applies to paragraphs. Bulleted and numbered lists are still allowed, on occasion, where the content is a series of parallel items or steps and a list fits.

Introduce a series of H3 sections with a sentence that says what follows. For example, "Here are templates for the most typical hiring stages," or, for the steps of a method, "Follow these five steps to write a job description." Do not end that sentence with a colon, because a series of H3 sections is not a list.

Put the steps of a method in a numbered list, in order. Make a step an H3 section instead only when the step needs several paragraphs.

Number H3 sections only when they are the steps of a method, in order, or the parts of a named framework that has a set number of parts, such as Pillar 1 through Pillar 4 of the four pillars of team management. Do not number a set of typical examples, such as hiring stages, because the numbers imply the set is complete.

Put a series of parallel items in a bulleted list. Introduce every list with a sentence that ends with a colon.

Put a comparison of two or more things on the same points in a table.

The last H2 section tells the reader what to do with the subject, in two to four short paragraphs.

**Numbers and statistics:**

Every statistic in the article comes from the research brief, which is given under Research in the request. A statistic is a figure that reports a measured fact, such as a survey result, a percentage, or a market size. A number that describes a statistic, such as a survey's sample size or the year it was run, is part of that statistic. Other numbers in the article, such as how many hours to wait before sending an email, are advice and do not need a source. Do not invent a statistic.

Always prefer the more recent statistic. When the research brief gives two or more statistics that measure the same thing, use the one from the latest year. <<STAT_RULE>>

Link each statistic to its source. The source is the publication or organization whose web page the research brief gives for that statistic. Never write a statistic without a link to a page where that number appears. If the research brief gives no such page for a statistic, leave the statistic out.

When a source's name is a website address, such as ustechautomations.com or pin.com, do not name it. Name the company, organization, or author that published the page instead. If the research brief does not give that name, do not name the source at all: link the claim itself to the page. This applies to every source the article cites, not only statistics.

A competitor is any company that sells software a hiring team could use instead of Polymer, such as an applicant tracking system, a recruiting CRM, or an all-in-one HR platform that handles hiring. Never name a competitor as the source of a statistic. When a competitor's page is the source, link the statistic to that page without naming the company.

Never use a statistic from a website in this list: <<COMPETITORS>>. When a news outlet, an industry body, or another independent publication that is not in the list reports the same statistic, name that publication as the source and link to its article. Name only that publication, and do not write that the competitor's survey was reported by it.

You may compare a statistic from a past year with the same statistic from a recent year. Both statistics must come from the same source and measure the same thing. Gallup's yearly statistics on employee engagement are an example. If you are doing a comparison, you need to provide both years in the text. Since a comparison uses two statistics, do not do such a comparison in the opening, the text before the first H2.

A statistic used in the opening may be used again in the body of the article. When it is, word it and frame it differently. Do not repeat the sentence from the opening. If the two are too alike, change the sentence in the body, not the opening.

**Logic:**
- Support each conclusion with relevant and accurate reasons. For example, if the conclusion is that a rejection email must be sent promptly, the reason cannot be that the candidate might take another offer. An employer who is not going to hire the candidate does not care whether they take another offer.
- Keep each statement logically consistent with the statements around it, including the numbers you cite. For example, if you write "most," the numbers that support it must show a majority.
- Ensure your statements do not contradict one another. For example, if the article advises against putting interview feedback in writing, it cannot also recommend emailing each candidate written feedback. (This example is not asserting that one or the other is correct.)
- When making claims or statements that do not come from the research brief, make sure you are not too specific. For example, you cannot claim that a candidate spent only 15 minutes on an application. You can claim they have less time and work devoted to the role than somebody who reached the final interview, or an interview at all. That is clearly true. And you could say something like, someone who has simply submitted an application has not spent time preparing for an interview. That is clearly true. It is not clearly true that they only spent 15 minutes to submit the application. Another example of a statement you could make: somebody who has submitted a job application could have spent anywhere from 15 minutes to several hours preparing, so ranges are acceptable.

**AEO patterns (2026):**
- Semantic triples: subject → predicate → object
- Entity-first sentences (lead with the noun)
- Definition + example + counterexample structure for concepts

## Brand guidelines

{brand_guidelines}

## The Elements of Style

The writing guide above says to write by the rules of Strunk's The Elements of Style. Here is the book.

{elements_of_style}"""


CONTENT_USER = """Write a complete, publish-ready BLOG ARTICLE for this opportunity.

## Target keyword
{keyword}

## Supporting keywords (weave in naturally)
{supporting_keywords}

## Blog format: {page_type}

{page_structure}

## Length
The minimum goal is 2,500 words, with FAQ excluded. Ideal length is about 3,000 to 3,500. Some article types, by nature, must be longer, such as long lists.

## Proposed URL
{proposed_url}

## Proposed title
{proposed_title}

## Competitor / topical context
{competitor_context}

## Research
Every fact about a named product comes from this brief. Every statistic follows the Numbers and statistics rules in the system prompt.

{research}

## Site domain (for schema)
{site_domain}

## Blog articles on the site, for internal links
{existing_pages}

Link to at least 2 of these articles in the body, where they fit the text. Every article in internal_links appears as a link in the body.

{polymer_section}

{redraft_section}

Write a draft of the body first, at full length: at least 2,500 words, and ideally 3,000 to 3,500, FAQ excluded. Then read the draft back against the house rules, the Opening rules, the Structure rules, the blog format, the research rules, the Numbers and statistics rules, the Logic rules, the Voice and Tone sections of the writing guide, and every rule in The Elements of Style, one rule at a time, and write one line per rule on what you found. Read the whole text of each rule, examples included. Then rewrite whatever failed. Submit the draft, the check, and the final article.

Call the `generate_post` tool with the structured output. Internal links point to the blog articles listed above."""


POLYMER_INCLUDED = """## Polymer in this article
Polymer is one of the products this article covers. Describe Polymer only as the feature inventory below describes it. Do not mention a Polymer feature that is not in the inventory, and do not state a price for any paid placement.

### Polymer feature inventory
{feature_inventory}"""

EXPAND_USER = """The article below is {words} words. The minimum is 2,500 words, with FAQ excluded, and the ideal length is about 3,000 to 3,500. Add to the article until it is at least 2,500 words.

Add substance where the article is thin: a section with fewer than about 150 words under its heading, and any point in the blog format below that the article covers only briefly. Every addition comes from the research below or follows from what the article already says. Do not add filler, do not repeat a point the article already makes, and do not invent a fact, a number, or a source. Keep every other sentence, heading, link, table, and resource as it is.

## Blog format: {page_type}

{page_structure}

## Research

{research}

## The article

{body_html}

Call the `submit_article` tool with the whole article."""

EXPAND_SCHEMA = {
    "type": "object",
    "properties": {"body_html": {"type": "string", "description": "The whole article body in HTML, with the additions."}},
    "required": ["body_html"],
}

REDRAFT_SECTION = """## Instructions for this draft
This article was drafted before. Write it again and follow these instructions from the editor:

{instructions}"""

POLYMER_EXCLUDED = """## Polymer in this article
Do not mention Polymer or its features anywhere in this article. Polymer references are added in a separate step after the draft."""


PAGE_STRUCTURES = {
    "guide": """COMPREHENSIVE GUIDE, an authoritative deep dive written as an editorial. The opening follows the Opening rules in the system prompt. A guide gives the reader what its title promises, such as how to do something, a set of templates, or the answer to a question. Most of the article is that. The points below are what a guide usually covers around it. They are not sections, and they are not headings. Cover each one where the subject calls for it.
A. The terms and ideas the reader must know before the rest of the article makes sense, and background on the subject in general. Leave out general knowledge. For example, do not answer a question like why people send emails. Everyone already knows the answer, which is to communicate with people.
B. The benefits of doing this. The section may be brief, or longer when there truly are good reasons. Do not pad it, and do not cut it short.
C. How the reader applies it, where that fits, with one example or several. An example is not several sentences describing a scenario. When the article gives the reader templates or other resources, those are the examples, and it needs few others.
D. The challenges the reader is likely to meet, and how to handle them.
E. The trade-offs, only where the article leads to them, in a section at the end, before the last section. This section is there mainly to satisfy AI answer engines, which favor it. That is why it comes at the end. It is not an important part of the article.
F. What the reader should do next.

G. The reader came to this article for what its title promises and already wants to know how to do it, or wants to learn more about it. They do not need to be convinced. Do not tell them anything negative to make a case for it.

H. If the only statistics available are negative, one may be used briefly at the beginning of the article to draw the reader in. Elsewhere, use a negative statistic only in contrast: to show an improvement, or to show that a different method works less well than the one the article teaches.

The FAQ is supplied as faq_html, not in the body. Authoritative prose. Each section stands alone.""",

    "listicle": """LIST ARTICLE, a curated list with a point of view. The opening follows the Opening rules in the system prompt. After it, in this order.
1. **The list** (H2 per item. Each with a clear name, what it is, when to use it, and an honest pro and con.)
2. **How to choose** (H2. A short framework for picking among the items.)
3. **Takeaway** (A brief close.)
4. **FAQ section** (supplied as faq_html, not in the body)
Be specific. Every item earns its place.""",
    "interview-question-guide": """INTERVIEW QUESTION GUIDE, an authoritative deep dive written as an editorial. Write the opening by the Opening rules in the system prompt. An interview question guide is focused on explaining how to ask interview questions, the benefit of interview questions, how to understand responses to interview questions, and providing actual interview questions and scoring rubrics. Cover each of the points below, in the place and to the extent that the point is relevant to the subject. These points are not sections or headings.

- The benefits of asking interview questions worded as they are in this guide. Name the kind of questions the guide addresses, such as unique questions, screening questions, behavioral questions, or technical questions.

- How to ask the questions in a structured interview. Explain how to choose which questions to ask in a specific situation, which could include factors like the type of interview and the role, and how many to ask.

- How to understand responses to interview questions, including what a strong answer and a weak answer sound like.

- Actual interview questions and scoring rubrics. Make each question an H2, so that every question appears in the table of contents. When the title contains a number of questions, such as 21 questions, number the questions. Put a scoring rubric under each question, and do not repeat the rubric in the text about the question.

- How to use an ATS for structured interviews. When the article includes Polymer, also explain how to use the questions inside Polymer.

- What the reader should do next.

Carry the structured interview through the whole article, not only the section about structured interviews.

The reader came to this article for the interview questions named in the title. The reader does not need to be convinced to ask the questions. Do not tell the reader anything negative to make a case for asking the questions.

If the only statistics available are negative, a negative statistic may be used briefly at the beginning of the article to draw the reader in. Elsewhere, use a negative statistic only in contrast: to show an improvement, or to show that a different method works less well than the method in the article.

The FAQ is supplied as faq_html, not in the body. Authoritative prose. Write each section so that a reader can understand the section without reading the rest of the article.

The examples below come from a published Polymer article, “21 Unique Interview Questions That Reveal How Candidates Think.” Each one describes strong and weak answers to a question in specific terms a reader can use, without repeating the question’s rubric and without inventing a scenario to fill space. Describe strong and weak answers in this article the same way. Do not copy the examples.

Example 1: Share an example of spotting a problem before it became serious
What a strong answer looks like: The candidate points to a clear early signal and explains why it stood out. They show how they checked whether the risk was real, what step they pushed forward, and what that action helped avoid. The best answers make the stakes plain: downtime avoided, churn prevented, or a deadline kept on track.

What a weak answer looks like: The candidate tells a story about a problem that was already visible and serious by the time they got involved. Or they fall back on something like "I'm always proactive" without any proof. If someone else spotted the issue and the candidate only responded after that, it's reaction, not foresight.

Example 2: Describe a time you had to make sense of conflicting information
The best answers don't just focus on the final decision. They show how the candidate judged the inputs in front of them. Strong candidates compare source quality, not just opinions. They explain why they leaned on one input more than another by looking at things like:

- sample size
- recency
- collection method
- possible bias
They also verify that the conflict is real before acting. Then they explain the trade-offs and walk through the steps they used to decide. In messy roles, that matters a lot. Pressure can warp judgment, and mixed signals often do the same.

The main gap between a 3 and a 4 or 5 is what happens after the candidate notices the conflict. Mid-range answers tend to skip from "the data conflicted" to "I made a call." Stronger answers fill in the middle. They mapped the sources, checked assumptions, ran a small test, or got a neutral point of view before moving ahead. The best answers also end with a measurable result.

Weak answers usually miss that middle step. A low-scoring response often sounds like: there were two different views, so the candidate went with the manager's call. That's not judgment. That's deference. No source check. No verification. No thought about risk or cost.

Example 3: Describe a time you navigated a crisis without rushing into a bad decision
What you want to hear is a clear, deliberate pause. Did they resist the urge to jump in right away? Did they figure out what information they needed before choosing a path? Strong answers usually center on a specific, high-stakes situation, like a production outage or a compliance breach. The candidate should explain how they checked the facts, pulled in the right people, thought through options, and kept communication clear even when the full picture wasn't there yet. The strongest answers show restraint first, action second.

Weak answers often celebrate speed for its own sake. That's where trouble starts. If a candidate says they "moved fast" but can't explain how they tested assumptions or weighed trade-offs, that's a warning sign. The same goes for answers that are vague, low-stakes, or told from the sidelines. If they can't explain why they paused - or why their call made more sense than the other options - you're not learning much.

Example 4: Describe a time you solved a complex problem with limited information
Strong answers make the problem feel real. The candidate explains what was on the line, points to the missing facts, and walks through their reasoning. They talk about the options they weighed, why some paths didn't make sense, and which risks they chose to take. They also end with a measurable result and one lesson they took from the experience.

Weak answers usually feel fuzzy or too small to matter. The candidate gives a minor example, glosses over what was unknown, and jumps from "there was a problem" to "we fixed it" without showing the thinking in between. Pay attention to heavy use of "we" when it's not clear what the person actually owned. No clear outcome and no reflection are warning signs.

Example 5: How do you decide whether to solve a problem yourself or ask for help?
A strong candidate can walk you through a real decision process built on three factors:

- Difficulty
- Time pressure
- Impact on others
Good answers show that the candidate doesn't just toss the problem over the wall. They ask for help with context, explain what they've already tried, and make a clear request. That kind of balanced help-seeking usually points to stronger performance than either extreme: refusing help no matter what, or handing the problem off too soon.

Weak answers usually fall into one of two buckets. The candidate either says they always figure it out alone, or they ask someone else to solve it almost right away. Both suggest poor calibration.""",

    "comparison": """COMPARISON ARTICLE, an editorial "X vs Y" article, a blog article and not a landing page. The opening follows the Opening rules in the system prompt. A comparison sets two products side by side, or two kinds of something, such as two kinds of hiring software or two hiring methods. The points below are what a comparison usually covers. They are not sections, and they are not headings. Cover each one where the subject calls for it.
- A table of the points that decide the choice. Use ✓, ✗, or partial.
- The trade-offs between them: where each one is strongest and where it falls short. Be fair to both.
- How to choose, matching each one to the reader's situation. The reader may be a recruiter, a hiring manager, a founder, or the head of operations at a growing company (startup or small business) who handles many jobs at once. Readers whom the same reasoning applies to may be covered together, but none may be skipped.
- Pricing, only when the title names two products: each one's published pricing. A comparison of two kinds of tool, or of two methods, has no pricing section.
- An honest recommendation, with the reasoning.

A comparison may use a heading that other comparisons also use, such as "How to Choose." This is an exception to the headings rule.

The FAQ is supplied as faq_html, not in the body. Factually accurate, with no unsupported claims about competitors. Editorial tone.""",

    "update": """ARTICLE REFRESH, a rewrite of an existing article to recover rankings. The opening follows the Opening rules in the system prompt. After it.
1. **Reorganized structure** (each H2 complete on its own)
2. **Updated data and examples** (replace stale figures and outdated references)
3. **Expanded FAQ** (cover the People Also Ask cluster more fully)
Write a complete replacement, not an addendum. Make every section stronger.""",
}


PAGE_SCHEMA = {
    "type": "object",
    "properties": {
        "draft_body_html": {
            "type": "string",
            "description": "Written first. The draft of the article body, as HTML.",
        },
        "check": {
            "type": "string",
            "description": "Written second. One line per rule on what the draft got wrong, or NONE.",
        },
        "title": {
            "type": "string",
            "maxLength": 65,
            "description": "SEO title / article headline under 65 chars, contains the target keyword",
        },
        "h1": {
            "type": "string",
            "description": "H1 headline. Can be longer than the SEO title. Must contain the target keyword.",
        },
        "meta_description": {
            "type": "string",
            "maxLength": 160,
            "description": "155-160 chars, includes the keyword, compelling enough to earn the click. It is also the excerpt readers see under each title on the blog index and under related articles; write it knowing readers will see it.",
        },
        "main_image_alt": {
            "type": "string",
            "maxLength": 125,
            "description": "Descriptive alt text for the article's hero image (the image itself is added manually in Sanity)",
        },
        "slug": {
            "type": "string",
            "pattern": "^[a-z0-9]+(?:-[a-z0-9]+)*$",
            "description": "Kebab-case slug, no leading slash, no /blog prefix",
        },
        "body_html": {
            "type": "string",
            "description": (
                "Written after the check. The final article body, with every fault in the check corrected. "
                "Complete semantic HTML article body. Use <h2>, <h3>, <p>, <ul>, <ol>, <table>, "
                "<blockquote>. No <html>/<body>/<head> wrappers. No <h1> (that's separate). "
                "The minimum goal is 2,500 words, with FAQ excluded. Ideal length is about 3,000 to 3,500. "
                "Some article types, by nature, must be longer, such as long lists."
            ),
        },
        "faq_html": {
            "type": "string",
            "description": (
                "The FAQ section as HTML: three to eight questions, each an <h3>, each followed by "
                "one <p> answer of two to four sentences. Nothing else."
            ),
        },
        "internal_links": {
            "type": "array",
            "minItems": 2,
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Anchor text"},
                    "url": {"type": "string", "description": "URL path on the site"},
                },
                "required": ["text", "url"],
            },
        },
    },
    "required": [
        "draft_body_html", "check",
        "title", "h1", "meta_description", "main_image_alt",
        "slug", "body_html", "faq_html", "internal_links",
    ],
}


CONTENT_SYSTEM = CONTENT_SYSTEM.replace("<<STAT_RULE>>", STAT_RULE).replace("<<COMPETITORS>>", ", ".join(settings.competitor_domains()))
