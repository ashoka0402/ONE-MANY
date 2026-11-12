"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import {
  AnimatePresence, motion, useMotionValueEvent, useReducedMotion,
  useScroll, useTransform,
} from "motion/react";
import {
  ArrowDown, ArrowRight, ArrowUpRight, CalendarDays, Check, CheckCircle2,
  CircleDollarSign, CreditCard, Fingerprint,
  HeartHandshake, LockKeyhole, Menu, MousePointer2, Plus,
  ReceiptText, ShieldCheck, Sparkles, Users, WandSparkles, X,
} from "lucide-react";

const examples = [
  {
    item: "Pressure washer",
    need: "I need to clean my patio this weekend.",
    icon: "01",
    area: "Baner, Pune",
    price: 400,
    members: 4,
    match: "3 potential neighbors",
    initials: ["A", "J", "M", "S"],
  },
  {
    item: "Portable projector",
    need: "A projector for our film nights.",
    icon: "02",
    area: "Aundh, Pune",
    price: 360,
    members: 3,
    match: "2 potential neighbors",
    initials: ["A", "R", "K"],
  },
  {
    item: "Cordless drill",
    need: "A drill for the shelves I am putting up.",
    icon: "03",
    area: "Hinjawadi, Pune",
    price: 240,
    members: 3,
    match: "2 potential neighbors",
    initials: ["A", "N", "T"],
  },
];

const stages = [
  {
    number: "01",
    eyebrow: "START WITH A NEED",
    title: "Just say what you need.",
    description: "No catalog hunting. Tell us the task, the area and the dates. Gemini can identify the reusable item behind your words.",
    pill: "AI EXTRACTION",
    quote: "I need to clean my patio this weekend.",
  },
  {
    number: "02",
    eyebrow: "FIND YOUR PEOPLE",
    title: "The right people find each other.",
    description: "Potential matches consider the item, the neighborhood and the dates. Requests are only discoverable when their owners choose to opt in.",
    pill: "OPT-IN DISCOVERY",
    quote: "3 compatible needs · Baner, Pune",
  },
  {
    number: "03",
    eyebrow: "MAKE A SHARED PLAN",
    title: "Everyone gets their turn.",
    description: "Review a hypothetical cost split, approve your own Sandbox contribution and plan usage on a shared calendar. Nobody is charged without choosing to participate.",
    pill: "CONSENT FIRST",
    quote: "One item. Four separate reasons.",
  },
];

const faqs = [
  {
    question: "Is this a live marketplace?",
    answer: "ONE / MANY is a working demo for matching compatible needs and coordinating potential shared purchases. Catalog results depend on the configured provider. Physical purchasing and handover are not automated.",
  },
  {
    question: "Are payments real?",
    answer: "No real-money payments are processed in this demo. Funding uses PayPal Sandbox, and the ledger distinguishes verified Sandbox captures from proposed or pending amounts.",
  },
  {
    question: "Does everyone get matched automatically?",
    answer: "No. Discovery is optional. People must explicitly opt in, and matching is based on compatible assets, locations, features and dates. A potential match is not an agreement.",
  },
  {
    question: "What does Gemini actually do?",
    answer: "Gemini extracts structured information from the request: reusable asset type, purpose, required or excluded features, and whether the item is suitable for sharing. You can inspect the result before taking any further action.",
  },
];

const numberFormat = (value: number) => "$" + value.toLocaleString("en-US", { maximumFractionDigits: 2, minimumFractionDigits: 2 });

function Reveal({ children, className = "", delay = 0 }: {
  children: React.ReactNode; className?: string; delay?: number;
}) {
  const reduced = useReducedMotion();
  return (
    <motion.div
      className={className}
      initial={reduced ? false : { opacity: 0, y: 30 }}
      whileInView={reduced ? undefined : { opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-8% 0px -8% 0px" }}
      transition={{ duration: 0.7, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </motion.div>
  );
}

function BrandMark({ light = false }: { light?: boolean }) {
  return (
    <Link href="/" className={"lp-logo" + (light ? " lp-logo-light" : "")} aria-label="ONE / MANY home">
      <span className="lp-logo-sign" aria-hidden="true"><HeartHandshake size={22} strokeWidth={2.2} /></span>
      <span>ONE <i>/</i> MANY</span>
    </Link>
  );
}

function MiniAvatar({ letter, index }: { letter: string; index: number }) {
  return <span className={"lp-avatar lp-avatar-" + index} aria-label={"Example person " + letter}>{letter}</span>;
}

function ProductPreview({ current, onChange }: { current: number; onChange: (n: number) => void }) {
  const item = examples[current];
  return (
    <div className="lp-preview">
      <div className="lp-preview-aura" aria-hidden="true" />
      <div className="lp-preview-topline">
        <span className="lp-green-dot" />
        <span>THE POSSIBILITY ENGINE</span>
        <span className="lp-preview-topline-right">INTERACTIVE PREVIEW / 001</span>
      </div>
      <div className="lp-preview-window">
        <div className="lp-preview-window-head">
          <div className="lp-window-dots"><span /><span /><span /></div>
          <span>one-many / discover</span>
          <span className="lp-preview-connected"><span /> sample environment</span>
        </div>
        <div className="lp-preview-window-body">
          <div className="lp-preview-kicker"><Sparkles size={13} /> FROM ONE IDEA TO A SHARED POSSIBILITY</div>
          <h3>Good things <em>go further.</em></h3>
          <p>Tell us what you need. See what sharing could look like.</p>
          <div className="lp-message">
            <div className="lp-message-user"><span className="lp-message-icon"><MousePointer2 size={16} /></span><span>YOUR NEED</span><span>01 / 03</span></div>
            <AnimatePresence mode="wait" initial={false}>
              <motion.p key={item.need} initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -7 }} transition={{ duration: .22 }}>
                “{item.need}”
              </motion.p>
            </AnimatePresence>
            <div className="lp-message-footer"><span><CheckCircle2 size={13} /> Extracted: {item.item}</span><span>{item.area}</span></div>
          </div>
          <div className="lp-preview-route" aria-hidden="true">
            <span className="lp-route-node"><Sparkles size={12} /></span>
            <div className="lp-route-track"><span /></div>
            <span className="lp-route-node"><Users size={12} /></span>
          </div>
          <div className="lp-preview-match">
            <div className="lp-preview-match-text"><span className="lp-micro-label">POSSIBLE COMMUNITY</span><strong>{item.match}</strong><small>Sample scenario · people are fictional</small></div>
            <div className="lp-avatar-stack">{item.initials.map((x, i) => <MiniAvatar key={i} letter={x} index={i} />)}</div>
          </div>
          <div className="lp-preview-total">
            <div><span className="lp-micro-label">ONE SHARED ITEM</span><strong>{item.item}</strong><small>Example item price: {numberFormat(item.price)}</small></div>
            <div className="lp-preview-saving"><small>Example share</small><strong>{numberFormat(item.price / item.members)}</strong><span>per person</span></div>
          </div>
        </div>
      </div>
      <div className="lp-preview-floating lp-float-one"><Check size={14} /> Need understood</div>
      <div className="lp-preview-floating lp-float-two"><Users size={14} /> {item.members} possible people</div>
      <div className="lp-preview-bottom">
        <div className="lp-preview-switches" aria-label="Choose an example">
          {examples.map((x, i) => (
            <button type="button" key={x.item} aria-pressed={i === current}
              className={i === current ? "is-active" : ""} onClick={() => onChange(i)}>
              <span>{x.icon}</span> {x.item}
            </button>
          ))}
        </div>
        <span>TRY A SCENARIO <ArrowUpRight size={14} /></span>
      </div>
    </div>
  );
}

function ScrollStory() {
  const ref = useRef<HTMLElement | null>(null);
  const reduced = useReducedMotion();
  const [active, setActive] = useState(0);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start 45%", "end 70%"] });
  const progress = useTransform(scrollYProgress, [0, 1], ["0%", "100%"]);
  useMotionValueEvent(scrollYProgress, "change", p => {
    if (reduced) return;
    const next = Math.min(2, Math.max(0, Math.floor(p * 3)));
    setActive(old => old === next ? old : next);
  });

  return (
    <section id="how-it-works" ref={ref} className="lp-story lp-container" aria-labelledby="lp-story-title">
      <div className="lp-story-head">
        <Reveal>
          <span className="lp-eyebrow"><span className="lp-index">01 /</span> AN EASIER WAY FORWARD</span>
          <h2 id="lp-story-title">From “I need this”<br />to <span className="lp-serif">“we have this.”</span></h2>
        </Reveal>
        <Reveal className="lp-story-head-right">Three small steps. One much better way to get things done.</Reveal>
      </div>
      <div className="lp-story-layout">
        <div className="lp-story-steps">
          <div className="lp-story-progress" aria-hidden="true"><motion.span style={{ height: progress }} /></div>
          {stages.map((s, i) => (
            <button key={s.number} type="button"
              className={"lp-story-step" + (active === i ? " is-active" : "")}
              aria-pressed={active === i} onClick={() => setActive(i)}>
              <span className="lp-step-number">{s.number}</span>
              <span><small>{s.eyebrow}</small><strong>{s.title}</strong><span className="lp-step-description">{s.description}</span></span>
              <ArrowUpRight size={18} />
            </button>
          ))}
        </div>
        <div className="lp-story-stage" aria-live="polite">
          <div className="lp-story-stage-top"><span><span className="lp-green-dot" /> ONE / MANY WORKSPACE</span><span>STAGE {stages[active].number} — 03</span></div>
          <AnimatePresence mode="wait" initial={false}>
            <motion.div key={active} className="lp-story-scene"
              initial={reduced ? false : { opacity: 0, y: 18, scale: .97 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={reduced ? {} : { opacity: 0, y: -14, scale: .98 }}
              transition={{ duration: .38, ease: "easeOut" }}>
              {active === 0 ? <>
                <div className="lp-scene-icon"><WandSparkles size={25} /></div>
                <span className="lp-scene-label">WHAT&apos;S ON YOUR MIND?</span>
                <div className="lp-scene-input">“{stages[0].quote}”<span className="lp-cursor" /></div>
                <div className="lp-scene-extraction"><span><Check size={15} /> Asset identified</span><strong>Pressure washer</strong><span>Reusable · physical asset</span></div>
              </> : active === 1 ? <>
                <div className="lp-scene-orbit"><div className="lp-scene-orbit-ring one" /><div className="lp-scene-orbit-ring two" /><span className="lp-orbit-core"><HeartHandshake size={32} /></span><span className="lp-orbit-person p1">A</span><span className="lp-orbit-person p2">J</span><span className="lp-orbit-person p3">M</span></div>
                <div className="lp-scene-matched"><CheckCircle2 size={17} /> 3 potential compatible neighbors</div>
                <small>Fictional illustration · opt-in required</small>
              </> : <>
                <div className="lp-scene-icon"><CircleDollarSign size={26} /></div>
                <span className="lp-scene-label">A CLEARER WAY TO SHARE</span>
                <div className="lp-scene-total">$400.00 <small>÷ 4 possible members</small></div>
                <div className="lp-scene-splits">{["A", "J", "M", "S"].map((letter, i) => <div key={letter}><MiniAvatar letter={letter} index={i} /><strong>$100</strong></div>)}</div>
                <div className="lp-scene-matched"><ShieldCheck size={17} /> Each person approves their own share</div>
              </>}
            </motion.div>
          </AnimatePresence>
          <div className="lp-story-stage-footer"><span>{stages[active].pill}</span><span>ILLUSTRATIVE FLOW <ArrowRight size={13} /></span></div>
        </div>
      </div>
    </section>
  );
}

export function LandingExperience() {
  const reduced = useReducedMotion();
  const [menuOpen, setMenuOpen] = useState(false);
  const [preview, setPreview] = useState(0);
  const [price, setPrice] = useState(400);
  const [members, setMembers] = useState(4);
  const [day, setDay] = useState(3);
  const [faq, setFaq] = useState<number | null>(0);

  const share = price / members;

  return (
    <div className="lp">
      <div className="lp-ambient lp-ambient-one" aria-hidden="true" />
      <div className="lp-ambient lp-ambient-two" aria-hidden="true" />
      <header className="lp-header">
        <div className="lp-header-inner lp-container">
          <BrandMark />
          <nav aria-label="Main navigation" className={"lp-nav" + (menuOpen ? " lp-nav-open" : "")}>
            <a href="#how-it-works" onClick={() => setMenuOpen(false)}>How it works</a>
            <a href="#explore" onClick={() => setMenuOpen(false)}>The experience</a>
            <a href="#the-math" onClick={() => setMenuOpen(false)}>The math</a>
            <a href="#faq" onClick={() => setMenuOpen(false)}>FAQ</a>
            <Link className="lp-mobile-cta" href="/app" onClick={() => setMenuOpen(false)}>Open workspace <ArrowUpRight size={16} /></Link>
          </nav>
          <div className="lp-header-actions"><span className="lp-header-live"><i /> BUILT FOR BETTER SHARING</span><Link href="/app" className="lp-header-button">Launch app <ArrowUpRight size={16} /></Link></div>
          <button type="button" className="lp-menu-button" aria-expanded={menuOpen} aria-label={menuOpen ? "Close menu" : "Open menu"} onClick={() => setMenuOpen(v => !v)}>{menuOpen ? <X size={23} /> : <Menu size={23} />}</button>
        </div>
      </header>

      <main id="main">
        <section className="lp-hero lp-container" aria-labelledby="lp-main-title">
          <div className="lp-hero-glow" aria-hidden="true" />
          <div className="lp-hero-copy">
            <Reveal className="lp-hero-pill"><span className="lp-green-dot" /> THE FUTURE OF THINGS IS SHARED <ArrowUpRight size={13} /></Reveal>
            <h1 id="lp-main-title">
              <motion.span initial={reduced ? false : { opacity: 0, y: 55 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .75 }}>Why own it</motion.span>
              <motion.span initial={reduced ? false : { opacity: 0, y: 55 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .75, delay: .12 }}>alone<span className="lp-title-punct">?</span></motion.span>
              <motion.span className="lp-hero-serif" initial={reduced ? false : { opacity: 0, y: 55 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .75, delay: .24 }}>Make it <em>ours.</em></motion.span>
            </h1>
            <Reveal className="lp-hero-paragraph" delay={.30}>
              That thing you need once in a while? Someone nearby needs it too. Discover possibilities, share the cost, and make more happen with less.
            </Reveal>
            <Reveal className="lp-hero-buttons" delay={.38}>
              <Link className="lp-button-primary" href="/app">Discover what&apos;s possible <ArrowUpRight size={19} /></Link>
              <a className="lp-button-ghost" href="#how-it-works"><span><ArrowDown size={16} /></span> See how it works</a>
            </Reveal>
            <Reveal className="lp-hero-caption" delay={.47}><div className="lp-caption-avatars">{["A", "J", "M"].map((letter, i) => <MiniAvatar letter={letter} index={i} key={letter} />)}</div><span>One idea. Many possibilities.<br /><strong>Explore a fictional example below.</strong></span></Reveal>
          </div>
          <Reveal className="lp-hero-visual" delay={.27}><ProductPreview current={preview} onChange={setPreview} /></Reveal>
          <div className="lp-scroll-cue"><span>SCROLL TO EXPLORE</span><ArrowDown size={15} /></div>
        </section>
        <section className="lp-signal">
          <div className="lp-signal-inner lp-container">
            <div><CheckCircle2 size={18} /><span>Built around real needs</span></div>
            <i />
            <div><Fingerprint size={18} /><span>Private until you opt in</span></div>
            <i />
            <div><CreditCard size={18} /><span>PayPal Sandbox demo</span></div>
            <i />
            <div><CalendarDays size={18} /><span>One shared calendar</span></div>
          </div>
        </section>

        <ScrollStory />

        <section id="explore" className="lp-explore lp-container" aria-labelledby="lp-explore-title">
          <Reveal className="lp-explore-intro">
            <span className="lp-eyebrow"><span className="lp-index">02 /</span> THOUGHTFUL BY DESIGN</span>
            <div><h2 id="lp-explore-title">Less friction.<br /><span className="lp-serif">More connection.</span></h2><p>Not another storefront. A place to turn everyday needs into shared possibilities, with a clear path from idea to agreement.</p></div>
          </Reveal>
          <div className="lp-bento">
            <Reveal className="lp-bento-card lp-bento-main">
              <div className="lp-bento-top"><span>01 / INTELLIGENT DISCOVERY</span><span className="lp-bento-icon"><WandSparkles size={20} /></span></div>
              <div className="lp-bento-chat">
                <span className="lp-chat-label"><Sparkles size={13} /> YOUR WORDS, UNDERSTOOD</span>
                <div className="lp-chat-bubble">“Need a projector for a neighborhood movie night.”</div>
                <div className="lp-chat-results"><span><CheckCircle2 size={14} /> Reusable asset</span><strong>Portable projector</strong><small>Gemini extraction in the live app</small></div>
              </div>
              <h3>Tell us the task. <em>Not the SKU.</em></h3>
              <p>Describe what you are doing. Let AI help identify the kind of item worth sharing.</p>
            </Reveal>
            <Reveal className="lp-bento-card lp-bento-privacy" delay={.08}>
              <div className="lp-bento-top"><span>02 / HUMAN CONSENT</span><span className="lp-bento-icon"><LockKeyhole size={20} /></span></div>
              <div className="lp-privacy-art"><div className="lp-privacy-outer"><div className="lp-privacy-inner"><Fingerprint size={64} strokeWidth={1} /></div></div><span className="lp-privacy-tag"><Check size={14} /> YOU&apos;RE IN CONTROL</span></div>
              <h3>Your need.<br /><em>Your choice.</em></h3><p>Discovery only happens with your permission. A match never means a purchase.</p>
            </Reveal>
            <Reveal className="lp-bento-card lp-bento-schedule" delay={.07}>
              <div className="lp-bento-top"><span>03 / SHARED TIME</span><span className="lp-bento-icon"><CalendarDays size={20} /></span></div>
              <div className="lp-week">
                {["M", "T", "W", "T", "F", "S", "S"].map((label, i) => (
                  <button type="button" key={i} onClick={() => setDay(i)}
                    aria-label={"Select example day " + (i + 1)} aria-pressed={day === i} className={day === i ? "active" : ""}>
                    <span>{label}</span><strong>{i + 16}</strong><i />
                  </button>
                ))}
              </div>
              <div className="lp-calendar-detail"><span className="lp-green-dot" /> {day === 3 || day === 5 ? "Example member booking" : "Example date available"}<span>Nov {day + 16}</span></div>
              <h3>One asset. <em>Everyone&apos;s turn.</em></h3><p>Coordinate the days on a shared, conflict-checked calendar after funding verification.</p>
            </Reveal>
            <Reveal className="lp-bento-card lp-bento-ledger" delay={.13}>
              <div className="lp-bento-top"><span>04 / ABSOLUTE CLARITY</span><span className="lp-bento-icon"><ReceiptText size={20} /></span></div>
              <div className="lp-ledger-visual"><div><span>Sample contribution</span><strong>$100.00</strong></div><span className="lp-ledger-success"><CheckCircle2 size={16} /> FICTIONAL EXAMPLE</span><div className="lp-ledger-line"><span /><span /><span /><span /></div></div>
              <h3>See every share. <em>Know the status.</em></h3><p>Clear funding states and a ledger based on server-verified Sandbox events.</p>
            </Reveal>
          </div>
        </section>

        <section id="the-math" className="lp-math" aria-labelledby="lp-math-title">
          <div className="lp-math-inner lp-container">
            <Reveal className="lp-math-copy">
              <span className="lp-eyebrow"><span className="lp-index">03 /</span> THE MATH FEELS DIFFERENT</span>
              <h2 id="lp-math-title">More than one person.<br /><span className="lp-serif">Less than the full price.</span></h2>
              <p>Play with a hypothetical cost split. The actual price, participants, taxes and terms still have to be confirmed before any decision.</p>
              <div className="lp-math-points"><span><Check size={16} /> No hidden assumptions</span><span><Check size={16} /> Your own decision</span><span><Check size={16} /> Shared use, clearly scheduled</span></div>
            </Reveal>
            <Reveal className="lp-calculator">
              <div className="lp-calculator-head"><div><span className="lp-micro-label">COST SHARING / INTERACTIVE</span><h3>Split the possibility.</h3></div><span><CircleDollarSign size={21} /></span></div>
              <label className="lp-calc-label" htmlFor="lp-price">Example item price <span>{numberFormat(price)}</span></label>
              <input id="lp-price" type="range" min={100} max={1000} step={50} value={price} onChange={e => setPrice(Number(e.target.value))} aria-valuetext={numberFormat(price)} />
              <div className="lp-calc-range"><span>$100</span><span>$1,000</span></div>
              <div className="lp-calc-members"><div><span className="lp-micro-label">HOW MANY PEOPLE?</span><strong>{members} people</strong></div><div className="lp-calc-member-buttons">{[2, 3, 4, 5].map(n => <button key={n} type="button" aria-pressed={members === n} onClick={() => setMembers(n)}>{n}</button>)}</div></div>
              <div className="lp-calc-result"><div><span>YOUR ILLUSTRATIVE SHARE</span><strong>{numberFormat(share)}</strong><small>of {numberFormat(price)} · split evenly</small></div><div><span>POTENTIAL DIFFERENCE</span><strong>{numberFormat(price - share)}</strong><small>vs. buying alone, before costs</small></div></div>
              <div className="lp-calculator-footer"><ShieldCheck size={16} /> Purely hypothetical. Not an offer, quote or actual saving.</div>
            </Reveal>
          </div>
        </section>

        <section className="lp-statement" aria-label="One many philosophy">
          <div className="lp-statement-track" aria-hidden="true"><span>OWN LESS <b>✳</b> DO MORE <b>✳</b> SHARE SMARTER <b>✳</b> OWN LESS <b>✳</b> DO MORE <b>✳</b> SHARE SMARTER <b>✳</b> </span></div>
          <div className="lp-statement-small">GOOD THINGS GET BETTER WHEN THEY&apos;RE SHARED.</div>
        </section>

        <section id="faq" className="lp-faq lp-container" aria-labelledby="lp-faq-title">
          <Reveal className="lp-faq-copy"><span className="lp-eyebrow"><span className="lp-index">04 /</span> A FEW GOOD QUESTIONS</span><h2 id="lp-faq-title">Clear minds.<br /><span className="lp-serif">Clear terms.</span></h2><p>We believe sharing should be easy to understand, not just easy to click.</p><Link href="/app" className="lp-inline-cta">Explore the workspace <ArrowUpRight size={17} /></Link></Reveal>
          <Reveal className="lp-accordions">
            {faqs.map((item, i) => <div className={"lp-faq-item" + (faq === i ? " active" : "")} key={item.question}>
              <h3><button type="button" onClick={() => setFaq(faq === i ? null : i)} aria-expanded={faq === i} aria-controls={"lp-faq-answer-" + i}><span>{item.question}</span><span className="lp-faq-toggle">{faq === i ? <X size={17} /> : <Plus size={17} />}</span></button></h3>
              <AnimatePresence initial={false}>{faq === i && <motion.div id={"lp-faq-answer-" + i} className="lp-faq-answer" initial={reduced ? false : { height: 0, opacity: 0 }} animate={{ height: "auto", opacity: 1 }} exit={reduced ? {} : { height: 0, opacity: 0 }} transition={{ duration: .28 }}><p>{item.answer}</p></motion.div>}</AnimatePresence>
            </div>)}
          </Reveal>
        </section>

        <section className="lp-final lp-container" aria-labelledby="lp-final-title">
          <div className="lp-final-glow" aria-hidden="true" />
          <Reveal className="lp-final-inner">
            <span className="lp-eyebrow"><span className="lp-green-dot" /> BETTER THINGS ARE BETTER TOGETHER</span>
            <h2 id="lp-final-title">One small need.<br /><em>A whole new way.</em></h2>
            <p>Start with your next project, errand, or idea. See what becomes possible when more people think together.</p>
            <Link href="/app" className="lp-button-primary">Step into ONE / MANY <ArrowUpRight size={19} /></Link>
            <span className="lp-final-disclaimer"><ShieldCheck size={15} /> PayPal Sandbox only · Physical purchases are not completed here</span>
          </Reveal>
        </section>
      </main>
      <footer className="lp-footer lp-container"><div><BrandMark light /><p>Less to own. More to do. Better together.</p></div><nav aria-label="Footer navigation"><a href="#how-it-works">How it works</a><a href="#explore">Features</a><a href="#faq">FAQ</a><Link href="/app">Launch app</Link></nav><div className="lp-footer-end"><span>ONE / MANY © 2026</span><span>DESIGNED FOR WHAT&apos;S NEXT.</span></div></footer>
    </div>
  );
}
