'use client'

import { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Settings, Save } from 'lucide-react'

interface ChatSettings {
  top_k: number
  rerank: boolean
  max_ctx_tokens: number
}

export default function SettingsPage() {
  const { data: session } = useSession()
  const [settings, setSettings] = useState<ChatSettings>({
    top_k: 10,
    rerank: false,
    max_ctx_tokens: 2000
  })
  const [saved, setSaved] = useState(false)

  useEffect(() => {
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('chatSettings')
    if (savedSettings) {
      setSettings(JSON.parse(savedSettings))
    }
  }, [])

  const handleSave = () => {
    localStorage.setItem('chatSettings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const handleReset = () => {
    const defaultSettings: ChatSettings = {
      top_k: 10,
      rerank: false,
      max_ctx_tokens: 2000
    }
    setSettings(defaultSettings)
    localStorage.setItem('chatSettings', JSON.stringify(defaultSettings))
  }

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white rounded-lg shadow-lg p-8">
          <div className="flex items-center space-x-3 mb-8">
            <Settings className="w-8 h-8 text-blue-500" />
            <h1 className="text-3xl font-bold">Chat Settings</h1>
          </div>

          <div className="space-y-6">
            {/* Top K */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Number of chunks to retrieve (top_k)
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={settings.top_k}
                onChange={(e) => setSettings(prev => ({ ...prev, top_k: parseInt(e.target.value) }))}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-sm text-gray-500 mt-1">
                Higher values retrieve more context but may be less relevant
              </p>
            </div>

            {/* Rerank */}
            <div>
              <label className="flex items-center space-x-3">
                <input
                  type="checkbox"
                  checked={settings.rerank}
                  onChange={(e) => setSettings(prev => ({ ...prev, rerank: e.target.checked }))}
                  className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                />
                <span className="text-sm font-medium text-gray-700">
                  Enable reranking
                </span>
              </label>
              <p className="text-sm text-gray-500 mt-1 ml-7">
                Rerank chunks for better relevance (slower but more accurate)
              </p>
            </div>

            {/* Max Context Tokens */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum context tokens
              </label>
              <input
                type="number"
                min="500"
                max="8000"
                step="500"
                value={settings.max_ctx_tokens}
                onChange={(e) => setSettings(prev => ({ ...prev, max_ctx_tokens: parseInt(e.target.value) }))}
                className="w-full border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-sm text-gray-500 mt-1">
                Maximum tokens to include in context (affects response quality and cost)
              </p>
            </div>

            {/* Buttons */}
            <div className="flex space-x-4 pt-6">
              <button
                onClick={handleSave}
                className="flex items-center space-x-2 bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors"
              >
                <Save className="w-4 h-4" />
                <span>{saved ? 'Saved!' : 'Save Settings'}</span>
              </button>
              <button
                onClick={handleReset}
                className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                Reset to Defaults
              </button>
            </div>
          </div>

          {/* Info */}
          <div className="mt-8 p-4 bg-blue-50 rounded-lg">
            <h3 className="font-medium text-blue-900 mb-2">How these settings work:</h3>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• <strong>top_k:</strong> Number of document chunks retrieved for context</li>
              <li>• <strong>rerank:</strong> Reorders chunks by relevance (more accurate but slower)</li>
              <li>• <strong>max_ctx_tokens:</strong> Limits total context size (affects cost and quality)</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}
