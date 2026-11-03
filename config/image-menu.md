# Reference post images: what they look like

Written 2026-09-22 from the live images on polymer.co/blog, not from the alt text. Covers every body image in the five reference posts and in `recruiting-generation-z`, plus the header images.

This file does two jobs for whoever plans images:

- **Choosing:** a menu of the image types the blog uses and what each one suits.
- **Describing:** the visual terms to describe a proposed image in, so the description says what the image looks like. The alt text in the reference posts is written for screen-reader users and lists every word in the picture; it is not a model for describing a design.

## The house frame (every in-house image uses it)

- Background: a soft pastel gradient, pink to peach to lilac, running corner to corner. The direction varies from image to image.
- A white panel sits on it with rounded corners and a faint shadow, leaving a wide margin of gradient on all sides.
- Type is a plain sans-serif. Titles are bold black, and body text is regular dark gray.
- Credit: "Source: <name>" in small gray type, bottom right inside the panel. It appears whenever the content came from somewhere else.
- Color is black, white, and gray only. The one accent is an emoji, which carries all the color.
- Emoji always sit in a small rounded-square tile with a thin gray outline, never loose on the panel.

## The menu

### 1. Emoji definition card
- One concept per card. The emoji sits centered at the top in its outlined tile. Below it, the concept name is centered in bold, then a one-sentence definition in gray, then the source line.
- The emoji is a literal visual pun on the name: 😇 halo effect, 🐏 groupthink, 🖼️ framing effect.
- **Suits:** a named concept with a one-line definition.
- **Describe it like this:** White rounded panel on the pink-peach gradient; 😇 centered in an outlined square tile; "The halo effect" in bold below; one-line definition in gray; "Source: yourbias.is" bottom right.
- Seen in: `first-impression-bias` (halo effect, groupthink, framing effect).

### 2. Emoji row
- A centered bold title, then several concepts side by side. Each concept is divided off in its own outlined emoji tile, with a short label centered beneath it.
- **Suits:** a small set of parallel concepts (three to five) that belong together under one name.
- **Describe it like this:** White rounded panel on the gradient; "The Four Pillars of the Employer Value Proposition (EVP)" centered in bold; four outlined emoji tiles in a row, 🧭 🌐 🙌 🌱, each with its label centered underneath ("Mission & Purpose", "Culture & Environment", "Rewards & Wellbeing", "Growth & Development").
- Seen in: `employer-branding-steps`.

### 3. Emoji column card
- A large bold title top left. Below it, a grid of fields in two columns. Each field has its own outlined emoji tile on the left, a bold label to the right of the tile, and a few words of gray text under the label. A last field can run the full width.
- **Suits:** a profile of one thing across several attributes. Two cards with the same fields and emoji make a side-by-side comparison.
- **Describe it like this:** White rounded panel on the gradient; "Millennials" large and bold top left; two columns of fields, each with an outlined emoji tile on the left (🎉 Years, 💪 Skills, 🙌 Noteworthy characteristics, 🤔 Concerned about, ❤️ Media they love, 🤗 Preferred communication style), bold label, gray text beneath; a full-width 😑 Misconceptions row at the bottom.
- Seen in: `recruiting-generation-z` (Generation Z, Millennials).

### 4. Bar chart
- Title top left: either the finding itself ("Gen Z are the most diverse employee group yet") or what the chart measures ("Percentage of candidates by generation who…").
- Solid black horizontal bars, with category labels in bold on the left. Values are printed in white inside the bars. A dashed gray line marks the baseline. Source line bottom right.
- Variants:
  - Plain bars
  - Stacked black and gray bars with a small dot legend top right
  - A single progress bar against a light gray track, with a triangle marker
  - Bars against a labeled 1–5 scale
- **Suits:** one statistic or a small comparison. Several findings can share one chart when they're measured the same way (four generations, two sources).
- **Describe it like this:** White rounded panel on the gradient; "Applicants vs hires by source" in bold top left; dot legend top right, gray "% of Applicants", black "% of Hires"; two stacked horizontal bars labeled Careers Page (13% gray, 26% black) and Sponsored Ads (23% gray, 9% black), values in white inside the segments; dashed baseline; "Source: 2024 CareerPlug Report" bottom right.
- Seen in: `employer-branding-steps` (generations, applicants vs hires, 72% progress bar), `behavioral-interview-scoring-matrix` (candidate scores), `recruiting-generation-z` (diversity by generation).

### 5. Before-and-after comparison
- A bold title top left. Two outlined boxes side by side, joined by a thin gray arrow. Each box holds emoji repeated to show quantity, above one centered line with the key number in bold.
- **Suits:** a ratio, a return, or a cause and effect that fits in two short statements.
- **Describe it like this:** White rounded panel on the gradient; "Mental health return on investment" in bold top left; two outlined boxes joined by an arrow; left box has one 💵 over "For **$1** invested into mental health treatment"; right box has four 💵 over "You get **$4** in better health and productivity"; "Source: The Lancet" bottom right.
- Seen in: `recruiting-generation-z`.

### 6. Ranked list
- A bold title and a gray sentence summarizing the ranking. Below them, outlined pills, one per item, each starting with a bold "#1", "#2"… and stepping diagonally down and to the right.
- **Suits:** a ranking or an ordered sequence of three to six short items.
- **Describe it like this:** White rounded panel on the gradient; "What Gen Z is looking for" in bold with a one-sentence gray summary; five outlined pills stepping down to the right, "#1 Work/life balance" through "#5 Management", the number bold; "Source: InsideOut Development" bottom right.
- Seen in: `recruiting-generation-z`.

### 7. Redrawn document or example
- An outside or example document, retyped in the house frame:
  - the Agile Manifesto, centered with bold key phrases
  - a candidate scorecard table with thin gray row rules and a bold total
  - example questions grouped under bold headings with bullets
  - an annotated scorecard with gray bracket labels down the left margin naming each part
- **Suits:** something the reader could copy or use: a template, a scorecard, a question set, a founding text.
- **Describe it like this:** White rounded panel on the gradient; "Candidate scorecard" in bold top left; two columns, Criteria and Candidate score, with thin gray rules between rows; each score a bold number followed by its label in gray ("4 Above standard"); "Total score 23" in bold at the bottom.
- Seen in: `agile-recruiting-process`, `behavioral-interview-scoring-matrix`.

### 8. Polymer product screenshot
- A crop of real Polymer UI inside the white panel on the gradient, with fictional sample data ("Tablespace Games", "Ella Patterson"). Sometimes cropped tight and enlarged on the part that matters.
- **Suits:** showing the reader the Polymer feature the paragraph names.
- **Describe it like this:** Polymer screenshot on the pink-peach gradient, framed in the white panel; the iOS Developer pipeline for Tablespace Games, stage list on the left with counts, candidate list in the middle with Ella Patterson selected, her Overview on the right.
- Seen in: every post except `behavioral-interview-scoring-matrix`: pipeline, messages, team members, job board page and settings.

### 9. Third-party screenshot
- A screenshot of someone else's product or post: Miro, Google Sheets, a scanned scorecard, HubSpot, Whalesync, a talent-collective page, a tweet.
- Product screenshots mostly sit on a flat light-gray background instead of the gradient, which marks them as outside material. Tweets (Cisco, Spotify) sit on the gradient.
- **Suits:** a real-world example the paragraph points to.
- **Describe it like this:** Screenshot of a Google Sheets interview scoring matrix on a flat light-gray background; criteria, sample questions and scores in columns, a 1–5 scoring scale on the right.

### 10. Diagram of a named experiment
- Redraws the stimulus the participants saw, under the question they were asked, with a source line. It shows the thing itself, not the study's design or its results.
- **Suits:** a famous experiment the reader can grasp by seeing what the participants saw.
- **Describe it like this:** White rounded panel on the gradient; "Which line is the same length as the line on the left?" in bold; a black reference bar labeled Line, then three black bars A, B and C of different heights on a dashed baseline; "Source: practicalpie.com" bottom right.
- Seen in: `first-impression-bias` (Asch line test).

### Header image (featureImage)
- A white outline icon on solid black, sometimes with dashed white circles. Examples: an eye with a stopwatch iris, a flame. Planned separately from body images.

## By post

- **first-impression-bias** (8 body): emoji cards ×3, Asch diagram, Miro screenshot (gray), Polymer pipeline, Polymer job board settings, scanned scorecard (gray).
- **a-player** (3 body): talent-collective cards on black (third-party), Polymer messages, Polymer pipeline.
- **agile-recruiting-process** (4 body): redrawn Agile Manifesto, Polymer job board, Polymer pipeline (enlarged), Polymer team members.
- **behavioral-interview-scoring-matrix** (5 body): annotated scorecard, redrawn candidate scorecard, redrawn example questions, Google Sheets matrix (gray), candidate scores bar chart.
- **employer-branding-steps** (8 body): generation bar chart, EVP emoji row, HubSpot culture code (gray), Cisco tweet, applicants vs hires stacked bars, Polymer job board page, Whalesync (gray), 72% progress bar.
- **recruiting-generation-z** (7 body): Generation Z emoji column card, Millennials emoji column card, diversity-by-generation stacked bars, Spotify tweet, Polymer messages, mental health before-and-after, ranked list of what Gen Z looks for.

## Using this

Pick from the menu the type that suits the content at that spot, and offer more than one where more than one fits. Describe each proposed image in the visual terms of its "Describe it like this" line — frame, tile, layout, where the title and source sit — and keep the text on it as short as the reference images keep theirs.
