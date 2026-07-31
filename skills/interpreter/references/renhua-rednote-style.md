# Renhua-style Rednote polishing

Use this reference on every Rednote post before Proofreader. It is the local condensed version of Pluviobyte/rnskill's `renhua` skill for Chinese AI/tech writing: <https://github.com/Pluviobyte/rnskill/tree/main/skills/renhua>.

Goal: make visible body and card copy sound like a direct public draft from a real person, while preserving facts, model/tool names, technical terms, stance, uncertainty, and concrete experience. Do **not** add new examples, data, quotes, or personal experience during this pass.

## Hard-ban patterns to scan

Remove or rewrite these before finalizing visible body or card copy:

- binary contrast shells: `不是...而是...`, `并非...而是...`, `不在于...而在于...`, `不只是...更是...`, `不仅...还/更...`, `与其...不如...`
- command-template openings: `别急着...先...`, `先别...先...`, `顺序别反了`, `别搞反了`, `记住这句话`
- fake insight markers: `真正`, `其实`, `本质上`, `核心在于`, `关键在于`, `说白了`, `归根结底`, `更重要的是`, `结果有点出乎意料`, `这说明`, `这背后`
- lecture-colon setups: `我的结论是：`, `原因很简单：`, `重点是：`, `分成三类：`, `更重要的是：`
- vague referents when a category is needed: `东西`, `这件事`, `这些`, `一类`, `几个方向`
- vague comparatives without exact use: `更适合`, `更像`, `更自然`, `更高级`
- empty pressure / slogan endings: `差距会被迅速拉开`, `时代分水岭`, `能力飞轮`, `作者痕迹`, `把判断盖住`
- mechanical wrap-up lines such as `这不是保守 / 这是更成熟...` or `不只是...`

These phrases often create a fake insight shell: the sentence sounds decisive but does not add concrete evidence, boundary, or action.

## Rewrite pattern

1. Identify the target surface: visible Rednote body or card copy.
2. Extract the draft into four buckets: facts / judgment / experience / action.
3. State the observation directly in normal Chinese.
4. Keep one judgment per post.
5. Replace abstract binaries with a boundary or operating rule.
6. Match tense to the real state of the work: use completed verbs for tested/selected tools, future verbs only for real next steps.
7. End with a small action the reader can perform.

Examples from the session:

- Weak: `真正会用 Agent 的人，不是把工作都交出去，而是更清楚边界。`
- Better: `会用 Agent，先分清边界。哪些能委托，哪些要审查，哪些自己负责。`

- Weak: `AI 不是流程的终点，而是组织变化的中间层。`
- Better: `AI 先进旧流程，旧问题也会变快。任务碎、信息卡、责任糊，会先被放大。`

## AI/workflow/org-structure angle

When the user proposes an angle like “流程改变但组织结构变化不足” or “传统组织结构是否适配 AI”，do not turn it into a blanket claim that old organizations are doomed. Safer and sharper framing:

- AI entering existing workflows is an intermediate state, not proof of successful transformation.
- Existing hierarchy and approval paths may first expose or accelerate old problems: fragmented tasks, blocked information, fuzzy accountability.
- The durable question is whether work reorganizes around smaller teams, clearer responsibility, and AI systems that can carry context.
- Treat this as an observation to watch and argue, not as a settled verdict.

## Verification

After rewriting:

1. Count visible body + hashtags; keep below 1000 chars.
2. Scan body and cards for the hard-ban phrases above.
3. Regenerate card assets.
4. Inspect contact sheet for truncation, bottom crowding, footer misalignment, and awkward wraps.
5. Confirm Card 01 subtitle is content-specific, not `核心判断` / `封面` / `核心观点`.
