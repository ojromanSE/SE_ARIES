import { Routes, Route, Navigate } from 'react-router-dom'
import { useStore } from './store/useStore'
import LoginPage from './pages/LoginPage'
import MainLayout from './pages/MainLayout'

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { token } = useStore()
  return token ? <>{children}</> : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/*"
        element={
          <PrivateRoute>
            <MainLayout />
          </PrivateRoute>
        }
      />
    </Routes>
  )
}
