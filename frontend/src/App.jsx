import { useEffect, useMemo, useState } from 'react'

const TOPICS = [
  'Philosophy',
  'History',
  'Mathematics',
  'Science',
  'Surprise me'
]

const EXTRA_TOPICS = [
  'Literature',
  'Psychology',
  'Economics',
  'Political Science',
  'Anthropology',
  'Physics',
  'Astronomy',
  'Biology',
  'Computer Science',
  'AI',
  'Logic Puzzles',
  'Trivia',
  'Ethical Dilemmas',
  'Stoicism',
  'Game Theory'
]

const INITIAL_BOT = {
  id: 'intro',
  role: 'bot',
  text: 'What do you want to chat about today?',
  bubbles: TOPICS
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080'

function bubbleClass(active = false) {
  return `glass px-4 py-2 rounded-full text-sm font-medium transition ${
    active ? 'bg-white/20' : 'hover:bg-white/15'
  }`
}

function ChatBubble({ role, text }) {
  const isBot = role === 'bot'
  return (
    <div className={`flex ${isBot ? 'justify-start' : 'justify-end'} w-full`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm leading-relaxed shadow-glass ${
          isBot ? 'glass text-mist' : 'bg-coral/90 text-ink-900'
        }`}
      >
        {text}
      </div>
    </div>
  )
}

export default function App() {
  const [messages, setMessages] = useState([INITIAL_BOT])
  const [userId, setUserId] = useState(() => localStorage.getItem('engagingchat_user'))
  const [conversationId, setConversationId] = useState(null)
  const [points, setPoints] = useState(0)
  const [streak, setStreak] = useState(0)
  const [topics, setTopics] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!userId) return
    localStorage.setItem('engagingchat_user', userId)
  }, [userId])

  const currentBubbles = useMemo(() => {
    const last = messages[messages.length - 1]
    return last?.bubbles || []
  }, [messages])

  async function sendMessage(text, topic) {
    const payload = {
      user_id: userId,
      topic: topic || null,
      user_message: text || null,
      conversation_id: conversationId || null
    }

    setLoading(true)
    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      })

      if (!response.ok) {
        throw new Error('Failed to reach assistant')
      }

      const data = await response.json()
      if (!userId && data?.user_id) {
        setUserId(data.user_id)
      }

      setConversationId(data.conversation_id)
      setPoints(data.total_points || 0)
      setStreak(data.current_streak || 0)
      setTopics(data.topics_of_interest || [])

      setMessages((prev) => [
        ...prev,
        text ? { id: crypto.randomUUID(), role: 'user', text } : null,
        {
          id: crypto.randomUUID(),
          role: 'bot',
          text: data.bot_message,
          bubbles: data.response_bubbles || []
        }
      ].filter(Boolean))
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { id: crypto.randomUUID(), role: 'bot', text: 'Something went wrong. Try again?', bubbles: TOPICS }
      ])
    } finally {
      setLoading(false)
    }
  }

  function handleBubbleClick(label) {
    const isTopic = TOPICS.includes(label) || EXTRA_TOPICS.includes(label)
    const topic = isTopic ? label : null
    sendMessage(label, topic)
  }

  return (
    <div className="min-h-screen px-4 py-8">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-6">
        <header className="flex flex-col gap-4 rounded-3xl bg-ink-800/70 p-6 shadow-glass">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h1 className="font-display text-3xl text-white">Curiosity Chat</h1>
              <p className="text-sm text-mist/80">Socratic, fact-based learning with streaks and points.</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="glass rounded-2xl px-4 py-2 text-sm">
                <span className="text-mint">??</span> Streak: {streak} days
              </div>
              <div className="glass rounded-2xl px-4 py-2 text-sm">
                <span className="text-glow">?</span> Points: {points}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2 text-xs text-mist/80">
            <span className="font-semibold uppercase tracking-widest">Topics explored</span>
            {topics.length === 0 && <span>None yet</span>}
            {topics.map((item) => (
              <span key={item} className="glass rounded-full px-3 py-1">{item}</span>
            ))}
          </div>
        </header>

        <main className="grid gap-6 lg:grid-cols-[2fr_1fr]">
          <section className="flex flex-col gap-4 rounded-3xl bg-ink-800/70 p-6 shadow-glass">
            <div className="chat-scroll flex h-[420px] flex-col gap-4 overflow-y-auto pr-2">
              {messages.map((message) => (
                <ChatBubble key={message.id} role={message.role} text={message.text} />
              ))}
              {loading && (
                <div className="text-sm text-mist/70">Thinking...</div>
              )}
            </div>
            <div className="flex flex-wrap gap-2">
              {currentBubbles.map((bubble) => (
                <button
                  key={bubble}
                  className={bubbleClass()}
                  onClick={() => handleBubbleClick(bubble)}
                  disabled={loading}
                >
                  {bubble}
                </button>
              ))}
            </div>
          </section>

          <aside className="flex flex-col gap-4 rounded-3xl bg-ink-800/70 p-6 shadow-glass">
            <div>
              <h2 className="font-display text-xl text-white">Try a new lane</h2>
              <p className="text-sm text-mist/80">Tap a topic to switch the conversation.</p>
            </div>
            <div className="flex flex-wrap gap-2">
              {EXTRA_TOPICS.map((topic) => (
                <button
                  key={topic}
                  className={bubbleClass()}
                  onClick={() => handleBubbleClick(topic)}
                  disabled={loading}
                >
                  {topic}
                </button>
              ))}
            </div>
            <div className="mt-auto rounded-2xl bg-ink-700/80 p-4 text-sm text-mist/80">
              <p className="font-semibold text-mist">How it works</p>
              <p>Every reply includes suggested answers. Pick one, or ask for a different subject.</p>
              <p className="mt-2">Correct answers boost points. Daily check-ins keep your streak alive.</p>
            </div>
          </aside>
        </main>
      </div>
    </div>
  )
}

