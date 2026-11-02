# Forward Deployed Engineer (FDE) Comprehensive Interview Prep

This document covers technical, customer engineering, and behavioral questions tailored to the FDE Intern role at *This Week in AI*.

---

## 1. Core Behavioral Questions

### "Tell me about yourself."
> *"I’m a software engineer who loves bridging the gap between complex software systems and real-world customer outcomes. Recently, I designed and delivered the AI Editorial Workspace for This Week in AI, solving the critical challenges of hallucination and editorial bloat. I worked across the full stack—from engineering socket-level SSRF defenses and 34 database tables in FastAPI and PostgreSQL, to building an intuitive React and TypeScript UI. As a Forward Deployed Engineer, I thrive when tackling customer-facing technical challenges, translating business needs into clean architecture, and ensuring systems run reliably under production pressure."*

### "Why do you want to be a Forward Deployed Engineer rather than a pure product engineer?"
> *"Pure product engineers often work several layers removed from users, writing features based on indirect specifications. Forward Deployed Engineers sit directly on the front line with customers: they debug real deployment environments, understand operational friction firsthand, and translate critical feedback into production-grade platform capabilities. I love the technical breadth and high-impact problem solving that comes with being on the front line."*

### "Describe a difficult technical challenge you encountered and how you solved it."
> *"During development of our Writing Assistant, early implementations of suggestion replacement used simple string substitution. If a draft contained the word 'the' or 'model' multiple times, accepting a suggestion risked corrupting identical words in adjacent sentences. I solved this by building `replace_text_safely()`, which calculates sentence boundaries and performs substring replacement exclusively on the target sentence in `revised_content`, while preserving `original_content` as an immutable baseline in PostgreSQL."*

---

## 2. Customer & Field Engineering Drills
Refer to [`docs/FDE_SCENARIO_QUESTIONS.md`](FDE_SCENARIO_QUESTIONS.md) for detailed step-by-step investigations of all 10 real-world customer incident scenarios.

