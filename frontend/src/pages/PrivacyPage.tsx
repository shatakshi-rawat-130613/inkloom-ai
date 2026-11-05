/**
 * Privacy Policy Page.
 * Real, appropriately scoped privacy disclosure for an enterprise AI brand-governance platform.
 */

export function PrivacyPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-12 space-y-8">
      <div className="space-y-2 border-b border-parchment-deep pb-6">
        <span className="text-xs uppercase tracking-widest text-sage font-medium">Data Protection</span>
        <h1 className="font-serif text-3xl font-bold text-ink">Privacy Policy</h1>
        <p className="text-xs text-ink-soft">Effective Date: 5 November 2026</p>
      </div>

      <div className="space-y-6 text-sm text-ink-soft leading-relaxed font-sans">
        <section className="space-y-2">
          <h2 className="font-serif text-lg font-semibold text-ink">1. Information We Collect</h2>
          <p>
            Inkloom AI collects information submitted directly by users to perform brand compliance evaluations,
            including:
          </p>
          <ul className="list-disc list-inside space-y-1 pl-2">
            <li>Content titles, content type classifications, and drafted marketing copy.</li>
            <li>Author and reviewer display names provided during submission and review workflows.</li>
            <li>Brand knowledge data including guidelines, approved facts, and approved terminology.</li>
            <li>Immutable audit event records (timestamps, actions taken, version history).</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="font-serif text-lg font-semibold text-ink">2. How Information is Processed</h2>
          <p>
            Content submitted for analysis is processed via our backend rule evaluation engine and passed securely to
            Google Gemini API solely for the purpose of generating contextual brand compliance assessments and structured
            explanations.
          </p>
          <p>
            In accordance with enterprise data protection agreements, submitted content is not used to train or improve
            commercial foundation models.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="font-serif text-lg font-semibold text-ink">3. Data Retention and Versioning</h2>
          <p>
            To maintain historical governance integrity, Inkloom AI retains version snapshots, analysis results, and
            reviewer comments in an append-only persistence layer. Organisations can track their compliance evolution
            and audit trails over time.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="font-serif text-lg font-semibold text-ink">4. Third-Party Services and Infrastructure</h2>
          <p>
            Inkloom AI utilizes verified cloud infrastructure partners:
          </p>
          <ul className="list-disc list-inside space-y-1 pl-2">
            <li>Supabase (managed PostgreSQL persistence with TLS encryption in transit and at rest).</li>
            <li>Render (backend API hosting and execution environment).</li>
            <li>Vercel (static edge delivery for the web client).</li>
            <li>Google Cloud (Gemini API for inference processing).</li>
          </ul>
        </section>

        <section className="space-y-2">
          <h2 className="font-serif text-lg font-semibold text-ink">5. Security and Data Protection</h2>
          <p>
            All network communication with Inkloom AI is secured via modern Transport Layer Security (TLS). API secrets
            and database credentials reside strictly within encrypted server-side environment variables and are never
            exposed to client applications.
          </p>
        </section>

        <section className="space-y-2">
          <h2 className="font-serif text-lg font-semibold text-ink">6. Contact and Inquiries</h2>
          <p>
            For privacy inquiries or data governance requests related to Inkloom AI, please consult the official
            hackathon project repository at{' '}
            <a
              href="https://github.com/shatakshi-rawat-130613/inkloom-ai"
              target="_blank"
              rel="noreferrer"
              className="text-sage hover:underline"
            >
              github.com/shatakshi-rawat-130613/inkloom-ai
            </a>
            .
          </p>
        </section>
      </div>
    </div>
  )
}
