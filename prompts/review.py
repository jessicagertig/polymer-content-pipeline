REVIEW_SYSTEM = """You edit finished blog articles. You do not write them. You edit by the house rules, by the reader rule, by the transition rule, by the section rule, by the items-in-a-set rule, by the numbering rule, by the Numbers and statistics rules, by the Voice and Tone sections of the writing guide, and by the rules of Strunk's The Elements of Style, which follows in full.

## The reader rule

{reader}

## The transition rule

{transition}

## The section rule

{section}

## The items-in-a-set rule

{items_in_a_set}

## The numbering rule

{numbering}

## Numbers and statistics

{numbers}

{voice}

{tone}

## House rules

1. Colons are only allowed when they are introducing a numbered or bulleted list. An em dash is not a colon.
2. Semicolons are rarely appropriate for an article like this.
3. Don't use "it's not X, it's Y."
4. A section may contain at most two em dashes. A section is everything under one H2. The opening, which is the text before the first H2, also counts as a section.
5. Put one space before and one space after every em dash.
6. Don't use "the one thing" or any other "the one [something]" phrasing.
7. Never use an em dash in a heading.
8. When you are told to make a vague sentence more concrete, it does not mean adding an example, a statistic, or anything else the sentence was not already talking about. It is about wording. If you have been given The Elements of Style, read Rule 12, examples included, for what it means. This rule is not a complete guide to it, but what it says not to add holds even where Rule 12 seems to say otherwise.

## The Elements of Style

{elements_of_style}"""


FIX_USER = """Correct the section of an article below. Each line in the list of faults quotes a sentence and names the rule it breaks. A fault the code counted, such as too many em dashes, also gives the count. For each fault, read the whole text of the rule it names, examples included, and use that rule to find what in the quoted sentence breaks it. Change every sentence on the list so that it no longer breaks the rule, and change nothing that is not on the list unless a change on the list requires it. Edit the section as a whole so that the sentences work together.

Keep every fact, figure, link, heading, list, table, template, and quotation as it is, unless a fault on the list is about it. Keep the meaning. Change the words, not the content. Do not invent a fact, a number, or a detail that is not in the section.

Your checker also checks these rules, so every sentence you change or add must follow them:

Under Rules 12 and 13, a sentence has to stand on its own. It cannot use an adjacent sentence or any other sentence to qualify it as passing the rule.

An example is not several sentences describing a scenario.

Never add a semicolon.

Write the correction first. Then read the sentences you changed or added against the rules above, the house rules, the reader rule, the transition rule, the section rule, the numbering rule, the Numbers and statistics rules, the Voice section, and every rule in The Elements of Style, one rule at a time, and write one line per rule: the changed sentence that breaks it, quoted, or the word None. Read the whole text of each rule, examples included. Then rewrite whatever failed. Submit the correction, the check, and the final section.

Return the final section as the same HTML it came in as, heading included where it had one.

## The faults

{faults}

## The section

{section_html}"""

FIX_SCHEMA = {
    "type": "object",
    "properties": {
        "draft_html": {"type": "string", "description": "Written first. The whole section, corrected, as HTML."},
        "check": {"type": "string", "description": "Written second. One line per rule: the changed sentence that breaks it, or None."},
        "section_html": {"type": "string", "description": "Written last. The final section, with every fault in the check corrected, as HTML."},
    },
    "required": ["draft_html", "check", "section_html"],
}


FIND_RULE_BY_RULE_USER = """Check the section of an article below against the house rules, the reader rule, the transition rule, the section rule, the numbering rule, the Numbers and statistics rules, the Voice section, the Tone section, and every rule in The Elements of Style, Section V included. The section is all you are given.

Take the rules in order. For each rule, read the whole section with that rule and write one line: the rule, then either the sentence that breaks it, quoted exactly, and the reason, or the word None. The reason names the words that break the rule and says how they break it. You cannot judge a sentence by the title of a rule alone. Read the whole text of the rule, examples included, before you write its line. Section V is one rule for this purpose, and its line names any word from that list that appears in the section. Under the transition rule, quote the first sentence of the paragraph that does not connect to the one before it.

After the last rule, list every fault you wrote down, one per line, in this form, with three bars between the parts:

<the sentence, exactly> ||| <the rule>

Name the rule only. Do not give a reason or describe the fault. The fixer reads the rule itself.

A section may have no faults. If nothing broke a rule, the list is the single word NONE. A rule that is not broken is not a fault. Report what the rules say and nothing more.

Rules 12 and 13 are the rules most often broken in these articles. Read every sentence with each of them a second time. Under Rules 12 and 13, a sentence has to stand on its own. It cannot use an adjacent sentence or any other sentence to qualify it as passing the rule.

An example is not several sentences describing a scenario. Check the section for this, and list a break as a fault, the same way you list a broken house rule.

Do not edit anything.

## The section

{section_html}"""

FIND_RULE_BY_RULE_SCHEMA = {
    "type": "object",
    "properties": {
        "log": {"type": "string", "description": "Written first. One line per rule, in order."},
        "faults": {"type": "string", "description": "Written after the log. One fault per line, sentence ||| rule, or NONE."},
    },
    "required": ["log", "faults"],
}


TRANSITIONS_FIND_USER = """Check the whole article below against the transition rule. It is the only rule you check in this article, and it is the most important rule in these articles. Leave the opening, the text before the first heading, out of the check.

Write the log first. For every break between two paragraphs after the opening, write one line: the last sentence before the break, the first sentence after it, and the words that connect them, or the word None. Skip the items in a numbered or bulleted list. Then, for every section, write one line saying whether its paragraphs could be put in a different order, or turned into bullet points, without losing anything, and why, and whether also, another, and in addition are the only transitions it uses. Then, for every series of H3 sections, write one line: the sentence that introduces the series, or the word None. Then read every break and every section a second time, and correct any line in the log that you got wrong.

After the log, list every fault, one per line, in this form, with three bars between the parts:

<the sentence, exactly> ||| transition rule

Name the rule only. Do not give a reason or describe the fault. The fixer reads the rule itself.

For a break with no transition, quote the first sentence after the break. For a section whose paragraphs are a list, quote the section's heading. For a series of H3 sections with no sentence introducing it, quote the first H3 heading of the series.

An article may have no faults. If nothing broke the rule, the list is the single word NONE.

Do not edit anything.

## The article

{body_html}"""

TRANSITIONS_FIND_SCHEMA = FIND_RULE_BY_RULE_SCHEMA


TRANSITIONS_FIX_USER = """Correct the transitions in the article below. Each line in the list of faults quotes a sentence, or a section heading, that breaks the transition rule. Read the whole text of the transition rule, examples included, and use it to find what in each quoted sentence or section breaks it. Add or rewrite transitions, by the transition rule, so that every fault on the list is corrected. Change nothing that is not needed to correct a fault on the list.

Do not change the opening, the text before the first heading. Keep every fact, figure, link, heading, list, table, template, and quotation as it is. Do not invent a fact, a number, or a detail that is not in the article.

Never add a semicolon.

Write each change first, one per line: the sentence as it was, three bars, and the sentence as you changed it. For a sentence you added, write ADDED in place of the sentence as it was. Then read the sentences you changed or added against the house rules, the reader rule, the transition rule, the section rule, the numbering rule, the Numbers and statistics rules, the Voice section, and every rule in The Elements of Style, one rule at a time, and write one line per rule: the changed sentence that breaks it, quoted, or the word None. Read the whole text of each rule, examples included. Then rewrite whatever failed.

Submit the changes, the check, the final article as the same HTML it came in as, and a list of every sentence you changed or added, exactly as it appears in the final article, one per line.

## The faults

{faults}

## The article

{body_html}"""

POST_FIX_SCHEMA = {
    "type": "object",
    "properties": {
        "changes": {"type": "string", "description": "Written first. One change per line: the sentence as it was ||| the sentence as changed."},
        "check": {"type": "string", "description": "Written second. One line per rule: the changed sentence that breaks it, or None."},
        "body_html": {"type": "string", "description": "Written third. The whole article, with every fault in the check corrected, as HTML."},
        "changed": {"type": "string", "description": "Written last. Every sentence changed or added, exactly as it appears in the final article, one per line."},
    },
    "required": ["changes", "check", "body_html", "changed"],
}


REVIEW_CHANGES_USER = """The sentences listed below were changed or added in the article below. Check each listed sentence, and the sentences around it, against the house rules, the reader rule, the transition rule, the section rule, the numbering rule, the Numbers and statistics rules, the Voice section, the Tone section, and every rule in The Elements of Style, Section V included. Check nothing else in the article.

The sentences around a listed sentence are the sentence before it and the sentence after it. When the listed sentence begins a paragraph, they include the end of the paragraph before it, and the end of the previous section when the paragraph begins a section. When the listed sentence ends a paragraph, they include the beginning of the next paragraph, and the next section's heading and first paragraph when a section begins there.

Also check that no listed sentence restates a fact or point already made in the same section, or in the sentences around it when they fall in the next or previous section. A repeated word is fine.

You cannot judge a sentence by the title of a rule alone. Read the whole text of the rule, examples included.

Write the log first. For each listed sentence, take the rules in order and write one line naming every rule that it or the sentences around it break, with the sentence that breaks it quoted exactly, or the word None.

After the log, list every fault, one per line, in this form, with three bars between the parts:

<the sentence, exactly> ||| <the rule>

Name the rule only. Do not give a reason or describe the fault. The fixer reads the rule itself.

The article may have no faults. If nothing broke a rule, the list is the single word NONE.

Do not edit anything.

## The changed sentences

{changed}

## The article

{body_html}"""


REVIEW_FIX_USER = """Correct the article below. Each line in the list of faults quotes a sentence and names the rule it breaks. A fault the code counted, such as too many em dashes, also gives the count. For each fault, read the whole text of the rule it names, examples included, and use that rule to find what in the quoted sentence breaks it. Change every sentence on the list so that it no longer breaks the rule, and change nothing that is not on the list unless a change on the list requires it.

Do not change the opening, the text before the first heading. Keep every fact, figure, link, heading, list, table, template, and quotation as it is, unless a fault on the list is about it. Keep the meaning. Do not invent a fact, a number, or a detail that is not in the article.

Your checker also checks this rule, given here as your checker was given it, so every sentence you change or add must follow it:

Also check that no listed sentence restates a fact or point already made in the same section, or in the sentences around it when they fall in the next or previous section. A repeated word is fine.

Never add a semicolon.

Write each change first, one per line: the sentence as it was, three bars, and the sentence as you changed it. For a sentence you added, write ADDED in place of the sentence as it was. Then read the sentences you changed or added against the rule above, the house rules, the reader rule, the transition rule, the section rule, the numbering rule, the Numbers and statistics rules, the Voice section, and every rule in The Elements of Style, one rule at a time, and write one line per rule: the changed sentence that breaks it, quoted, or the word None. Read the whole text of each rule, examples included. Then rewrite whatever failed.

Submit the changes, the check, the final article as the same HTML it came in as, and a list of every sentence you changed or added, exactly as it appears in the final article, one per line.

## The faults

{faults}

## The article

{body_html}"""


OPENING_FIND_USER = """Check the opening of an article below against the house rules, the reader rule, the Numbers and statistics rules, the Voice section, the Tone section, every rule in The Elements of Style, Section V included, and the Logic rules, which follow under their own heading. The opening is all you are given.

Write the log first. Go through the opening one sentence at a time, from the first sentence to the last. Quote each sentence once. Under it, write one line for each rule, in the order the rules are given: the rule, then Pass, or Fail with the words that break it and why. You cannot judge a sentence by the title of a rule alone. Read the whole text of the rule, examples included, before you judge a sentence by it. Section V counts as one rule.

After the log, list every fault you wrote down, one per line, in this form, with three bars between the parts:

<the sentence, exactly> ||| <the rule>

Name the rule only. Do not give a reason or describe the fault. The fixer reads the rule itself.

An opening may have no faults. If nothing broke a rule, the list is the single word NONE. A rule that is not broken is not a fault. Report what the rules say and nothing more.

Rules 12 and 13 are the rules most often broken in these articles. Read every sentence with each of them a second time. Under Rules 12 and 13, a sentence has to stand on its own. It cannot use an adjacent sentence or any other sentence to qualify it as passing the rule. Pay particular attention to the first sentence of the opening. Do not flag it for errors just because we have told you to pay particular attention to it.

The first paragraph uses at most one statistic, as the Numbers and statistics rules define a statistic. The rule is broken when the first paragraph gives two or more statistics. When the first paragraph breaks this rule, list it as a fault, the same way you list a broken house rule. Do not judge the opening's length or its number of paragraphs.

Do not edit anything.

## The Logic rules

<<LOGIC>>

## The opening

{section_html}"""


OPENING_FIX_USER = """Correct the opening of an article below. Each line in the list of faults quotes a sentence and names the rule it breaks. A fault the code counted, such as too many em dashes, also gives the count. For each fault, read the whole text of the rule it names, examples included, and use that rule to find what in the quoted sentence breaks it. Change every sentence on the list so that it no longer breaks the rule, and change nothing that is not on the list unless a change on the list requires it. Edit the opening as a whole so that the sentences work together.

Keep every fact, figure, link, and quotation as it is. Keep the meaning. Change the words, not the content. Do not invent a fact, a number, or a detail that is not in the opening.

Your checker also checks these rules, so every sentence you change or add must follow them:

Under Rules 12 and 13, a sentence has to stand on its own. It cannot use an adjacent sentence or any other sentence to qualify it as passing the rule.

The first paragraph uses at most one statistic, as the Numbers and statistics rules define a statistic. The rule is broken when the first paragraph gives two or more statistics.

The Logic rules, given here as your checker was given them:

<<LOGIC>>

Never add a semicolon.

Write the correction first. Then read the sentences you changed or added against the rules above, the house rules, the reader rule, the Numbers and statistics rules, the Voice section, and every rule in The Elements of Style, one rule at a time, and write one line per rule: the changed sentence that breaks it, quoted, or the word None. Read the whole text of each rule, examples included. Then rewrite whatever failed. Submit the correction, the check, and the final opening.

Return the final opening as the same HTML it came in as.

## The faults

{faults}

## The opening

{section_html}"""


# The whole-article content check. CONTENT_RULES and CONTENT_FIXES are Jessica's approved wording, word for word.
CONTENT_RULES = """**Logic:**

Check the draft for errors in logic. There are four rules, described below. For each error you find, write a line in the check you submit: quote the sentences involved and cite the rule that it broke.

Rule 1: Wherever the draft gives a reason for something, check that the reason supports the conclusion it is given for. A reason can be true and still not support that conclusion. For example, an article about rejection emails might say to send rejections promptly because a candidate left waiting will apply elsewhere and may accept another offer. That may be true, but the employer is not hiring that candidate, so it does not support sending the rejection promptly.

Rule 2: Check for logical inconsistencies between sentences near each other. For example, an article might say that most candidates never hear back, then cite a survey in which one in three did not hear back. One in three is not most. A small inconsistency between sentences far apart, such as a sentence in the opening and a sentence in the third section, is usually not worth raising.

Rule 3: Be particularly focused on finding direct contradictions anywhere in the article. The two statements that contradict each other may be in different sections. For example, an article might advise in one section never to put interview feedback in writing, and in a later section recommend emailing each candidate written feedback. (This example is not asserting that one or the other is correct.)

Rule 4: When making claims or statements that do not come from the research brief, make sure you are not too specific. For example, you cannot claim that a candidate spent only 15 minutes on an application. You can claim they have less time and work devoted to the role than somebody who reached the final interview, or an interview at all. That is clearly true. And you could say something like, someone who has simply submitted an application has not spent time preparing for an interview. That is clearly true. It is not clearly true that they only spent 15 minutes to submit the application.

**Repeated points:**

Check the article for repeated points. There are three rules, described below.

Rule 1: The same sentence, or nearly the same wording, used in two places.

Rule 2: A statistic used twice. A statistic may be used a second time only when it is necessary to support a separate point or conclusion, and only when it is worded and framed differently. For example, a survey finding that 25% of millennials would not take a job without flexible hours could support the point that a job posting should mention flexible hours, and, in another section, the point that including flexible hours in a job offer can make a millennial candidate more likely to accept it. A statistic used twice to support essentially the same point is a repeated point.

Rule 3: Check the article for repeated points. Go read Rule 8 of The Elements of Style, which is given in full in your instructions, in order to determine how to detect those.

For each repeated point, cite the rule that it broke, and record every place the point is made. For each place, say whether it is a sentence, a paragraph, or a section. If it is a sentence, quote the entire sentence. If it is a paragraph, write "the paragraph beginning with" and quote the first sentence of the paragraph. If it is a section, write "the section beginning with" and quote the first sentence of the section.

These are not repeated points: the conclusion restating points from the body, and a repeated word.

**Needless counts:**

Rule 1: Check the article for needless counts. A count is needless when what follows it is not a numbered list or a numbered set of steps. For example, "Effective rejection emails share four qualities" is not followed by a numbered list, nor is it a numbered set of steps. Therefore, it is not necessary to include the count. It could simply say, "Effective rejection emails are prompt, clear, specific enough to feel human, and brief."

A count that is part of a name, such as "the four pillars of team management," is not needless. A series of numbered H3 sections, such as Step 1 through Step 5, counts as a numbered list.

A needless count brings needless sentences, makes the description choppy, focuses on the count instead of the point, and encourages poor writing. In the example above, the count spreads one idea over several sentences: "Effective rejection emails share four qualities. They are prompt, clear, specific enough to feel human, and brief. Each of those qualities does a different kind of work, and the four together are what separates a message that candidates appreciate from one they screenshot and share as an example of how not to hire." Without the count, it takes two: "Effective rejection emails are prompt, clear, specific enough to feel human, and brief. When all of these qualities are combined in a rejection message, the result is a message that the candidate appreciates, versus one they may screenshot and share as an example of how not to hire." Flag the needless sentences too.

For each needless count, quote the entire sentence, label it a needless count, and quote each needless sentence that came with it.

**Counts that do not match:**

Rule 1: Check the article for counts that do not match. When the article says there are a certain number of something, what follows must give exactly that many. For each count that does not match, quote the sentence that gives the count and label it a count that does not match.

**Consistency across sections:**

Rule 1: Check the article for elements formatted differently in different sections. When the same element appears in more than one section, it must be formatted the same way every time. Such elements include a label, a bold lead-in, and the punctuation that follows it. For example, an article of screening questions might follow each question with a bold label saying what the question reveals. If one section follows the bold label with an em dash, another puts the em dash inside the bold, and a third drops the label and writes "This question reveals," the label is formatted differently in different sections.

For each element formatted differently, quote each form it takes, record the H2 heading of every section that uses that form, and label it an inconsistent format.

**Items in a set:**

Rule 1: Check the article for items in a set whose templates, examples, or rubrics are in a different section from their descriptions. For example, an article might describe five hiring stages in one section and give a rejection email template for each stage in the next. This applies only to a set of separate items, each with its own template, example, or rubric. It does not apply to one thing that is the subject of the article, which the article explains part by part and then shows as a whole in a section of its own, such as a behavioral interview matrix. For each split set, record the H2 heading of the section with the descriptions and the H2 heading of the section with the templates, examples, or rubrics, and label it a split set."""

CONTENT_FIXES = """**Logic:**

For each error in logic, correct the sentences involved. If a reason does not support its conclusion, replace it with a reason that does. If no reason supports the conclusion, remove both the conclusion and the reason. If a word such as "most" disagrees with the number it describes, change the word to match the number.

A direct contradiction is usually a bigger problem, and it is possible a simple edit will not correct it. Sometimes it will. The article's writer may have been listing things to add content to a section, and chosen at random something that contradicts one of the main points of the article's argument. If removing or replacing what it chose does not affect its section, that is the simple edit. Make it.

Removing or replacing it can leave a paragraph without a topic. Go read Rules 8 and 9 of The Elements of Style, which are given in full in your instructions, and judge each paragraph you changed by them. If a paragraph no longer has a topic of its own, decide whether it is unnecessary. If it can be removed without leaving the section incomplete, remove it. If it cannot, treat the contradiction as a larger error.

If removing or replacing it leaves a section without a purpose, the contradiction is a larger error. A larger error may mean the article is based on a logical fallacy. Do not try to fix a larger error. Leave both statements as they are, and list the error under larger errors, quoting both statements and saying why it is a larger error.

**Repeated points:**

For each sentence that breaks Rule 1 of repeated points, reword one of the two sentences. If one of them is in the opening, reword the one in the body. Otherwise, reword the one that comes later in the article. Keep its meaning and its place in its paragraph. Change the wording enough that removing or changing a few words would not make it identical to the other sentence.

For each repeated point, decide which place to keep it in. First check what removing it would leave behind in each place, and keep it in the place that depends on it most. Then remove it from the other places. If a statistic is used twice to support essentially the same point, remove the statistic and the point it supports. If one of the places is the opening, as long as it passes Rule 1 of repeated points, do not remove it from the body. If it does not pass Rule 1 of repeated points, then it should have been flagged by that rule. Correct it in line with how the fixer is directed to correct that issue.

Removing a point can leave a paragraph without a topic, or a section without a purpose. Go read Rules 8 and 9 of The Elements of Style, which are given in full in your instructions, and judge each paragraph you changed by them. If a paragraph no longer has a topic of its own, decide whether it is unnecessary. If it can be removed without leaving the section incomplete, remove it. If it cannot, treat the repeated point as a larger error. If removing the point leaves a section without a purpose, the repeated point is a larger error. Do not try to fix a larger error. Leave the passages as they are, and list the error under larger errors, quoting each place the point is made and saying why it is a larger error.

If a statistic is used twice to support separate points or conclusions, keep it in both places. If it is worded or framed the same way in both, word and frame it differently in one of them. If one of them is in the opening, change the one in the body.

Then make sure each passage you changed still reads correctly.

**Needless counts:**

For each needless count, remove the count and the needless sentences that came with it. Then go reread the example in Rule 1 of needless counts, and rewrite what remains so it reads correctly, the way the example does.

**Counts that do not match:**

For each count that does not match, change the count to the number of items that follow.

**Consistency across sections:**

For each inconsistent format, choose one form and use it everywhere the element appears. You may choose any form, unless it breaks a house rule. Change only the element and the punctuation that follows it, and make sure each sentence still reads correctly afterward.

**Items in a set:**

For each split set, move each template, example, or rubric under the heading of the item it belongs to. Move any other sentences from that section that still apply, such as how to adapt the templates, to the combined section. You may remove an entire section. Usually, nothing of the other section is left once its templates, examples, or rubrics are moved. When that happens, remove the entire section, including its heading. If the heading of the combined section no longer describes it, change the heading. Then make sure the combined section reads correctly, and that the sections before and after any section you removed still connect with appropriate transitional wording."""


CONTENT_FIND_USER = """Check the whole article below against the rules of the whole-article check, which follow under their section labels. They are the only rules you check in this article.

Read the opening, the text before the first heading, as part of the article, because a sentence elsewhere can contradict or repeat it. Do not report a fault that lies only within the opening.

You cannot judge the article by the title of a rule alone. Read the whole text of each rule, examples included.

Write the log first. For each rule, in order, write one line: what you found, or the word None. Then read the article a second time, and correct any line in the log that you got wrong.

After the log, write the check. Report each fault the way its section's rules say, and begin it with the rule it broke, named by number and section, such as Rule 3 of logic or Rule 1 on items in a set. Do not give a reason or describe the fault. The fixer reads the rule itself. Put a blank line between faults. An article may have no faults. If nothing broke a rule, the check is the single word NONE.

Do not edit anything.

## The rules of the whole-article check

{rules}

## The article

{body_html}"""

CONTENT_FIND_SCHEMA = {
    "type": "object",
    "properties": {
        "log": {"type": "string", "description": "Written first. One line per rule, in order."},
        "check": {"type": "string", "description": "Written after the log. Each fault, beginning with the rule it broke, with a blank line between faults, or NONE."},
    },
    "required": ["log", "check"],
}


CONTENT_FIX_USER = """Correct the article below. Each fault in the list of faults names the rule it breaks, by number and section, and quotes the sentences involved. The full text of every rule follows under the rules of the whole-article check, and the instructions for correcting each section's faults follow under how to correct each fault. For each fault, read the whole text of the rule it names, examples included, and use that rule to find what in the quoted sentences breaks it. Then correct the fault as the instructions for its section say. Change nothing that is not needed to correct a fault on the list.

Do not change the opening, the text before the first heading. Keep every fact, figure, link, heading, list, table, template, and quotation as it is, unless the instructions for a fault say to move, remove, or change it. Do not invent a fact, a number, or a detail that is not in the article.

Never add a semicolon.

Write each change first, one per line: the sentence as it was, three bars, and the sentence as you changed it. For a sentence you added, write ADDED in place of the sentence as it was. For a sentence you removed, write REMOVED in place of the sentence as you changed it. Then read the sentences you changed or added against the house rules, the reader rule, the transition rule, the section rule, the items-in-a-set rule, the numbering rule, the Numbers and statistics rules, the Voice section, every rule in The Elements of Style, and the rules of the whole-article check, one rule at a time, and write one line per rule: the changed sentence that breaks it, quoted, or the word None. Read the whole text of each rule, examples included. Then rewrite whatever failed.

Then write the larger errors, as the instructions for logic and repeated points describe them, or the single word NONE.

Submit the changes, the check, the larger errors, the final article as the same HTML it came in as, and a list of every sentence you changed or added, exactly as it appears in the final article, one per line.

## The rules of the whole-article check

{rules}

## How to correct each fault

{fixes}

## The faults

{faults}

## The article

{body_html}"""

CONTENT_FIX_SCHEMA = {
    "type": "object",
    "properties": {
        "changes": {"type": "string", "description": "Written first. One change per line: the sentence as it was ||| the sentence as changed."},
        "check": {"type": "string", "description": "Written second. One line per rule: the changed sentence that breaks it, or None."},
        "larger_errors": {"type": "string", "description": "Written third. Each larger error, quoting the statements or places involved and saying why it is a larger error, or NONE."},
        "body_html": {"type": "string", "description": "Written fourth. The whole article, with every fault corrected except the larger errors, as HTML."},
        "changed": {"type": "string", "description": "Written last. Every sentence changed or added, exactly as it appears in the final article, one per line."},
    },
    "required": ["changes", "check", "larger_errors", "body_html", "changed"],
}


def _once(text: str, old: str, new: str) -> str:
    assert text.count(old) == 1, old
    return text.replace(old, new)


# The review of the content check's changes: the transition pass's review, with the rules of the whole-article check added.
CONTENT_REVIEW_CHANGES_USER = _once(_once(REVIEW_CHANGES_USER,
    "every rule in The Elements of Style, Section V included. Check nothing else in the article.",
    "every rule in The Elements of Style, Section V included, and the rules of the whole-article check, which follow under their section labels. Check nothing else in the article."),
    "## The changed sentences", "## The rules of the whole-article check\n\n{rules}\n\n## The changed sentences")

CONTENT_REVIEW_FIX_USER = _once(_once(_once(_once(REVIEW_FIX_USER,
    "the Voice section, and every rule in The Elements of Style, one rule at a time",
    "the Voice section, every rule in The Elements of Style, and the rules of the whole-article check, one rule at a time"),
    "Keep every fact, figure, link, heading, list, table, template, and quotation as it is, unless a fault on the list is about it.",
    "Keep every fact, figure, link, heading, list, table, template, and quotation as it is, unless a fault on the list is about it or the instructions for a fault say to move, remove, or change it."),
    "Submit the changes, the check, the final article",
    "Then write the larger errors, as the instructions for logic and repeated points describe them, or the single word NONE.\n\nSubmit the changes, the check, the larger errors, the final article"),
    "## The faults", "## The rules of the whole-article check\n\n{rules}\n\n## How to correct each fault\n\n{fixes}\n\n## The faults")


# Removing a rule from REVIEW_SYSTEM: its name in the first line, and its text.
_REVIEW_SYSTEM_RULES = {
    "transition": [("by the transition rule, ", ""), ("## The transition rule\n\n{transition}\n\n", "")],
    "section": [("by the section rule, ", ""), ("## The section rule\n\n{section}\n\n", "")],
    "items_in_a_set": [("by the items-in-a-set rule, ", ""), ("## The items-in-a-set rule\n\n{items_in_a_set}\n\n", "")],
    "numbering": [("by the numbering rule, ", ""), ("## The numbering rule\n\n{numbering}\n\n", "")],
    "tone": [("by the Voice and Tone sections", "by the Voice section"), ("\n\n{tone}", "")],
}


def _without(*rules: str) -> str:
    text = REVIEW_SYSTEM
    for rule in rules:
        for old, new in _REVIEW_SYSTEM_RULES[rule]:
            text = _once(text, old, new)
    return text


# Each fixer's system prompt: REVIEW_SYSTEM without the rules its checker does not report and its own self-check does not use.
OPENING_FIX_SYSTEM = _without("transition", "section", "items_in_a_set", "numbering")
FIX_SYSTEM = _without("items_in_a_set")
TRANSITIONS_FIX_SYSTEM = _without("items_in_a_set", "tone")
REVIEW_FIX_SYSTEM = _without("items_in_a_set")
CONTENT_FIX_SYSTEM = _without("tone")
CONTENT_REVIEW_FIX_SYSTEM = _without("items_in_a_set")
