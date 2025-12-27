import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'

export function useTelegramBackButton() {
  const navigate = useNavigate()
  const location = useLocation()

  useEffect(() => {
    const tg = window.Telegram?.WebApp?.BackButton

    if (!tg) return

    // Show back button if not on home page
    if (location.pathname !== '/intake' && location.pathname !== '/') {
      tg.show()
    } else {
      tg.hide()
    }

    const handleBack = () => {
      navigate(-1)
    }

    tg.onClick(handleBack)

    return () => {
      tg.offClick(handleBack)
    }
  }, [location.pathname, navigate])
}


