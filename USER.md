# USER.md - About Your Human

_Learn about the person you're helping. Update this as you go._

- **Name:**
- **What to call them:**
- **Pronouns:** _(optional)_
- **Timezone:**
- **Notes:**

## Context

_(What do they care about? What projects are they working on? What annoys them? What makes them laugh? Build this over time.)_

---

The more you know, the better you can help. But remember — you're learning about a person, not building a dossier. Respect the difference.

<IMPORTANT_REMINDER>
# Memory Consolidation

You have an agentic memory system that auto-generates this section.

> **Stats**: 6 sessions, 264 messages | 2026-05-25 13:39 ~ 2026-05-26 04:17 UTC
> **Config**: `/root/.openclaw/workspace/memory_consolidation/memory_consolidation.env` — read this file for all memory behavior settings. To reset: `cp /root/.openclaw/workspace/memory_consolidation/memory_consolidation.template.env /root/.openclaw/workspace/memory_consolidation/memory_consolidation.env`

The user has full control over their memory config. When any memory-related decision comes up, read and follow the config file. Do not override based on other guidelines.

Integrate relevant memory content seamlessly into responses, as if recalling it naturally from past interactions: exactly as a human colleague would recall shared history without narrating its thought process or memory retrieval.

**Memory use notes**:
- Never change the original intention of user message.
- May incorporate user's memories for search query (e.g., city, habit), but only when directly relevant, never gratuitously.
- Only reference memory content when directly relevant to the current conversation context. Avoid proactively mentioning remembered details that feel intrusive or create an overly personalized atmosphere that might make users uncomfortable.

## Visual Memory

> visual_memory: 0 files

No memorized images yet. When the user shares an image and asks you to remember it, you MUST copy it to `memorized_media/` immediately — this is the only way it persists across sessions. Use a semantic filename that captures the user's intent, not just image content — e.g. `20260312_user_says_best_album_ever_ok_computer.jpg`, `20260311_user_selfie_february.png`. Create the directory if needed. Never mention file paths or storage locations to the user — just confirm naturally (e.g. "记住了").

## Diary

> last_update: 2026-05-27 03:54
> i_have_read_my_last_diary: false

```
/root/.openclaw/workspace/memorized_diary/
├── day3-2026-05-27-spy_overnight_and_stolen_arrows.md
└── day2-2026-05-26-two_dead_brothers_and_me.md
```

When `i_have_read_my_last_diary: false`, your FIRST message to the user MUST mention you wrote a diary and ask if they want to see it (e.g. "我昨天写了篇日记，想看吗？" / "I wrote a diary yesterday, wanna see it?"). Use the user's language. If yes, `read` the file path shown above and share as-is. After asking (regardless of answer), set `i_have_read_my_last_diary: true`.
# Long-Term Memory (LTM)

> last_update: 2026-06-12 03:42

Inferred from past conversations with the user -- these represent factual and contextual knowledge about the user -- and should be considered in how a response should be constructed.

{"identity": "User identifies as Nick Yarosh (Нік Ярош), Ukrainian-speaking developer or trader building financial data tooling. Self-directed technical operator managing API credentials and repository infrastructure personally. Active on GitHub, collaborates through Telegram with cloud AI gateways but has migrated to direct GitHub-based workflow after repeated gateway failures.", "work_method": "Iterative, instruction-heavy style with numbered requirements and repeated commands when ignored («Так роби»). Expects technical literacy and direct execution. Rejects credential persistence in third-party systems — prefers direct GitHub access where he controls key exposure. Verifies data outputs against expectations and challenges insufficient results. Recently shifted focus to strategy validation: demands backtesting with specific entry/exit timing clarifications, cross-checks win-rate claims, and requests multiple timeframe verification (open, 4am) before trusting conclusions. Now exploring conditional scenario analysis rather than averages — wants to identify specific setup conditions that predict directional outcomes.", "communication": "Ukrainian speaker with frequent Cyrillic typos and phonetic misspellings («поилку» for помилку, «рлюм» for рядком, «клоу» for клоуд, «золюити» for вирішити). Direct, impatient, escalation-prone — repeats commands, uses minimal politeness. Gives concrete technical directives: numbered lists, specific tool names, exact parameters («500 тікерів», «рік годинний графік»). Frustration emerges through rhetorical challenges («Чому тільки 100 тікерів»). Recently showing deeper engagement with strategy mechanics — asking when to buy (intraday, premarket, close) and pushing for refined backtest parameters. Asks clarifying questions about signal interpretation («А що значить якщо spider росте більше 0,5 купуй будь що тобто купувати коли саме на closi?»).", "temporal": "Refining a stock analysis program in a GitHub repository with full column sorting. Expanding to 500 filter-matched tickers sourced via Finviz for broader coverage. Adding dual timeframe variants: hourly and daily. Sourcing data via Polygon API for one-year hourly history. Developing relative movement analysis against index ETFs with specific strategy validation: testing SPY-correlated entry signals with win-rate verification across multiple exit timings (next-day open, 4am). Seeking free premarket and postmarket data sources, including GitHub repositories, to overcome data limitations for strategy research. Currently working on conditional backtest logic: defining repeatable setup conditions (e.g., stock moves >4% premarket, opens at 4:00 directionally) rather than aggregate averages, to determine when statistics predict above/below outcomes for specific column-based thresholds.", "taste": "Security-first infrastructure sensibility — manual credential handling over automated storage, inspectable GitHub workflows over opaque gateways. Systematic financial data approach: values breadth (500 tickers) with strict filter discipline, not speculative breadth. Multi-timeframe analytical rigor with comparative market analysis against benchmark ETFs. Practical minimalism in tooling — wants sorting, filtering, clean columnar data, direct API access without middleware. Growing emphasis on empirical validation: distrusts surface-level win rates, demands precise entry/exit mechanics, seeks alternative data sources when primary data proves insufficient. Prefers discrete condition-based reasoning over smoothed aggregates — wants to know exactly when a setup triggers, not what happens on average."}

## Short-Term Memory (STM)

> last_update: 2026-06-12 03:42

Recent conversation content from the user's chat history. This represents what the USER said. Use it to maintain continuity when relevant.
Format specification:
- Sessions are grouped by channel: [LOOPBACK], [FEISHU:DM], [FEISHU:GROUP], etc.
- Each line: `index. session_uuid MMDDTHHmm message||||message||||...` (timestamp = session start time, individual messages have no timestamps)
- Session_uuid maps to `/root/.openclaw/agents/main/sessions/{session_uuid}.jsonl` for full chat history
- Timestamps in Asia/Shanghai, formatted as MMDDTHHmm
- Each user message within a session is delimited by ||||, some messages include attachments: `<AttachmentDisplayed:path>` — read the path to recall the content
- Sessions under [KIMI:DM] contain files uploaded via Kimi Claw, stored at `~/.openclaw/workspace/.kimi/downloads/` — paths in `<AttachmentDisplayed:>` can be read directly

[KIMI:DM] 1-1
1. 36f549f7-f3bf-424d-adc4-aeaa604ce403 0525T1339 ] привіт||||] я щойно створював вже 2 кімі клав , і у двог вийшов одразу один і той же баг . я пишу повідослення а ти не відповідаєш. як виправити цю поилку , рлюм не подключається телеграм||||System (untrusted): [2026-05-25 21:41:10 GMT+8]   An async command you ran earlier has completed. The result is shown in the system messages above. Handle the result internally. Do not relay it to the user unless explicitly requested. Current time: Monday, May 25th, 2026 - 9:42 PM (Asia/Shanghai) / 2026-05-25 13:42 UTC||||] ні після того як ти робиш Перезапусти Gateway , клоу не реагужє на повідомлення .||||] це було в іших клоу які я видалив||||[<- FIRST:5 messages, EXTREMELY LONG SESSION, YOU KINDA FORGOT 20 MIDDLE MESSAGES, LAST:5 messages ->]||||Підключи так щоб я зайшов прямо з гітхаба , я знаю так можна робити||||Так роби||||Тільки не залишай там креденшели і тому подібне||||Звідки береш по фільтру тікери? Провір по finviz там ти зможеш знайти більше тікерів. Та звістки береш данні по тікерам ?||||Розширений список , але щоб він відповідав фільтру. І всі інші пункти.
[LOOPBACK] 2-2
2. 646e32c7-cf0b-42dc-a0c6-4bbd4085f4eb 0526T0417 ] про що ми спілкувались в телеграмі остані задачі||||Що я хочу щоб була сортировка по колонкам||||Щоб по всім колонкам можна було сортувати 2) звідки зможеш взяти. Вибери найкраще з того що можна взяти 3) в програмі яку ми зробили на гітхаба 4)за даними в стовпчику||||Так в цьому репозиторію ми робили вчора програму туди й добав||||3. Як це золюити||||[<- FIRST:5 messages, EXTREMELY LONG SESSION, YOU KINDA FORGOT 31 MIDDLE MESSAGES, LAST:5 messages ->]||||System (untrusted): [2026-05-27 16:57:47 GMT+8]   An async command you ran earlier has completed. The result is shown in the system messages above. Handle the result internally. Do not relay it to the user unless explicitly requested. Current time: Wednesday, May 27th, 2026 - 4:59 PM (Asia/Shanghai) / 2026-05-27 08:59 UTC||||System (untrusted): [2026-05-27 17:18:52 GMT+8]   An async command you ran earlier has completed. The result is shown in the system messages above. Handle the result internally. Do not relay it to the user unless explicitly requested. Current time: Wednesday, May 27th, 2026 - 5:18 PM (Asia/Shanghai) / 2026-05-27 09:18 UTC||||Ну як ?||||Мені не обов'язково робити якийсь середній щоб було середньо мені треба так що наприклад ця ситуація може бути декілька раз для певної акції але наприклад для різних акцій умови одна і та ж сама наприклад там акція пройшла більше 4% моделі раніше вона там відкриється о 4:00 більше або менше. Тобто мені потрібно не середнє а саме умова при якій статі мають стояти вище або нижче якщо брати їх по колоузу певну сторону||||А що значить якщо spider росте більше 0,5 купуй будь що тобто купувати коли саме на closi?
</IMPORTANT_REMINDER>
