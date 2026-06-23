# EZCollegeApp Advertorial Agent Knowledge Base

Last reviewed: 2026-05-27

This knowledge base is for an advertising, native-content, or advertorial generation agent. Its job is to help the agent understand the current EZCollegeApp product deeply enough to write accurate promotional content, choose the right product angle, and include the same kind of in-app navigation memory that the current chatbot uses.

The goal is not hype. The goal is accurate, useful, product-grounded marketing.

Important compliance rule: if a channel requires disclosure for ads, sponsored posts, affiliate posts, paid creator content, or native advertising, the generated content must disclose that relationship according to the channel's rules. Do not disguise paid content as a real student's independent story.

## 1. One-Sentence Product Positioning

EZCollegeApp is an AI-powered college application workspace for US undergraduate admissions. It connects document upload, student profile building, school selection, school-specific application forms, Common App and supplemental essay writing, admissions forecasting, submission tracking, and AI counselor chat in one guided workflow.

Recommended positioning:

- "Not just a generic chatbot: an AI application workspace organized around the actual college application process."
- "A place where students can connect their profile, documents, school list, school forms, and essays."
- "A navigation-aware AI counselor that can point students to the exact product page they need next."
- "A school-based writing workflow: essays are organized by the schools the student is applying to, not just by a generic blank editor."

Avoid positioning:

- "Guaranteed admission."
- "Official Common App partner."
- "Automatically submits applications for the student."
- "Always has every school's latest requirement."
- "Replaces human counselors or admissions officers."
- "Completes the whole application without student review."

## 2. Primary Audiences

### 2.1 Students

Common pains:

- They do not know where to start.
- School lists, essays, forms, files, and deadlines are scattered across different tools.
- They do not know which essays each school requires.
- They struggle to reuse stories across Common App and supplemental prompts without sounding copied.
- They want an AI that remembers their background, documents, target schools, and current application stage.

Strong content angles:

- "Turn a messy application season into a step-by-step workspace."
- "Start from your school list, then see the essays each school actually needs."
- "When you get stuck, the AI counselor can send you to the right page instead of giving generic advice."

### 2.2 Parents

Common pains:

- They want visibility into progress without micromanaging every draft.
- They worry about missed documents, missed deadlines, and school-specific requirements.
- They do not want the application process to live in spreadsheets, text messages, and scattered files.

Strong content angles:

- "Not a tool that applies for the student, but a tool that makes the process visible and trackable."
- "School list, form progress, writing status, and submission status live in one system."

### 2.3 Counselors and Small Advising Teams

Common pains:

- Student materials are scattered.
- Counselors repeatedly ask for basic profile, activity, testing, and school-list information.
- School-specific supplemental prompts and form questions are difficult to track across many students.
- Essay review is time-consuming, but generic AI feedback is not good enough.

Strong content angles:

- "Use AI for organization, retrieval, first-pass diagnostics, and navigation while preserving human judgment."
- "A student-facing application status board and writing diagnostic assistant."

## 3. Product Workflow

The logged-in product can be described as six connected chapters:

1. Prepare: upload application materials and build the student's knowledge base.
2. Build Profile: create a Common App-style student profile from typed fields and uploaded evidence.
3. Colleges: search schools, add them to the student's list, and classify them as Reach, Target, or Safety.
4. School Forms: open each school's application form, view questions, save answers, and use the form helper.
5. My Writing: organize the Common App essay and school-specific writing tasks by school; draft, evaluate, snapshot, revise, and export.
6. Admission Forecast and Submit: refresh predictions after profile or school-list changes, then track readiness and submitted status.

Marketing content should not reduce the product to "AI chat." The stronger and more accurate claim is that chat, student data, school selection, school forms, and writing are connected inside the product.

## 4. Navigation Memory

The current chatbot has a product navigation prompt in:

`apps/core-api/fast_api_server/prompts/counselor/product_navigation.md`

When the chatbot recommends an in-product action, it is instructed to use a Markdown link whose href starts with `/`. The portal renders those Markdown links as in-app navigation buttons.

Use these route memories in advertorial content when the target reader is already a logged-in user or the content is meant to describe in-app behavior.

| Page | Route | When to recommend it | Example CTA |
| --- | --- | --- | --- |
| Build Profile | `/build-profile` | The student needs to complete background, academics, activities, awards, testing, or uploaded evidence. | Open [Build Profile](/build-profile) first so the AI can ground writing and strategy in the student's real record. |
| AI Counselor | `/consultant` | The student wants strategy, essay advice, deadline help, school-list advice, or next-step planning. | Open [AI Counselor](/consultant) and ask the question in context. |
| Colleges | `/colleges` | The student wants to search universities, add schools, classify Reach / Target / Safety, or open a school application. | Open [Colleges](/colleges), search the school, choose Reach / Target / Safety, then click Add. |
| Admission Forecast | `/admission-forecast` | The student changed their profile or school list and wants updated portfolio or per-school predictions. | Open [Admission Forecast](/admission-forecast) after updating your profile or school list. |
| My Writing | `/my-writing` | The student wants to draft, revise, evaluate, snapshot, or export essays. | Open [My Writing](/my-writing), pick the school or Common App essay, then run review. |
| Submit | `/submit` | The student wants to review deadlines, submission readiness, portal shortcuts, or mark applications submitted. | Open [Submit](/submit) to check which schools are ready and which are still pending. |
| Product Guide | `/product-guide` | The student needs onboarding or a visual map of the product. | Open [Product Guide](/product-guide) if you want the guided map first. |

Implemented but not part of the current product navigation prompt:

| Page | Route | Accuracy note |
| --- | --- | --- |
| Final Read | `/final-read` | This route exists in the app and shows a cross-essay final-read board. The current product navigation prompt does not list it, so use it sparingly unless the content is specifically about final essay readiness. |

Rules for route usage:

- Do not invent routes.
- Do not link directly to dynamic routes like `/college/<code>` unless a real school code is already available in the current context.
- For school-specific forms, route users through [Colleges](/colleges) and tell them to click "Open application."
- For public acquisition content, prefer public CTAs such as signup, pricing, product guide, or the homepage. Use authenticated product routes only when describing in-app behavior or targeting logged-in users.

## 5. AI Counselor Memory

### 5.1 What the Agentic Chat Is

The main agent prompt is in:

`apps/core-api/fast_api_server/prompts/agentic_chat_prompt.md`

The AI counselor is designed for US college application advising. It can use:

- Long-term memory
- Episodic memory
- A database-generated student snapshot
- Uploaded documents and the student's knowledge base
- University FAQ / admissions policy search
- The student's Build Profile
- The student's target school list
- Personal statement draft retrieval
- School-specific essay draft retrieval
- Testing, activities, and honors detail retrieval
- Admission prediction tools

Accurate marketing language:

- "The counselor is grounded in the student's profile, uploaded materials, essays, and school list when those are available."
- "For time-sensitive facts like deadlines, fees, and school requirements, the system should rely on verified database or official-source-backed information rather than guessing."
- "The assistant can connect advice to the student's current product state."

Avoid:

- "It knows every school's latest policy automatically."
- "It can answer deadlines and fees accurately without checking data."
- "It submits official applications for the student."

### 5.2 Counselor Roles

The workspace supports a Team Room and specialist roles:

- Admissions Strategist: priorities, school fit, and Reach / Target / Safety strategy.
- Essay Coach: essay idea quality, narrative development, prompt fit, admissions-reader reality checks, and revision strategy.
- Application Coordinator: materials, deadlines, forms, and submission progress.
- Team Room: a group chat that can use shared case notes and route to the right specialist.

Good advertorial angle:

- "The AI is not treated as one generic assistant. Strategy, writing, and coordination are separated into specialist modes."
- "The conversation carries product context such as profile completeness, tracked schools, applications in progress, submitted applications, and uploaded file count."

### 5.3 Navigation-Aware Responses

The product navigation prompt tells the chatbot to recommend exact pages, not vague actions. Examples:

- If the student asks how to add schools, recommend [Colleges](/colleges).
- If the student asks how to improve an essay, recommend [My Writing](/my-writing) or [Build Profile](/build-profile), depending on whether the missing piece is draft work or background evidence.
- If the student asks what is due, recommend [Submit](/submit) or [AI Counselor](/consultant), depending on the question.

The frontend also renders internal Markdown links as button-like links and can show route suggestion chips such as "Open Build Profile," "Open Colleges," or "Open My Writing."

Advertorial content should imitate this product behavior: end with a concrete next product step, not just "try the AI."

## 6. School-Based Writing System

This is one of the most important product differences from generic essay tools.

### 6.1 Writing Is Not Just a Blank Editor

The `/my-writing` page, implemented in `apps/portal-web/src/pages/MyWriting.tsx`, organizes:

- Common App Personal Statement
- School-specific essay requirements for tracked schools
- Essay cards grouped by school
- Prompt text
- Word limit
- Due date when available
- Required / optional / conditional status when available
- Source metadata
- Word count
- Latest evaluation score
- Next edit summary
- Saved / evaluated / readiness state
- Snapshot versions
- Export to Word / PDF
- Essay Coach chat panel

Accurate marketing language:

- "The writing page is school-based. Students first see what each school needs, then write."
- "After a school is added, the writing page can show the writing tasks associated with that school when form data exists."
- "Each writing task can carry prompt, word limit, requirement status, draft state, and review state."

Boundary language:

- "School essay lists depend on the backend database's school form / Common App schema data."
- "If a school has no form data in the database, the system should not invent official prompts."
- "Word limits come from form fields or prompt parsing. If a value is uncertain, students should verify official requirements."

### 6.2 How School Questions Become Writing Tasks

The backend endpoint `/api/agent/essay/requirements` is implemented in:

`apps/core-api/fast_api_server/routers/essay_workflow.py`

It:

1. Loads the student's target schools.
2. Retrieves school form detail through the school form service.
3. Filters form questions to identify writing-like prompts.
4. Derives a title, essay category, prompt text, word limit, requirement metadata, and source.
5. Groups writing requirements by school for My Writing.
6. Attaches matching evaluation data only when the saved answer's hash matches the latest evaluation run.

Accurate marketing language:

- "When school form data is available, EZCollegeApp can turn school-specific long-answer questions into writing tasks."
- "Writing tasks are derived from stored school form schema and answers, not guessed from memory."
- "This lets the student move from a school list to a school-by-school writing checklist."

Avoid:

- "The system live-scrapes the student's Common App page."
- "Every school and every cycle is guaranteed to have complete prompts."
- "The system can know every school's prompt without stored form data."

### 6.3 Evaluation Is Prompt- and Word-Limit-Aware

The essay evaluation prompt is in:

`apps/core-api/fast_api_server/prompts/essay_eval/essay_evaluation.md`

It receives:

- Essay type
- Essay text
- Numbered paragraphs
- Word limit
- Actual word count
- Prompt context
- Dimension list

The prompt explicitly says that if the prompt context is a short supplemental answer, the evaluator should switch from full-essay diagnostics to focused response review. For short answers, the best feedback should focus on exact prompt fit and high-leverage edits, not a 650-word Common App narrative structure.

Accurate marketing language:

- "Review changes with the assignment. A 150-word short answer should not be graded like a 650-word personal statement."
- "For short supplements, the evaluator focuses on direct prompt fit, one clear claim, concrete evidence, and staying within the limit."
- "For longer essays, the evaluator can analyze self-revelation, specificity, reflection, structure, voice, differentiation, and AI-feel risk."

### 6.4 Essay Coach Context Inside My Writing

The Essay Coach panel is implemented in:

`apps/portal-web/src/components/mywriting/AIDraftPanel.tsx`

It passes writing context such as:

- Draft vs selected-passage mode
- Common App prompt
- Selected passage text
- Selected writing/review skills
- Latest evaluation summary
- Repurpose target: school code, school name, prompt
- Product case state

Accurate marketing language:

- "Essay Coach is not isolated chat. It knows which essay or passage the student is working on and can use evaluation context."
- "It supports story mining, voice calibration, prompt-fit review, repurposing, admissions-reader review, and integrity checks."

Boundary:

- "Essay Coach should not invent student experiences, awards, quotes, dialogue, emotions, or school facts."
- "If it lacks context, it should ask for specific facts or direct the student to [Build Profile](/build-profile)."

## 7. School Forms System

### 7.1 Colleges Page

The `/colleges` page supports:

- Searching the school catalog
- Adding schools to the student's list
- Choosing Reach / Target / Safety when adding
- Sorting by category, deadline, or name
- Viewing application progress
- Opening a school's application form with "Open application"
- Changing category
- Removing schools

Accurate marketing language:

- "The school list is not just a saved list. It connects to form progress, writing tasks, admissions forecast, and submit tracking."

### 7.2 School Application Form Page

The dynamic route `/college/:code` exists, but the navigation prompt says not to invent dynamic links. In promotional copy, direct the user to [Colleges](/colleges), then tell them to click "Open application."

The school form page can:

- Display a "Pages" sidebar.
- Load school-specific form pages and questions.
- Handle question types, options, choice values, requirement rules, and dynamic choice groups.
- Save answers.
- Auto-save individual answers.
- Generate long-answer drafts through the school form generation endpoint.
- Let the student add a question into the Application Form Helper context.
- Export a form payload for plugin or JSON use.

Accurate marketing language:

- "Students can open a school-specific application form and see concrete questions, not just a school name."
- "For long-answer questions, the product can help draft from saved answers and available context."

Boundary:

- "School form functionality depends on database-backed form schema."
- "Official application submission still requires student review and use of the official application platform."
- "Long-answer generation should not invent facts that are not in the student's saved answers or available context."

### 7.3 Application Form Helper

The form helper prompt is in:

`apps/core-api/fast_api_server/prompts/college/college_agentic_chat_prompt.md`

Its scope is intentionally narrow:

- Answer application form questions.
- Use attached form question context as canonical.
- Avoid broad admissions consulting in that mode.
- Use university FAQ search for policy/compliance questions.
- Use uploaded document search for student-specific evidence.
- Do not invent policies, requirements, or deadlines.

Accurate marketing language:

- "The form helper stays focused on the form question in front of the student."
- "It can answer choice questions or short free-text questions using the form context."

## 8. Build Profile and Student Knowledge Base

### 8.1 Build Profile Page

The `/build-profile` page includes:

- Personal Information
- Family
- Education
- Testing
- Academic Interests
- Activities
- Honors & Awards
- Writing
- Supplementary Files
- Auto-save
- Profile reset
- Document-based autofill suggestions

Students can upload supporting materials. Those files can support:

- Knowledge base retrieval
- Chatbot grounding
- Build Profile autofill
- Essay Coach grounding
- Admissions strategy context

Accurate marketing language:

- "Upload transcripts, resumes, activity lists, test reports, recommendation-related materials, or essay drafts so the system can ground suggestions in evidence."
- "Autofill suggestions are reviewable. The student can accept, edit, or reject them."

Boundary:

- "The system should use only information supported by documents or entered profile data."
- "It should not infer sensitive demographics, citizenship, address, or other personal details from a name or school."
- "Students remain responsible for checking official application forms before submission."

## 9. Admission Forecast and Submit

### 9.1 Admission Forecast

The `/admission-forecast` page can show:

- Portfolio-level probability
- Per-school probabilities
- Confidence
- Change over time
- Opportunity and risk signals
- Stale warnings when profile or school list changes
- Per-school analysis and recommendations

Accurate marketing language:

- "Refresh the forecast after profile or school-list changes."
- "Use it as a planning and interpretation tool."

Avoid:

- "This is the final admissions outcome."
- "The probability guarantees admission or rejection."

### 9.2 Submit

The `/submit` page can show:

- Target-school submission status
- Deadline and cycle information
- Portal shortcuts
- List view and board view
- Ability to mark an application as submitted

Accurate marketing language:

- "The final stage is not just finishing essays. It is checking whether every school has actually been submitted."

## 10. Product Guide and Public Pages

### 10.1 Product Guide

The `/product-guide` page is a visual onboarding and help-article surface. Use it when the reader is new or does not know where to start.

Example:

- "Start with [Product Guide](/product-guide) if you want the map before entering the workspace."

### 10.2 Public Landing Site

The public landing copy emphasizes:

- "College apps, finally easy."
- School matching
- AI counselor team
- Essay drafting and scoring
- Forecasting
- Autofill
- Invitation / rewards mechanics

Important: public landing copy contains stronger marketing claims such as outcomes, accuracy, advisor backgrounds, student testers, free trials, and reward tiers. The advertorial agent must not expand these into factual promises unless the business has approved them for the target campaign.

Claims that require business approval before use:

- Specific prediction accuracy rates
- "100K+ past outcomes" style claims
- Student tester counts or school names
- Advisor identities or "former admissions reader" claims
- Free trial, pricing, discounts, and reward tiers
- Competitor comparisons, including claims about ChatGPT or Claude
- Any school logo or university name used in a way that implies endorsement

## 11. Recommended Messaging Pillars

### 11.1 School-Based Writing

Core message:

- Students do not just write "a college essay."
- Each target school may have its own supplements, short answers, word limits, and requirements.
- EZCollegeApp organizes writing by school.
- Review changes with the prompt and word limit, instead of applying one Common App standard to every answer.

Possible headlines:

- "Your essay tool should know which schools you are applying to."
- "The hard part is not one essay. It is every school's supplement."
- "From school list to essay checklist."

### 11.2 Navigation-Aware AI Counselor

Core message:

- The chatbot can recommend the exact page and action.
- It can use product state such as profile completeness, tracked schools, application status, and uploaded file count.
- Content should end with a concrete product step.

Possible headlines:

- "An AI counselor that can show you the next page, not just the next sentence."
- "Advice is better when it knows where you are in the application."

### 11.3 Evidence-Grounded AI

Core message:

- The best AI application workflow starts by understanding the student.
- Build Profile and uploaded files provide grounding for writing, form help, and strategy.
- The system should not fabricate experiences.

Possible headlines:

- "Before the AI writes, it needs to know what is true."
- "From transcript and resume to application-ready context."

### 11.4 Whole-Application Workspace

Core message:

- Documents, school list, forms, essays, forecast, and submission status are connected.
- The product reduces switching between docs, spreadsheets, trackers, and chat threads.

Possible headlines:

- "Bring the application season back into one workspace."
- "School list, forms, essays, and submission status should not live in separate tabs."

## 12. Content Agent Decision Tree

1. If the pain is "I do not know where to start":
   - Lead with Product Guide, AI Counselor, and Build Profile.
   - CTA: [Product Guide](/product-guide) or [AI Counselor](/consultant).

2. If the pain is "AI does not know me":
   - Lead with uploaded files, Build Profile, student snapshot, and knowledge base.
   - CTA: [Build Profile](/build-profile).

3. If the pain is "My school list is messy":
   - Lead with Colleges, Reach / Target / Safety, and forecast refresh.
   - CTA: [Colleges](/colleges), then [Admission Forecast](/admission-forecast).

4. If the pain is "I do not know what each school wants me to write":
   - Lead with school-based My Writing and school form requirements.
   - CTA: Add schools in [Colleges](/colleges), then open [My Writing](/my-writing).

5. If the pain is "I do not know whether this supplement is good":
   - Lead with prompt-aware, word-limit-aware review.
   - CTA: [My Writing](/my-writing).

6. If the pain is "Forms are overwhelming":
   - Lead with school form pages, auto-save, long-answer drafting, and Form Helper.
   - CTA: [Colleges](/colleges), then click "Open application."

7. If the pain is "Deadlines are close":
   - Lead with Application Coordinator, Submit, deadlines, and status tracking.
   - CTA: [Submit](/submit).

## 13. Suggested Internal Output Contract for the Advertorial Agent

Before writing final copy, the agent should internally decide:

```yaml
target_persona: student | parent | counselor
pain_point: ""
product_anchor:
  - page: ""
    route: ""
    feature: ""
proof_from_product: ""
cta_route: ""
claims_to_avoid:
  - ""
disclosure_needed: true | false
final_copy: ""
```

The final public copy does not need to show this YAML. It is a planning structure for the generation agent.

## 14. Reusable Content Templates

### 14.1 Student-Facing Short Post

Structure:

1. Name the pain: applying is not just writing one essay.
2. Introduce the product: add schools first, then see school-based essay tasks.
3. Make it concrete: prompt, word limit, requirement status, draft status.
4. CTA: Colleges or My Writing.

Example:

> A lot of essay tools ask, "What do you want to write?" The harder question is: what does each school on your list actually require? In EZCollegeApp, the writing workspace is organized by school. You can see the Common App essay, each school's supplements, word limits, requirement status, and draft progress in one place. Start by adding schools in [Colleges](/colleges), then write in [My Writing](/my-writing).

### 14.2 Parent-Facing Short Post

Structure:

1. Name the pain: progress is hard to see.
2. Introduce the product: school list, forms, writing, and submit status are connected.
3. Clarify the boundary: it does not apply for the student.
4. CTA: Colleges or Submit.

Example:

> The stressful part of application season is not just one essay. It is everything being scattered. EZCollegeApp connects the school list, school-specific form questions, writing progress, and submission status in one workspace. The student still reviews and submits official applications, but the next step is much easier to see. Start with [Colleges](/colleges).

### 14.3 Counselor-Facing Short Post

Structure:

1. Name the pain: student materials and drafts are scattered.
2. Introduce the product: Build Profile, uploaded files, target schools, and writing diagnostics.
3. Clarify the role: AI supports organization and first-pass review, not final human judgment.
4. CTA: Build Profile or AI Counselor.

Example:

> A lot of advising time goes into asking students for the same profile details, activity context, and school requirements again and again. EZCollegeApp organizes uploaded files, Build Profile data, target schools, and writing tasks before the AI counselor answers. It is useful for organization, retrieval, and first-pass diagnostics while keeping final judgment with the student and counselor. Start with [Build Profile](/build-profile).

### 14.4 School Form Long-Answer Scenario

Structure:

1. Name the pain: a short school answer is not a Common App essay.
2. Introduce the product: long-answer form questions can become school-linked writing tasks.
3. Emphasize prompt- and word-limit-aware review.
4. CTA: Colleges -> Open application -> My Writing.

Example:

> "Why this major at Georgia Tech?" should not be reviewed like a 650-word personal statement. When school form data is available, EZCollegeApp can identify long-answer school questions, connect them to the school, and review the response against the prompt and word limit. Start in [Colleges](/colleges), click "Open application," then continue drafting in [My Writing](/my-writing).

## 15. Prohibited or Approval-Required Claims

### 15.1 Prohibited

- Guaranteed admission, scholarships, or score improvements.
- Claiming EZCollegeApp is an official Common App or university partner unless the business has approved and documented that relationship.
- Fabricated student testimonials, admission outcomes, counselor identities, or school endorsements.
- Claims that the system bypasses official application platforms.
- Claims that students do not need to verify official deadlines, fees, or requirements.
- Claims that AI can fabricate experiences or write untruthful application material.
- Absolute claims such as "all schools are covered" or "always latest."

### 15.2 Requires Business Approval

- Specific prediction accuracy numbers.
- "100K+ outcomes" or any dataset-size claim.
- Student tester counts and school names.
- "Former admissions reader" or advisor-background claims.
- Pricing, trial, discount, and referral/reward details.
- Direct competitor comparisons.
- University logos, marks, or names used as endorsement signals.

### 15.3 Safer Wording

- "When school form data is available..."
- "Helps organize and review..."
- "A planning reference, not an admissions guarantee..."
- "Students should verify official requirements..."
- "Grounded in uploaded and entered materials..."
- "Reduces blank-page work and tool switching..."

## 16. Source Discipline and Fact Hierarchy

When the advertorial agent generates claims, it should trust information in this order:

1. Current product code and routes.
2. Backend prompts, services, and API contracts.
3. Database-backed school form, FAQ, student profile, and essay document data.
4. Approved public landing-page copy.
5. General admissions knowledge only for stable concepts, not deadlines, fees, or school requirements.

For school requirements, deadlines, fees, and admissions policies:

- Do not invent missing facts.
- If verified data is absent, direct the user to the school's official website or admissions office.

## 17. Content Quality Checklist

Before publishing generated native content, check:

- Is the target persona clear?
- Does the content describe a real product capability?
- Does it include one concrete product next step?
- Does it avoid official endorsement, admission guarantees, and fake testimonials?
- Does it separate AI guidance from official application submission?
- Does it explain writing as school-based, not just a generic essay editor?
- Does it state that school essay lists depend on target schools and database-backed form data?
- Does it avoid dynamic `/college/:code` links unless a real code is known?
- Does it disclose advertising or partnership status when required by the channel?

## 18. Accuracy Notes From Code Review

This KB was checked against these product sources:

- Product navigation prompt: `apps/core-api/fast_api_server/prompts/counselor/product_navigation.md`
- Product navigation builder: `apps/core-api/fast_api_server/services/product_navigation.py`
- Agentic chat prompt: `apps/core-api/fast_api_server/prompts/agentic_chat_prompt.md`
- Counselor specialist prompts: `apps/core-api/fast_api_server/prompts/counselor/*.md`
- Frontend routes: `apps/portal-web/src/App.tsx`
- Route suggestion helper: `apps/portal-web/src/utils/productNavigation.ts`
- Chat Markdown link rendering: `apps/portal-web/src/components/chat/ChatMessages.tsx`
- AI Counselor workspace: `apps/portal-web/src/pages/Workspace.tsx`
- Build Profile page: `apps/portal-web/src/pages/BuildProfile.tsx`
- Colleges page: `apps/portal-web/src/pages/Colleges.tsx`
- School form page: `apps/portal-web/src/pages/College.tsx`
- School form API client: `apps/portal-web/src/services/agent/schoolForms.ts`
- My Writing workbench: `apps/portal-web/src/pages/MyWriting.tsx`
- Essay Coach panel: `apps/portal-web/src/components/mywriting/AIDraftPanel.tsx`
- Essay requirements / evaluation / final-read backend: `apps/core-api/fast_api_server/routers/essay_workflow.py`
- Essay evaluation prompt: `apps/core-api/fast_api_server/prompts/essay_eval/essay_evaluation.md`
- School form helper prompt: `apps/core-api/fast_api_server/prompts/college/college_agentic_chat_prompt.md`
- School long-answer draft prompt: `apps/core-api/fast_api_server/prompts/college/school_form_draft_generation.md`
- Admission Forecast page: `apps/portal-web/src/pages/Strategy.tsx`
- Submit page: `apps/portal-web/src/pages/Submit.tsx`
- Product Guide pages: `apps/portal-web/src/pages/productGuide/*`
- Landing copy: `apps/landing-web/src/i18n/locales/en.json`

Specific accuracy notes:

- The official product navigation prompt currently lists Build Profile, AI Counselor, Colleges, Admission Forecast, My Writing, Submit, and Product Guide.
- The app route table also includes Final Read, but Final Read is not listed in the current product navigation prompt.
- The navigation prompt explicitly says not to invent dynamic `/college/<code>` links.
- School-based writing tasks are generated from target schools and school form data through `/api/agent/essay/requirements`.
- The essay evaluator has explicit instructions to adapt for short supplemental answers.
- School form drafting uses saved answers and current question context; it should not invent unsupported facts.

## 19. Final Rules for the Advertorial Agent

1. Identify the user's pain before choosing the product angle.
2. For writing content, start from schools and prompts, not a generic essay editor.
3. When mentioning school prompt coverage, state the data dependency: stored school form / schema data is required.
4. When mentioning AI writing, state the integrity boundary: use the student's materials, do not invent experiences.
5. When mentioning forecasting, state the planning boundary: it is guidance, not a guarantee.
6. When mentioning forms or submission, state the official-platform boundary: students still review and complete official submissions.
7. Use internal Markdown links such as `[My Writing](/my-writing)` when appropriate.
8. Do not generate dynamic school form routes unless a real code is known.
9. Do not expand unapproved landing-page claims into campaign facts.
10. Make every advertorial concrete, useful, and tied to a real next step.
