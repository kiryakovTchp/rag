import { test, expect } from '@playwright/test'

test.describe('Chat Flow', () => {
  test('complete flow: login → upload → progress → question → stream → citation', async ({ page }) => {
    // Mock authentication
    await page.goto('/')
    
    // Mock session
    await page.addInitScript(() => {
      window.localStorage.setItem('next-auth.session-token', 'mock-token')
    })

    // Mock API responses
    await page.route('**/api/proxy/ingest', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          document_id: 1,
          status: 'uploaded'
        })
      })
    })

    await page.route('**/api/proxy/answer/stream', async route => {
      const response = `data: {"type":"chunk","text":"Hello"}\n\n`
        + `data: {"type":"chunk","text":" world"}\n\n`
        + `data: {"type":"done","citations":[{"doc_id":1,"chunk_id":1,"page":1,"score":0.95}]}\n\n`
      
      await route.fulfill({
        status: 200,
        contentType: 'text/plain',
        body: response
      })
    })

    // Mock WebSocket
    await page.route('**/ws/jobs', async route => {
      await route.fulfill({
        status: 101,
        headers: {
          'Upgrade': 'websocket',
          'Connection': 'Upgrade'
        }
      })
    })

    // Navigate to upload page
    await page.click('text=Upload Documents')
    await expect(page).toHaveURL('/upload')

    // Upload a file
    const fileInput = page.locator('input[type="file"]')
    await fileInput.setInputFiles({
      name: 'test.pdf',
      mimeType: 'application/pdf',
      buffer: Buffer.from('fake pdf content')
    })

    await page.click('text=Upload 1 file')

    // Wait for upload to complete
    await expect(page.locator('text=Upload successful')).toBeVisible()

    // Navigate to chat
    await page.click('text=Start Chatting')
    await expect(page).toHaveURL('/chat')

    // Ask a question
    await page.fill('input[placeholder*="question"]', 'What is this document about?')
    await page.click('button[type="submit"]')

    // Wait for streaming response
    await expect(page.locator('text=Hello world')).toBeVisible()

    // Check for citations
    await expect(page.locator('text=Sources:')).toBeVisible()
    await expect(page.locator('text=Document 1')).toBeVisible()

    // Click on citation
    await page.click('text=Document 1')

    // Check citation modal
    await expect(page.locator('text=Citation Details')).toBeVisible()
    await expect(page.locator('text=Document ID: 1')).toBeVisible()

    // Close modal
    await page.click('button:has([data-testid="close"])')

    // Give feedback
    await page.click('button[aria-label="thumbs up"]')
    await expect(page.locator('text=Feedback submitted')).toBeVisible()
  })

  test('settings page functionality', async ({ page }) => {
    await page.goto('/settings')

    // Check settings controls
    await expect(page.locator('text=Chat Settings')).toBeVisible()
    await expect(page.locator('input[type="range"]')).toHaveCount(2)
    await expect(page.locator('input[type="checkbox"]')).toBeVisible()

    // Modify settings
    await page.locator('input[type="range"]').first().fill('15')
    await page.locator('input[type="checkbox"]').check()

    // Save settings
    await page.click('text=Save Settings')
    await expect(page.locator('text=Settings saved successfully')).toBeVisible()
  })

  test('authentication flow', async ({ page }) => {
    await page.goto('/auth/signin')

    // Check sign in page
    await expect(page.locator('text=Sign in to PromoAI RAG')).toBeVisible()
    await expect(page.locator('text=Sign in with Google')).toBeVisible()

    // Mock Google OAuth
    await page.route('**/api/auth/signin/google', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          url: '/api/auth/callback/google?code=mock-code'
        })
      })
    })

    await page.click('text=Sign in with Google')

    // Should redirect to home after successful auth
    await expect(page).toHaveURL('/')
  })
})
