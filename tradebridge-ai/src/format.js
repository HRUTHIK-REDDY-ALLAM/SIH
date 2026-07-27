const fmt = new Intl.NumberFormat('en-IN')

export const inr = (n) => '₹' + fmt.format(n)

export const cx = (...parts) => parts.filter(Boolean).join(' ')

export const mmss = (s) => `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
