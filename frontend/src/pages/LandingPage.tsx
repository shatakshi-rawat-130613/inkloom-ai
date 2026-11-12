/**
 * Dedicated Public Homepage inspired by Pod.ai's information architecture.
 * Features:
 * - Alternating light (parchment/sand/rose) and dark (deep plum) sections.
 * - Split hero with editorial headline, supporting narrative, live visual card, and audience actions.
 * - In-depth presentation of Round 3's three master improvements.
 * - Dedicated solutions for Brand Teams and Agencies.
 * - Transparent 3-step 'How It Works' workflow.
 * - Enterprise Call to Action and grounded governance principles.
 */

import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export function LandingPage() {
  const navigate = useNavigate()
  const { user, activeBrand, demoLogin } = useAuth()

  const handleDemoLaunch = async (role: 'admin' | 'creator' | 'reviewer') => {
    try {
      const res = await demoLogin(role)
      if (res.status === 'single' || res.status === 'restored') {
        navigate('/workspace')
      } else {
        navigate('/select-brand')
      }
    } catch {
      navigate('/login')
    }
  }

  return (
    <div className="bg-ivory text-ink">
      {/* SECTION 1: HERO (Warm Parchment & Sand Split Hero) */}
      <section id="home" className="relative pt-12 pb-20 sm:pt-20 sm:pb-28 overflow-hidden bg-parchment/60 border-b border-parchment-deep">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            {/* Left Hero Column */}
            <div className="lg:col-span-7 space-y-6 sm:space-y-8">
              <div className="inline-flex items-center space-x-2 px-3 py-1 bg-parchment rounded-sm border border-parchment-deep text-xs font-semibold uppercase tracking-wider text-plum">
                <span className="h-2 w-2 rounded-full bg-terracotta" />
                <span>Enterprise Autonomous Brand Governance</span>
              </div>

              <h1 className="font-serif text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-ink leading-[1.12]">
                Governing <span className="text-plum italic">Brands</span>,{' '}
                Unifying <span className="text-terracotta">Workspaces</span>,{' '}
                Verifying <span className="text-sage">Every Claim</span>.
              </h1>

              <p className="text-base sm:text-lg text-ink-soft leading-relaxed max-w-xl">
                The intelligent brand-governance engine that unites brand managers, content creators, and compliance reviewers in a single, verifiable workspace across multiple corporate and client brands.
              </p>

              {/* Dual Audience Actions inspired by Pod.ai hero buttons */}
              <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 pt-2">
                <div className="flex-1 sm:flex-initial space-y-1">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-soft">
                    For Brand Teams
                  </div>
                  <Link
                    to={user ? '/workspace' : '/login'}
                    className="inline-flex items-center justify-center w-full sm:w-auto px-5 py-3 bg-terracotta text-ivory text-xs sm:text-sm font-semibold rounded-sm hover:bg-terracotta-dark transition-colors shadow-sm group"
                  >
                    <span>Champion Brand Integrity</span>
                    <span className="ml-2 group-hover:translate-x-1 transition-transform">→</span>
                  </Link>
                </div>

                <div className="flex-1 sm:flex-initial space-y-1">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-soft">
                    For Agencies
                  </div>
                  <Link
                    to={user ? '/workspace' : '/login'}
                    className="inline-flex items-center justify-center w-full sm:w-auto px-5 py-3 bg-plum text-ivory text-xs sm:text-sm font-semibold rounded-sm hover:bg-plum-soft transition-colors shadow-sm group"
                  >
                    <span>Verify Multi-Brand Copy</span>
                    <span className="ml-2 group-hover:translate-x-1 transition-transform">→</span>
                  </Link>
                </div>
              </div>

              {/* Assurance Badges */}
              <div className="pt-4 grid grid-cols-1 sm:grid-cols-3 gap-3 border-t border-parchment-deep/80 text-xs text-ink-soft">
                <div className="flex items-center space-x-2">
                  <span className="text-sage font-bold">✓</span>
                  <span>Multi-Tenant RBAC</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sage font-bold">✓</span>
                  <span>OCR & Scanned PDF Extraction</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sage font-bold">✓</span>
                  <span>Visual Logo Verification</span>
                </div>
              </div>
            </div>

            {/* Right Hero Column: Interactive Product Visual Card */}
            <div className="lg:col-span-5 relative">
              <div className="relative mx-auto max-w-md bg-ivory rounded-sm border border-parchment-deep p-6 shadow-md space-y-5">
                {/* Visual Header */}
                <div className="flex items-center justify-between border-b border-parchment-deep pb-3">
                  <div className="flex items-center space-x-2">
                    <span className="h-2.5 w-2.5 rounded-full bg-sage" />
                    <span className="font-serif text-sm font-bold text-ink">Inkloom Governance Engine</span>
                  </div>
                  <span className="text-[11px] font-semibold uppercase tracking-wider text-plum bg-plum-light px-2 py-0.5 rounded-sm">
                    {activeBrand ? activeBrand.name : 'LumaCare Skincare'}
                  </span>
                </div>

                {/* Sample Evaluated Copy */}
                <div className="space-y-1.5">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-soft">
                    Submitted Promotional Copy
                  </div>
                  <div className="p-3 bg-parchment/60 rounded-sm border border-parchment-deep text-xs font-serif text-ink leading-relaxed">
                    &ldquo;Our daily restorative cream <mark className="bg-terracotta-soft text-terracotta-dark font-sans px-1 rounded">guarantees 100% acne removal</mark> in just <mark className="bg-ochre-soft text-ochre font-sans px-1 rounded">7 days</mark>.&rdquo;
                  </div>
                </div>

                {/* Findings Preview */}
                <div className="space-y-2">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-ink-soft flex items-center justify-between">
                    <span>Active Rule & Evidence Grounding</span>
                    <span className="text-terracotta font-semibold text-[10px]">Action Required</span>
                  </div>

                  <div className="p-2.5 bg-rose-soft/80 border border-terracotta/30 rounded-sm space-y-1 text-xs">
                    <div className="flex items-center justify-between font-semibold text-terracotta-dark">
                      <span>GUIDE-001 (Outcome Claim)</span>
                      <span className="text-[10px] uppercase tracking-wider bg-terracotta text-ivory px-1.5 py-0.2 rounded-sm">Critical</span>
                    </div>
                    <p className="text-[11px] text-ink-soft">
                      Prohibits absolute outcome guarantees. Grounded in brand rule against unapproved medical promises.
                    </p>
                  </div>

                  <div className="p-2.5 bg-sand-soft/80 border border-sand rounded-sm space-y-1 text-xs">
                    <div className="flex items-center justify-between font-semibold text-ink">
                      <span>FACT-002 (Clinical Evidence Check)</span>
                      <span className="text-[10px] uppercase tracking-wider bg-ochre text-ivory px-1.5 py-0.2 rounded-sm">High</span>
                    </div>
                    <p className="text-[11px] text-ink-soft">
                      No 7-day cure timeframe has been clinically approved in LumaCare fact repository.
                    </p>
                  </div>
                </div>

                {/* Visual Asset Verification Pill */}
                <div className="p-2.5 bg-sage-light border border-sage/30 rounded-sm flex items-center justify-between text-xs">
                  <div className="flex items-center space-x-2">
                    <span className="text-sage text-sm">✦</span>
                    <span className="font-semibold text-sage">Visual Logo Match</span>
                  </div>
                  <span className="text-[11px] font-medium text-sage">Approved Reference (94% confidence)</span>
                </div>

                {/* One-Click Demo CTA inside card */}
                <div className="pt-2 text-center">
                  <button
                    type="button"
                    onClick={() => handleDemoLaunch('admin')}
                    className="text-xs font-semibold text-plum hover:text-terracotta transition-colors underline underline-offset-4"
                  >
                    Open live verification workspace as Brand Manager →
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 2: THE THREE ROUND 3 MASTER CAPABILITIES (Deep Plum Contrasting Dark Section) */}
      <section id="platform" className="py-20 sm:py-28 bg-plum text-ivory border-b border-plum-soft">
        <div className="mx-auto max-w-6xl px-6 space-y-14">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <div className="text-xs uppercase tracking-widest text-terracotta font-semibold">
              Master Capabilities
            </div>
            <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-bold text-ivory">
              Three Pillars of Enterprise Brand Governance
            </h2>
            <p className="text-sm sm:text-base text-ivory/80 leading-relaxed">
              Inkloom AI delivers the three core architectural improvements committed in our Round 2 master directive.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Capability 1 */}
            <div className="bg-plum-soft/60 rounded-sm border border-ivory/15 p-8 flex flex-col justify-between space-y-6 hover:border-terracotta transition-colors">
              <div className="space-y-4">
                <div className="h-10 w-10 rounded-sm bg-terracotta text-ivory flex items-center justify-center font-serif text-lg font-bold">
                  1
                </div>
                <h3 className="font-serif text-2xl font-bold text-ivory">
                  Multi-Brand Management & Tenant RBAC
                </h3>
                <p className="text-xs sm:text-sm text-ivory/70 leading-relaxed">
                  Establish independent brand profiles, guidelines, clinical facts, and preferred/prohibited terminology per brand. Enforce role-based access for Brand Managers, Content Creators, and Compliance Reviewers with strict tenant isolation.
                </p>
              </div>

              <div className="pt-4 border-t border-ivory/10 space-y-2 text-xs text-ivory/80">
                <div className="flex items-center space-x-2">
                  <span className="text-terracotta">✦</span>
                  <span>Instant brand switching</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-terracotta">✦</span>
                  <span>Versioned Alembic database migrations</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-terracotta">✦</span>
                  <span>Zero cross-tenant data leakage</span>
                </div>
              </div>
            </div>

            {/* Capability 2 */}
            <div className="bg-plum-soft/60 rounded-sm border border-ivory/15 p-8 flex flex-col justify-between space-y-6 hover:border-sage-muted transition-colors">
              <div className="space-y-4">
                <div className="h-10 w-10 rounded-sm bg-sage-muted text-plum flex items-center justify-center font-serif text-lg font-bold">
                  2
                </div>
                <h3 className="font-serif text-2xl font-bold text-ivory">
                  Multimodal Ingestion & Visual Compliance
                </h3>
                <p className="text-xs sm:text-sm text-ivory/70 leading-relaxed">
                  Extract visible copy from promotional images (PNG/JPG), multi-page scanned PDF documents via Gemini OCR, and native DOCX files. Compare embedded visual logos against approved references using perceptual and feature-based matching.
                </p>
              </div>

              <div className="pt-4 border-t border-ivory/10 space-y-2 text-xs text-ivory/80">
                <div className="flex items-center space-x-2">
                  <span className="text-sage-muted">✦</span>
                  <span>Promotional image & PDF OCR</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sage-muted">✦</span>
                  <span>Approved, incorrect & missing logo audit</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-sage-muted">✦</span>
                  <span>Visual reference comparison</span>
                </div>
              </div>
            </div>

            {/* Capability 3 */}
            <div className="bg-plum-soft/60 rounded-sm border border-ivory/15 p-8 flex flex-col justify-between space-y-6 hover:border-rose transition-colors">
              <div className="space-y-4">
                <div className="h-10 w-10 rounded-sm bg-rose text-plum flex items-center justify-center font-serif text-lg font-bold">
                  3
                </div>
                <h3 className="font-serif text-2xl font-bold text-ivory">
                  Explainable Governance & Claim-Level Grounding
                </h3>
                <p className="text-xs sm:text-sm text-ivory/70 leading-relaxed">
                  Pair 100% deterministic rule verification with grounded Gemini semantic analysis. Every finding quotes verbatim text located by exact character offsets, while evidence is reconstructed server-side to guarantee zero hallucinations.
                </p>
              </div>

              <div className="pt-4 border-t border-ivory/10 space-y-2 text-xs text-ivory/80">
                <div className="flex items-center space-x-2">
                  <span className="text-rose">✦</span>
                  <span>Verbatim offset quote location</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-rose">✦</span>
                  <span>Human-in-the-loop review decisions</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="text-rose">✦</span>
                  <span>Immutable audit logging</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 3: AUDIENCE-ORIENTED SOLUTIONS (Sage & Dusty Rose Sections) */}
      <section id="solutions" className="py-20 sm:py-28 bg-ivory border-b border-parchment-deep">
        <div className="mx-auto max-w-6xl px-6 space-y-16">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <div className="text-xs uppercase tracking-widest text-sage font-semibold">
              Tailored Solutions
            </div>
            <h2 className="font-serif text-3xl sm:text-4xl font-bold text-ink">
              Built for Brand Custodians and Content Agencies
            </h2>
            <p className="text-sm sm:text-base text-ink-soft">
              Different team roles require different permissions and capabilities. Inkloom AI delivers role-specific interfaces for every workflow.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* For Brand Teams (Sage Surface) */}
            <div className="bg-sage-light rounded-sm border border-sage-soft p-8 sm:p-10 space-y-6 flex flex-col justify-between">
              <div className="space-y-4">
                <span className="inline-block px-3 py-1 bg-sage/15 text-sage text-xs font-semibold uppercase tracking-wider rounded-sm">
                  For Brand Teams
                </span>
                <h3 className="font-serif text-2xl sm:text-3xl font-bold text-ink">
                  Centralised Brand Repositories & Approval Governance
                </h3>
                <p className="text-sm text-ink-soft leading-relaxed">
                  Brand Managers can author enforceable guidelines, verified factual statements, prohibited phrase banks, and approved logo assets in one authoritative database.
                </p>

                <ul className="space-y-2.5 text-xs text-ink-soft pt-2">
                  <li className="flex items-start space-x-2">
                    <span className="text-sage font-bold">✓</span>
                    <span>Administer multiple brands within your enterprise organisation</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-sage font-bold">✓</span>
                    <span>Manage team members and enforce creator vs reviewer roles</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-sage font-bold">✓</span>
                    <span>Track full audit logs of submissions, analysis runs, and reviews</span>
                  </li>
                </ul>
              </div>

              <div className="pt-4 border-t border-sage-soft">
                <button
                  type="button"
                  onClick={() => handleDemoLaunch('admin')}
                  className="inline-flex items-center text-xs font-semibold text-sage hover:text-ink transition-colors group"
                >
                  <span>Experience Brand Manager Workspace</span>
                  <span className="ml-1 group-hover:translate-x-1 transition-transform">→</span>
                </button>
              </div>
            </div>

            {/* For Agencies (Dusty Rose Surface) */}
            <div className="bg-rose-soft/60 rounded-sm border border-rose/30 p-8 sm:p-10 space-y-6 flex flex-col justify-between">
              <div className="space-y-4">
                <span className="inline-block px-3 py-1 bg-rose/30 text-terracotta-dark text-xs font-semibold uppercase tracking-wider rounded-sm">
                  For Agencies & Creators
                </span>
                <h3 className="font-serif text-2xl sm:text-3xl font-bold text-ink">
                  Instant Pre-Flight Compliance & Revision Workflows
                </h3>
                <p className="text-sm text-ink-soft leading-relaxed">
                  Content creators and agency copywriters can upload marketing drafts, social briefs, or promotional artwork to receive instant, claim-level compliance feedback before client review.
                </p>

                <ul className="space-y-2.5 text-xs text-ink-soft pt-2">
                  <li className="flex items-start space-x-2">
                    <span className="text-terracotta font-bold">✓</span>
                    <span>Verify copy against client-specific rules in milliseconds</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-terracotta font-bold">✓</span>
                    <span>Receive exact character offset highlights and suggested corrections</span>
                  </li>
                  <li className="flex items-start space-x-2">
                    <span className="text-terracotta font-bold">✓</span>
                    <span>Submit versioned revisions with side-by-side run comparisons</span>
                  </li>
                </ul>
              </div>

              <div className="pt-4 border-t border-rose/30">
                <button
                  type="button"
                  onClick={() => handleDemoLaunch('creator')}
                  className="inline-flex items-center text-xs font-semibold text-terracotta hover:text-ink transition-colors group"
                >
                  <span>Experience Content Creator Workspace</span>
                  <span className="ml-1 group-hover:translate-x-1 transition-transform">→</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 4: HOW IT WORKS (Parchment & Sand Editorial Steps) */}
      <section id="how-it-works" className="py-20 sm:py-28 bg-parchment/40 border-b border-parchment-deep">
        <div className="mx-auto max-w-6xl px-6 space-y-16">
          <div className="text-center max-w-2xl mx-auto space-y-3">
            <div className="text-xs uppercase tracking-widest text-plum font-semibold">
              Step-by-Step Architecture
            </div>
            <h2 className="font-serif text-3xl sm:text-4xl font-bold text-ink">
              How Inkloom AI Verifies Every Message
            </h2>
            <p className="text-sm sm:text-base text-ink-soft">
              A transparent, repeatable workflow from raw ingestion to immutable audit trail.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 relative">
            {/* Step 1 */}
            <div className="bg-ivory rounded-sm border border-parchment-deep p-8 space-y-4 shadow-sm relative">
              <div className="text-xs font-bold text-terracotta tracking-widest uppercase">
                Step 01
              </div>
              <h3 className="font-serif text-xl font-bold text-ink">
                Ingest & Extract
              </h3>
              <p className="text-xs sm:text-sm text-ink-soft leading-relaxed">
                Submit marketing copy as plain text, promotional image uploads (PNG/JPG), scanned PDFs, or native DOCX files. Inkloom extracts text and extracts visual logo references automatically.
              </p>
            </div>

            {/* Step 2 */}
            <div className="bg-ivory rounded-sm border border-parchment-deep p-8 space-y-4 shadow-sm relative">
              <div className="text-xs font-bold text-plum tracking-widest uppercase">
                Step 02
              </div>
              <h3 className="font-serif text-xl font-bold text-ink">
                Grounded Evaluation
              </h3>
              <p className="text-xs sm:text-sm text-ink-soft leading-relaxed">
                Content is analyzed against the active brand&apos;s knowledge base. Deterministic pattern checks and grounded Gemini verification flag confirmed violations, unsupported claims, and sensitive credentials.
              </p>
            </div>

            {/* Step 3 */}
            <div className="bg-ivory rounded-sm border border-parchment-deep p-8 space-y-4 shadow-sm relative">
              <div className="text-xs font-bold text-sage tracking-widest uppercase">
                Step 03
              </div>
              <h3 className="font-serif text-xl font-bold text-ink">
                Review & Audit
              </h3>
              <p className="text-xs sm:text-sm text-ink-soft leading-relaxed">
                Authorized Compliance Reviewers inspect claim-level findings, request creator revisions, or issue final approvals. Every action is recorded in an immutable, tenant-isolated audit log.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* SECTION 5: ENTERPRISE CALL TO ACTION (Deep Plum Section) */}
      <section className="py-20 sm:py-24 bg-plum text-ivory">
        <div className="mx-auto max-w-4xl px-6 text-center space-y-8">
          <div className="space-y-4">
            <h2 className="font-serif text-3xl sm:text-4xl lg:text-5xl font-bold text-ivory">
              Ready to Secure Your Brand&apos;s Voice?
            </h2>
            <p className="text-sm sm:text-base text-ivory/80 max-w-xl mx-auto leading-relaxed">
              Explore Inkloom AI with our pre-seeded LumaCare demo or register your enterprise organisation for isolated multi-brand governance.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              to={user ? '/workspace' : '/login'}
              className="w-full sm:w-auto px-8 py-3.5 bg-terracotta text-ivory text-sm font-semibold rounded-sm hover:bg-terracotta-dark transition-colors shadow-sm"
            >
              {user ? 'Enter Inkloom Workspace →' : 'Log In to Your Workspace →'}
            </Link>

            <button
              type="button"
              onClick={() => handleDemoLaunch('reviewer')}
              className="w-full sm:w-auto px-6 py-3.5 bg-plum-soft border border-ivory/20 text-ivory text-sm font-semibold rounded-sm hover:bg-ivory hover:text-plum transition-colors"
            >
              Try Compliance Auditor Demo
            </button>
          </div>
        </div>
      </section>

      {/* SECTION 6: ABOUT & STANDARDS */}
      <section id="about" className="py-16 bg-ivory border-t border-parchment-deep text-xs text-ink-soft">
        <div className="mx-auto max-w-6xl px-6 space-y-4 text-center">
          <h4 className="font-serif text-sm font-bold text-ink uppercase tracking-wider">
            About Inkloom AI
          </h4>
          <p className="max-w-2xl mx-auto leading-relaxed">
            Inkloom AI was engineered for rigorous enterprise brand governance. Built on a hybrid architecture combining deterministic rules, multimodal document ingestion, perceptual logo verification, and grounded Gemini semantic analysis, Inkloom ensures zero hallucinated rules and 100% verifiable compliance.
          </p>
        </div>
      </section>
    </div>
  )
}
