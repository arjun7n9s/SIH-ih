import { Link } from "react-router-dom";
import { FeatureIcon } from "../components/FeatureIcon";
import { FEATURES } from "../lib/api";
import { MARK_SRC } from "../lib/brand";

const STEPS = [
  {
    title: "Ask the campus question",
    body: "Fees, attendance, hostels, refunds — in English or Hinglish, typed or spoken.",
  },
  {
    title: "Retrieve from official docs",
    body: "Suchna searches the curated IIITDMJ corpus and surfaces the chunks that matter.",
  },
  {
    title: "Read with receipts",
    body: "Citations, freshness dates, tables, and open contradictions stay on the page.",
  },
];

export function Landing() {
  return (
    <div className="suchna-paper min-h-dvh">
      <header className="border-b-2 border-ink">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <div className="flex items-center gap-3">
            <img src={MARK_SRC} alt="" className="h-10 w-10 object-contain" />
            <div>
              <p className="suchna-kicker">PDPM IIITDM Jabalpur</p>
              <p className="text-lg font-semibold tracking-tight">Suchna</p>
            </div>
          </div>
          <nav className="flex items-center gap-4 font-mono text-[11px] uppercase tracking-[0.16em]">
            <a href="#features" className="hidden hover:text-poster sm:inline">
              Features
            </a>
            <Link to="/contradictions" className="hidden hover:text-poster md:inline">
              Contradictions
            </Link>
            <Link to="/app" className="suchna-stamp" style={{ fontSize: "0.95rem", padding: "0.5rem 0.9rem" }}>
              Open →
            </Link>
          </nav>
        </div>
        <div className="suchna-tripwire" />
      </header>

      <main>
        <section className="relative mx-auto grid max-w-6xl gap-12 px-5 pb-16 pt-12 lg:grid-cols-[1.15fr_0.85fr] lg:items-end lg:pb-20 lg:pt-16">
          <div className="relative">
            <span className="suchna-edge-label absolute -left-1 -top-3 sm:-left-2">
              Official corpus
            </span>
            <p className="suchna-kicker suchna-slam mt-8">Campus knowledge assistant</p>
            <h1 className="suchna-poster suchna-slam suchna-slam-delay mt-4 max-w-[11ch] text-[clamp(3.2rem,8vw,5.6rem)] text-ink">
              Ask the
              <br />
              institute.
              <br />
              <span className="text-poster">Get the page.</span>
            </h1>
            <div className="suchna-rule mt-6 max-w-md" />
            <p className="suchna-slam mt-5 max-w-md text-base leading-relaxed text-muted sm:text-lg">
              Suchna answers IIITDM Jabalpur policy questions with citations, fee tables,
              freshness badges, and honest contradiction cards — for students who need
              the ordinance, not a guess.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link to="/app" className="suchna-stamp">
                Start asking →
              </Link>
              <a href="#how" className="suchna-stamp-ghost">
                How it works
              </a>
            </div>
            <ul className="mt-8 grid max-w-lg gap-2 font-mono text-[11px] uppercase tracking-[0.14em] text-muted sm:grid-cols-2">
              {[
                "Official corpus only",
                "Hinglish voice",
                "Streaming answers",
                "Open contradictions",
              ].map((item) => (
                <li key={item} className="flex items-center gap-2 border-b border-ink/15 pb-2">
                  <span className="inline-block h-2 w-2 bg-poster" />
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <div className="relative lg:mb-4">
            <div className="suchna-panel suchna-panel-blue p-5 sm:p-6">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <img
                    src={MARK_SRC}
                    alt=""
                    className="h-14 w-14 object-contain"
                  />
                  <div>
                    <p className="font-semibold">Hello — Suchna</p>
                    <p className="mt-0.5 text-sm text-muted">Your campus knowledge partner</p>
                  </div>
                </div>
                <span className="border-2 border-ink bg-green-soft px-2 py-0.5 font-mono text-[10px] uppercase tracking-wider">
                  Live
                </span>
              </div>

              <div className="suchna-rule my-5" />

              <div className="space-y-2">
                {[
                  ["Ask fees & refunds", "Tables when money is on the line."],
                  ["Catch disagreeing PDFs", "Both sources stay visible."],
                  ["Speak Hinglish", "Talk, then send a cited answer."],
                ].map(([title, body]) => (
                  <div
                    key={title}
                    className="flex items-center justify-between gap-3 border-2 border-ink bg-mist/60 px-3 py-3"
                  >
                    <div>
                      <p className="text-sm font-semibold">{title}</p>
                      <p className="mt-0.5 text-xs text-muted">{body}</p>
                    </div>
                    <span className="font-mono text-xs text-trip">→</span>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex items-end gap-2 border-b-2 border-ink pb-2">
                <span className="flex-1 font-mono text-xs uppercase tracking-wider text-muted">
                  Ask anything campus…
                </span>
                <span className="suchna-kicker" style={{ color: "var(--color-trip)" }}>Enter</span>
              </div>
            </div>
          </div>
        </section>

        <section id="features" className="border-y-2 border-ink bg-mist/50">
          <div className="mx-auto max-w-6xl px-5 py-16">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
              <div className="max-w-xl">
                <p className="suchna-kicker" style={{ color: "var(--color-trip)" }}>Features</p>
                <h2 className="suchna-poster mt-2 text-4xl text-ink sm:text-5xl">
                  Built for
                  <br />
                  confusing paperwork
                </h2>
              </div>
              <p className="max-w-sm text-sm leading-relaxed text-muted">
                Built on IIITDMJ ordinances, fee circulars, and hostel pages — so a
                student can open the same PDF the answer came from.
              </p>
            </div>

            <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {FEATURES.map((f, i) => (
                <article
                  key={f.title}
                  className={`border-2 border-ink bg-paper p-5 ${
                    i % 3 === 1 ? "suchna-panel-blue shadow-[6px_6px_0_var(--color-trip)]" : "shadow-[6px_6px_0_var(--color-poster)]"
                  }`}
                >
                  <FeatureIcon name={f.icon} />
                  <h3 className="mt-4 text-base font-semibold">{f.title}</h3>
                  <p className="mt-2 text-sm leading-relaxed text-muted">{f.body}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="how" className="mx-auto max-w-6xl px-5 py-16">
          <div className="grid gap-10 lg:grid-cols-[0.85fr_1.15fr] lg:items-start">
            <div>
              <p className="suchna-kicker">How it works</p>
              <h2 className="suchna-poster mt-2 text-4xl sm:text-5xl">
                Type your prompt.
                <br />
                <span className="text-trip">Get receipts.</span>
              </h2>
              <p className="mt-4 text-sm leading-relaxed text-muted">
                Ask in the language you actually use. Suchna searches the campus corpus
                and keeps sources, dates, and disagreements on the page.
              </p>
            </div>
            <ol className="space-y-3">
              {STEPS.map((step, i) => (
                <li
                  key={step.title}
                  className="flex gap-4 border-2 border-ink bg-paper p-5 shadow-[5px_5px_0_var(--color-ink)]"
                >
                  <span className="suchna-poster grid h-10 w-10 shrink-0 place-items-center bg-poster text-lg text-paper">
                    {i + 1}
                  </span>
                  <div>
                    <h3 className="font-semibold">{step.title}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-muted">{step.body}</p>
                  </div>
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section className="px-5 pb-20">
          <div className="suchna-ink-field mx-auto flex max-w-6xl flex-col items-start justify-between gap-6 border-2 border-ink px-6 py-10 sm:flex-row sm:items-center sm:px-10">
            <div>
              <p className="suchna-kicker">Ready for demo day</p>
              <h2 className="suchna-poster mt-2 text-3xl text-paper sm:text-4xl">
                Open Suchna.
                <br />
                Ask a real question.
              </h2>
              <p className="mt-3 max-w-xl text-sm text-paper/75">
                Hostel fees, attendance, refund windows — type or speak, including
                Hinglish, then open the circular yourself.
              </p>
            </div>
            <Link
              to="/app"
              className="suchna-stamp"
              style={{
                background: "var(--color-paper)",
                color: "var(--color-ink)",
                boxShadow: "7px 7px 0 var(--color-trip)",
              }}
            >
              Launch →
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t-2 border-ink">
        <div className="mx-auto flex max-w-6xl flex-col gap-2 px-5 py-6 font-mono text-[11px] uppercase tracking-[0.16em] text-muted sm:flex-row sm:items-center sm:justify-between">
          <p>Suchna · PDPM IIITDM Jabalpur · SIH</p>
          <p>PDPM IIITDM Jabalpur campus knowledge desk</p>
        </div>
      </footer>
    </div>
  );
}
