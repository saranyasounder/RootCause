import { useMemo, useState } from 'react'

const API = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000'

const EXAMPLES = [
  'What does error S-3005 mean on SVR-R740-02?',
  'How do I replace a failed hard drive?',
  'How long is the warranty?',
]

const CITATION_SPLIT = /(\[pages?\s+[\d\s,–-]+\])/gi
const isCitation = (s) => /^\[pages?\s+[\d\s,–-]+\]$/i.test(s)

function citedPages(text) {
  return [...text.matchAll(/\[pages?\s+([\d\s,–-]+)\]/gi)].flatMap((m) =>
    m[1].match(/\d+/g).map(Number),
  )
}

function groupSources(sources) {
  const byPage = new Map()
  sources.forEach((s) => {
    const current = byPage.get(s.page_number) || { page: s.page_number, hit: false }
    current.hit = current.hit || Boolean(s.is_hit)
    byPage.set(s.page_number, current)
  })
  return [...byPage.values()].sort((a, b) => a.page - b.page)
}

function Inline({ text, lit, onHover, onPin }) {
  return text.split(CITATION_SPLIT).map((piece, i) => {
    if (isCitation(piece)) {
      return piece.match(/\d+/g).map((n) => {
        const page = Number(n)
        return (
          <button
            key={`${i}-${page}`}
            type="button"
            className={`cite${lit === page ? ' lit' : ''}`}
            onMouseEnter={() => onHover(page)}
            onMouseLeave={() => onHover(null)}
            onFocus={() => onHover(page)}
            onBlur={() => onHover(null)}
            onClick={() => onPin(page)}
            aria-label={`Manual page ${page}`}
          >
            p. {page}
          </button>
        )
      })
    }
    return piece.split(/(\*\*[^*]+\*\*)/g).map((chunk, j) =>
      chunk.startsWith('**') && chunk.endsWith('**') && chunk.length > 4 ? (
        <strong key={`${i}-${j}`}>{chunk.slice(2, -2)}</strong>
      ) : (
        <span key={`${i}-${j}`}>{chunk}</span>
      ),
    )
  })
}

function AnswerText({ text, lit, onHover, onPin }) {
  const blocks = []
  let list = null
  text.split('\n').forEach((raw) => {
    const line = raw.trim()
    if (!line) {
      list = null
      return
    }
    const item = line.match(/^(?:[-•*]|\d+[.)])\s+(.*)$/)
    if (item) {
      if (!list) {
        list = { type: 'list', ordered: /^\d/.test(line), items: [] }
        blocks.push(list)
      }
      list.items.push(item[1])
    } else {
      list = null
      blocks.push({ type: 'p', text: line })
    }
  })

  const inline = (t) => <Inline text={t} lit={lit} onHover={onHover} onPin={onPin} />

  return (
    <div className="answer">
      {blocks.map((b, i) => {
        if (b.type === 'p') return <p key={i}>{inline(b.text)}</p>
        const Tag = b.ordered ? 'ol' : 'ul'
        return (
          <Tag key={i}>
            {b.items.map((t, j) => (
              <li key={j}>{inline(t)}</li>
            ))}
          </Tag>
        )
      })}
    </div>
  )
}

function SemanticResult({ data }) {
  const [hover, setHover] = useState(null)
  const [pinned, setPinned] = useState(null)
  const lit = hover ?? pinned
  const pages = useMemo(() => groupSources(data.sources || []), [data])
  const cited = useMemo(
    () => new Set(data.answer ? citedPages(data.answer) : []),
    [data],
  )
  const togglePin = (p) => setPinned((cur) => (cur === p ? null : p))

  return (
    <div className="layout">
      <div className="main">
        <p className="path">Searched the service manual</p>
        {data.answer ? (
          <AnswerText text={data.answer} lit={lit} onHover={setHover} onPin={togglePin} />
        ) : (
          <p className="notice">
            {data.error || 'No answer was generated.'} The manual pages that matched your
            question are listed at the right.
          </p>
        )}
      </div>

      <aside className="margin" aria-label="Manual pages used">
        <h2>Manual pages</h2>
        <ul className="tabs">
          {pages.map((p) => (
            <li
              key={p.page}
              className={`tab${p.hit ? ' hit' : ''}${cited.has(p.page) ? ' cited' : ''}${
                lit === p.page ? ' lit' : ''
              }`}
            >
              p. {p.page}
            </li>
          ))}
        </ul>
        <ul className="legend">
          <li>
            <span className="swatch hit" />
            Top match for your question
          </li>
          <li>
            <span className="swatch" />
            Added for context
          </li>
          {data.answer && (
            <li>
              <span className="swatch marker" />
              Cited in the answer
            </li>
          )}
        </ul>
      </aside>
    </div>
  )
}

function StructuredResult({ data }) {
  const rows = data.results || []
  const subject = [data.error_code, data.equipment_id && `on ${data.equipment_id}`]
    .filter(Boolean)
    .join(' ')

  return (
    <div className="layout single">
      <div className="main">
        <p className="path">Looked up in the error-code database</p>
        {rows.length === 0 ? (
          <p className="notice">
            No record matches {subject}. Check the code and the equipment ID.
          </p>
        ) : (
          rows.map((r) => (
            <section className="record" key={`${r.equipment_id}-${r.error_code}`}>
              <h2>
                {r.error_code} on {r.equipment_id}
              </h2>
              <p className="record-sub">
                {r.model}, {r.equipment_type}
              </p>
              <dl>
                <dt>Severity</dt>
                <dd className={`sev sev-${String(r.severity).toLowerCase()}`}>{r.severity}</dd>
                <dt>What it means</dt>
                <dd>{r.error_description}</dd>
                <dt>Likely cause</dt>
                <dd>{r.typical_cause}</dd>
                <dt>Recommended action</dt>
                <dd>{r.recommended_action}</dd>
              </dl>
            </section>
          ))
        )}
      </div>
    </div>
  )
}

export default function App() {
  const [question, setQuestion] = useState('')
  const [status, setStatus] = useState('idle')
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [runId, setRunId] = useState(0)

  async function run(q) {
    setStatus('loading')
    setResult(null)
    setError(null)
    try {
      const res = await fetch(`${API}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: q }),
      })
      if (!res.ok) throw new Error(`The API returned status ${res.status}.`)
      setResult(await res.json())
      setRunId((n) => n + 1)
      setStatus('done')
    } catch (e) {
      setError(
        e instanceof TypeError
          ? `Can't reach the API at ${API}. Start it with: python -m uvicorn main:app --reload`
          : e.message,
      )
      setStatus('error')
    }
  }

  function onSubmit(e) {
    e.preventDefault()
    const q = question.trim()
    if (q) run(q)
  }

  function useExample(q) {
    setQuestion(q)
    run(q)
  }

  return (
    <div className="app">
      <main className="sheet">
        <h1>Equipment Support Copilot</h1>
        <p className="lede">
          Ask about an error code or a repair procedure. Answers come from the Dell PowerEdge
          R740 service manual and the error-code database, and each claim names its page.
        </p>

        <form className="ask" onSubmit={onSubmit}>
          <label htmlFor="q" className="visually-hidden">
            Your question
          </label>
          <input
            id="q"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Describe the problem or enter an error code"
            autoComplete="off"
          />
          <button type="submit" disabled={status === 'loading'}>
            Ask
          </button>
        </form>

        <div className="examples">
          <span>Try</span>
          {EXAMPLES.map((ex) => (
            <button key={ex} type="button" onClick={() => useExample(ex)} disabled={status === 'loading'}>
              {ex}
            </button>
          ))}
        </div>

        <div className="result" aria-live="polite">
          {status === 'loading' && (
            <p className="notice" role="status">
              Searching the manual…
            </p>
          )}
          {status === 'error' && <p className="notice error">{error}</p>}
          {status === 'done' && result && result.path === 'structured' && (
            <StructuredResult key={runId} data={result} />
          )}
          {status === 'done' && result && result.path !== 'structured' && (
            <SemanticResult key={runId} data={result} />
          )}
        </div>

        <p className="fine">
          Source: Dell PowerEdge R740 Installation and Service Manual. The equipment and
          error-code records are synthetic data created for this project.
        </p>
      </main>
    </div>
  )
}