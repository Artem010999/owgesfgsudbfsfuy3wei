import { useCallback, useEffect, useRef, useState } from 'react';

const HOLD_MS = 2000;
const GRID_COLS = 40;
const GRID_ROWS = 25; // 40 * 25 = 1000 tiles
const STEP_DELAY = 18; // ms per diagonal step

const API_BASE = import.meta.env.VITE_BACKEND_URL ?? 'http://127.0.0.1:8000';

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}

function useResizeObserver(targetRef, callback) {
  useEffect(() => {
    if (!targetRef.current) return;
    const observer = new ResizeObserver(() => callback());
    observer.observe(targetRef.current);
    return () => observer.disconnect();
  }, [targetRef, callback]);
}

function Tiles({ containerRef, active }) {
  const [tiles, setTiles] = useState([]);

  const rebuild = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const tileWidth = rect.width / GRID_COLS;
    const tileHeight = rect.height / GRID_ROWS;
    const overlap = 1;
    const next = [];
    for (let y = 0; y < GRID_ROWS; y++) {
      for (let x = 0; x < GRID_COLS; x++) {
        const diagIndex = x + (GRID_ROWS - 1 - y);
        const delay = diagIndex * STEP_DELAY;
        next.push({
          key: `${x}-${y}`,
          left: Math.floor(x * tileWidth) - overlap / 2,
          top: Math.floor(y * tileHeight) - overlap / 2,
          width: Math.ceil(tileWidth) + overlap,
          height: Math.ceil(tileHeight) + overlap,
          delay,
          dx: `${((Math.random() * 2 - 1) * 240).toFixed(1)}px`,
          dy: `${(-160 - Math.random() * 200).toFixed(1)}px`,
          rot: `${((Math.random() * 2 - 1) * 180).toFixed(1)}deg`,
        });
      }
    }
    setTiles(next);
  }, [containerRef]);

  useEffect(() => {
    rebuild();
  }, [rebuild]);

  useResizeObserver(containerRef, rebuild);

  return (
    <div className="tiles" aria-hidden="true">
      {tiles.map((tile) => (
        <div
          key={tile.key}
          className={`tile${active ? ' fly' : ''}`}
          style={{
            left: `${tile.left}px`,
            top: `${tile.top}px`,
            width: `${tile.width}px`,
            height: `${tile.height}px`,
            '--delay': `${tile.delay}ms`,
            '--dx': tile.dx,
            '--dy': tile.dy,
            '--rot': tile.rot,
          }}
        />
      ))}
    </div>
  );
}

function Overlay({ onFinished }) {
  const overlayRef = useRef(null);
  const contentRef = useRef(null);
  const progressRef = useRef(null);
  const mainRef = useRef(null);
  const [flying, setFlying] = useState(false);
  const [holding, setHolding] = useState(false);

  useEffect(() => {
    mainRef.current = document.getElementById('main-content');
  }, []);

  useEffect(() => {
    let raf = 0;
    let startTs = 0;

    const update = () => {
      if (!holding) return;
      const elapsed = performance.now() - startTs;
      const ratio = clamp(elapsed / HOLD_MS, 0, 1);
      if (progressRef.current) {
        progressRef.current.style.transform = `translateX(${(-100 + ratio * 100).toFixed(2)}%)`;
      }
      if (elapsed >= HOLD_MS) {
        setHolding(false);
        setFlying(true);
        if (contentRef.current) contentRef.current.classList.add('fade-out');

        const maxDelay = (GRID_COLS - 1 + GRID_ROWS - 1) * STEP_DELAY;
        const duration = 1200;
        const total = maxDelay + duration + 120;
        setTimeout(() => {
          onFinished?.();
          setFlying(false);
          if (mainRef.current) mainRef.current.focus();
        }, total);
        return;
      }
      raf = requestAnimationFrame(update);
    };

    if (holding) {
      startTs = performance.now();
      if (progressRef.current) progressRef.current.style.transform = 'translateX(-100%)';
      raf = requestAnimationFrame(update);
    }

    return () => {
      if (raf) cancelAnimationFrame(raf);
    };
  }, [holding, onFinished]);

  const start = (event) => {
    event.preventDefault();
    if (!holding) setHolding(true);
  };

  const cancel = () => {
    if (!holding) return;
    setHolding(false);
    if (progressRef.current) progressRef.current.style.transform = 'translateX(-100%)';
  };

  useEffect(() => {
    window.addEventListener('mouseup', cancel);
    window.addEventListener('touchend', cancel);
    window.addEventListener('touchcancel', cancel);
    return () => {
      window.removeEventListener('mouseup', cancel);
      window.removeEventListener('touchend', cancel);
      window.removeEventListener('touchcancel', cancel);
    };
  }, [holding]);

  return (
    <div id="intro-overlay" aria-modal="true" role="dialog" ref={overlayRef}>
      <div className="overlay-bg" aria-hidden="true" />
      <div className="tunnel" aria-hidden="true">
        {Array.from({ length: 6 }).map((_, i) => (
          <span
            key={i}
            style={{
              '--delay': `${i * 1330}ms`,
              '--rot': `${(i % 3 - 1) * 2}deg`,
            }}
          />
        ))}
      </div>
      <Tiles containerRef={overlayRef} active={flying} />
      <div className="overlay-content" ref={contentRef}>
        <div className="overlay-text">
          <p className="line-1">
            В поисках <em>рабочего</em> вайба?
          </p>
          <p className="line-2">Тогда ты по адресу!</p>
        </div>
        <button
          id="hold-button"
          type="button"
          aria-label="Удерживай 2 секунды, чтобы продолжить"
          onMouseDown={start}
          onTouchStart={start}
        >
          Погнали!
          <span className="hold-progress" ref={progressRef} aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}

function ChatLog({ items }) {
  return (
    <div className="chat-log">
      {items.map((message, index) => (
        <div key={index} className={`chat-msg ${message.role === 'bot' ? 'bot' : 'user'}`}>
          {message.text}
        </div>
      ))}
    </div>
  );
}

function ChatInput({ onSend }) {
  const [value, setValue] = useState('');

  return (
    <div className="chat-input-row">
      <input
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Напишите сообщение..."
        onKeyDown={(event) => {
          if (event.key === 'Enter') {
            onSend(value);
            setValue('');
          }
        }}
      />
      <button
        type="button"
        onClick={() => {
          onSend(value);
          setValue('');
        }}
      >
        Отправить
      </button>
    </div>
  );
}

function CarouselContent({ index }) {
  const items = [1, 2, 3, 4, 5, 6, 7].map((n) => (
    <div
      key={n}
      style={{
        opacity: 0.92,
        border: '1px solid #1a1a1a',
        borderRadius: 12,
        padding: 20,
        minWidth: 240,
      }}
    >
      <h3 style={{ marginTop: 0 }}>Рабочая карточка сотрудника — {n}</h3>
      <p style={{ color: '#bdbdbd' }}>Здесь будет компонент №{n}.</p>
    </div>
  ));
  return items[index];
}

function NoisePlaceholder() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let raf = 0;

    const resize = () => {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
    };

    const draw = () => {
      const { width, height } = canvas;
      if (width === 0 || height === 0) {
        raf = requestAnimationFrame(draw);
        return;
      }
      const imgData = ctx.createImageData(width, height);
      for (let i = 0; i < imgData.data.length; i += 4) {
        const value = Math.random() * 255;
        imgData.data[i] = value;
        imgData.data[i + 1] = value;
        imgData.data[i + 2] = value;
        imgData.data[i + 3] = 35 + Math.random() * 60;
      }
      ctx.putImageData(imgData, 0, 0);
      raf = requestAnimationFrame(draw);
    };

    resize();
    raf = requestAnimationFrame(draw);
    window.addEventListener('resize', resize);
    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div className="noise-placeholder">
      <canvas className="noise-canvas" ref={canvasRef} />
      <div className="rendering-label">Рендерим вайб…</div>
    </div>
  );
}

function ImagePanel({ url }) {
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    setLoaded(false);
  }, [url]);

  return (
    <div className="image-panel">
      {!loaded && <NoisePlaceholder />}
      {url ? (
        <img
          src={url}
          onLoad={() => setLoaded(true)}
          className={loaded ? 'visible' : ''}
          alt="Визуализация рабочего вайба"
        />
      ) : (
        <div className="rendering-label">Ожидаем картинку…</div>
      )}
    </div>
  );
}

function SettingsModal() {
  const [open, setOpen] = useState(false);
  const [sounds, setSounds] = useState([
    { id: 'rain', name: 'Дождь', enabled: true, volume: 60 },
    { id: 'cafe', name: 'Кофейня', enabled: false, volume: 40 },
    { id: 'white', name: 'White Noise', enabled: false, volume: 50 },
  ]);

  useEffect(() => {
    const handler = () => setOpen(true);
    window.addEventListener('open-settings', handler);
    return () => window.removeEventListener('open-settings', handler);
  }, []);

  if (!open) return null;

  return (
    <div
      style={{
        position: 'fixed',
        inset: 0,
        display: 'grid',
        placeItems: 'center',
        background: 'rgba(0,0,0,0.5)',
        zIndex: 80,
      }}
      onClick={() => setOpen(false)}
    >
      <div
        style={{
          minWidth: 320,
          background: '#0b0b0b',
          border: '1px solid #1a1a1a',
          borderRadius: 12,
          padding: 14,
        }}
        onClick={(event) => event.stopPropagation()}
      >
        <h3 style={{ marginTop: 0 }}>Настройки звуков</h3>
        <div style={{ display: 'grid', gap: 10 }}>
          {sounds.map((sound) => (
            <div
              key={sound.id}
              style={{
                display: 'grid',
                gridTemplateColumns: '1fr auto',
                gap: 8,
                alignItems: 'center',
              }}
            >
              <div>
                <div style={{ fontWeight: 600 }}>{sound.name}</div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={sound.volume}
                  onChange={(event) =>
                    setSounds((prev) =>
                      prev.map((item) =>
                        item.id === sound.id
                          ? { ...item, volume: Number(event.target.value) }
                          : item,
                      ),
                    )
                  }
                />
              </div>
              <label style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                <input
                  type="checkbox"
                  checked={sound.enabled}
                  onChange={(event) =>
                    setSounds((prev) =>
                      prev.map((item) =>
                        item.id === sound.id
                          ? { ...item, enabled: event.target.checked }
                          : item,
                      ),
                    )
                  }
                />
                Вкл
              </label>
            </div>
          ))}
        </div>
        <div style={{ display: 'grid', gridAutoFlow: 'column', gap: 8, marginTop: 12, justifyContent: 'end' }}>
          <button className="menu-toggle" type="button" onClick={() => setOpen(false)}>
            Закрыть
          </button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const [showOverlay, setShowOverlay] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
  const [chat, setChat] = useState([]);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [imageUrl, setImageUrl] = useState('');
  const [conversationId, setConversationId] = useState(null);

  const resetSession = () => {
    setChat([]);
    setCarouselIndex(0);
    setImageUrl('');
    setMenuOpen(false);
    setConversationId(null);
  };

  return (
    <div id="app">
      {showOverlay && <Overlay onFinished={() => setShowOverlay(false)} />}

      <header className="site-header">
        <div className="brand">
          <span className="logo">ЛОГОТИП</span>
          <span className="tagline">генератор вайба</span>
        </div>
        <button
          className="menu-toggle"
          type="button"
          onClick={() => setMenuOpen((value) => !value)}
          aria-label="Меню"
        >
          ≡
        </button>
      </header>

      <nav className={`quick-menu${menuOpen ? ' open' : ''}`}>
        <a href="https://example.com" target="_blank" rel="noreferrer">
          Проф. Тест
        </a>
        <button type="button" onClick={() => window.dispatchEvent(new CustomEvent('open-settings'))}>
          Настройки
        </button>
        <button type="button" onClick={resetSession}>
          Начать заново
        </button>
        <div className="row">
          <a href="https://t.me/your_bot" target="_blank" rel="noreferrer">
            Telegram
          </a>
        </div>
      </nav>

      <main className="main-grid" id="main-content" tabIndex={-1} aria-live="polite">
        <section className="chat-panel">
          <h3 className="chat-title">Чат ИИ</h3>
          <ChatLog items={chat} />
          <ChatInput
            onSend={async (text) => {
              if (!text.trim()) return;
              setChat((prev) => [...prev, { role: 'user', text }]);
              try {
                const response = await fetch(`${API_BASE}/api/chat`, {
                  method: 'POST',
                  headers: { 'Content-Type': 'application/json' },
                  body: JSON.stringify({ message: text, conversation_id: conversationId ?? undefined }),
                });
                if (!response.ok) {
                  throw new Error(`API error: ${response.status}`);
                }
                const data = await response.json();
                setConversationId(data.conversation_id);
                setChat((prev) => [...prev, { role: 'bot', text: data.reply }]);
                setImageUrl(`https://picsum.photos/seed/${encodeURIComponent(Date.now() + text)}/1200/800`);
              } catch (error) {
                console.error(error);
                setChat((prev) => [...prev, { role: 'bot', text: 'Ошибка соединения с сервером' }]);
              }
            }}
          />
        </section>

        <section className="right-grid">
          <div className="card-carousel">
            <div className="carousel-title">Карточки (7 шт.)</div>
            <button
              className="arrow left"
              type="button"
              disabled={carouselIndex === 0}
              onClick={() => setCarouselIndex((value) => Math.max(0, value - 1))}
            >
              {'<'}
            </button>
            <div className="carousel-inner">
              <CarouselContent index={carouselIndex} />
            </div>
            <button
              className="arrow right"
              type="button"
              disabled={carouselIndex === 6}
              onClick={() => setCarouselIndex((value) => Math.min(6, value + 1))}
            >
              {'>'}
            </button>
          </div>

          <ImagePanel url={imageUrl} />
        </section>
      </main>

      <SettingsModal />
    </div>
  );
}

