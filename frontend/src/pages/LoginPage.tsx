import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Activity } from 'lucide-react'
import { authApi } from '../utils/api'
import { useStore } from '../store/useStore'

export default function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const { setToken, setUser } = useStore()
  const navigate = useNavigate()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const res = await authApi.login(username, password)
      const token = res.data.access_token
      setToken(token)
      // Fetch user info
      const meRes = await authApi.me()
      setUser(meRes.data)
      navigate('/')
    } catch {
      setError('Invalid username or password')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        {/* Logo */}
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center justify-center w-16 h-16 rounded-xl bg-aries-800 mb-4">
            <Activity className="w-8 h-8 text-aries-300" />
          </div>
          <h1 className="text-2xl font-bold text-white">SE_ARIES</h1>
          <p className="text-sm text-gray-400 mt-1">Petroleum Economics Platform</p>
        </div>

        {/* Form */}
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 shadow-2xl">
          <h2 className="text-base font-semibold text-white mb-4">Sign In</h2>

          {error && (
            <div className="mb-4 p-3 bg-red-900/30 border border-red-700 text-red-400 text-sm rounded-lg">
              {error}
            </div>
          )}

          <form onSubmit={handleLogin} className="space-y-4">
            <div>
              <label className="label">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="input-field"
                placeholder="admin"
                autoFocus
                required
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="input-field"
                placeholder="••••••••"
                required
              />
            </div>
            <button
              type="submit"
              disabled={loading}
              className="btn-primary w-full mt-2"
            >
              {loading ? 'Signing in...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-4 text-xs text-gray-500 text-center">
            Default: admin / admin123
          </div>
        </div>
      </div>
    </div>
  )
}
