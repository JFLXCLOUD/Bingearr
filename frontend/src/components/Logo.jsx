export default function Logo() {
  return (
    <div className="logo">
      <div className="logo-mark">
        <svg viewBox="0 0 32 32" width="30" height="30" aria-hidden="true">
          <defs>
            <linearGradient id="logo-grad" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#8b5cff" />
              <stop offset="1" stopColor="#d65cff" />
            </linearGradient>
          </defs>
          <rect x="1.5" y="1.5" width="29" height="29" rx="9" fill="url(#logo-grad)" />
          <path d="M12.8 10.4 L22 16 L12.8 21.6 Z" fill="#fff" />
        </svg>
      </div>
      <div className="logo-word">
        Binge<span>arr</span>
      </div>
    </div>
  );
}
