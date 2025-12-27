import { useEffect, useCallback } from 'react'

interface MainButtonOptions {
  text: string
  onClick: () => void
  isVisible?: boolean
  isActive?: boolean
  showProgress?: boolean
}

export function useTelegramMainButton({
  text,
  onClick,
  isVisible = true,
  isActive = true,
  showProgress = false,
}: MainButtonOptions) {
  const handleClick = useCallback(() => {
    // Haptic feedback
    window.Telegram?.WebApp?.HapticFeedback?.impactOccurred('medium')
    onClick()
  }, [onClick])

  useEffect(() => {
    const mainButton = window.Telegram?.WebApp?.MainButton

    if (!mainButton) return

    mainButton.setText(text)

    if (isVisible) {
      mainButton.show()
    } else {
      mainButton.hide()
    }

    if (isActive) {
      mainButton.enable()
    } else {
      mainButton.disable()
    }

    if (showProgress) {
      mainButton.showProgress()
    } else {
      mainButton.hideProgress()
    }

    mainButton.onClick(handleClick)

    return () => {
      mainButton.offClick(handleClick)
      mainButton.hide()
    }
  }, [text, isVisible, isActive, showProgress, handleClick])
}


