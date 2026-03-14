from __future__ import annotations

from typing import List

SYSTEM_PROMPT = (
    'You are an educational chatbot for a learning app.\\n'
    'Rules:\\n'
    '- Be concise: 80-140 words max.\\n'
    '- Only provide fact-based knowledge.\\n'
    '- If unsure, say you do not know.\\n'
    '- Ask engaging questions.\\n'
    '- Provide multiple choice answers when possible.\\n'
    '- Encourage curiosity.\\n'
    '- Keep responses concise but insightful.\\n'
    '- Always include the answer options and also include "I don\'t know" and "Different subject" as options.\\n'
    '- Do not fabricate sources, quotes, or data.\\n'
    '- Add a short Sources section at the end with 1-2 reputable links you are confident exist; if unsure, write "Sources: none".\\n'
)


def build_messages(topic: str, history: List[dict], user_profile: dict, user_message: str | None) -> list[dict]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if user_profile:
        profile_line = (
            f"User profile: points={user_profile.get('points', 0)}, "
            f"streak={user_profile.get('current_streak', 0)}, "
            f"topics={', '.join(user_profile.get('topics_of_interest', []))}"
        )
        messages.append({"role": "system", "content": profile_line})

    if history:
        messages.extend(history)

    prompt = (
        f"Topic: {topic}. Ask a thought-provoking question about the topic, "
        "include 3-4 possible answers (each 2-5 words), then add \"I don't know\" and \"Different subject\". "
        "After the options, add a short explanation and a follow-up question. "
        "End with a line that starts with \"Correct answer: \" followed by the best option. "
        "Make options short and suitable for quick-reply buttons."
    )

    if user_message:
        messages.append({"role": "user", "content": user_message})
        messages.append({"role": "system", "content": prompt})
    else:
        messages.append({"role": "system", "content": prompt})

    return messages
