import { useState } from 'react'
import RoleSelector from './pages/RoleSelector'
import ChatPage from './pages/ChatPage'
import './index.css'

export default function App() {
  const [role, setRole] = useState<'customer' | 'manager' | null>(null)

  if (!role) return <RoleSelector onSelect={setRole} />
  return <ChatPage role={role} onBack={() => setRole(null)} />
}
