const { useEffect, useMemo, useRef, useState } = React;

// Типы для Speech Recognition API
if (typeof window !== 'undefined') {
  window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
}

const HOLD_MS = 1000;
const GRID_COLS = 40;
const GRID_ROWS = 20; // 40 * 20 = 800 tiles
const STEP_DELAY = 18; // ms per diagonal step

const JSON_MARKER = '<<JSON>>';

const GREETING_TEXT = 'Привет! Кем бы ты хотел себя почувствовать? Если ты еще не знаешь, то можешь пройти тест по профориентации (ссылка на тест).';

function createGreetingMessage() {
  return {
    role: "bot",
    text: (
      <span>
        {GREETING_TEXT.replace(' (ссылка на тест)', '')}
        {' '}(
        <a href="/hhh.html" target="_blank" rel="noreferrer">ссылка на тест</a>
        ).
      </span>
    ),
  };
}

const PRESET_STRUCTURES = {
  frontend: {
    profession: 'Фронтенд-разработчик',
    schedule: {
      morning: [
        '09:00 — Стенд-ап с командой',
        '10:00 — Код-ревью пул-реквестов',
        '11:00 — Вёрстка нового интерфейсного модуля',
      ],
      lunch: [
        '13:00 — Синк с дизайнером по UI-деталям',
        '13:30 — Оптимизация бандла и настройка CI',
        '14:30 — Тестирование в основных браузерах',
      ],
      evening: [
        '16:00 — Интеграция с API и написание unit-тестов',
        '17:30 — Демонстрация прогресса продукт-менеджеру',
        '18:30 — Планирование задач на следующий спринт',
      ],
    },
    tech_stack: [
      { name: 'TypeScript', note: 'Основной язык для фронтенд-разработки' },
      { name: 'React + Next.js', note: 'Компонентный подход и SSR' },
      { name: 'Jest + Testing Library', note: 'Покрытие ключевых сценариев тестами' },
    ],
    company_benefits: [
      { title: 'Рост конверсии', detail: 'Новые UI-паттерны увеличивают заявки на 18%' },
      { title: 'Скорость релизов', detail: 'Оптимизированная сборка сокращает деплой до 8 минут' },
      { title: 'Качество кода', detail: 'Автотесты предотвращают 70% регрессий' },
    ],
    career_growth: [
      { title: 'Middle фронтенд-разработчик', detail: 'Ведёт фичи и наставляет джунов' },
      { title: 'Senior / Tech Lead', detail: 'Отвечает за архитектуру и перфоманс фронта' },
      { title: 'Head of Frontend / Product Engineer', detail: 'Работает со стратегией продукта и бизнесом' },
    ],
    colleague_messages: {
      short: [
        'Менеджер: Статистика по A/B тесту уже в Confluence, глянешь?',
        'Дизайнер: Проверь, сохранилась ли анимация на карточке скидок.',
        'QA: Закинул новый сценарий на регрессию, нужна твоя проверка.',
      ],
      medium: [
        'Коллега: Было бы круто завтра обсудить миграцию на React 19, есть минут 20?',
        'PM: Клиенты хвалят onboarding — напиши пару инсайтов к демо.',
      ],
      long: [
        'Тимлид: Сегодня вечером выходим на прод с рекомендателем. Пройдись по чеклисту перфоманса и отпиши, успеваем ли включить lazy-loading изображений.'
      ],
    },
    growth_table: {
      growth_points: [
        { label: 'Внимание к UX', value: 'Собираешь инсайты и быстро внедряешь улучшения' },
        { label: 'Production-ready код', value: 'Поддерживаешь высокий coverage и автоматизацию' },
        { label: 'Синхронизация с backend', value: 'Держишь в порядке контракты API и коммуникацию' },
      ],
      vacancies: [
        { title: 'Фронтенд-разработчик (React)', salary: 'от 150 000 ₽', link: 'https://hh.ru/vacancy/123456' },
        { title: 'Middle Frontend Engineer', salary: 'до 220 000 ₽', link: 'https://hh.ru/vacancy/654321' },
        { title: 'Senior Frontend Developer', salary: '250 000–320 000 ₽', link: 'https://hh.ru/vacancy/112233' },
      ],
      courses: [
        { title: 'Профессия Фронтенд-разработчик', provider: 'Яндекс Практикум', link: 'https://practicum.yandex.ru/frontend-developer/' },
        { title: 'Frontend-разработчик с нуля до middle', provider: 'Нетология', link: 'https://netology.ru/programs/front-end' },
        { title: 'Modern React with Redux', provider: 'Udemy', link: 'https://www.udemy.com/course/react-redux/' },
      ],
    },
    image_description: 'Рабочее место фронтендера с двумя мониторами, макетом в Figma и открытым редактором кода.',
    sound_description: 'Щёлчки механической клавиатуры, уведомления Slack и мягкий эмбиент из наушников.',
  },
  accountant: {
    profession: 'Бухгалтер',
    schedule: {
      morning: [
        '08:30 — Проверка входящих первичных документов',
        '09:30 — Сверка банковских выписок с 1C',
        '11:00 — Подготовка платежных поручений',
      ],
      lunch: [
        '12:30 — Консультация с юристом по контрактам',
        '13:00 — Внесение данных в учетные системы',
        '14:00 — Контроль налоговых вычетов и льгот',
      ],
      evening: [
        '16:00 — Формирование управленческой отчетности',
        '17:00 — Отправка деклараций через ЭДО',
        '18:00 — Архивация документов и план задач на завтра',
      ],
    },
    tech_stack: [
      { name: '1C:Бухгалтерия', note: 'Учет операций и расчет заработной платы' },
      { name: 'Диадок / Контур.Экстерн', note: 'Электронный документооборот и сдача отчетности' },
      { name: 'Excel + Power Query', note: 'Аналитика и сверка с управленческими данными' },
    ],
    company_benefits: [
      { title: 'Финансовая прозрачность', detail: 'Своевременные отчеты ускоряют управленческие решения' },
      { title: 'Снижение рисков', detail: 'Корректные налоги исключают штрафы и пени' },
      { title: 'Оптимизация бюджета', detail: 'Контроль расходов экономит до 12% операционных затрат' },
    ],
    career_growth: [
      { title: 'Ведущий бухгалтер', detail: 'Курирует участок учета и обучает коллег' },
      { title: 'Главный бухгалтер', detail: 'Руководит финансовой отчетностью компании' },
      { title: 'Финансовый директор', detail: 'Стратегия финансов и взаимодействие с аудиторами' },
    ],
    colleague_messages: {
      short: [
        'Экономист: Подскажи, какие суммы заносить в отчет по командировкам?',
        'HR: Нужен срочный расчет отпускных для нового сотрудника.',
        'Менеджер: Проверь, пришёл ли счет от поставщика логистики.',
      ],
      medium: [
        'Руководитель: Сегодня до 17:00 нужно согласовать бюджет по новому проекту, подготовишь цифры?',
        'Юрист: Есть вопрос по договору аренды — обсудим индексацию на созвоне.',
      ],
      long: [
        'Главбух: Завтра аудиторы запросят выборку по затратам за квартал. Собери документы и проверь, чтобы все подписи и счета-фактуры были в порядке.'
      ],
    },
    growth_table: {
      growth_points: [
        { label: 'Точность учета', value: 'Ведёшь операции без расхождений и доработок' },
        { label: 'Актуальность регламентов', value: 'Оперативно внедряешь изменения законодательства' },
        { label: 'Автоматизация', value: 'Настраиваешь интеграции и шаблоны для типовых задач' },
      ],
      vacancies: [
        { title: 'Бухгалтер по учету ТМЦ', salary: '80 000–110 000 ₽', link: 'https://hh.ru/vacancy/224466' },
        { title: 'Ведущий бухгалтер', salary: '120 000–160 000 ₽', link: 'https://hh.ru/vacancy/335577' },
        { title: 'Главный бухгалтер', salary: 'от 180 000 ₽', link: 'https://hh.ru/vacancy/446688' },
      ],
      courses: [
        { title: 'Бухгалтерия на практике', provider: 'Skillbox', link: 'https://skillbox.ru/course/accounting-practice/' },
        { title: 'Главный бухгалтер: повышение квалификации', provider: 'Stepik', link: 'https://stepik.org/course/114920' },
        { title: 'Финансовый учет и налогообложение', provider: 'Нетология', link: 'https://netology.ru/programs/accounting' },
      ],
    },
    image_description: 'Офис бухгалтера с аккуратными стопками документов и открытой 1C на ноутбуке.',
    sound_description: 'Тиканье настенных часов, щелчки клавиатуры и уведомления службы электронного документооборота.',
  },
  hero_miner: {
    profession: 'Шахтёр-супергерой',
    schedule: {
      morning: [
        '07:00 — Проверка экзоскелета и дыхательных фильтров',
        '08:00 — Спуск в шахту и брифинг с командой',
        '09:30 — Усиление крепи и установка сенсоров безопасности',
      ],
      lunch: [
        '12:00 — Подзарядка реактивного ранца и энергетический батончик',
        '12:30 — Спасение стажеров из сложного участка',
        '13:30 — Анализ пород и подготовка к контролируемому подрыву',
      ],
      evening: [
        '16:00 — Вывод породы на поверхность с помощью гравимагнита',
        '17:30 — Контроль технического состояния снаряжения',
        '19:00 — Брифинг по спасательным операциям и план на ночь',
      ],
    },
    tech_stack: [
      { name: 'Экзоскелет X-Rig', note: 'Усиливает силу и снижает нагрузку на суставы' },
      { name: 'Дроны-разведчики', note: 'Сканируют штреки и ищут потенциальные обвалы' },
      { name: 'Георадар и лазерные резаки', note: 'Точно картируют породу и добывают редкие минералы' },
    ],
    company_benefits: [
      { title: 'Безопасность смены', detail: 'Сенсоры снижают аварийность на 95%' },
      { title: 'Рекорд добычи', detail: 'Редкие сверхпроводники доставлены на 30% быстрее графика' },
      { title: 'Командный дух', detail: 'Тренировки поддерживают боевой настрой всей бригады' },
    ],
    career_growth: [
      { title: 'Наставник супергероев', detail: 'Обучаешь новичков работе с экзоскелетами' },
      { title: 'Координатор спасательных миссий', detail: 'Планируешь операции и взаимодействуешь с диспетчерской' },
      { title: 'Герой планетарного масштаба', detail: 'Ведёшь проекты по добыче редких элементов' },
    ],
    colleague_messages: {
      short: [
        'Диспетчер: Сигнал тревоги на третьем уровне, проверь датчики.',
        'Геолог: Нашёл жилу ирилия, нужен твой лазерный резак.',
        'Стажёр: Можно с тобой на обход? Хочу увидеть гравимагнит в деле.',
      ],
      medium: [
        'Командир смены: Если успеешь, загляни на тренировку по эвакуации — ребятам нужен показательный пример.',
        'Инженер: Новый фильтр воздуха требует калибровки, протестируешь в полевых условиях?',
      ],
      long: [
        'Штаб спасателей: На северном участке возможен обвал. Нужен твой план действий: как укрепим свод, какую технику задействуем и кто будет прикрывать стажёров.'
      ],
    },
    growth_table: {
      growth_points: [
        { label: 'Героическая выносливость', value: 'Держишь темп и восстанавливаешься быстрее команды' },
        { label: 'Технологическая смелость', value: 'Первым тестируешь инновационные устройства и делишься фидбеком' },
        { label: 'Миссия по спасению', value: 'Продумываешь операции так, чтобы каждый возвращался домой' },
      ],
      vacancies: [
        { title: 'Шахтёр-спасатель', salary: 'от 140 000 ₽ + надбавки', link: 'https://hh.ru/vacancy/557799' },
        { title: 'Оператор горнодобывающих экзоскелетов', salary: '160 000–210 000 ₽', link: 'https://hh.ru/vacancy/668800' },
        { title: 'Инженер по безопасности шахт', salary: 'до 240 000 ₽', link: 'https://hh.ru/vacancy/779901' },
      ],
      courses: [
        { title: 'Горная безопасность и спасательные работы', provider: 'Skillbox PRO', link: 'https://skillbox.ru/course/mine-safety/' },
        { title: 'Работа с дронами в добыче', provider: 'GeekBrains', link: 'https://gb.ru/courses/drone-mining' },
        { title: 'Физподготовка для горноспасателей', provider: 'Stepik', link: 'https://stepik.org/course/899999' },
      ],
    },
    image_description: 'Подземная галерея с неоновым освещением, шахтёр в экзоскелете и летающие дроны.',
    sound_description: 'Гул вентиляции, сигнал тревоги вдали и тяжёлые шаги экзоскелета по породе.',
  },
};

const PRESET_ALIASES = {
  'фронтенд разработчик': 'frontend',
  'фронтенд-разработчик': 'frontend',
  'frontend разработчик': 'frontend',
  'frontend developer': 'frontend',
  'разработчик фронтенда': 'frontend',
  'бухгалтер': 'accountant',
  'главный бухгалтер': 'accountant',
  'бухгалтерия': 'accountant',
  'шахтер супергерой': 'hero_miner',
  'шахтер-супергерой': 'hero_miner',
  'шахтёр супергерой': 'hero_miner',
  'шахтёр-супергерой': 'hero_miner',
};

function normalizeProfessionName(value = '') {
  return value
    .toString()
    .toLowerCase()
    .replace(/ё/g, 'е')
    .replace(/[^a-zа-я0-9\s]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function getPresetForProfession(profession) {
  if (!profession) return null;
  const key = PRESET_ALIASES[normalizeProfessionName(profession)];
  if (!key) return null;
  const template = PRESET_STRUCTURES[key];
  return template ? JSON.parse(JSON.stringify(template)) : null;
}

function extractProfessionFromSummary(message = '') {
  if (!message) return null;
  const normalized = message.toLowerCase();
  if (!normalized.includes('спасибо за ответы')) return null;
  const match = message.match(/профессию\s+([^.!?\n]+)/i);
  if (!match) return null;
  const raw = match[1]
    .replace(/[«»\"\(\)]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
  return raw || null;
}

function createJsonDisplay(payload) {
  const content = typeof payload === 'string'
    ? payload
    : JSON.stringify(payload, null, 2);
  return (
    <pre className="chat-json">
      {`${JSON_MARKER}\n${content}`}
    </pre>
  );
}

function extractAssistantParts(reply = '') {
  if (!reply) {
    return { text: '', json: null };
  }
  const markerIndex = reply.indexOf(JSON_MARKER);
  if (markerIndex === -1) {
    return { text: reply.trim(), json: null };
  }
  const text = reply.slice(0, markerIndex).trim();
  const jsonChunk = reply.slice(markerIndex + JSON_MARKER.length).trim();
  return {
    text,
    json: jsonChunk.length ? jsonChunk : null,
  };
}

function parseSchedule(schedule = {}) {
  const parseSlot = (value) => {
    if (!value) return null;
    const normalized = String(value);
    let [timePart, ...rest] = normalized.split('—');
    if (rest.length === 0) {
      [timePart, ...rest] = normalized.split('-');
    }
    const time = (timePart || '').trim();
    const title = rest.join('—').trim();
    return {
      time: time || '—',
      title: title || normalized.trim(),
    };
  };

  const ensureThree = (list) => {
    const parsed = (Array.isArray(list) ? list : []).map(parseSlot).filter(Boolean).slice(0, 3);
    const filled = [...parsed];
    while (filled.length < 3) {
      filled.push({ time: '—', title: 'Задача в разработке' });
    }
    return filled;
  };

  return {
    morning: ensureThree(schedule.morning),
    afternoon: ensureThree(schedule.lunch ?? schedule.afternoon),
    evening: ensureThree(schedule.evening),
  };
}

function toMatrixItems(list = [], fallbackPrefix) {
  return list.map((entry, idx) => {
    if (typeof entry === 'string') {
      return { title: entry, description: '' };
    }
    return {
      title: entry?.title ?? entry?.name ?? `${fallbackPrefix} ${idx + 1}`,
      description: entry?.description ?? entry?.detail ?? entry?.note ?? '',
    };
  });
}

function padToThree(items, fallbackPrefix) {
  const filled = [...items];
  while (filled.length < 3) {
    const index = filled.length;
    filled.push({ title: `${fallbackPrefix} ${index + 1}`, description: '' });
  }
  return filled.slice(0, 3);
}

function normalizeMessages(messages = {}) {
  const pick = (arr, limit) => (Array.isArray(arr) ? arr.filter(Boolean).slice(0, limit) : []);
  return {
    long: pick(messages.long, 1),
    medium: pick(messages.medium, 2),
    short: pick(messages.short, 3),
  };
}

function normalizeStats(list = []) {
  return padToThree(
    list.map((item, idx) => {
      if (typeof item === 'string') {
        const [label, ...rest] = item.split(':');
        if (rest.length) {
          return { label: label.trim(), value: rest.join(':').trim() };
        }
        return { label: item.trim(), value: '' };
      }
      return {
        label: item?.label ?? item?.title ?? `Показатель ${idx + 1}`,
        value: item?.value ?? item?.detail ?? '',
      };
    }),
    'Показатель'
  );
}

function normalizeVacancies(list = []) {
  return list.slice(0, 3).map((item, idx) => {
    if (typeof item === 'string') {
      const parts = item.split('|').map((part) => part.trim());
      const [title, salary, link] = parts;
      return {
        title: title || `Вакансия ${idx + 1}`,
        salary: salary || 'З/п по договорённости',
        href: link || '#',
      };
    }
    return {
      title: item?.title ?? `Вакансия ${idx + 1}`,
      salary: item?.salary ?? item?.pay ?? 'З/п по договорённости',
      href: item?.link ?? item?.href ?? '#',
    };
  });
}

function normalizeCourses(list = []) {
  return list.slice(0, 3).map((item, idx) => {
    if (typeof item === 'string') {
      const parts = item.split('|').map((part) => part.trim());
      const [title, provider, link] = parts;
      return {
        title: title || `Курс ${idx + 1}`,
        provider: provider || 'Провайдер уточняется',
        href: link || '#',
      };
    }
    return {
      title: item?.title ?? `Курс ${idx + 1}`,
      provider: item?.provider ?? item?.school ?? 'Провайдер уточняется',
      href: item?.link ?? item?.href ?? '#',
    };
  });
}

function buildSummaryArtifacts(aiData) {
  if (!aiData) return null;
  const profession = aiData.profession || 'специалиста';
  const schedule = parseSchedule(aiData.schedule);
  const scheduleLines = [...schedule.morning, ...schedule.afternoon, ...schedule.evening]
    .map(({ time, title }) => `${time} — ${title}`)
    .filter(Boolean)
    .slice(0, 4);
  const techItems = padToThree(
    toMatrixItems(aiData.tech_stack ?? [], 'Стек'),
    'Стек'
  ).map(({ title, description }) => description ? `${title}: ${description}` : title);
  const benefitItems = padToThree(
    toMatrixItems(aiData.company_benefits ?? [], 'Польза'),
    'Польза'
  ).map(({ title, description }) => description ? `${title}: ${description}` : title);
  const growthItems = padToThree(
    toMatrixItems(aiData.career_growth ?? [], 'Рост'),
    'Рост'
  ).map(({ title, description }) => description ? `${title}: ${description}` : title);

  const plainText = [
    `Результат: ${profession}`,
    scheduleLines.length ? `Типичный день: ${scheduleLines.join('; ')}` : null,
    techItems.length ? `Стек: ${techItems.join(', ')}` : null,
    benefitItems.length ? `Польза: ${benefitItems.join('; ')}` : null,
    growthItems.length ? `Рост: ${growthItems.join(' → ')}` : null,
  ].filter(Boolean).join(' | ');

  return {
    node: (
      <div className="chat-summary">
        <div className="chat-summary__section">
          <span className="chat-summary__title">Результат:</span>
          <span>{profession}</span>
        </div>
        <div className="chat-summary__section">
          <span className="chat-summary__title">Типичный день:</span>
          <div className="chat-summary__schedule">
            {scheduleLines.map((line, idx) => (
              <span key={idx} className="chat-summary__schedule-line">{line}</span>
            ))}
          </div>
        </div>
        <div className="chat-summary__section">
          <span className="chat-summary__title">Стек:</span>
          <span>{techItems.join(', ')}</span>
        </div>
        <div className="chat-summary__section">
          <span className="chat-summary__title">Польза:</span>
          <span>{benefitItems.join('; ')}</span>
        </div>
        <div className="chat-summary__section">
          <span className="chat-summary__title">Рост:</span>
          <span>{growthItems.join(' → ')}</span>
        </div>
      </div>
    ),
    text: plainText,
  };
}

function buildAiCards(aiData) {
  if (!aiData) return null;

  const schedule = parseSchedule(aiData.schedule);
  const profession = aiData.profession || 'специалиста';
  const stackItems = padToThree(toMatrixItems(aiData.tech_stack ?? [], 'Стек'), 'Стек');
  const impactItems = padToThree(toMatrixItems(aiData.company_benefits ?? [], 'Эффект'), 'Эффект');
  const growthItems = padToThree(toMatrixItems(aiData.career_growth ?? [], 'Рост'), 'Рост');
  const messages = normalizeMessages(aiData.colleague_messages ?? {});
  const stats = normalizeStats(aiData?.growth_table?.growth_points ?? []);
  const vacancies = normalizeVacancies(aiData?.growth_table?.vacancies ?? []);
  const courses = normalizeCourses(aiData?.growth_table?.courses ?? []);

  return [
    {
      key: 'schedule',
      render: () => <ScheduleCard profession={profession} schedule={schedule} />,
    },
    {
      key: 'growth',
      render: () => (
        <GrowthMatrixCard stack={stackItems} impact={impactItems} growth={growthItems} />
      ),
    },
    {
      key: 'messages',
      render: () => <MessagesCard messages={messages} profession={profession} />,
    },
    {
      key: 'opportunity',
      render: () => <OpportunityCard stats={stats} vacancies={vacancies} courses={courses} />,
    },
  ];
}

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
          aria-label="Удерживай 1 секунду, чтобы продолжить"
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
  const [showOverlay, setShowOverlay] = useState(() => {
    try {
      return window.localStorage.getItem('overlay-dismissed') === 'true' ? false : true;
    } catch (error) {
      return true;
    }
  });
  const [menuOpen, setMenuOpen] = useState(false);
  const [chat, setChat] = useState(() => [createGreetingMessage()]);
  const [backendHistory, setBackendHistory] = useState(() => [
    { role: 'assistant', content: GREETING_TEXT },
  ]);
  const [aiData, setAiData] = useState(null);
  const [dataVersion, setDataVersion] = useState(0);
  const [lastSummaryCard, setLastSummaryCard] = useState(null);
  const [carouselIndex, setCarouselIndex] = useState(0);
  const [imageUrl, setImageUrl] = useState('');
  const [conversationId, setConversationId] = useState(null);
  const hasUserInput = useMemo(() => chat.some(msg => msg.role === "user" && String(msg.text ?? '').trim().length > 0), [chat]);
  const [theme, setTheme] = useState(() => {
    try {
      const saved = window.localStorage.getItem('app-theme');
      if (saved === 'light') return 'light';
    } catch (error) {
      console.warn('Cannot read theme from storage', error);
    }
    return 'dark';
  });
  const logRef = useRef(null);

  const resetSession = () => {
    setChat([createGreetingMessage()]);
    setCarouselIndex(0);
    setImageUrl('');
    setConversationId(null);
    setAiData(null);
    setBackendHistory([{ role: 'assistant', content: GREETING_TEXT }]);
  };

  const cards = useMemo(() => {
    if (!aiData) {
      return [{ key: 'placeholder', render: () => <PlaceholderCard /> }];
    }
    console.log('[cards] building with aiData version', dataVersion, aiData);
    const generated = buildAiCards(aiData) ?? [];
    return generated.length
      ? generated
      : [{ key: 'placeholder', render: () => <PlaceholderCard /> }];
  }, [aiData, dataVersion]);

  const maxCardIndex = cards.length - 1;

  useEffect(() => {
    if (carouselIndex > maxCardIndex) {
      setCarouselIndex(maxCardIndex);
    }
  }, [carouselIndex, maxCardIndex]);

  useEffect(() => {
    setCarouselIndex(0);
  }, [cards.length]);

  const handleRandom = () => {
    if (cards.length <= 1) return;
    const randomIndex = Math.floor(Math.random() * cards.length);
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

  const handleOverlayFinished = () => {
    try {
      window.localStorage.setItem('overlay-dismissed', 'true');
    } catch (error) {
      // ignore
    }
    setShowOverlay(false);
  };

  useEffect(() => {
    const elements = Array.from(document.querySelectorAll('.tilt-follow'));
    if (!elements.length) {
      return;
    }

    const maxTilt = 2;
    const maxShift = 3;
    const perspective = 1200;

    const applyInitial = () => {
      elements.forEach((el) => {
        el.style.transform = `perspective(${perspective}px) translate3d(0, 0, 0) rotateX(0deg) rotateY(0deg)`;
      });
    };

    applyInitial();

    const handleMouseMove = (event) => {
      elements.forEach((el) => {
        const rect = el.getBoundingClientRect();
        const depth = Number(el.dataset.tiltDepth || 1);
        const offsetX = event.clientX - (rect.left + rect.width / 2);
        const offsetY = event.clientY - (rect.top + rect.height / 2);
        const percentX = offsetX / (rect.width / 2);
        const percentY = offsetY / (rect.height / 2);

        const tiltX = -(percentY * maxTilt * depth);
        const tiltY = percentX * maxTilt * depth;
        const shiftX = percentX * maxShift * depth;
        const shiftY = percentY * maxShift * depth;
        el.style.transform = `perspective(${perspective}px) translate3d(${shiftX.toFixed(1)}px, ${shiftY.toFixed(1)}px, 0) rotateX(${tiltX.toFixed(2)}deg) rotateY(${tiltY.toFixed(2)}deg)`;
      });
    };

    const resetTilt = () => {
      elements.forEach((el) => {
        el.style.transform = `perspective(${perspective}px) translate3d(0, 0, 0) rotateX(0deg) rotateY(0deg)`;
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseleave', resetTilt);

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseleave', resetTilt);
    };
  }, []);

  useEffect(() => {
    const handler = (e) => {
      if (e.key === 'Tab') {
        e.preventDefault();
        setMenuOpen((v) => !v);
        return;
      }
      if (e.key === 'Escape') {
        e.preventDefault();
        setMenuOpen((v) => !v);
        return;
      }
      if (!hasUserInput || cards.length <= 1) return;
      if (e.target && ['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return;
      const maxIndex = cards.length - 1;
      if (e.key === 'ArrowLeft') {
        setCarouselIndex((value) => Math.max(0, value - 1));
      }
      if (e.key === 'ArrowRight') {
        setCarouselIndex((value) => Math.min(maxIndex, value + 1));
      }
    };
    window.addEventListener('keydown', handler);
    return () => {
      window.removeEventListener('keydown', handler);
    };
  }, [hasUserInput, cards.length]);

  return (
    <div id="app">
      {showOverlay && (
        <Overlay onFinished={handleOverlayFinished} />
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
              href="https://t.me/VibeChater_bot"
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
        <section className="chat-panel glass tilt-follow" data-tilt-depth="1">
          <h3 className="chat-title">Вайбовый чат</h3>
          <ChatLog items={chat} logRef={logRef} />
          <ChatInput onSend={async (text) => {
            if (!text.trim()) return;
            const trimmed = text.trim();
            const historyPayload = [...backendHistory, { role: "user", content: trimmed }];
            setChat(prev => [...prev, { role: "user", text: trimmed }]);
            try {
              const res = await fetch("http://127.0.0.1:8000/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                  message: trimmed,
                  conversation_id: conversationId,
                  history: historyPayload,
                }),
              });
              const data = await res.json();
              if (data?.conversation_id) {
              setConversationId(data.conversation_id);
              }
              const rawReply = data?.reply ?? '';
              console.log('[chat] raw reply:', rawReply);
              const structuredFromBackend = data?.structured_data;
              let updatedHistory = [...historyPayload];
              const { text: assistantText, json } = extractAssistantParts(rawReply);
              const conversationForCards = data?.conversation_id || conversationId;
              const professionHint = extractProfessionFromSummary(assistantText);
              let jsonMessageDisplayed = false;

              const pushJsonMessage = (payload) => {
                if (!payload || jsonMessageDisplayed) {
                  return;
                }
                jsonMessageDisplayed = true;
                setChat(prev => [...prev, { role: "bot", text: createJsonDisplay(payload) }]);
              };

              const loadCardsData = async ({ sourceData = null, cardsFileUrl = null, professionHint: hint = null } = {}) => {
                let cardsPayload = null;

                const resolveUrl = (url) => {
                  if (!url) return null;
                  if (url.startsWith('http://') || url.startsWith('https://')) {
                    return url;
                  }
                  const base = window.location?.origin ?? 'http://127.0.0.1:8000';
                  return `${base}${url.startsWith('/') ? url : `/${url}`}`;
                };

                if (cardsFileUrl) {
                  try {
                    const response = await fetch(resolveUrl(cardsFileUrl));
                    if (response.ok) {
                      cardsPayload = await response.json();
                    }
                  } catch (err) {
                    console.error('Ошибка чтения JSON-файла карточек', err, cardsFileUrl);
                  }
                }

                if (conversationForCards) {
                  try {
                    const response = await fetch(`http://127.0.0.1:8000/api/conversation/${conversationForCards}/cards`);
                    if (response.ok) {
                      const payload = await response.json();
                      if (!cardsPayload && payload?.file) {
                        const fileResponse = await fetch(resolveUrl(payload.file));
                        if (fileResponse.ok) {
                          cardsPayload = await fileResponse.json();
                        }
                      }
                      if (!cardsPayload) {
                        cardsPayload = payload?.data ?? null;
                      }
                    }
                  } catch (err) {
                    console.error('Ошибка получения карточек из БД', err);
                  }
                }

                if ((!cardsPayload || !cardsPayload.profession) && sourceData && sourceData.profession) {
                  cardsPayload = sourceData;
                }

                const presetSource = hint || sourceData?.profession;
                if ((!cardsPayload || !cardsPayload.profession) && presetSource) {
                  const presetPayload = getPresetForProfession(presetSource);
                  if (presetPayload) {
                  console.log('[cards] using preset payload for profession:', presetPayload.profession);
                    cardsPayload = presetPayload;
                  }
                }

                if ((!cardsPayload || !cardsPayload.profession) && sourceData) {
                  cardsPayload = sourceData;
                }

                if (!cardsPayload || !cardsPayload.profession) {
                  return { summaryText: null, payload: null };
                }

                console.log('[cards] data ready for rendering:', cardsPayload);
                setAiData(cardsPayload);
                setDataVersion((v) => v + 1);
                const summary = buildSummaryArtifacts(cardsPayload);
                if (summary) {
                  setChat(prev => [...prev, { role: "bot", text: summary.node }]);
                  setLastSummaryCard(summary.node);
                  setCarouselIndex(0);
                  return { summaryText: summary.text, payload: cardsPayload };
                }
                return { summaryText: null, payload: cardsPayload };
              };

              if (assistantText) {
                setChat(prev => [...prev, { role: "bot", text: assistantText }]);
                updatedHistory.push({ role: 'assistant', content: assistantText });
              }

              const cardsFile = data?.cards_file;
              const userPresetCandidate = getPresetForProfession(trimmed);
              let summaryHistoryText = null;

              const handleCardsResult = (result) => {
                if (!result) return;
                if (result.payload && !jsonMessageDisplayed) {
                  pushJsonMessage(result.payload);
                }
                if (result.summaryText) {
                  summaryHistoryText = result.summaryText;
                }
              };

              if (structuredFromBackend && structuredFromBackend.profession) {
                console.log('[chat] structured_data from backend:', structuredFromBackend);
                pushJsonMessage(structuredFromBackend);
                const result = await loadCardsData({
                  sourceData: structuredFromBackend,
                  cardsFileUrl: cardsFile,
                  professionHint: structuredFromBackend.profession,
                });
                handleCardsResult(result);
              } else if (json) {
                try {
                  const parsed = JSON.parse(json);
                  pushJsonMessage(parsed);
                  const result = await loadCardsData({
                    sourceData: parsed,
                    cardsFileUrl: cardsFile,
                    professionHint: parsed.profession ?? professionHint,
                  });
                  handleCardsResult(result);
                } catch (error) {
                  console.error('Ошибка разбора JSON от ассистента', error, json);
                  pushJsonMessage(json);
                }
              } else if (cardsFile) {
                const result = await loadCardsData({
                  cardsFileUrl: cardsFile,
                  professionHint,
                });
                handleCardsResult(result);
              }

              if (!summaryHistoryText && professionHint) {
                const presetPayload = getPresetForProfession(professionHint);
                if (presetPayload) {
                  pushJsonMessage(presetPayload);
                  const result = await loadCardsData({
                    sourceData: presetPayload,
                    professionHint,
                  });
                  handleCardsResult(result);
                }
              }

              if (!summaryHistoryText && userPresetCandidate) {
                if (!aiData || aiData.profession !== userPresetCandidate.profession) {
                  pushJsonMessage(userPresetCandidate);
                  const result = await loadCardsData({
                    sourceData: userPresetCandidate,
                    professionHint: userPresetCandidate.profession,
                  });
                  handleCardsResult(result);
                }
              }

              if (summaryHistoryText) {
                updatedHistory.push({ role: 'assistant', content: summaryHistoryText });
              }

              setBackendHistory(updatedHistory);

              setImageUrl(`https://picsum.photos/seed/${encodeURIComponent(Date.now() + text)}/1200/900`);
            } catch (e) {
              console.error('Ошибка запроса к /api/chat', e);
              setChat(prev => [...prev, { role: "bot", text: "Ошибка соединения с сервером" }]);
              setBackendHistory(historyPayload);
            }
          }} logRef={logRef} />
        </section>

        <section className="right-grid">
          <div className="card-carousel tilt-follow" data-tilt-depth="0.8" tabIndex={0}
            onKeyDown={(e) => {
              if (!hasUserInput || cards.length <= 1) return;
              const maxIndex = cards.length - 1;
              if (e.key === 'ArrowLeft') {
                setCarouselIndex((value) => Math.max(0, value - 1));
              }
              if (e.key === 'ArrowRight') {
                setCarouselIndex((value) => Math.min(maxIndex, value + 1));
              }
            }}
          >
            <div className="carousel-title">Твоя карточка профессии</div>
            {hasUserInput && cards.length > 0 && (
              <>
                {carouselIndex > 0 && (
                  <button
                    className="arrow left"
                    type="button"
                    onClick={() => setCarouselIndex((value) => Math.max(0, value - 1))}
                  >
                    {'<'}
                  </button>
                )}
                {carouselIndex < maxCardIndex && (
                  <button
                    className="arrow right"
                    type="button"
                    onClick={() => setCarouselIndex((value) => Math.min(maxCardIndex, value + 1))}
                  >
                    {'>'}
                  </button>
                )}
              </>
            )}
            <div className="carousel-inner">
              <CarouselContent index={carouselIndex} cards={cards} />
            </div>
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
function ChatLog({ items, logRef }) {
  useEffect(() => {
    const container = logRef?.current;
    if (container) {
      container.scrollTo({ top: container.scrollHeight, behavior: 'smooth' });
    }
  }, [items, logRef]);

  return (
    <div className="chat-log" ref={logRef}>
      {items.map((m, i) => (
        <div key={i} className={"chat-msg " + (m.role === "bot" ? "bot" : "user")}>
          {m.text}
        </div>
      ))}
    </div>
  );
}

function ChatInput({ onSend, logRef }) {
  const [value, setValue] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSpeechSupported, setIsSpeechSupported] = useState(true);
  const textareaRef = useRef(null);
  const recognitionRef = useRef(null);
  const maxRows = 4;

  const ensureLogScroll = () => {
    const container = logRef?.current;
    if (container) {
      container.scrollTop = container.scrollHeight;
    }
  };

  const autoResize = () => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    textarea.style.height = 'auto';
    const lineHeight = parseFloat(getComputedStyle(textarea).lineHeight) || 20;
    const maxHeight = lineHeight * maxRows +
      parseFloat(getComputedStyle(textarea).paddingTop) +
      parseFloat(getComputedStyle(textarea).paddingBottom);
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = `${newHeight}px`;
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden';
    ensureLogScroll();
  };

  useEffect(() => {
    autoResize();
  }, []);

  // Speech Recognition API
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

    if (!SpeechRecognition) {
      setIsSpeechSupported(false);
      return;
    }

    recognitionRef.current = new SpeechRecognition();
    recognitionRef.current.continuous = false;
    recognitionRef.current.interimResults = true;
    recognitionRef.current.lang = 'ru-RU';

    recognitionRef.current.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0])
        .map((result) => result.transcript)
        .join('');
      setValue(transcript);
    };

    recognitionRef.current.onerror = (event) => {
      console.error('Speech recognition error', event.error);
      setIsListening(false);
      if (event.error === 'not-allowed') {
        alert('Пожалуйста, разрешите доступ к микрофону в настройках браузера');
      }
    };

    recognitionRef.current.onend = () => {
      setIsListening(false);
    };

    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, []);

  const handleSend = () => {
    const trimmed = value.trim();
    if (!trimmed) return;
    onSend(trimmed);
    setValue('');
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.overflowY = 'hidden';
    }
    ensureLogScroll();
  };

  const toggleListening = () => {
    if (!isSpeechSupported) {
      alert('Распознавание речи не поддерживается в вашем браузере. Пожалуйста, используйте Chrome, Edge или Safari.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      try {
        setValue('');
        recognitionRef.current.start();
        setIsListening(true);
      } catch (error) {
        console.error('Error starting speech recognition:', error);
        alert('Ошибка доступа к микрофону. Проверьте разрешения.');
        setIsListening(false);
      }
    }
  };

  return (
    <div className="chat-input-row">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          autoResize();
        }}
        placeholder="Напишите сообщение..."
        rows={1}
        className="chat-input"
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
          }
        }}
      />
      <div className="chat-actions">
        <button type="button" className="chat-action-btn" onClick={handleSend} aria-label="Отправить сообщением">
          ⌯⌲
        </button>
        <button 
          type="button" 
          className={`chat-action-btn ${isListening ? 'listening' : ''}`}
          onClick={toggleListening}
          aria-label={isListening ? 'Остановить запись' : 'Записать голосовое'}
        >
          🎙️
        </button>
      </div>
    </div>
  );
}

// Carousel placeholder content for 7 steps
function CarouselContent({ index, cards }) {
  const items = cards;
  if (!items.length) {
    return null;
  }
  const clamped = Math.max(0, Math.min(index, items.length - 1));
  const card = items[clamped];
  return (
    <div className="carousel-card">
      {card?.render()}
    </div>
  );
}

function PlaceholderCard() {
  return (
    <div className="placeholder-card">
      <h3>Ожидаем ваше воображение...</h3>
      <p>
        Расскажите немного о себе, и мы подберём идеальные карточки с расписанием,
        задачами и вдохновением для вашей новой профессии.
      </p>
    </div>
  );
}

function ScheduleCard({ profession, schedule }) {
  return (
    <div className="schedule-card">
      <header className="schedule-card__header">
        <h3>Типичный день {profession}</h3>
        <p>
          Гибкое расписание на весь рабочий день — чем живёт специалист на практике.
        </p>
      </header>
      <div className="schedule-grid">
        {[
          { key: 'morning', label: 'Утро', events: schedule.morning },
          { key: 'afternoon', label: 'День', events: schedule.afternoon },
          { key: 'evening', label: 'Вечер', events: schedule.evening },
        ].map((column) => (
          <div className="schedule-column" key={column.key}>
            <div className="schedule-column__title">{column.label}</div>
            <div className="schedule-events">
              {column.events.map((event, idx) => (
                <div className="schedule-event" key={idx}>
                  <span className="schedule-event__time">{event.time}</span>
                  <span className="schedule-event__text">{event.title}</span>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function GrowthMatrixCard({ stack, impact, growth }) {
  const columns = [
    { key: 'stack', label: 'Стек технологий', items: stack },
    { key: 'impact', label: 'Польза для компании', items: impact },
    { key: 'growth', label: 'Пути роста', items: growth },
  ];

  const rows = stack.slice(0, 3).map((_, idx) => idx);

  return (
    <div className="matrix-card">
      <header className="matrix-card__header">
        <h3>Карта развития компетенций</h3>
        <p>Какие навыки растишь, какой эффект приносишь и куда движешься дальше.</p>
      </header>
      <div className="matrix-table">
        {columns.map((column) => (
          <div className="matrix-table__cell matrix-table__cell--head" key={`head-${column.key}`}>
            {column.label}
          </div>
        ))}
        {rows.map((rowIdx) => (
          columns.map((column) => {
            const item = column.items[rowIdx];
            return (
              <div className="matrix-table__cell" key={`${column.key}-${rowIdx}`}>
                <span className="matrix-item__title">{item.title}</span>
                <span className="matrix-item__description">{item.description}</span>
              </div>
            );
          })
        ))}
      </div>
    </div>
  );
}

function InboxPreviewCard() {
  const messages = useMemo(() => {
    const source = [
      {
        type: 'long',
        author: 'Team Lead',
        preview: 'Круто закрыл фичу! Закинул тебе ревью на следующую задачу — глянь, там есть интересный эксперимент с серверными компонентами. '
          + 'Если будут идеи по оптимизации, пиши прямо в тред, обсудим вместе.',
      },
      {
        type: 'short',
        author: 'Product Manager',
        preview: 'Готов ли прототип новой воронки? Хочу показать на демо клиенту завтра утром.',
      },
      {
        type: 'short',
        author: 'Design Chapter',
        preview: 'Залил фреймы в Figma, там новые анимации и ховеры под твой компонент.',
      },
      {
        type: 'short',
        author: 'QA Team',
        preview: 'Сборка зелёная. Нашёл один edge-case с валидацией — смотри тикет #347.',
      },
      {
        type: 'medium',
        author: 'HR Partner',
        preview: 'Напоминаю про митап по карьере завтра в 16:00. Будет блок про менторство и дележ опыта.',
      },
      {
        type: 'medium',
        author: 'Analytics',
        preview: 'Новая метрика по вовлечённости выросла на 12%. Можно обсудить, как закрепить результат.',
      },
    ];

    const shuffled = [...source]
      .map(item => ({ item, sort: Math.random() }))
      .sort((a, b) => a.sort - b.sort)
      .map(({ item }) => item);

    const selection = shuffled.reduce(
      (acc, message) => {
        if (message.type === 'long' && !acc.long) acc.long = message;
        else if (message.type === 'short' && acc.shorts.length < 3) acc.shorts.push(message);
        else if (message.type === 'medium' && acc.mediums.length < 2) acc.mediums.push(message);
        return acc;
      },
      { long: null, shorts: [], mediums: [] }
    );

    const sectionOrder = ['long', 'shorts', 'mediums']
      .map(type => ({ type, sort: Math.random() }))
      .sort((a, b) => a.sort - b.sort)
      .map(({ type }) => type);

    return { ...selection, order: sectionOrder };
  }, []);

  if (!messages.long) {
    return null;
  }

  return (
    <div className="inbox-card">
      <header className="inbox-card__header">
        <h3>Тебе пришло 6 новых сообщений!</h3>
        <p>Команда делится апдейтами, держим руку на пульсе.</p>
      </header>
      <div className="inbox-list">
        {messages.order.map((section) => {
          if (section === 'long') {
            return <MessageBubble variant="long" message={messages.long} key="long" />;
          }
          if (section === 'shorts') {
            return (
              <div className="inbox-row inbox-row--shorts" key="shorts">
                {messages.shorts.map((msg, idx) => (
                  <MessageBubble variant="short" message={msg} key={`short-${idx}`} />
                ))}
              </div>
            );
          }
          return (
            <div className="inbox-row inbox-row--mediums" key="mediums">
              {messages.mediums.map((msg, idx) => (
                <MessageBubble variant="medium" message={msg} key={`medium-${idx}`} />
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}

function MessagesCard({ messages, profession }) {
  const longBubble = messages.long?.[0]
    ? { type: 'long', author: 'Руководитель', preview: messages.long[0] }
    : null;
  const mediumBubbles = (messages.medium ?? []).map((text, idx) => ({
    type: 'medium',
    author: `Коллега ${idx + 1}`,
    preview: text,
  }));
  const shortBubbles = (messages.short ?? []).map((text, idx) => ({
    type: 'short',
    author: `Команда ${idx + 1}`,
    preview: text,
  }));

  return (
    <div className="inbox-card">
      <header className="inbox-card__header">
        <h3>Команда приветствует {profession}</h3>
        <p>Испытай атмосферу — задачи, вопросы и поддержка на лету.</p>
      </header>
      <div className="inbox-list">
        {longBubble && <MessageBubble variant="long" message={longBubble} key="long-ai" />}
        {shortBubbles.length > 0 && (
          <div className="inbox-row inbox-row--shorts" key="shorts-ai">
            {shortBubbles.map((msg, idx) => (
              <MessageBubble variant="short" message={msg} key={`short-ai-${idx}`} />
            ))}
          </div>
        )}
        {mediumBubbles.length > 0 && (
          <div className="inbox-row inbox-row--mediums" key="mediums-ai">
            {mediumBubbles.map((msg, idx) => (
              <MessageBubble variant="medium" message={msg} key={`medium-ai-${idx}`} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function MessageBubble({ variant, message }) {
  const className = `message-bubble message-bubble--${variant}`;
  return (
    <div className={className}>
      <span className="message-bubble__author">{message.author}</span>
      <span className="message-bubble__text">{message.preview}</span>
    </div>
  );
}

function OpportunityCard({ stats, vacancies, courses }) {
  return (
    <div className="opportunity-card">
      <header className="opportunity-card__header">
        <h3>Перспективы и точки роста</h3>
        <p>Куда двигаться дальше и где применять навыки прямо сейчас.</p>
      </header>
      <div className="opportunity-grid">
        <div className="opportunity-column opportunity-column--stats">
          <div className="opportunity-column__title">Точки роста</div>
          <div className="opportunity-stats">
            {stats.map((item, idx) => (
              <div className="opportunity-stat" key={idx}>
                <span className="opportunity-stat__label">{item.label}</span>
                <span className="opportunity-stat__value">{item.value}</span>
              </div>
            ))}
          </div>
        </div>
        <div className="opportunity-column">
          <div className="opportunity-column__title">Вакансии</div>
          <div className="opportunity-cards">
            {vacancies.map((vac, idx) => (
              <a className="opportunity-card__link" href={vac.href} target="_blank" rel="noreferrer" key={`vac-${idx}`}>
                <span className="opportunity-card__title">{vac.title}</span>
                <div className="opportunity-card__footer">
                  <span className="opportunity-card__meta">{vac.salary}</span>
                  <span className="opportunity-card__icon" aria-hidden="true">⬊</span>
                </div>
              </a>
            ))}
          </div>
        </div>
        <div className="opportunity-column">
          <div className="opportunity-column__title">Курсы</div>
          <div className="opportunity-cards">
            {courses.map((course, idx) => (
              <a className="opportunity-card__link" href={course.href} target="_blank" rel="noreferrer" key={`course-${idx}`}>
                <span className="opportunity-card__title">{course.title}</span>
                <div className="opportunity-card__footer">
                  <span className="opportunity-card__meta">{course.provider}</span>
                  <span className="opportunity-card__icon" aria-hidden="true">⬊</span>
                </div>
              </a>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// Image panel with animated noise placeholder
function ImagePanel({ url }) {
  const [loaded, setLoaded] = useState(false);
  useEffect(()=>{ setLoaded(false); }, [url]);
  return (
    <div className="image-panel tilt-follow" data-tilt-depth="0.6">
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
      <div className="rendering-label">{waiting ? 'Ожидаем ваше воображение…' : 'Рендерим вайб…'}</div>
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
    <div className="settings-backdrop" role="presentation" onClick={()=>setOpen(false)}>
      <div
        className="settings-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="settings-title"
        onClick={e=>e.stopPropagation()}
      >
        <h3 id="settings-title" className="settings-title">Настройки звуков</h3>
        <div className="settings-list">
          {sounds.map(s=> (
            <div key={s.id} className="settings-item">
              <div className="settings-info">
                <div className="settings-name">{s.name}</div>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={s.volume}
                  className="settings-slider"
                  onChange={e=> setSounds(prev=> prev.map(p=> p.id===s.id? {...p, volume:Number(e.target.value)}:p))}
                />
              </div>
              <label className="settings-toggle">
                <input
                  type="checkbox"
                  checked={s.enabled}
                  onChange={e=> setSounds(prev=> prev.map(p=> p.id===s.id? {...p, enabled:e.target.checked}:p))}
                />
                <span className="settings-toggle-track"><span className="settings-toggle-thumb" /></span>
                <span className="settings-toggle-text">Вкл</span>
              </label>
            </div>
          ))}
        </div>
        <div className="settings-actions">
          <button className="settings-close" type="button" onClick={()=> setOpen(false)}>Закрыть</button>
        </div>
      </div>
    </div>
  );
}

