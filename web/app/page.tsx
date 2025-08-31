'use client'

import { useSession } from 'next-auth/react'
import { redirect } from 'next/navigation'
import Link from 'next/link'

export default function HomePage() {
  const { data: session, status } = useSession()

  if (status === 'loading') {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-gray-900 mx-auto"></div>
          <p className="mt-4 text-lg">Loading...</p>
        </div>
      </div>
    )
  }

  if (!session) {
    redirect('/auth/signin')
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-gray-900 mb-8">
            Welcome to PromoAI RAG
          </h1>
          <p className="text-xl text-gray-600 mb-12">
            Upload documents and chat with your data using AI
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <Link href="/upload" 
                  className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 px-8 rounded-lg transition duration-200">
              Upload Documents
            </Link>
            <Link href="/chat" 
                  className="bg-green-600 hover:bg-green-700 text-white font-semibold py-4 px-8 rounded-lg transition duration-200">
              Start Chatting
            </Link>
          </div>
          
          <div className="mt-12">
            <Link href="/settings" 
                  className="text-blue-600 hover:text-blue-800 underline">
              Settings
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
