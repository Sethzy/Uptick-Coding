https://docs.anthropic.com/en/docs/test-and-evaluate/define-success

https://docs.anthropic.com/en/docs/about-claude/use-case-guides/overview

Ticket routing, customer support agent, content moderation, legal summarisation

Jet New, [19 Jul 2025 at 7:07:42 PM]:
For Claude only because Anthropic chose it to finetune model on it

OAI’s models are markdown because OAI finetuned it by markdown

Gudiebook on prompting:

https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview

Jet's recommendation:

https://dspy.ai/tutorials/

https://fullstackdeeplearning.com/llm-bootcamp/spring-2023/prompt-engineering/

The prompt report:

https://arxiv.org/pdf/2406.06608

Product-Focused Prompting
For use inside applications rather than conversational use.
➤ Focus is on robustness and reliability across millions of user inputs.
Key aspects:

Not visible to end-users

Must be trusted to work at scale

Often paired with internal evaluation and A/B testing

🧪 Multi-Expert Prompting (Debate / Jury of AIs)
Use multiple prompts or agents (same model or different ones), each with a different role or perspective.
➤ Then compare or aggregate answers to reach a more reliable result.
Also known as: Multi-agent prompting, LLM-as-a-committee.

📚 Context Injection
Manually insert background knowledge or relevant definitions into the prompt (e.g., legal terms, product specs)
➤ Ensures the model understands specialized terminology or task requirements.

🗂️ Step-by-Step / Chain-of-Thought Prompting
Ask the model to break down the task into steps before solving.
Prompt: “What are all the steps that need to be done first?”
➤ Mimics human planning and improves logical reasoning.

🧩 Few-Shot Prompting
Provide examples of good output before giving the task.
➤ Helps the model align its response with a desirable format or content quality.
Often used with:

XML formatting

Schema structures

Structured examples (e.g., Q&A, before/after). Q&A is really important.

🔁 Self-Criticism / Self-Reflection
Ask the model to critique its own response
Prompt: “Can you review your response and improve it?”
➤ Useful for boosting quality and catching errors.
