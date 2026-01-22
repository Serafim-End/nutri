import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

const STORAGE_KEY = 'start_param_handled'

export function useStartParamRedirect() {
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const tg = window.Telegram?.WebApp
    const startParam = tg?.initDataUnsafe?.start_param
    if (!startParam || typeof startParam !== 'string') return

    const lastHandled = sessionStorage.getItem(STORAGE_KEY)
    if (lastHandled === startParam) return

    const match = startParam.match(/^payment_(success|fail)_(.+)$/)
    if (!match) return

    const status = match[1]
    const bookingId = match[2]
    const target = status === 'success'
      ? `/payment/success?order_id=${bookingId}`
      : `/payment/fail?order_id=${bookingId}`

    sessionStorage.setItem(STORAGE_KEY, startParam)
    if (location.pathname + location.search !== target) {
      navigate(target, { replace: true })
    }
  }, [location.pathname, location.search, navigate])
}
