/**
 * Content Submission & Analysis Page.
 * Allows drafting or pre-loading content, selecting content type,
 * and triggering immediate deterministic + AI compliance analysis.
 */

import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { ContentType } from '../api/types'
import { DEMO_TEST_CASES, type DemoTestCase } from '../data/demoTestCases'

export function SubmitPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const initialData = location.state as DemoTestCase | undefined

  const [title, setTitle] = useState(initialData?.title || 'LumaCare Social Announcement')
  const [contentType, setContentType] = useState<ContentType>(initialData?.type || 'social_post')
  const [authorName, setAuthorName] = useState('Demo Editor')
  const [body, setBody] = useState(initialData?.content || '')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const charCount = body.length
  const wordCount = body.trim() ? body.trim().split(/\s+/).length : 0

  const handlePreload = (tc: DemoTestCase) => {
    setTitle(tc.title)
    setContentType(tc.type)
    setBody(tc.content)
    setError(null)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim() || !body.trim()) {
      setError('Please provide both a title and content body.')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      // 1. Fetch brand to get its ID
      const brand = await api.getBrand('lumacare')

      // 2. Create submission (creates version 1)
      const submission = await api.createSubmission({
        brand_id: brand.id,
        title: title.trim(),
        content_type: contentType,
        body: body.trim(),
        author_name: authorName.trim() || 'Demo Editor',
      })

      // 3. Immediately trigger analysis
      await api.analyzeSubmission(submission.id)

      // 4. Redirect to submission inspection detail
      navigate(`/submissions/${submission.id}`)
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to submit and analyse content.'
      setError(errorMsg)
      setIsSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-4xl px-6 py-10 space-y-8">
      <div>
        <span className="text-xs uppercase tracking-widest text-sage font-medium">New Evaluation</span>
        <h1 className="mt-1 font-serif text-3xl font-bold text-ink">Submit Content for Governance</h1>
        <p className="mt-2 text-sm text-ink-soft">
          Evaluate your communication copy against LumaCare approved guidelines, facts and terminology.
        </p>
      </div>

      {/* Pre-fill test cases bar */}
      <div className="p-4 bg-parchment/60 border border-parchment-deep rounded-sm space-y-2">
        <span className="text-xs uppercase tracking-wider font-semibold text-ink-soft">
          Quick Evaluation Templates (Judge Test Scenarios):
        </span>
        <div className="flex flex-wrap gap-2">
          {DEMO_TEST_CASES.map((tc) => (
            <button
              key={tc.id}
              type="button"
              onClick={() => handlePreload(tc)}
              className="px-3 py-1.5 text-xs font-medium bg-ivory text-ink border border-parchment-deep rounded-sm hover:border-sage transition-colors"
            >
              {tc.label}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="p-4 bg-terracotta-soft/30 border border-terracotta/40 rounded-sm text-xs text-terracotta">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-ivory border border-parchment-deep p-6 rounded-sm space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-1.5">
            <label htmlFor="title" className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
              Content Title
            </label>
            <input
              id="title"
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Spring Skincare Launch Post"
              className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm text-ink focus:border-sage focus:outline-none"
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="content_type" className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
              Content Type
            </label>
            <select
              id="content_type"
              value={contentType}
              onChange={(e) => setContentType(e.target.value as ContentType)}
              className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm text-ink focus:border-sage focus:outline-none"
            >
              <option value="social_post">Social Post</option>
              <option value="advertisement">Advertisement</option>
              <option value="email">Email Campaign</option>
              <option value="web_page">Web Page Copy</option>
              <option value="product_description">Product Description</option>
              <option value="press_release">Press Release</option>
              <option value="other">Other</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
              Brand Workspace
            </label>
            <input
              type="text"
              readOnly
              value="LumaCare (Demo)"
              className="w-full px-3 py-2 text-sm bg-parchment/40 border border-parchment-deep rounded-sm text-ink-soft cursor-not-allowed"
            />
          </div>

          <div className="space-y-1.5">
            <label htmlFor="author" className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
              Author
            </label>
            <input
              id="author"
              type="text"
              value={authorName}
              onChange={(e) => setAuthorName(e.target.value)}
              className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm text-ink focus:border-sage focus:outline-none"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label htmlFor="body" className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
              Content Body
            </label>
            <span className="text-xs text-ink-soft font-mono">
              {wordCount} words | {charCount} / 10,000 chars
            </span>
          </div>

          <textarea
            id="body"
            required
            rows={8}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Paste or write the marketing and communication copy to analyse..."
            className="w-full p-4 text-sm font-sans leading-relaxed bg-ivory border border-parchment-deep rounded-sm text-ink focus:border-sage focus:outline-none resize-y"
          />
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-parchment-deep/60">
          <button
            type="button"
            onClick={() => navigate('/')}
            className="px-4 py-2 text-xs font-medium text-ink-soft hover:text-ink transition-colors"
          >
            Cancel
          </button>

          <button
            type="submit"
            disabled={isSubmitting || !body.trim()}
            className="px-6 py-2.5 bg-ink text-ivory text-sm font-medium rounded-sm hover:bg-ink-soft disabled:opacity-50 transition-colors flex items-center space-x-2"
          >
            {isSubmitting ? (
              <>
                <span className="h-3 w-3 rounded-full border-2 border-ivory border-t-transparent animate-spin mr-2" />
                <span>Analysing with Brand Engine...</span>
              </>
            ) : (
              <span>Submit and Analyse</span>
            )}
          </button>
        </div>
      </form>
    </div>
  )
}
