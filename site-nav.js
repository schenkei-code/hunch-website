(() => {
  const toggles = document.querySelectorAll('[data-mobile-menu-toggle]')

  for (const toggle of toggles) {
    const targetID = toggle.getAttribute('aria-controls')
    const menu = targetID ? document.getElementById(targetID) : null
    if (!menu) continue

    const headerNav = toggle.closest('#nav') || toggle.closest('nav')
    const headerPeers = Array.from(toggle.parentElement?.children || []).filter((node) => node !== toggle)
    const pageRegions = Array.from(document.body.children).filter((node) => {
      return node !== headerNav && node !== menu && node.tagName !== 'SCRIPT'
    })
    const inertState = new Map()

    const setBackgroundInert = (active) => {
      const regions = [...headerPeers, ...pageRegions]
      if (active) {
        for (const region of regions) {
          if (inertState.has(region)) continue
          inertState.set(region, region.hasAttribute('inert'))
          region.setAttribute('inert', '')
        }
        return
      }
      for (const [region, wasInert] of inertState) {
        if (!wasInert) region.removeAttribute('inert')
      }
      inertState.clear()
    }

    const focusable = () => {
      const menuNodes = Array.from(menu.querySelectorAll('a[href], button')).filter((node) => {
        return !node.hasAttribute('disabled') && node.getAttribute('aria-hidden') !== 'true'
      })
      return [toggle, ...menuNodes]
    }

    const close = (restoreFocus = false) => {
      menu.hidden = true
      toggle.setAttribute('aria-expanded', 'false')
      document.documentElement.classList.remove('mobile-menu-open')
      document.body.classList.remove('mobile-menu-open')
      setBackgroundInert(false)
      if (restoreFocus) toggle.focus()
    }

    const open = () => {
      menu.hidden = false
      toggle.setAttribute('aria-expanded', 'true')
      document.documentElement.classList.add('mobile-menu-open')
      document.body.classList.add('mobile-menu-open')
      setBackgroundInert(true)
      const firstMenuControl = focusable()[1]
      if (firstMenuControl) firstMenuControl.focus()
      else toggle.focus()
    }

    const focusHashTarget = (url) => {
      let targetIDFromHash = url.hash.slice(1)
      try {
        targetIDFromHash = decodeURIComponent(targetIDFromHash)
      } catch {
        // Keep the literal fragment when it is not valid percent-encoding.
      }
      const target = document.getElementById(targetIDFromHash)
      if (!target) return false

      close(false)
      if (window.location.hash !== url.hash) {
        try {
          window.history.pushState(window.history.state, '', url.hash)
        } catch {
          window.location.hash = url.hash
        }
      }

      const needsTemporaryTabIndex = !target.hasAttribute('tabindex')
      if (needsTemporaryTabIndex) target.setAttribute('tabindex', '-1')
      target.focus({ preventScroll: true })
      target.scrollIntoView({ block: 'start' })
      if (needsTemporaryTabIndex) {
        target.addEventListener('blur', () => target.removeAttribute('tabindex'), { once: true })
      }
      return true
    }

    toggle.addEventListener('click', () => {
      if (toggle.getAttribute('aria-expanded') === 'true') close(true)
      else open()
    })

    menu.addEventListener('click', (event) => {
      const eventTarget = event.target instanceof Element ? event.target : null
      const link = eventTarget?.closest('a[href]')
      if (!link) return

      const url = new URL(link.href, document.baseURI)
      const sameDocumentHash = url.origin === window.location.origin
        && url.pathname === window.location.pathname
        && url.search === window.location.search
        && Boolean(url.hash)
      if (sameDocumentHash) {
        if (focusHashTarget(url)) {
          event.preventDefault()
          return
        }
      }
      close(true)
    })

    document.addEventListener('keydown', (event) => {
      if (menu.hidden) return
      if (event.key === 'Escape') {
        event.preventDefault()
        close(true)
        return
      }
      if (event.key !== 'Tab') return
      const nodes = focusable()
      if (!nodes.length) return
      const first = nodes[0]
      const last = nodes[nodes.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    })

    const desktop = window.matchMedia('(min-width: 901px)')
    const closeAtDesktop = (event) => {
      if (!event.matches || menu.hidden) return
      close(false)
      const desktopFocusTarget = headerNav?.querySelector('.logo, .nav-links a, .nav-cta')
      desktopFocusTarget?.focus()
    }
    desktop.addEventListener?.('change', closeAtDesktop)
    closeAtDesktop(desktop)
  }
})()
