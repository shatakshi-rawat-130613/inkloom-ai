/**
 * Shared demo test cases for 1-click evaluation by judges and users.
 */

import type { ContentType } from '../api/types'

export interface DemoTestCase {
  id: string
  title: string
  type: ContentType
  label: string
  description: string
  content: string
}

export const DEMO_TEST_CASES: DemoTestCase[] = [
  {
    id: 'test-1',
    title: 'Test 1: Non-Compliant Ad Copy',
    type: 'advertisement',
    label: 'Test 1: Non-Compliant',
    description: 'Guaranteed acne removal in 2 days (violates GUIDE-001, FACT-002, TERM-001).',
    content:
      'Our revolutionary cream guarantees 100% acne removal in just 2 days! Buy now and get flawless skin instantly.',
  },
  {
    id: 'test-2',
    title: 'Test 2: Compliant Social Post',
    type: 'social_post',
    label: 'Test 2: Compliant',
    description: 'Friendly, reassuring approach using approved preferred terminology.',
    content:
      'Discover a simple addition to your skincare routine with LumaCare. Our cream is designed to support clearer-looking skin. Enjoy a gentle, reassuring approach to everyday skincare.',
  },
  {
    id: 'test-3',
    title: 'Test 3: Partially Compliant Post',
    type: 'social_post',
    label: 'Test 3: Partially Compliant',
    description: 'Approved terminology paired with unapproved 7-day acne reduction timeframe.',
    content:
      'Make your skincare routine simpler with LumaCare. Our cream supports clearer-looking skin and helps reduce acne within 7 days. Experience a gentle approach to everyday skincare.',
  },
]
