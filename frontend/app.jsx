const { useEffect, useMemo, useRef, useState } = React;

const HOLD_MS = 1000;
const GRID_COLS = 40;
const GRID_ROWS = 20; // 40 * 20 = 800 tiles
const STEP_DELAY = 18; // ms per diagonal step

function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }

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

  const rebuild = React.useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const tileWidth = rect.width / GRID_COLS;
    const tileHeight = rect.height / GRID_ROWS;
    const overlap = 2; // extra overlap to avoid seams
    const next = [];
    for (let y = 0; y < GRID_ROWS; y++) {
      for (let x = 0; x < GRID_COLS; x++) {
        const diagIndex = x + (GRID_ROWS - 1 - y);
        const delay = diagIndex * STEP_DELAY;
        next.push({
          key: `${x}-${y}`,
          left: Math.floor(x * tileWidth) - 1,
          top: Math.floor(y * tileHeight) - 1,
          width: Math.ceil(tileWidth) + overlap,
          height: Math.ceil(tileHeight) + overlap,
          delay,
          dx: ((Math.random() * 2 - 1) * 240).toFixed(1) + "px",
          dy: (-160 - Math.random() * 200).toFixed(1) + "px",
          rot: ((Math.random() * 2 - 1) * 180).toFixed(1) + "deg",
        });
      }
    }
    setTiles(next);
  }, [containerRef]);

  useEffect(() => { rebuild(); }, [rebuild]);
  useResizeObserver(containerRef, rebuild);

  return (
    <div className="tiles" aria-hidden="true">
      {tiles.map(t => (
        <div
          key={t.key}
          className={"tile" + (active ? " fly" : "")}
          style={{
            left: t.left + "px",
            top: t.top + "px",
            width: t.width + "px",
            height: t.height + "px",
            ["--delay"]: t.delay + "ms",
            ["--dx"]: t.dx,
            ["--dy"]: t.dy,
            ["--rot"]: t.rot,
          }}
        />
      ))}
    </div>
  );
}

function Overlay({ onFinished }) {
  const overlayRef = useRef(null);
  const contentRef = useRef(null);
  const [flying, setFlying] = useState(false);
  const [holding, setHolding] = useState(false);
  const progressRef = useRef(null);
  const mainRef = useRef(null);

  useEffect(() => { mainRef.current = document.getElementById("main-content"); }, []);

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
        contentRef.current && contentRef.current.classList.add("fade-out");

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
      if (progressRef.current) progressRef.current.style.transform = "translateX(-100%)";
      raf = requestAnimationFrame(update);
    }
    return () => raf && cancelAnimationFrame(raf);
  }, [holding, onFinished]);

  const start = (e) => { e.preventDefault(); if (!holding) setHolding(true); };
  const cancel = () => { if (holding) setHolding(false); if (progressRef.current) progressRef.current.style.transform = "translateX(-100%)"; };

  useEffect(() => {
    window.addEventListener("mouseup", cancel);
    window.addEventListener("touchend", cancel);
    window.addEventListener("touchcancel", cancel);
    return () => {
      window.removeEventListener("mouseup", cancel);
      window.removeEventListener("touchend", cancel);
      window.removeEventListener("touchcancel", cancel);
    };
  }, [holding]);

  return (
      <div
        id="intro-overlay"
        className={flying ? "finishing" : ""}
        aria-modal="true"
        role="dialog"
        ref={overlayRef}
      >
        <div className="overlay-bg" aria-hidden="true"/>
        <div className="tunnel" aria-hidden="true">
          {Array.from({length: 6}).map((_, i) => (
              <span
                  key={i}
                  style={{
                      ["--delay"]: `${i * 1330}ms`,
                      ["--rot"]: `${(i % 3 - 1) * 2}deg`
                  }}
              />
          ))}
        </div>
        <Tiles containerRef={overlayRef} active={flying}/>
        <div className="overlay-content" ref={contentRef}>
          <div className="overlay-text">
            <p className="line-1">В поисках <em>рабочего</em> вайба?</p>
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
            <span className="hold-progress" ref={progressRef} aria-hidden="true"/>
          </button>
        </div>
      </div>
  );
}

function App() {
  const [showOverlay, setShowOverlay] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
  const [chat, setChat] = useState([]);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [imageUrl, setImageUrl] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const [theme, setTheme] = useState(() => {
    try {
      const saved = window.localStorage.getItem('app-theme');
      if (saved === 'light') return 'light';
    } catch (error) {
      console.warn('Cannot read theme from storage', error);
    }
    return 'dark';
  });

  const resetSession = () => {
    setChat([]);
    setCarouselIndex(0);
    setImageUrl('');
    setConversationId(null);
  };

  const handleRandom = () => {
    const randomIndex = Math.floor(Math.random() * 7);
    setCarouselIndex(randomIndex);
    setImageUrl(`https://picsum.photos/seed/${Date.now()}-${Math.random()}/1200/900`);
  };

  useEffect(() => {
    const root = document.documentElement;
    if (showOverlay) {
      root.removeAttribute('data-theme');
    } else {
      if (theme === 'light') {
        root.setAttribute('data-theme', 'light');
      } else {
        root.removeAttribute('data-theme');
      }
    }

    try {
      window.localStorage.setItem('app-theme', theme);
    } catch (error) {
      console.warn('Cannot store theme', error);
    }
  }, [theme, showOverlay]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
  };

  return (
    <div id="app">
      {showOverlay && (
        <Overlay onFinished={() => setShowOverlay(false)} />
      )}

      <header className="site-header">
        <div className="brand">
          <span className="logo">ЛОГОТИП</span>
          <span className="tagline">генератор вайба</span>
        </div>
        <div className="menu-area">
          <nav
            className={"quick-menu" + (menuOpen ? " open" : "")}
            style={{ "--count": 6 }}
            aria-hidden={!menuOpen}
          >
            <a
              className="menu-item"
              style={{ "--i": 5 }}
              href="hhh.html"
              onClick={() => {
               }}
            >
              Проф. Тест
            </a>
            <button
              className="menu-item"
              style={{ "--i": 4 }}
              onClick={resetSession}
              type="button"
            >
              Начать заново
            </button>
            <button
              className="menu-item"
              style={{ "--i": 3 }}
              onClick={handleRandom}
              type="button"
            >
              Рандом
            </button>
            <button
              className="menu-item"
              style={{ "--i": 2 }}
              onClick={() => {
                window.dispatchEvent(new CustomEvent("open-settings"));
               }}
              type="button"
            >
              Настройки
            </button>
            <a
              className="menu-item"
              style={{ "--i": 1 }}
              href="https://t.me/your_bot"
              target="_blank"
              rel="noreferrer"
              onClick={() => setMenuOpen(false)}
            >
              Telegram
            </a>
            <button
              className="menu-item"
              style={{ "--i": 0 }}
              onClick={() => {
                toggleTheme();
               }}
              type="button"
            >
              {theme === 'light' ? 'Тёмная тема' : 'Светлая тема'}
            </button>
          </nav>
          <button
            className="menu-toggle"
            onClick={() => setMenuOpen(v => !v)}
            aria-label="Меню"
            aria-expanded={menuOpen}
            type="button"
          >
            ≡
          </button>
        </div>
      </header>

      <main className="main-grid" id="main-content" tabIndex={-1} aria-live="polite">
        <section className="chat-panel">
          <h3 className="chat-title">Чат ИИ</h3>
          <ChatLog items={chat} />
          <ChatInput onSend={async (text) => {
            if (!text.trim()) return;
            setChat(prev => [...prev, { role: "user", text }]);
            // Запрос к бэку (заглушка)
            try {
              const res = await fetch("http://127.0.0.1:8000/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: text, conversation_id: conversationId }),
              });
              const data = await res.json();
              setConversationId(data.conversation_id);
              setChat(prev => [...prev, { role: "bot", text: data.reply }]);
              // при ответе меняем картинку (заглушка URL)
              setImageUrl(`https://picsum.photos/seed/${encodeURIComponent(Date.now()+text)}/1200/900`);
            } catch(e) {
              setChat(prev => [...prev, { role: "bot", text: "Ошибка соединения с сервером" }]);
            }
          }} />
        </section>

        <section className="right-grid">
          <div className="card-carousel">
            <div className="carousel-title">Твоя карточка профессии :D</div>
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

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);

// Chat subcomponents
function ChatLog({ items }) {
  return (
    <div className="chat-log">
      {items.map((m, i) => (
        <div key={i} className={"chat-msg " + (m.role==="bot"?"bot":"user")}>{m.text}</div>
      ))}
    </div>
  );
}

function ChatInput({ onSend }) {
  const [value, setValue] = useState('');
  return (
    <div className="chat-input-row">
      <input value={value} onChange={e=>setValue(e.target.value)} placeholder="Напишите сообщение..." onKeyDown={e=>{ if(e.key==="Enter"){ onSend(value); setValue(''); } }} />
      <button onClick={()=>{ onSend(value); setValue(''); }}>Отправить</button>
    </div>
  );
}

// Carousel placeholder content for 7 steps
function CarouselContent({ index }) {
  const items = [1,2,3,4,5,6,7].map(n => (
    <div
      key={n}
      style={{
        width: '100%',
        maxWidth: 'min(480px, 90%)',
        background: 'var(--surface)',
        border: '1px solid var(--panel-border)',
        borderRadius: 16,
        padding: 'clamp(16px, 2.6vw, 28px)',
        display: 'grid',
        gap: 'clamp(6px, 1.4vw, 12px)',
        boxShadow: '0 6px 24px rgba(0, 0, 0, 0.18)'
      }}
    >
      <h3 style={{margin: 0, fontSize: 'clamp(1rem, 2vw, 1.3rem)', color: 'var(--text)'}}>Рабочая карточка сотрудника — {n}</h3>
      <p style={{color:'var(--text-muted)', fontSize: 'clamp(0.95rem, 1.6vw, 1.1rem)', margin: 0}}>Здесь будет компонент №{n}.</p>
    </div>
  ));
  return items[index];
}

// Image panel with animated noise placeholder
function ImagePanel({ url }) {
  const [loaded, setLoaded] = useState(false);
  useEffect(()=>{ setLoaded(false); }, [url]);
  return (
    <div className="image-panel">
      {!loaded && <NoisePlaceholder waiting={!url} />}
      {url ? (
        <img
          src={url}
          onLoad={() => setLoaded(true)}
          className={loaded ? 'visible' : ''}
          alt="Визуализация рабочего вайба"
        />
      ) : null}
    </div>
  );
}

function NoisePlaceholder({ waiting = false }) {
  const canvasRef = useRef(null);
  useEffect(()=>{
    let raf=0; const canvas = canvasRef.current; if(!canvas) return;
    const ctx = canvas.getContext("2d");
    function resize(){ canvas.width = canvas.clientWidth; canvas.height = canvas.clientHeight; }
    resize();
    const draw = ()=>{
      const {width, height} = canvas; const imgData = ctx.createImageData(width, height);
      for (let i=0;i<imgData.data.length;i+=4){
        const v = Math.random()*255;
        imgData.data[i]=v; imgData.data[i+1]=v; imgData.data[i+2]=v; imgData.data[i+3]= 35+Math.random()*60;
      }
      ctx.putImageData(imgData,0,0);
      raf = requestAnimationFrame(draw);
    };
    raf = requestAnimationFrame(draw);
    const onResize = ()=> resize();
    window.addEventListener("resize", onResize);
    return ()=>{ cancelAnimationFrame(raf); window.removeEventListener("resize", onResize); };
  },[]);
  return (
    <div className="noise-placeholder">
      <canvas className="noise-canvas" ref={canvasRef}></canvas>
      <div className="rendering-label">{waiting ? 'Ожидаем картинку…' : 'Рендерим вайб…'}</div>
    </div>
  );
}

// Settings modal (sounds toggles and volume)
function SettingsModal() {
  const [open, setOpen] = useState(false);
  const [sounds, setSounds] = useState([
    { id: "rain", name: "Дождь", enabled: true, volume: 60 },
    { id: "cafe", name: "Кофейня", enabled: false, volume: 40 },
    { id: "white", name: "White Noise", enabled: false, volume: 50 },
  ]);

  useEffect(()=>{
    const handler = ()=> setOpen(true);
    window.addEventListener("open-settings", handler);
    return ()=> window.removeEventListener("open-settings", handler);
  },[]);

  if (!open) return null;
  return (
    <div style={{position:"fixed", inset:0, display:"grid", placeItems:"center", background:"rgba(0,0,0,0.5)", zIndex:80}} onClick={()=>setOpen(false)}>
      <div style={{minWidth:320, background:"#0b0b0b", border:"1px solid #1a1a1a", borderRadius:12, padding:14}} onClick={e=>e.stopPropagation()}>
        <h3 style={{marginTop:0}}>Настройки звуков</h3>
        <div style={{display:"grid", gap:10}}>
          {sounds.map(s=> (
            <div key={s.id} style={{display:"grid", gridTemplateColumns:"1fr auto", gap:8, alignItems:"center"}}>
              <div>
                <div style={{fontWeight:600}}>{s.name}</div>
                <input type="range" min="0" max="100" value={s.volume} onChange={e=> setSounds(prev=> prev.map(p=> p.id===s.id? {...p, volume:Number(e.target.value)}:p))} />
              </div>
              <label style={{display:"inline-flex", alignItems:"center", gap:6}}>
                <input type="checkbox" checked={s.enabled} onChange={e=> setSounds(prev=> prev.map(p=> p.id===s.id? {...p, enabled:e.target.checked}:p))} /> Вкл
              </label>
            </div>
          ))}
        </div>
        <div style={{display:"grid", gridAutoFlow:"column", gap:8, marginTop:12, justifyContent:"end"}}>
          <button className="menu-toggle" onClick={()=> setOpen(false)}>Закрыть</button>
        </div>
      </div>
    </div>
  );
}
