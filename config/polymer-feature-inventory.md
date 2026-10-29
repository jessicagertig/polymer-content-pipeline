# Polymer feature inventory

Facts about what Polymer does, from Polymer's own site, help center, changelog, and FAQ.

## 1. Account and organization

- **User account** with first name, last name, email, password, optional profile picture, global theme. Account settings apply across every organization the user belongs to. Sign in with Google. reCAPTCHA on login and signup.
- **Organization** created after email confirmation. Name becomes the job board display name and the default job board URL slug; both editable later. A user can belong to more than one organization, with per-organization notification preferences.
- **App settings** (gear icon) split into user preferences and, for Admins, the admin sections: Organization, Team, Message templates, Review templates, Job board, Job categories, Integrations, Plan & billing. Members see a reduced nav. Admins also have a Plato AI section and a Your API key tab.
- **Organization-wide exports**, three CSVs: all candidates, each with references to their job applications and the jobs they are in; all job applications individually, each with a reference to its candidate; and all jobs with their job data. Processed in the background for large datasets.

## 2. Team, roles, and access

Four roles, set at invite and changeable later from Team management. An Admin cannot change their own role.

- **Owner**: one per organization, full permissions, cannot be deactivated, is the organization's default email address, can assign Admin, can transfer ownership.
- **Admin**: sees and creates all jobs, purchases subscriptions and configures billing, configures and purchases distribution, invites users and sets roles, deactivates Admins and Members, assigns hiring teams.
- **Member**: sees only jobs they're on the hiring team for; can publish and edit those jobs, view their candidates, send review requests, create organization-wide message and review templates. Cannot buy distribution, invite, set roles, assign teams, or touch billing.
- **Interviewer**: sees only the candidate applications they've been sent a review request for, via the Review kit link. Can submit a review and manage their own account. Cannot see messages, files, the overview feed, templates, or job posts.
- **Unlimited users** on every plan.
- **Invites** by email with a role; pending invites show "Invite sent, not yet accepted" and can be cancelled or resent. A pending invitee can be added to a hiring team by email before they register.
- **Deactivate / re-activate** any user except the Owner; access is restored with the same control.
- **Changing a role is one click** from Team management. Hiring team membership is the job-level permission: adding someone to a job's hiring team lets them edit and configure that job and no other, while Admins see every job. There is no further permission configuration.
- **Hiring teams per job**: the Admin who creates a job is on it automatically; Members get job access only through hiring team membership; membership means the job shows in their list, they can edit it, work its candidates, and get its notifications.
- **Custom permissions**: custom application questions can be marked Admin-only so Member-role users don't see the answers, for salary expectations and similar. Admin-only questions come with every plan. The messaging feed, comments, reviews, and the salary expectation field can each be limited to Admins. With reviews limited to Admins, a hiring team member who is not an Admin sees only their own reviews. None of this needs an additional role.

## 3. Jobs and job setup

Job setup is one screen with tabs; everything stays editable after publishing.

- **Job details**: title, job category (categories managed org-wide in App settings), employment type including "Full-time or Part-time", hiring location, remote options (No remote, Remote friendly, Hybrid, Remote only), required country residency for remote roles, salary or wage with a unit, external listings on/off per job, per-job social share image override.
- **Job description** in a rich editor. Featured **video header** at the top of a post. **Location map** for physical locations.
- **Application form**: standard fields set to required, optional, or hidden; **custom questions** with custom fields, file uploads, and multiple choice; Admin-only visibility per question; candidate file uploads as a custom question type. Single-page, mobile-ready form; branded confirmation email after submitting.
- **Knockout questions**: a question on the application form whose answer passes or fails the candidate. Each candidate's answer is marked passed, failed, or not answered.
- **Document template**: a per-job hiring document template; each candidate gets a copy as their hiring document on apply, for process outlines, question lists, reference material. Can be added to a candidate later from the overview.
- **Hiring stages**: default Inbox, Screen, Interview, Decide, Offer, Hired, Archived. Rename, reorder by drag and drop, add, delete. Inbox, Hired, Archived are fixed; a stage with candidates in it can't be deleted; new stages land before Hired.
- **Hiring team** tab: add and remove members per job.
- **Automations** tab: an application-received automation that sends a templated message on apply and replaces the generic confirmation; and one **hiring stage message automation** per stage (see §5).
- **Preview** a temporary job post page before publishing.
- **Publish** to the board. Publishing the first job post starts the 14-day free trial.
- **Hide a job post**: removes it from the board and closes the application form while the job stays published and the team keeps messaging, reviewing, and commenting. Reversible. Hidden jobs still bill; archived jobs don't. **Archive** a job to stop billing for it; an archived job can be reverted to draft and republished.
- **Clone a job**: copies the job with all of its hiring stages, custom questions, and other configuration.
- **Job list** dashboard: title, publication status, category, employment type, location, remote tag, Inbox count, total candidates, gear, View job board link, "Your assigned jobs" filter, Create new job.
- **Share job post** button with quick links for LinkedIn, X, and other networks.
- **Candidate source tracking** with custom source links.
- **LinkedIn status in Job setup** showing whether the job meets LinkedIn's requirements, with real-time feedback.

## 4. Candidate management

- **Pipeline view per job**: stages in the left rail with counts, candidate list per stage, candidate panel, content pane. Move a candidate with one click; every stage change is tracked.
- **Filtering within a hiring stage**: filter the candidates in a stage by source, by whether they have a resume, by Plato fit score, and by a knockout question's result, passed, failed, or not answered. A filtered set can then be selected for a bulk action, such as moving every candidate who failed a knockout question to Archived or sending them all one message.
- **Sorting within a hiring stage**: sort the candidates in a stage by Plato fit score, by last candidate activity, by first name, by last name, or by applied-on date, each ascending or descending.
- **Bulk actions** within a hiring stage: select all candidates, deselect all, or select and deselect one at a time, then run a bulk action on the selection: **bulk move** to any stage (the automation indicator shows what will fire, with an option to skip the destination stage's automation), **bulk message** with a template or a typed body, delivered to each candidate individually, or **bulk Plato run** to review every selected candidate.
- **Move or clone a candidate to another job**: move a candidate to a different job and remove them entirely from the original job, or clone them so that an instance of the candidate, with their candidate information and job application answers, is added to the other job.
- **Candidate profile**: contact info, links (LinkedIn, X, GitHub, Dribbble, website), source, desired compensation; tabs for Overview, Resume, Messages, Files, Private notes.
- **Overview feed**: the hiring document at the top if one exists, custom question answers, then a running timeline of comments, reviews, review requests, stage moves, data deletion requests, and other events.
- **Resume**: view, download, upload, replace. **Resume parsing**: Polymer parses resumes but does not render the parsed result anywhere. The parsed data feeds Plato AI reviews.
- **Files**: application attachments, message attachments, and anything the team uploads, in one place.
- **Private notes**: a per-candidate notes page visible only to the author.
- **Shared comments**: time-stamped, visible to the hiring team.
- **Candidate reviews**: written feedback with a score, visible to the hiring team. **Review templates**: reusable content any user can create, reorder, insert into a review (multiple per review, fully editable after insert).
- **Request a review**: any hiring team member can request a review of a candidate from any organization member or from a new email address. The recipient gets a Review kit with contact info, links, resume, and hiring document, but no access to the job or the rest of the candidate. A new email becomes an Interviewer. Requests show in the overview feed.
- **Manually add a candidate** to a job with contact info, links, source, desired compensation, and a resume upload. **Bulk import** of candidates into a job from a CSV in a specified format, with contact info and, where a row includes an external URL for a resume, the resume downloaded from it. **Edit a candidate**: basic info and links apply to the candidate's global profile across jobs; source and desired compensation are per application.
- **Quick search** across candidates from the top bar.
- **Per-job exports**: all of a job's applications, with the candidate data, to CSV with name, email, resume URL, phone, location, links, notes, stage, applied date, source, and custom question answers; and a **bulk resume export** of every resume on the job as a ZIP with one PDF per application.
- **Candidate data deletion**: every confirmation and message email carries a "manage your data" link to a pre-filled, organization-scoped request form. The Owner is emailed, the overview feed shows the request to the whole hiring team, and only an Admin can complete it. Completion is irreversible, strips all personally identifying data and files from every application in the org, archives what's left as "Anonymized candidate," and emails the candidate a confirmation. Admins can also delete without a form submission.
- **Candidate source and funnel tracking** via custom source links and the source field.

## 5. Candidate communication

- **Messaging** from the candidate's Messages tab, delivered to the email they applied with; replies land in the same feed labelled Candidate, the sender gets an email, and the full history is visible to the whole hiring team.
- **Message templates**: organization-wide, created by any user, reorderable, with placeholders for candidate first name, candidate full name, job title, sender first name, sender full name, organization name. Create a template from an already-sent message.
- **Bulk messaging** to all or selected candidates in a stage.
- **Hiring stage message automations**: one per stage, choose the stage, once or every time, and a template. Fires on any move into the stage, including bulk moves and moves from another job. A lightning-bolt indicator says "N automations will run" before you move, with an info box. Edit, delete, disable, re-enable. Automated messages come from the organization, not a person; a sender-name placeholder resolves to whoever moved the candidate, or sign as "the team" for anonymous rejections.
- **Application confirmation**: automatic branded email on apply, or replaced by the application-received automation.
- **Notification hub** (bell icon): New candidates, New activity (reviews and comments by others), New messages. Filter by type or job with counts, mark read/unread, dismiss, bulk actions on the filtered list. One notification per candidate/job for activity and messages. Users only see jobs they're on. Per-user email notifications for every message, review, and comment, controllable in User preferences.

## 6. Job board and careers site

- **Instant job board** created at signup at jobs.polymer.co/<slug>, listing all published jobs with a page per job and an application form on each.
- **Branding**: logo, banner, custom text; header shows logo and name, name only, or logo only. Board title and intro content. Navigation settings. Careers page style refresh with prominent banners and job videos, tag icons, better mobile.
- **Custom domain**: point jobs.yourdomain.com or careers.yourdomain.com at the board via a CNAME to jobs-proxy.polymer.co and a TXT record; Polymer validates and issues SSL. Old jobs.polymer.co links keep working.
- **Job board SEO**: control the board's title and meta description.
- **Social share images**: board-level 1200 by 630 image that becomes the default for jobs, with per-job overrides.
- **Localization**: Dutch, Swedish, Spanish, French, German; more on request.
- **Job categories** to group posts on the board.
- **Job board subscriptions**: job seekers subscribe and get notified of new openings.
- **Embedded job board**: display jobs on any site you run with your own styles.
- **Job board API** and **Webflow CMS sync** for a fully custom careers site (see §7 and §8).
- Mobile-ready throughout.

## 7. Distribution

Included at no extra cost, enabled and configured in Integrations, and each can be disabled per job under External Listings:

- **Google Jobs**: on by default when a job publishes; "Show jobs in Google Search" toggle. Google indexes the post on its own schedule, which can take up to seven days.
- **LinkedIn Limited Listings** ("Basic Jobs"): posts to the company page's Jobs tab; needs the LinkedIn company ID saved in Polymer and the company page configured to allow basic job posting with Polymer connected as the ATS. Jobs need a hiring location and a 150+ character description; Polymer reformats descriptions and maps remote options to LinkedIn workplace types. Approval by LinkedIn is not guaranteed. Once approved, a listing appears within 24 hours, usually 6.
- **X Hiring**: free organic job posts; needs location and description; only yearly or hourly salary units and only full-time, part-time, or full-time contract carry over. Verified Organizations contact X to feature roles.

Paid placements bought inside Polymer:

- **We Work Remotely**: post directly from Polymer.
- **WhatJobs**: post to 500+ partner job boards, with a preview before publishing.

Plus **easy sharing links** and **custom source links** for tracking where applicants come from.

## 8. Integrations and API

- **Slack**: a channel receives the full application on every new candidate; separate settings for new-application and channel-message notifications; candidate replies post to Slack.
- **Discord**: same for a server channel.
- **Webflow**: sync published jobs into a CMS collection with mapped fields (title, published at, category, employment type, location, remote friendliness, description, application URL); on API v2. Edit in Polymer, not in Webflow.
- **Zapier**: three triggers, job published, new application received, candidate moved to Hired, authenticated with an API key and URL from the Zapier integration screen.
- **Google Analytics**: paste a GA4 measurement ID to track board traffic, on jobs.polymer.co or the custom domain.
- **Public API** at developer.polymer.co: unauthenticated, rate-limited job listings for an organization (all jobs, one job) for building a custom careers site.
- **Customer API**. Bearer-token auth with a key any Admin generates from the "Your API key" settings tab. Base `https://api.polymer.co/v1/hire`, paginated lists, `updated_since` filters for incremental sync.
  - **Organization**: get your org.
  - **Organization users**: list active, list deactivated, get one, with roles.
  - **Jobs**: list with status filter (published, draft, archived, public), get one with its application form standard fields and custom questions, get its hiring stages including whether each has an active message automation.
  - **Resume export**: start and poll an async export of every resume on a job, delivered as a ZIP with one PDF per application, signed URL good for 7 days. The same export exists in the app.
  - **Candidates**: list with email filter, get one, optionally with all their applications.
  - **Job applications**: list with job, stage, and candidate filters; get one; **apply** (submit a full application from anywhere, with resume, links, custom question answers including file uploads, and a choice of whether the candidate gets the confirmation email); **import** (add a sourced or migrated candidate straight into Inbox without form fields, no email sent); duplicate detection by email per job.
  - **Stage moves**: move an application to any stage on its job with an explicit choice to run or skip that stage's message automation; archive; read the full stage-transition history with who moved it and when.
  - **Reviews**: list, create with a rating and HTML body, update, delete your own.
  - **Comments**: list, create with an HTML body, update, delete your own; API-created ones are tagged as such.
  - **Messages**: read every email exchanged on an application with sender type.
  - **HTML body format**: sanitized allowed-element set for comments and reviews.

## 9. Plato AI candidate review

- Turned on per role as **auto-reviews**; runs the moment a candidate applies. **Bulk AI screening** of existing candidates; a "Run Plato" control in the pipeline rail.
- Pulls core, preferred, and bonus requirements from the job description and marks each as clear evidence (full match), related evidence (partial), or no evidence (no match), with reasoning under every criterion.
- Overall **fit level**: Excellent, Good, Mixed, Weak, Poor. Filter candidates by fit.
- **Anonymized before scoring**: name, location, email removed.
- A review returns a headline, a "Fit for this role" analysis, a scoring detail with met/partial/unmet counts, notable achievements, and relevant experience.
- **Included on every plan**: 50 / 100 / 150 credits a month on Starter / Growth / Scale; one credit is one completed review; failed runs don't consume a credit; top-ups and a credit subscription available; no per-seat AI charge. Credit add-on pricing is not published.

## 10. Plans, trial, and billing

- **Plans**: Starter $124, Growth $233, Scale $415 per month billed annually; $149, $279, $499 month to month. Every plan has the complete feature set, unlimited users, unlimited candidates. Plans differ by published jobs (5, 20, 50) and monthly Plato credits (50, 100, 150). Contact for more than 50 jobs.
- **Before the trial**: a company signs up without a credit card and can explore Polymer, create its hiring stages, invite users, add its branding and preview the job board, and create job drafts and preview the job postings, all without starting a trial.
- **Trial**: publishing the first job post starts the 14-day free trial. During it, publish as many jobs as you like and switch plans without ending it.
- **Billing**: Plan & billing in App settings for Owners and Admins; monthly or annual; invoices; promo codes once per subscription.

## 11. Data, privacy, and security

- Candidate data deletion flow (§4) with candidate-facing confirmation.
- Per-job CSV export and whole-organization export.
- Personal details stripped before AI scoring.
- Admin-only custom questions.
- reCAPTCHA on login and signup.
