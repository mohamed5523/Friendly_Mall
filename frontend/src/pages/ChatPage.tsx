import { useState, useRef, useEffect, KeyboardEvent } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

interface Props {
  role: 'customer' | 'manager'
  onBack: () => void
}

const CUSTOMER_SUGGESTIONS = [
  'عندكم ثلاجات؟', 'بكام الكنبة؟', 'في مراوح متاحة؟',
  'عايز أشتري تلفزيون', 'اعرضلي منتجات المطبخ', 'احجزلي مكيف',
]

const MANAGER_SUGGESTIONS = [
  'تقرير المبيعات', 'الأرباح الشهر ده', 'أكثر منتج بيتباع',
  'منتجات قريبة من النفاد', 'توقع مبيعات الثلاجة', 'رؤى شاملة عن المول',
]

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8008'
const SESSION_KEY = 'mall_session_id'

function getOrCreateSession(): string {
  let id = sessionStorage.getItem(SESSION_KEY)
  if (!id) {
    id = crypto.randomUUID()
    sessionStorage.setItem(SESSION_KEY, id)
  }
  return id
}

export default function ChatPage({ role, onBack }: Props) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const sessionId = getOrCreateSession()

  const suggestions = role === 'customer' ? CUSTOMER_SUGGESTIONS : MANAGER_SUGGESTIONS
  const roleLabel = role === 'customer' ? 'عميل' : 'مدير'
  const roleIcon = role === 'customer' ? '🛍️' : '📊'

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  async function sendMessage(text: string) {
    if (!text.trim() || loading) return
    const userMsg: Message = { role: 'user', content: text.trim() }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await fetch(`${API_URL}/api/chat/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'x-session-id': sessionId,
        },
        body: JSON.stringify({ query: text.trim(), role }),
      })
      const data = await res.json()
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: data.answer || 'عذراً، مش قادر أرد دلوقتي.',
      }])
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: '⚠️ حصلت مشكلة في الاتصال. تأكد إن السيرفر شغال.',
      }])
    } finally {
      setLoading(false)
    }
  }

  function handleKey(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage(input)
    }
  }

  return (
    <div className="chat-layout">
      {/* Header */}
      <div className="chat-header">
        <div className="chat-header__info">
          <span className="chat-header__icon">{roleIcon}</span>
          <div>
            <div className="chat-header__title">مول البيت 🏪</div>
            <div className="chat-header__role">دور: {roleLabel}</div>
          </div>
        </div>
        <button className="btn-back" onClick={onBack}>← تغيير الدور</button>
      </div>

      {/* Messages */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-card">
            <div className="welcome-card__icon">{roleIcon}</div>
            <div className="welcome-card__title">
              {role === 'customer' ? 'أهلاً بك في مول البيت!' : 'لوحة تحكم المدير'}
            </div>
            <div className="welcome-card__text">
              {role === 'customer'
                ? 'ممكن تسأل عن أي منتج، تعرف سعره، توافره، وتحجز أو تشتري على طول!'
                : 'ممكن تسأل عن المبيعات، الأرباح، التنبؤات، وتحليل أداء المنتجات.'}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`message message--${m.role}`}>
            <div className="message__avatar">
              {m.role === 'user' ? '👤' : '🤖'}
            </div>
            <div className="message__bubble">{m.content}</div>
          </div>
        ))}

        {loading && (
          <div className="message message--assistant">
            <div className="message__avatar">🤖</div>
            <div className="message__bubble">
              <div className="typing-indicator">
                <div className="typing-dot" />
                <div className="typing-dot" />
                <div className="typing-dot" />
              </div>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="chat-input-area">
        {messages.length === 0 && (
          <div className="suggestions">
            {suggestions.map(s => (
              <button key={s} className="suggestion-btn" onClick={() => sendMessage(s)}>
                {s}
              </button>
            ))}
          </div>
        )}
        <form className="chat-input-form" onSubmit={e => { e.preventDefault(); sendMessage(input) }}>
          <textarea
            className="chat-input"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={handleKey}
            placeholder={role === 'customer' ? 'اكتب سؤالك عن المنتجات...' : 'اكتب استفسارك...'}
            rows={1}
          />
          <button className="btn-send" type="submit" disabled={loading || !input.trim()}>
            {loading ? '...' : 'إرسال ←'}
          </button>
        </form>
      </div>
    </div>
  )
}
