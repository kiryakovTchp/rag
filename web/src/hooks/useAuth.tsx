import React, { useState, useEffect, createContext, useContext } from 'react'
import { User, login as loginApi, register as registerApi, getMe } from '@/services/auth'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (data: { email: string; password: string }) => Promise<void>
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
        const storedToken = localStorage.getItem('auth_token')
        if (storedToken) {
          setToken(storedToken)
          // Try to get user info
          try {
            const userData = await getMe()
            setUser(userData)
          } catch (error) {
            // Token invalid, clear it
            localStorage.removeItem('auth_token')
            setToken(null)
          }
        }
      } catch (error) {
        console.error('Failed to load user:', error)
        localStorage.removeItem('auth_token')
      } finally {
        setLoading(false)
      }
    }

    loadUser()
  }, [])

  const login = async (email: string, password: string) => {
    try {
      console.log('Attempting login with:', { email, password: '***' })
      const response = await loginApi({ email, password })
      console.log('Login response:', response)
      const { access_token } = response
      
      // Store token
      localStorage.setItem('auth_token', access_token)
      setToken(access_token)
      
      // Get user info
      console.log('Getting user info...')
      const userData = await getMe()
      console.log('User data:', userData)
      setUser(userData)
    } catch (error: any) {
      console.error('Login failed:', error)
      if (error.response) {
        console.error('Error response:', error.response.data)
        console.error('Error status:', error.response.status)
      }
      throw error
    }
  }

  const register = async (data: { email: string; password: string }) => {
    try {
      const userData = await registerApi(data)
      // After registration, set user and login automatically
      setUser(userData)
      await login(data.email, data.password)
    } catch (error: any) {
      console.error('Registration failed:', error)
      throw error
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
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
