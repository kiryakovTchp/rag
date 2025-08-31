'use client'

import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { redirect } from 'next/navigation'
import { Settings, Save, RotateCcw } from 'lucide-react'

interface ChatSettings {
  top_k: number
  rerank: boolean
  max_ctx_tokens: number
}

const defaultSettings: ChatSettings = {
  top_k: 10,
  rerank: true,
  max_ctx_tokens: 2000
}

export default function SettingsPage() {
  const { data: session, status } = useSession()
  const [settings, setSettings] = useState<ChatSettings>(defaultSettings)
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    if (status === 'loading') return
    if (!session) {
      redirect('/auth/signin')
    }

    // Load settings from localStorage
    const savedSettings = localStorage.getItem('chatSettings')
    if (savedSettings) {
      try {
        setSettings(JSON.parse(savedSettings))
      } catch (error) {
        console.error('Error loading settings:', error)
      }
    }
  }, [session, status])

  const handleSave = () => {
    localStorage.setItem('chatSettings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleReset = () => {
    setSettings(defaultSettings)
    localStorage.removeItem('chatSettings')
  }

  const handleChange = (key: keyof ChatSettings, value: any) => {
    setSettings(prev => ({ ...prev, [key]: value }))
  }

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg shadow-lg p-6">
          <div className="flex items-center mb-8">
            <Settings className="w-8 h-8 text-gray-600 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">Chat Settings</h1>
          </div>

          <div className="space-y-6">
            {/* Top K Setting */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of chunks to retrieve (top_k)
              </label>
              <div className="flex items-center space-x-4">
                <input
                  type="range"
                  min="1"
                  max="20"
                  value={settings.top_k}
                  onChange={(e) => handleChange('top_k', parseInt(e.target.value))}
                  className="flex-1"
                />
                <span className="text-sm text-gray-600 w-12">{settings.top_k}</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Higher values retrieve more context but may be less relevant
              </p>
            </div>

            {/* Rerank Setting */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={settings.rerank}
                  onChange={(e) => handleChange('rerank', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm font-medium text-gray-700">
                  Enable reranking
                </span>
              </label>
              <p className="text-sm text-gray-500 mt-1">
                Rerank chunks for better relevance to your question
              </p>
            </div>

            {/* Max Context Tokens */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum context tokens
              </label>
              <div className="flex items-center space-x-4">
                <input
                  type="range"
                  min="500"
                  max="4000"
                  step="500"
                  value={settings.max_ctx_tokens}
                  onChange={(e) => handleChange('max_ctx_tokens', parseInt(e.target.value))}
                  className="flex-1"
                />
                <span className="text-sm text-gray-600 w-16">{settings.max_ctx_tokens}</span>
              </div>
              <p className="text-sm text-gray-500 mt-1">
                Maximum tokens to include in context (affects response quality and cost)
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex space-x-4 pt-6 border-t border-gray-200">
              <button
                onClick={handleSave}
                className="flex items-center bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg transition duration-200"
              >
                <Save className="w-4 h-4 mr-2" />
                Save Settings
              </button>
              <button
                onClick={handleReset}
                className="flex items-center bg-gray-300 hover:bg-gray-400 text-gray-700 px-4 py-2 rounded-lg transition duration-200"
              >
                <RotateCcw className="w-4 h-4 mr-2" />
                Reset to Defaults
              </button>
            </div>

            {/* Save Confirmation */}
            {saved && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-green-800 text-sm">
                  Settings saved successfully!
                </p>
              </div>
            )}

            {/* Settings Info */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="text-sm font-medium text-blue-800 mb-2">How these settings work:</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• <strong>Top K:</strong> Number of document chunks retrieved for context</li>
                <li>• <strong>Reranking:</strong> Reorders chunks by relevance to your question</li>
                <li>• <strong>Max Context:</strong> Limits total tokens sent to AI (affects cost)</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
