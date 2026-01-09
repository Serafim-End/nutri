import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReviewsPage } from './ReviewsPage'
import * as api from '@/lib/api'

// Mock the API module
vi.mock('@/lib/api', () => ({
  adminApi: {
    getReviews: vi.fn(),
    hideReview: vi.fn(),
    showReview: vi.fn(),
    deleteReview: vi.fn(),
  },
}))

const mockReviews = [
  {
    id: 'review-1',
    booking_id: 'booking-123',
    rating: 5,
    text: 'Great nutritionist!',
    nutritionist_id: 'nutri-1',
    nutritionist_name: 'John Doe',
    client_id: 'client-1',
    is_hidden: false,
    is_problematic: false,
    created_at: '2024-01-15T10:00:00Z',
  },
  {
    id: 'review-2',
    booking_id: 'booking-456',
    rating: 2,
    text: 'Not satisfied',
    nutritionist_id: 'nutri-2',
    nutritionist_name: 'Jane Smith',
    client_id: 'client-2',
    is_hidden: false,
    is_problematic: true,
    created_at: '2024-01-16T10:00:00Z',
  },
  {
    id: 'review-3',
    booking_id: 'booking-789',
    rating: 4,
    text: null,
    nutritionist_id: 'nutri-3',
    nutritionist_name: 'Bob Wilson',
    client_id: 'client-3',
    is_hidden: true,
    is_problematic: false,
    created_at: '2024-01-17T10:00:00Z',
  },
]

function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })
}

function renderWithProviders(ui: React.ReactElement) {
  const queryClient = createTestQueryClient()
  return render(
    <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
  )
}

describe('ReviewsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Reviews List', () => {
    it('displays loading state initially', () => {
      vi.mocked(api.adminApi.getReviews).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      renderWithProviders(<ReviewsPage />)

      // Check for loading spinner (the component uses a div with animate-spin class)
      const loadingElement = document.querySelector('.animate-spin')
      expect(loadingElement).toBeInTheDocument()
    })

    it('displays error message when API fails', async () => {
      vi.mocked(api.adminApi.getReviews).mockRejectedValue(
        new Error('API Error')
      )

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('Failed to load reviews')).toBeInTheDocument()
      })
    })

    it('displays empty state when no reviews', async () => {
      vi.mocked(api.adminApi.getReviews).mockResolvedValue({
        reviews: [],
      })

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('No reviews found')).toBeInTheDocument()
        expect(
          screen.getByText('No reviews have been submitted yet.')
        ).toBeInTheDocument()
      })
    })

    it('displays reviews list with correct data', async () => {
      vi.mocked(api.adminApi.getReviews).mockResolvedValue({
        reviews: mockReviews,
      })

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('Great nutritionist!')).toBeInTheDocument()
        expect(screen.getByText('Not satisfied')).toBeInTheDocument()
        expect(screen.getByText('John Doe')).toBeInTheDocument()
        expect(screen.getByText('Jane Smith')).toBeInTheDocument()
      })

      // Check ratings are displayed
      expect(screen.getByText('5')).toBeInTheDocument()
      expect(screen.getByText('2')).toBeInTheDocument()
      expect(screen.getByText('4')).toBeInTheDocument()
    })

    it('displays "No text provided" for reviews without text', async () => {
      vi.mocked(api.adminApi.getReviews).mockResolvedValue({
        reviews: [mockReviews[2]], // Review with null text
      })

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('No text provided')).toBeInTheDocument()
      })
    })

    it('displays status badges correctly', async () => {
      vi.mocked(api.adminApi.getReviews).mockResolvedValue({
        reviews: mockReviews,
      })

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('Visible')).toBeInTheDocument()
        expect(screen.getByText('Problematic')).toBeInTheDocument()
        expect(screen.getByText('Hidden')).toBeInTheDocument()
      })
    })

    it('filters reviews by rating', async () => {
      const user = userEvent.setup()

      vi.mocked(api.adminApi.getReviews).mockImplementation((params) => {
        if (params?.rating_lte === 3) {
          return Promise.resolve({
            reviews: [mockReviews[1]], // Only low-rated review
          })
        }
        return Promise.resolve({ reviews: mockReviews })
      })

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('Great nutritionist!')).toBeInTheDocument()
      })

      const lowRatingButton = screen.getByRole('button', {
        name: 'Rating ≤ 3',
      })
      await user.click(lowRatingButton)

      await waitFor(() => {
        expect(api.adminApi.getReviews).toHaveBeenCalledWith({
          rating_lte: 3,
        })
        expect(screen.getByText('Not satisfied')).toBeInTheDocument()
        expect(screen.queryByText('Great nutritionist!')).not.toBeInTheDocument()
      })
    })
  })

  describe('Hide/Show Actions', () => {
    it('calls hideReview API when Hide button is clicked', async () => {
      const user = userEvent.setup()

      vi.mocked(api.adminApi.getReviews).mockResolvedValue({
        reviews: [mockReviews[0]], // Visible review
      })
      vi.mocked(api.adminApi.hideReview).mockResolvedValue({
        message: 'Review hidden',
      })

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('Great nutritionist!')).toBeInTheDocument()
      })

      const hideButton = screen.getByRole('button', { name: 'Hide' })
      await user.click(hideButton)

      await waitFor(() => {
        expect(api.adminApi.hideReview).toHaveBeenCalledWith('review-1')
      })
    })

    it('calls showReview API when Show button is clicked', async () => {
      const user = userEvent.setup()

      vi.mocked(api.adminApi.getReviews).mockResolvedValue({
        reviews: [mockReviews[2]], // Hidden review
      })
      vi.mocked(api.adminApi.showReview).mockResolvedValue({
        message: 'Review shown',
      })

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('Show')).toBeInTheDocument()
      })

      const showButton = screen.getByRole('button', { name: 'Show' })
      await user.click(showButton)

      await waitFor(() => {
        expect(api.adminApi.showReview).toHaveBeenCalledWith('review-3')
      })
    })

    it('disables Hide button while mutation is pending', async () => {
      const user = userEvent.setup()

      vi.mocked(api.adminApi.getReviews).mockResolvedValue({
        reviews: [mockReviews[0]],
      })
      vi.mocked(api.adminApi.hideReview).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('Great nutritionist!')).toBeInTheDocument()
      })

      const hideButton = screen.getByRole('button', { name: 'Hide' })
      await user.click(hideButton)

      await waitFor(() => {
        expect(hideButton).toBeDisabled()
      })
    })

    it('refetches reviews after successful hide action', async () => {
      const user = userEvent.setup()

      vi.mocked(api.adminApi.getReviews).mockResolvedValue({
        reviews: [mockReviews[0]],
      })
      vi.mocked(api.adminApi.hideReview).mockResolvedValue({
        message: 'Review hidden',
      })

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('Great nutritionist!')).toBeInTheDocument()
      })

      const hideButton = screen.getByRole('button', { name: 'Hide' })
      await user.click(hideButton)

      await waitFor(() => {
        // Should refetch after mutation
        expect(api.adminApi.getReviews).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Delete Action', () => {
    beforeEach(() => {
      // Mock window.confirm to return true
      window.confirm = vi.fn(() => true)
    })

    it('calls deleteReview API when Delete button is clicked and confirmed', async () => {
      const user = userEvent.setup()

      vi.mocked(api.adminApi.getReviews).mockResolvedValue({
        reviews: [mockReviews[0]],
      })
      vi.mocked(api.adminApi.deleteReview).mockResolvedValue({
        message: 'Review deleted successfully',
      })

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('Great nutritionist!')).toBeInTheDocument()
      })

      const deleteButton = screen.getByRole('button', { name: 'Delete' })
      await user.click(deleteButton)

      await waitFor(() => {
        expect(window.confirm).toHaveBeenCalledWith(
          'Are you sure you want to delete this review? This action cannot be undone.'
        )
        expect(api.adminApi.deleteReview).toHaveBeenCalledWith('review-1')
      })
    })

    it('does not call deleteReview API when user cancels confirmation', async () => {
      const user = userEvent.setup()

      // Mock window.confirm to return false
      window.confirm = vi.fn(() => false)

      vi.mocked(api.adminApi.getReviews).mockResolvedValue({
        reviews: [mockReviews[0]],
      })

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('Great nutritionist!')).toBeInTheDocument()
      })

      const deleteButton = screen.getByRole('button', { name: 'Delete' })
      await user.click(deleteButton)

      await waitFor(() => {
        expect(window.confirm).toHaveBeenCalled()
        expect(api.adminApi.deleteReview).not.toHaveBeenCalled()
      })
    })

    it('disables Delete button while mutation is pending', async () => {
      const user = userEvent.setup()

      vi.mocked(api.adminApi.getReviews).mockResolvedValue({
        reviews: [mockReviews[0]],
      })
      vi.mocked(api.adminApi.deleteReview).mockImplementation(
        () => new Promise(() => {}) // Never resolves
      )

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('Great nutritionist!')).toBeInTheDocument()
      })

      const deleteButton = screen.getByRole('button', { name: 'Delete' })
      await user.click(deleteButton)

      await waitFor(() => {
        expect(deleteButton).toBeDisabled()
      })
    })

    it('refetches reviews after successful delete action', async () => {
      const user = userEvent.setup()

      vi.mocked(api.adminApi.getReviews).mockResolvedValue({
        reviews: [mockReviews[0]],
      })
      vi.mocked(api.adminApi.deleteReview).mockResolvedValue({
        message: 'Review deleted successfully',
      })

      renderWithProviders(<ReviewsPage />)

      await waitFor(() => {
        expect(screen.getByText('Great nutritionist!')).toBeInTheDocument()
      })

      const deleteButton = screen.getByRole('button', { name: 'Delete' })
      await user.click(deleteButton)

      await waitFor(() => {
        // Should refetch after mutation
        expect(api.adminApi.getReviews).toHaveBeenCalledTimes(2)
      })
    })
  })
})
