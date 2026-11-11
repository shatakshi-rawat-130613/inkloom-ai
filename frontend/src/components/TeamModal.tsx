/**
 * Team & Organisation Member Management Modal.
 * Enables Brand Managers to inspect existing team members and invite/provision
 * Content Creators (Editors) and Compliance Reviewers directly into their organisation.
 */

import { useEffect, useState } from 'react'
import { api, ApiError } from '../api/client'
import type { UserResponse, UserRole } from '../api/types'
import { useAuth } from '../context/AuthContext'

interface TeamModalProps {
  isOpen: boolean
  onClose: () => void
}

export function TeamModal({ isOpen, onClose }: TeamModalProps) {
  const { user } = useAuth()
  const [members, setMembers] = useState<UserResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  // Member invitation form state
  const [isInviting, setIsInviting] = useState(false)
  const [newDisplayName, setNewDisplayName] = useState('')
  const [newEmail, setNewEmail] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [newRole, setNewRole] = useState<UserRole>('editor')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const isAdmin = user?.role === 'admin'

  useEffect(() => {
    if (!isOpen) return
    let active = true

    api.listMembers()
      .then((list) => {
        if (active) {
          setMembers(list)
          setLoading(false)
        }
      })
      .catch((err) => {
        if (active) {
          if (err instanceof ApiError) {
            setError(err.message)
          } else {
            setError('Failed to load organisation team members.')
          }
          setLoading(false)
        }
      })

    return () => {
      active = false
    }
  }, [isOpen])

  const refreshMembers = async () => {
    try {
      setLoading(true)
      const list = await api.listMembers()
      setMembers(list)
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Failed to load organisation team members.')
      }
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  const handleCreateMember = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setIsSubmitting(true)

    try {
      const created = await api.createMember({
        display_name: newDisplayName.trim(),
        email: newEmail.trim().toLowerCase(),
        password: newPassword,
        role: newRole,
      })
      setSuccess(`Successfully provisioned member: ${created.display_name} (${created.role})`)
      setNewDisplayName('')
      setNewEmail('')
      setNewPassword('')
      setIsInviting(false)
      await refreshMembers()
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.message)
      } else {
        setError('Failed to provision new member.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  const getRoleBadge = (role: UserRole) => {
    switch (role) {
      case 'admin':
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-sage/10 text-sage border border-sage/20 rounded">Brand Manager</span>
      case 'editor':
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-ink/5 text-ink border border-parchment-deep rounded">Creator (Editor)</span>
      case 'reviewer':
        return <span className="px-2 py-0.5 text-[10px] font-semibold bg-ochre/10 text-ochre border border-ochre/30 rounded">Compliance Reviewer</span>
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 backdrop-blur-xs p-4">
      <div className="w-full max-w-2xl bg-ivory border border-parchment-deep rounded-sm shadow-xl overflow-hidden animate-fadeIn">
        <div className="px-6 pt-6 pb-4 border-b border-parchment-deep flex items-baseline justify-between">
          <div>
            <h2 className="font-serif text-xl font-bold text-ink">Organisation Team & Access</h2>
            <p className="text-xs text-ink-soft mt-1">
              Organisation: <strong className="text-ink">{user?.organisation_name || 'Active Organisation'}</strong>
            </p>
          </div>
          <button onClick={onClose} className="text-ink-soft hover:text-ink text-sm px-2 py-1">
            ✕
          </button>
        </div>

        <div className="p-6 space-y-6 max-h-[75vh] overflow-y-auto">
          {error && (
            <div className="p-3 bg-terracotta/10 border border-terracotta/30 text-terracotta text-xs rounded-sm">
              {error}
            </div>
          )}

          {success && (
            <div className="p-3 bg-sage/10 border border-sage/30 text-sage text-xs rounded-sm">
              {success}
            </div>
          )}

          {/* Members List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs uppercase tracking-wider font-semibold text-ink-soft">
                Members ({members.length})
              </span>
              {isAdmin && !isInviting && (
                <button
                  type="button"
                  onClick={() => setIsInviting(true)}
                  className="px-3 py-1 bg-ink text-ivory text-xs font-semibold uppercase tracking-wider rounded-sm hover:bg-sage transition-colors"
                >
                  + Add Member
                </button>
              )}
            </div>

            {loading ? (
              <div className="py-6 text-center text-xs text-ink-soft">Loading team directory...</div>
            ) : (
              <div className="border border-parchment-deep rounded-sm divide-y divide-parchment-deep overflow-hidden">
                {members.map((m) => (
                  <div key={m.id} className="p-3 bg-ivory flex items-center justify-between">
                    <div>
                      <div className="text-sm font-semibold text-ink flex items-center space-x-2">
                        <span>{m.display_name}</span>
                        {m.id === user?.id && (
                          <span className="text-[10px] text-sage font-mono">(You)</span>
                        )}
                      </div>
                      <div className="text-xs text-ink-soft">{m.email}</div>
                    </div>
                    <div>{getRoleBadge(m.role)}</div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Provision New Member Form (Admin only) */}
          {isAdmin && isInviting && (
            <form onSubmit={handleCreateMember} className="p-4 bg-parchment/40 border border-parchment-deep rounded-sm space-y-4">
              <div className="flex items-baseline justify-between border-b border-parchment-deep pb-2">
                <span className="text-xs font-semibold text-ink uppercase tracking-wider">
                  Provision New Team Member
                </span>
                <button
                  type="button"
                  onClick={() => setIsInviting(false)}
                  className="text-xs text-ink-soft hover:text-ink"
                >
                  Cancel
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-ink uppercase tracking-wider mb-1">
                    Display Name
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Jordan Lee"
                    value={newDisplayName}
                    onChange={(e) => setNewDisplayName(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-ink uppercase tracking-wider mb-1">
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    placeholder="jordan@company.com"
                    value={newEmail}
                    onChange={(e) => setNewEmail(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-semibold text-ink uppercase tracking-wider mb-1">
                    Temporary Password
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    placeholder="Min 8 characters"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
                    className="w-full px-3 py-1.5 text-xs bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-ink uppercase tracking-wider mb-1">
                    Assigned Role
                  </label>
                  <select
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value as UserRole)}
                    className="w-full px-3 py-1.5 text-xs bg-ivory border border-parchment-deep rounded-sm focus:outline-none focus:border-sage"
                  >
                    <option value="editor">Content Creator (Editor)</option>
                    <option value="reviewer">Compliance Reviewer</option>
                    <option value="admin">Brand Manager (Admin)</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end pt-2">
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-ink text-ivory text-xs font-bold uppercase tracking-wider rounded-sm hover:bg-sage transition-colors disabled:opacity-50"
                >
                  {isSubmitting ? 'Provisioning...' : 'Provision Member'}
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
