/**
 * Content Submission & Multi-Modal Analysis Page.
 * Supports manual text drafting, quick test scenarios, and PDF / document / image upload.
 * Integrated with Role-Based Access Control and active brand workspace.
 */

import { useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import type { ContentType } from '../api/types'
import { useAuth } from '../context/AuthContext'
import { DEMO_TEST_CASES, type DemoTestCase } from '../data/demoTestCases'

export function SubmitPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const initialData = location.state as DemoTestCase | undefined
  const { user, activeBrand } = useAuth()

  const [title, setTitle] = useState(initialData?.title || 'LumaCare Social Announcement')
  const [contentType, setContentType] = useState<ContentType>(initialData?.type || 'social_post')
  const [authorName] = useState(user?.display_name || 'Demo Editor')
  const [body, setBody] = useState(initialData?.content || '')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Document & Visual Upload state
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadedFileName, setUploadedFileName] = useState<string | null>(null)
  const [visualNotice, setVisualNotice] = useState<string | null>(null)

  const charCount = body.length
  const wordCount = body.trim() ? body.trim().split(/\s+/).length : 0

  const isReviewer = user?.role === 'reviewer'

  const handlePreload = (tc: DemoTestCase) => {
    setTitle(tc.title)
    setContentType(tc.type)
    setBody(tc.content)
    setError(null)
    setUploadedFileName(null)
    setVisualNotice(null)
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setError(null)

    try {
      const res = await api.extractDocument(file, activeBrand?.id)
      setUploadedFileName(file.name)
      if (res.extracted_text) {
        setBody(res.extracted_text)
        setTitle(file.name.replace(/\.[^/.]+$/, ''))
      }

      if (res.extraction_source === 'ocr' || res.extraction_metadata?.has_ocr_text) {
        setContentType('advertisement')
        setVisualNotice(
          `Extracted ${res.extraction_metadata?.word_count || 0} words from promotional image via Multimodal OCR. Please review copy before analysis.`
        )
      } else if (res.file_type.startsWith('image/')) {
        setContentType('advertisement')
        if (res.visual_findings && res.visual_findings.length > 0) {
          setVisualNotice(
            `Extracted image palette and detected ${res.visual_findings.length} visual compliance observation(s).`
          )
        } else {
          setVisualNotice('Visual image colors, logo standards and dimensions verified against brand palette.')
        }
      } else if (res.file_type === 'docx') {
        setContentType('press_release')
        setVisualNotice(`Extracted ${res.extraction_metadata?.paragraph_count || 0} paragraphs from Word (.docx) document.`)
      } else if (res.file_type === 'pdf') {
        setContentType('product_description')
        if (res.extraction_source === 'ocr') {
          setVisualNotice(`Extracted text from scanned PDF via Multimodal OCR.`)
        } else {
          setVisualNotice(`Extracted ${res.extraction_metadata?.page_count || 1} page(s) from PDF document.`)
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to extract document contents.'
      setError(msg)
    } finally {
      setIsUploading(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (isReviewer) {
      setError('Reviewer accounts cannot create content submissions. Please sign in as Creator or Brand Manager.')
      return
    }

    if (!title.trim() || !body.trim()) {
      setError('Please provide both a title and content body.')
      return
    }

    setIsSubmitting(true)
    setError(null)

    try {
      // 1. Fetch brand to get its ID
      const brandSlugOrId = activeBrand ? activeBrand.id : 'lumacare'
      const brand = await api.getBrand(brandSlugOrId)

      // 2. Create submission (creates version 1)
      const submission = await api.createSubmission({
        brand_id: brand.id,
        title: title.trim(),
        content_type: contentType,
        body: body.trim(),
        author_name: user?.display_name || authorName.trim() || 'Demo Editor',
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
        <div className="flex items-center space-x-2">
          <span className="text-xs uppercase tracking-widest text-sage font-medium">New Evaluation</span>
          <span className="text-xs text-ink-soft">/</span>
          <span className="text-xs font-semibold text-ink bg-parchment px-2 py-0.5 rounded-sm border border-parchment-deep">
            {activeBrand ? activeBrand.name : 'LumaCare'}
          </span>
        </div>
        <h1 className="mt-2 font-serif text-3xl font-bold text-ink">Submit Content for Governance</h1>
        <p className="mt-2 text-sm text-ink-soft">
          Evaluate your communication copy, promotional imagery, or marketing PDF against{' '}
          <strong className="text-ink">{activeBrand ? activeBrand.name : 'LumaCare'}</strong> approved
          guidelines, facts, terminology, and visual standards.
        </p>
      </div>

      {isReviewer && (
        <div className="p-4 bg-terracotta/10 border border-terracotta/30 rounded-sm text-xs text-terracotta">
          <strong>Reviewer Access:</strong> You are currently signed in with the Reviewer role. Reviewer
          accounts inspect and approve submissions in human review workflows. To create submissions, sign
          in with a Content Creator (Editor) or Brand Manager account.
        </div>
      )}

      {/* Multi-Modal Ingestion Zone (File Upload) */}
      <div className="p-6 bg-parchment/40 border border-dashed border-parchment-deep rounded-sm space-y-3">
        <div className="flex items-baseline justify-between">
          <span className="text-xs uppercase tracking-wider font-semibold text-ink">
            Document & Visual Asset Ingestion
          </span>
          <span className="text-[11px] text-ink-soft">Supports PDF, DOCX, TXT, PNG, JPG, WEBP (up to 10MB)</span>
        </div>

        <div className="flex items-center space-x-4">
          <input
            type="file"
            ref={fileInputRef}
            onChange={handleFileUpload}
            accept=".pdf,.docx,.txt,.md,.png,.jpg,.jpeg,.webp"
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="px-4 py-2 bg-ivory text-ink text-xs font-semibold rounded-sm border border-parchment-deep hover:border-sage transition-colors disabled:opacity-50"
          >
            {isUploading ? 'Extracting File...' : 'Upload Document or Image'}
          </button>
          {uploadedFileName && (
            <span className="text-xs font-mono text-sage bg-sage-soft/30 px-2 py-1 rounded-sm border border-sage/20">
              Loaded: {uploadedFileName}
            </span>
          )}
        </div>

        {visualNotice && (
          <div className="p-2.5 bg-sage-soft/30 border border-sage/30 rounded-sm text-xs text-sage font-medium">
            {visualNotice}
          </div>
        )}
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
            <label htmlFor="contentType" className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
              Content Channel / Type
            </label>
            <select
              id="contentType"
              value={contentType}
              onChange={(e) => setContentType(e.target.value as ContentType)}
              className="w-full px-3 py-2 text-sm bg-ivory border border-parchment-deep rounded-sm text-ink focus:border-sage focus:outline-none"
            >
              <option value="social_post">Social Post</option>
              <option value="email">Marketing Email</option>
              <option value="web_page">Web Landing Page</option>
              <option value="advertisement">Advertisement / Banner</option>
              <option value="product_description">Product Description</option>
              <option value="press_release">Press Release</option>
              <option value="other">Other Communication</option>
            </select>
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label htmlFor="body" className="block text-xs font-semibold uppercase tracking-wider text-ink-soft">
              Content Copy
            </label>
            <div className="text-[11px] font-mono text-ink-soft">
              {wordCount} words | {charCount} / 10,000 chars
            </div>
          </div>
          <textarea
            id="body"
            rows={10}
            required
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Type, paste, or upload communication content..."
            className="w-full p-4 text-sm bg-ivory border border-parchment-deep rounded-sm text-ink font-serif leading-relaxed focus:border-sage focus:outline-none resize-y"
          />
        </div>

        <div className="pt-2 flex items-center justify-between border-t border-parchment-deep">
          <span className="text-xs text-ink-soft">
            Evaluates rule-based constraints, factual consistency, and AI semantic compliance.
          </span>
          <button
            type="submit"
            disabled={isSubmitting || isReviewer}
            className="px-6 py-2.5 bg-ink text-ivory text-xs font-bold uppercase tracking-wider rounded-sm hover:bg-sage transition-colors disabled:opacity-50"
          >
            {isSubmitting ? 'Evaluating Content...' : 'Run Compliance Analysis'}
          </button>
        </div>
      </form>
    </div>
  )
}
