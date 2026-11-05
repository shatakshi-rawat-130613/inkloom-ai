/**
 * Editorial footer for Inkloom AI.
 */

import { Link } from 'react-router-dom'

export function Footer() {
  return (
    <footer className="mt-20 border-t border-parchment-deep bg-ivory text-ink-soft">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-1">
            <p className="font-serif text-base font-semibold text-ink">Inkloom AI</p>
            <p className="text-xs text-ink-soft max-w-md">
              Intelligent brand-governance platform evaluating content against approved brand identity,
              guidelines, facts, and messaging standards. Final approval remains with human reviewers.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-6 text-xs">
            <Link to="/" className="hover:text-ink transition-colors">
              Brand Workspace
            </Link>
            <Link to="/submissions/new" className="hover:text-ink transition-colors">
              Submit Content
            </Link>
            <Link to="/terms" className="hover:text-ink transition-colors">
              Terms of Service
            </Link>
            <Link to="/privacy" className="hover:text-ink transition-colors">
              Privacy Policy
            </Link>
          </div>
        </div>

        <div className="mt-8 pt-6 border-t border-parchment-deep/60 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-ink-soft">
          <p>
            LumaCare is a fictional demonstration brand. All guidelines and product statements are illustrative.
          </p>
          <p>Inkloom AI Hackathon MVP (Round 2)</p>
        </div>
      </div>
    </footer>
  )
}
