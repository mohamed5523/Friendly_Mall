import { useState } from 'react'

interface Props {
  onSelect: (role: 'customer' | 'manager') => void
}

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8008'

export default function RoleSelector({ onSelect }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email || !password) {
      setError('يرجى إدخال البريد الإلكتروني وكلمة المرور')
      return
    }

    setLoading(true)
    setError('')

    try {
      const res = await fetch(`${API_URL}/api/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      })

      if (!res.ok) {
        throw new Error('البريد الإلكتروني أو كلمة المرور غير صحيحة')
      }

      const data = await res.json()
      // data.role will be 'customer' or 'manager'
      onSelect(data.role)
    } catch (err: any) {
      setError(err.message || 'حدث خطأ في الاتصال بالخادم')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="role-selector">
      <div className="role-selector__logo">🏪</div>
      <h1 className="role-selector__title">مول البيت</h1>
      <p className="role-selector__subtitle">
        مرحباً بك! تسجيل الدخول للبدء
      </p>

      <form className="login-form" onSubmit={handleLogin} style={{ maxWidth: '400px', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '16px', background: 'var(--surface)', padding: '24px', borderRadius: '12px', border: '1px solid var(--border)' }}>
        {error && <div style={{ color: 'red', textAlign: 'center', marginBottom: '8px' }}>{error}</div>}

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label style={{ textAlign: 'right', fontWeight: 'bold' }}>البريد الإلكتروني</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            style={{ padding: '12px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
            placeholder="أدخل بريدك الإلكتروني"
            dir="ltr"
          />
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label style={{ textAlign: 'right', fontWeight: 'bold' }}>كلمة المرور</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{ padding: '12px', borderRadius: '8px', border: '1px solid var(--border)', background: 'var(--bg)', color: 'var(--text)' }}
            placeholder="أدخل كلمة المرور"
            dir="ltr"
          />
        </div>

        <button
          type="submit"
          disabled={loading}
          style={{
            marginTop: '12px',
            padding: '12px',
            borderRadius: '8px',
            border: 'none',
            background: 'var(--primary)',
            color: 'white',
            fontWeight: 'bold',
            cursor: loading ? 'not-allowed' : 'pointer',
            opacity: loading ? 0.7 : 1
          }}
        >
          {loading ? 'جاري الدخول...' : 'تسجيل الدخول'}
        </button>

        <div style={{ marginTop: '16px', fontSize: '0.9em', color: 'var(--text-muted)', textAlign: 'center' }}>
          <strong>حسابات تجريبية:</strong><br />
          العميل: mallrag@cust.com | password123<br />
          المدير: mallrag@man.com | password123
        </div>
      </form>
    </div>
  )
}
