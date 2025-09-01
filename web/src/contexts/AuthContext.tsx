import React, { createContext, useContext, useEffect, useState } from 'react'
import { User, LoginForm, RegisterForm } from '@/types'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (data: LoginForm) => Promise<boolean>
  register: (data: RegisterForm) => Promise<boolean>
  logout: () => void
  refreshProfile: () => Promise<void>
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
  const [loading, setLoading] = useState(true)

  // Load user from localStorage on mount
  useEffect(() => {
    const loadUser = async () => {
      try {
        const token = localStorage.getItem('auth_token')
        if (token) {
          // TODO: Validate token with backend
          const userData = localStorage.getItem('user_data')
          if (userData) {
            setUser(JSON.parse(userData))
          }
        }
      } catch (error) {
        console.error('Failed to load user:', error)
        localStorage.removeItem('auth_token')
        localStorage.removeItem('user_data')
      } finally {
        setLoading(false)
      }
    }

    loadUser()
  }, [])

  const login = async (data: LoginForm): Promise<boolean> => {
    try {
      setLoading(true)
      
      // TODO: Replace with real API call
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        throw new Error('Login failed')
      }

      const result = await response.json()
      const { user: userData, token } = result

      // Store auth data
      localStorage.setItem('auth_token', token)
      localStorage.setItem('user_data', JSON.stringify(userData))
      
      setUser(userData)
      return true
    } catch (error) {
      console.error('Login error:', error)
      return false
    } finally {
      setLoading(false)
    }
  }

  const register = async (data: RegisterForm): Promise<boolean> => {
    try {
      setLoading(true)
      
      // TODO: Replace with real API call
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          name: data.name,
          email: data.email,
          password: data.password,
        }),
      })

      if (!response.ok) {
        throw new Error('Registration failed')
      }

      const result = await response.json()
      const { user: userData, token } = result

      // Store auth data
      localStorage.setItem('auth_token', token)
      localStorage.setItem('user_data', JSON.stringify(userData))
      
      setUser(userData)
      return true
    } catch (error) {
      console.error('Registration error:', error)
      return false
    } finally {
      setLoading(false)
    }
  }

  const logout = () => {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_data')
    setUser(null)
  }

  const refreshProfile = async () => {
    try {
      const token = localStorage.getItem('auth_token')
      if (!token) return

      // TODO: Replace with real API call
      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (response.ok) {
        const userData = await response.json()
        localStorage.setItem('user_data', JSON.stringify(userData))
        setUser(userData)
      }
    } catch (error) {
      console.error('Failed to refresh profile:', error)
    }
  }

  const value: AuthContextType = {
    user,
    loading,
    login,
    register,
    logout,
    refreshProfile,
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
