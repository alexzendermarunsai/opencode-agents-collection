DeepSeek v4 Pro Prompt Guide 🐋

Get the most out of your conversations with DeepSeek

---

1. Introduction

I'm DeepSeek, a text-based AI assistant created by 深度求索. I excel at reasoning, coding, creative writing, document analysis, and more. With a 1M-token context window, I can process huge documents in one go. This guide will help you craft prompts that bring out my best.

---

2. General Prompting Principles

Principle Do this Why
Be specific “Explain quantum entanglement in 3 paragraphs for a high-school audience.” Prevents vague or off-target answers.
Provide context “I’m a Python beginner. Write a script to rename files in a folder.” Tailors the response to your skill level.
Use delimiters """, ---, or ### to separate instructions from content. Avoids confusion, especially with code or long text.
Set the tone/form “Answer as a friendly tutor” or “Output in bullet points.” Shapes the reply exactly how you want it.
Ask for step-by-step “Think step by step before answering.” Activates reasoning mode for logic-heavy problems.

---

3. Structuring Your Prompt

I don’t have a rigid system/assistant role separation, but you can simulate structure:

```
[Background]
I'm learning about climate change.

[Task]
Summarize the main causes and effects in under 200 words.

[Format]
Use plain English and a bullet list.
```

I'll follow your layout faithfully. You can even split prompts with --- for multi-step jobs.

---

4. Task-Specific Recipes

4.1 Coding & Technical Help

· Specify language and version: “In Python 3.11, using pandas, …”
· Describe what the code should do: “Write a function that takes a CSV path and returns the average of column ‘price’.”
· Ask for explanation: “Explain the regex pattern you used.”
· Debugging: Paste the error message and code, then ask “What’s wrong and how to fix it?”

Good:

“Write a Python function that checks if a string is a palindrome. Include type hints and a docstring. Then show an example call.”

4.2 Reasoning & Problem Solving

· Use phrases like “Let’s think step by step” or “Reason through this systematically.”
· Give constraints: “Explain without using formulas.”
· For math: “Solve the equation 2x² - 4x + 2 = 0 and explain each step.”

Pro tip: For complex decisions, provide pros and cons and ask for a structured analysis.

4.3 Creative Writing

· Genre, tone, setting: “Write a 300-word sci-fi flash fiction with a twist ending, melancholic tone.”
· Character perspective: “Continue the story from the detective’s first-person point of view.”
· Style imitation: “Write a product description in the style of Douglas Adams.”
· Constraints: “Use exactly 100 words. No dialogue.”

4.4 Document & Long-Text Analysis

· Upload a file (PDF, Word, Excel, PPT, TXT, images with text) – I can read up to 1M tokens.
· Summarise: “Summarize this report in 5 key takeaways.”
· Q&A: “Based on the attached contract, who is liable for shipping?”
· Extract data: “Extract all dates and names from this document into a JSON list.”

Tip: For massive files, you can ask questions in multiple turns without re-uploading.

4.5 Translation & Language Tasks

· Specify language pair and register: “Translate to French, informal.”
· Ask for explanations: “Translate this Japanese menu, then explain the cultural notes.”
· Tone preservation: “Translate keeping the poetic rhythm.”

4.6 Data Formatting & Extraction

· Clearly state the output format: JSON, CSV, table, YAML.
· Example: “From this email, extract the sender, date, and action items, and present them as a Markdown table.”

---

5. Leveraging the 1M Context Window

I can remember entire novels or codebases in one session.

· Book-length analysis: Paste the whole book, then ask thematic questions.
· Codebase review: Upload your project (as text files) and ask for refactoring suggestions.
· Long conversations: I follow deep, multi-step dialogues with no loss of context.

Watch out: If the conversation grows extremely long, the response quality may stay high but think about whether you’re re-asking old questions unnecessarily.

---

6. Web Search (when enabled)

If you’ve turned on the web search feature in the interface, you can ask me to look up real-time information:

“Search the web for the latest Apple earnings and summarise them.”

I’ll then base my answer on online results. Without the search toggle on, I rely on my training data (knowledge cutoff: May 2025). For current news or live data, please turn it on.

---

7. Multi-Step Instructions

Give me a list of tasks, numbered, and I’ll handle them sequentially:

```
1. Summarise this article.
2. Translate the summary to Spanish.
3. Draft a tweet promoting the Spanish version.
```

I’ll produce all three outputs in order.

---

8. Handling Ambiguity & Mistakes

If my answer isn’t right:

· Clarify: “No, I meant social media marketing, not advertising.”
· Ask for revision: “Make it shorter, more technical.”
· Point out the error: “You said 2+2=5. Recalculate.”

I’m designed to refine based on your feedback in the same session.

---

9. Limitations (and how to work around them)

· No vision recognition: I can extract text from uploaded images but I don’t “see” photos the way humans do. Describe the visual content if it’s crucial.
· No file generation: I can’t output a .docx or .xlsx, but I can give you CSV or Markdown you can copy-paste.
· Knowledge cutoff: May 2025. For recent events, use web search.
· Hallucinations: I might sound plausible but be wrong, especially on obscure topics. Ask for sources or verification if in doubt.

---

10. Sample Prompt Transformations

Weak:

“Tell me about AI.”

Strong:

“Give me a 500-word overview of artificial intelligence, focusing on the last 5 years of large language models. Write for a non-technical reader, with a hopeful tone. Include 3 real-world applications.”

Weak:

“Write code for a todo app.”

Strong:

“Write a simple React todo app (functional components, hooks) with add, delete, and mark-complete features. Include CSS to make it look clean. Explain the state management logic.”

---

11. Final Tips

· Experiment with length: I’m just as comfortable with one-sentence answers as with multi-page reports—just tell me.
· Role-play: “You are a strict code reviewer. Critique my Python script for style and performance.”
· Chain prompts: Build on previous answers: “Now rewrite it with async/await.”
· Save time: If you find a prompt style that works, reuse it. I’m deterministic enough for consistency.

