import React, { useState, useEffect, createContext, useContext } from 'react'
import { User, login as loginApi, register as registerApi, getMe } from '@/services/auth'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (email: string, password: string) => Promise<void>
  logout: () => void
  loading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = async () => {
      try {
        const storedToken = localStorage.getItem('rag_access_token')
        if (storedToken) {
          setToken(storedToken)
          // Try to get user info
          try {
            const userData = await getMe()
            setUser(userData)
          } catch (error) {
            // Token invalid, clear it
            localStorage.removeItem('rag_access_token')
            setToken(null)
          }
        }
      } catch (error) {
        console.error('Failed to load user:', error)
        localStorage.removeItem('rag_access_token')
      } finally {
        setLoading(false)
      }
    }

    loadUser()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      const response = await loginApi({ email, password })
      const { access_token } = response
      
      // Store token
      localStorage.setItem('rag_access_token', access_token)
      setToken(access_token)
      
      // Get user info
      const userData = await getMe()
      setUser(userData)
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  const register = async (email: string, password: string) => {
    try {
      await registerApi({ email, password })
      // After registration, login automatically
      await login(email, password)
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('rag_access_token')
    setToken(null)
    setUser(null)
  }

  const value: AuthContextType = {
    user,
    token,
    login,
    register,
    logout,
    loading,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
