from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import streamlit as st
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
for _env_path in (ROOT / ".env", ROOT.parent / ".env"):
    try:
        load_dotenv(_env_path)
    except OSError:
        pass

INDEX_HTML = r'''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="theme-color" content="#091115" />
  <title>Aura Voice Intelligence</title>
</head>
<body>
  <section id="key-screen" class="screen active" aria-hidden="false">
    <canvas id="key-canvas" aria-hidden="true"></canvas>
    <div class="screen-vignette" aria-hidden="true"></div>
    <main class="key-layout">
      <section class="key-intro" aria-labelledby="welcome-title">
        <div class="brand-lockup">
          <span class="brand-emblem" aria-hidden="true"><span></span></span>
          <span class="brand-wordmark"><strong>AURA</strong><small>PERSONAL VOICE INTELLIGENCE</small></span>
        </div>
        <p class="eyebrow"><span class="eyebrow-mark"></span> A more natural way to think out loud</p>
        <h1 class="welcome-title" id="welcome-title">Ready when<br /><span>you are.</span></h1>
        <p class="welcome-copy">A voice partner for ideas, useful answers, and the things happening right now. Speak naturally, switch languages, and let Aura look up current facts when you need them.</p>
        <div class="capability-list" aria-label="Aura capabilities">
          <div class="capability-row"><span class="capability-index">01</span><span><strong>Natural conversation</strong><small>Talk, pause, interrupt, and carry on.</small></span></div>
          <div class="capability-row"><span class="capability-index">02</span><span><strong>Live web research</strong><small>Current answers arrive with clickable sources.</small></span></div>
          <div class="capability-row"><span class="capability-index">03</span><span><strong>Your language</strong><small>Urdu, English, Hindi, and more.</small></span></div>
        </div>
        <div class="key-footbar"><span class="signal-pip"></span><span>PRIVATE SESSION</span><span class="footbar-separator"></span><span>12 LANGUAGES</span></div>
      </section>

      <section class="key-shell" aria-labelledby="key-title">
        <div class="key-panel">
          <div class="panel-head">
            <div class="panel-symbol" aria-hidden="true"><span></span></div>
            <div class="panel-title"><p class="eyebrow">SECURE ACCESS</p><h2 id="key-title">Connect your key</h2></div>
            <span class="local-lock" title="Your key stays on this server">LOCAL</span>
          </div>
          <p class="panel-copy">Aura uses your OpenAI key for live voice and web research.</p>
          <button id="speak-prompt-btn" class="voice-cue-btn" type="button" title="Hear setup instructions">
            <span class="cue-signal" aria-hidden="true"></span><span id="voice-cue-text">Hear setup instructions</span><span class="cue-action" aria-hidden="true">PLAY</span>
          </button>
          <div class="input-group">
            <label for="api-key-input">OpenAI API key</label>
            <div class="input-wrap">
              <input id="api-key-input" type="password" placeholder="sk-proj-…" autocomplete="off" spellcheck="false" aria-describedby="key-hint" />
              <button id="toggle-vis" class="eye-btn" type="button" title="Show or hide key" aria-label="Show or hide key">
                <svg id="eye-open" viewBox="0 0 24 24" fill="none" width="19" height="19" aria-hidden="true"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z" stroke="currentColor" stroke-width="1.7"/><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.7"/></svg>
                <svg id="eye-closed" class="hidden" viewBox="0 0 24 24" fill="none" width="19" height="19" aria-hidden="true"><path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19m-6.72-1.07a3 3 0 11-4.24-4.24" stroke="currentColor" stroke-width="1.7"/><path d="M3 3l18 18" stroke="currentColor" stroke-width="1.7"/></svg>
              </button>
            </div>
            <span class="hint-text" id="key-hint">Your key stays in this local session.</span>
          </div>
          <button id="save-key-btn" class="primary-btn" type="button">
            <span id="save-btn-text">Initialize Aura</span><span class="button-orbit" aria-hidden="true">↗</span><span id="save-btn-spinner" class="spinner hidden" aria-hidden="true"></span>
          </button>
          <div id="key-error" class="error-box" role="alert" aria-live="polite"></div>
          <div class="panel-footnote"><span>OPENAI PLATFORM</span><span class="footnote-line"></span><span>KEY NEVER SHOWN</span></div>
        </div>
      </section>
    </main>
  </section>

  <section id="voice-screen" class="screen" aria-hidden="true">
    <div class="screen-vignette" aria-hidden="true"></div>
    <div class="voice-shell">
      <header class="top-bar">
        <div class="brand-lockup compact">
          <span class="brand-emblem" aria-hidden="true"><span></span></span>
          <span class="brand-wordmark"><strong>AURA</strong><small>VOICE INTERFACE</small></span>
        </div>
        <div class="topbar-controls">
          <div class="status-shell"><span class="status-dot" id="status-dot"></span><span id="status-label">Ready</span></div>
          <label class="select-control"><span>Language</span><select id="language-select" aria-label="Choose conversation language">
            <option value="auto">Auto detect</option><option value="en">English</option><option value="ur">اردو · Urdu</option><option value="hi">हिन्दी · Hindi</option><option value="ar">العربية · Arabic</option><option value="es">Español · Spanish</option><option value="fr">Français · French</option><option value="de">Deutsch · German</option><option value="zh">中文 · Mandarin</option><option value="pt">Português · Portuguese</option><option value="ja">日本語 · Japanese</option><option value="tr">Türkçe · Turkish</option><option value="ru">Русский · Russian</option>
          </select></label>
          <label class="select-control voice-control"><span>Voice</span><select id="voice-select" aria-label="Choose Aura voice"><option value="marin">Marin</option><option value="cedar">Cedar</option><option value="coral">Coral</option><option value="alloy">Alloy</option></select></label>
          <button id="settings-btn" class="icon-btn" type="button" title="Change API key" aria-label="Change API key"><svg viewBox="0 0 24 24" fill="none" width="19" height="19" aria-hidden="true"><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="1.7"/><path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.33 2 2 0 01-2.33 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2.5 2.5 0 01-5 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.33 0 2 2 0 010-2.33l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2.5 2.5 0 010-5h.09A1.65 1.65 0 014.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 010-2.33 2 2 0 012.33 0l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2.5 2.5 0 015 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.33 0 2 2 0 010 2.33l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2.5 2.5 0 010 5h-.09a1.65 1.65 0 00-1.51 1z" stroke="currentColor" stroke-width="1.5"/></svg></button>
        </div>
      </header>

      <main class="command-layout">


        <section class="voice-stage" aria-label="Aura voice control">
          <div class="stage-meta"><span>VOICE CORE</span><span id="stage-focus">Ready when you are</span></div>
          <div class="mic-container" id="mic-container">
            <canvas id="voice-canvas" aria-hidden="true"></canvas>
            <div class="orb-backlight" aria-hidden="true"></div><div class="ring r3" aria-hidden="true"></div><div class="ring r2" aria-hidden="true"></div><div class="ring r1" aria-hidden="true"></div>
            <button class="mic-btn" id="mic-btn" type="button" aria-label="Start voice conversation" title="Start or end voice conversation">
              <svg id="mic-icon" class="btn-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="9" y="2" width="6" height="12" rx="3" fill="currentColor"/><path d="M19 10a7 7 0 01-14 0" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><path d="M12 19v3m-4 0h8" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>
              <svg id="stop-icon" class="btn-icon hidden" viewBox="0 0 24 24" fill="none" aria-hidden="true"><rect x="6" y="6" width="12" height="12" rx="2.5" fill="currentColor"/></svg>
            </button>
            <div class="core-label"><span class="core-live-pip"></span><span>READY TO LISTEN</span></div>
          </div>
          <p class="mic-hint" id="mic-hint">Start a voice session</p>
        </section>

        <aside class="transcript-panel" aria-labelledby="transcript-title">
          <div class="transcript-head"><div><p class="eyebrow">AURA CHAT</p><h2 id="transcript-title">Conversation</h2><small>Speak or type. Your conversation stays together.</small></div><button id="clear-chat-btn" class="clear-btn" type="button">Clear</button></div>
          <div id="transcript-state" class="transcript-state"><span class="state-pip"></span> Ready for a message</div>
          <div class="transcript-area" id="transcript-area" aria-live="polite"><div class="transcript-inner" id="transcript-inner"><div id="empty-chat" class="empty-state"><span class="empty-orbit" aria-hidden="true"></span><p>What would you like to explore?</p><small>Ask by voice or start typing below.</small></div></div></div>
          <button id="scroll-latest-btn" class="jump-latest hidden" type="button" aria-label="Scroll to the latest message">↓ Latest</button>
          <div class="transcript-foot"><span><i class="secure-pip"></i> PRIVATE SESSION</span><span id="turn-count">0 turns</span></div>
          <div class="quick-prompts" aria-label="Suggested prompts"><button class="prompt-chip" type="button" data-prompt="What are the latest headlines today?">Today’s headlines</button><button class="prompt-chip" type="button" data-prompt="Explain this clearly in Urdu.">Urdu please</button><button class="prompt-chip" type="button" data-prompt="Tell me something useful I might not know.">Surprise me</button></div>
          <div class="message-composer"><input id="message-input" type="text" maxlength="4000" autocomplete="off" placeholder="Message Aura…" aria-label="Type a message to Aura" /><button id="send-text-btn" type="button" aria-label="Send message"><span>Send</span><span class="send-arrow" aria-hidden="true">↗</span></button></div>
          <p class="composer-note">Enter to send · use the mic for a hands-free conversation</p>
        </aside>
      </main>

      <footer class="session-footer"><span><i class="secure-pip"></i> Key held in local session memory</span><span>REALTIME VOICE <b>·</b> LIVE WEB SOURCES</span></footer>
    </div>
  </section>
</body>
</html>
'''

STYLES_CSS = r''':host {
  --aura-bg: #091115;
  --aura-panel: rgba(14,25,29,.80);
  --aura-line: rgba(189,225,220,.13);
  --aura-text: #edf6f3;
  --aura-muted: #9aacad;
  --aura-dim: #6e8183;
  --aura-accent: #76dfd1;
  --aura-accent-strong: #a0f3e8;
  --aura-accent-wash: rgba(118,223,209,.10);
  --aura-shadow: rgba(49,159,151,.16);
  color: var(--aura-text);
  background: var(--aura-bg);
  font-family: "Aptos","Segoe UI Variable",system-ui,sans-serif;
}
*,*::before,*::after { box-sizing: border-box; }
html,body { width:100%; height:100%; overflow:hidden; margin:0; color:var(--aura-text); background:var(--aura-bg); font-family:"Aptos","Segoe UI Variable",system-ui,sans-serif; -webkit-font-smoothing:antialiased; }
button,input,select { font:inherit; color:inherit; }
.screen { position:fixed; inset:0; display:flex; overflow:hidden; align-items:stretch; justify-content:center; background:var(--aura-bg); opacity:0; pointer-events:none; transition:opacity 780ms cubic-bezier(.16,1,.3,1); }
.screen.active { opacity:1; pointer-events:auto; }
.screen-vignette { position:absolute; inset:0; z-index:1; pointer-events:none; background:radial-gradient(ellipse at 50% 45%,transparent 22%,rgba(4,10,13,.32) 100%),linear-gradient(180deg,rgba(8,17,21,.04),rgba(8,17,21,.18)); }
canvas { position:absolute; inset:0; z-index:0; display:block; width:100% !important; height:100% !important; pointer-events:none; }
.key-layout { position:relative; z-index:2; width:min(1320px,calc(100vw - 72px)); min-height:100dvh; margin:auto; padding:clamp(30px,5.5vh,66px) 0; display:grid; grid-template-columns:minmax(0,1.08fr) minmax(350px,.78fr); align-items:center; gap:clamp(38px,7vw,110px); }
.key-intro { max-width:610px; padding:10px 0 10px 4px; animation:rise-in 850ms cubic-bezier(.16,1,.3,1) both; }
.brand-lockup { display:flex; align-items:center; gap:12px; min-width:0; }
.brand-emblem { width:42px; height:42px; flex:0 0 42px; display:grid; place-items:center; position:relative; border:1px solid rgba(154,223,214,.5); border-radius:15px; transform:rotate(-9deg); background:linear-gradient(145deg,rgba(112,217,204,.19),rgba(15,38,42,.68)); box-shadow:inset 0 1px 0 rgba(255,255,255,.16),0 8px 26px var(--aura-shadow); }
.brand-emblem::before,.brand-emblem::after { content:""; position:absolute; border:1px solid rgba(149,238,226,.65); border-radius:50%; transform:rotate(25deg); }
.brand-emblem::before { width:19px; height:19px; }
.brand-emblem::after { width:8px; height:8px; background:var(--aura-accent); box-shadow:0 0 15px rgba(118,223,209,.65); }
.brand-emblem>span { position:absolute; width:31px; height:31px; border:1px solid rgba(149,238,226,.28); border-radius:50%; }
.brand-wordmark { display:flex; flex-direction:column; gap:3px; line-height:1; }
.brand-wordmark strong { font-size:14px; font-weight:700; letter-spacing:.22em; color:var(--aura-text); }
.brand-wordmark small { color:var(--aura-dim); font-size:8px; letter-spacing:.17em; font-weight:600; }
.eyebrow { color:var(--aura-muted); font-size:9px; font-weight:650; letter-spacing:.18em; line-height:1.4; text-transform:uppercase; }
.key-intro>.eyebrow { display:flex; align-items:center; gap:10px; margin:clamp(36px,7vh,82px) 0 21px; }
.eyebrow-mark { width:22px; height:1px; background:var(--aura-accent); box-shadow:0 0 12px var(--aura-accent); }
.welcome-title { max-width:700px; margin:0; color:var(--aura-text); font-size:clamp(54px,6.4vw,86px); font-weight:520; letter-spacing:-.075em; line-height:.96; text-wrap:balance; }
.welcome-title span { color:var(--aura-accent-strong); font-weight:430; }
.welcome-copy { max-width:460px; margin:25px 0 30px; color:#a6b6b6; font-size:15px; line-height:1.7; }
.capability-list { display:grid; gap:14px; max-width:510px; }
.capability-row { display:grid; grid-template-columns:31px 1fr; gap:12px; align-items:start; padding:0 0 13px; border-bottom:1px solid rgba(189,225,220,.085); }
.capability-index { padding-top:2px; color:var(--aura-accent); font:10px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace; }
.capability-row>span:last-child { display:grid; gap:4px; }
.capability-row strong { font-size:12px; font-weight:620; color:#dce8e5; }
.capability-row small { color:var(--aura-muted); font-size:11px; line-height:1.45; }
.key-footbar { display:flex; align-items:center; gap:10px; margin-top:26px; color:var(--aura-dim); font:8px/1.4 ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.14em; }
.signal-pip,.secure-pip,.core-live-pip { width:6px; height:6px; display:inline-block; border-radius:50%; background:var(--aura-accent); box-shadow:0 0 12px rgba(118,223,209,.72); }
.footbar-separator { width:1px; height:11px; margin:0 3px; background:var(--aura-line); }
.key-shell { width:100%; max-width:450px; justify-self:end; padding:8px; border:1px solid rgba(194,233,227,.17); border-radius:31px; background:linear-gradient(145deg,rgba(214,252,246,.10),rgba(25,49,52,.12) 30%,rgba(5,13,16,.46)); box-shadow:inset 0 1px 0 rgba(255,255,255,.12),0 36px 100px rgba(0,0,0,.28),0 0 70px rgba(73,194,184,.07); transform:perspective(1400px) rotateY(-3deg); animation:card-arrive 950ms cubic-bezier(.16,1,.3,1) both; }
.key-panel { position:relative; overflow:hidden; padding:clamp(26px,3.6vw,38px); border:1px solid rgba(202,237,232,.12); border-radius:24px; background:linear-gradient(150deg,rgba(17,31,35,.96),rgba(10,20,24,.97) 63%,rgba(12,29,32,.95)); box-shadow:inset 0 1px 0 rgba(255,255,255,.08),inset 0 -22px 60px rgba(0,0,0,.17); }
.key-panel::before { content:""; position:absolute; inset:-45% -20% auto 30%; height:230px; pointer-events:none; background:radial-gradient(ellipse,rgba(102,216,203,.10),transparent 68%); }
.panel-head { position:relative; display:flex; align-items:center; gap:14px; }
.panel-symbol { position:relative; width:42px; height:42px; flex:0 0 42px; display:grid; place-items:center; border:1px solid rgba(142,224,213,.30); border-radius:14px; background:rgba(95,199,187,.09); }
.panel-symbol::before,.panel-symbol::after { content:""; position:absolute; border:1px solid var(--aura-accent); border-radius:50%; }
.panel-symbol::before { width:18px; height:18px; opacity:.55; }
.panel-symbol::after { width:7px; height:7px; background:var(--aura-accent); box-shadow:0 0 14px var(--aura-accent); }
.panel-title { min-width:0; }
.panel-title .eyebrow { margin:0 0 5px; color:var(--aura-accent); font-size:8px; }
.panel-title h2 { margin:0; color:var(--aura-text); font-size:23px; font-weight:620; letter-spacing:-.045em; }
.local-lock { margin-left:auto; padding:5px 7px; border:1px solid rgba(118,223,209,.23); border-radius:7px; color:var(--aura-accent); font:8px/1 ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.12em; }
.panel-copy { margin:19px 0 18px; color:var(--aura-muted); font-size:12px; line-height:1.55; }
.voice-cue-btn { width:100%; display:flex; align-items:center; gap:10px; margin:0 0 25px; padding:11px 13px; border:1px solid rgba(189,225,220,.12); border-radius:12px; color:#c6d6d3; background:rgba(255,255,255,.025); text-align:left; cursor:pointer; transition:background 380ms cubic-bezier(.16,1,.3,1),border-color 380ms cubic-bezier(.16,1,.3,1),transform 380ms cubic-bezier(.16,1,.3,1); }
.voice-cue-btn:hover { border-color:rgba(118,223,209,.35); background:var(--aura-accent-wash); transform:translateY(-1px); }
.cue-signal { width:16px; height:16px; flex:0 0 16px; border:1px solid rgba(118,223,209,.65); border-radius:50%; position:relative; }
.cue-signal::after { content:""; position:absolute; inset:4px; border-radius:50%; background:var(--aura-accent); }
.voice-cue-btn span:nth-child(2) { flex:1; font-size:11px; }
.cue-action { color:var(--aura-dim); font:8px ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.12em; }
.input-group { margin:0 0 18px; text-align:left; }
.input-group label { display:block; margin-bottom:8px; color:#c7d8d4; font-size:11px; font-weight:600; text-transform:none; letter-spacing:.02em; }
.input-wrap { position:relative; }
.input-wrap input { width:100%; min-height:52px; padding:0 50px 0 14px; border:1px solid rgba(189,225,220,.20); border-radius:12px; outline:none; color:var(--aura-text); background:rgba(5,13,16,.64); font:12px ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.02em; transition:border-color 300ms cubic-bezier(.16,1,.3,1),box-shadow 300ms cubic-bezier(.16,1,.3,1),background 300ms cubic-bezier(.16,1,.3,1); }
.input-wrap input::placeholder { color:#6e8282; font:11px "Aptos","Segoe UI Variable",system-ui,sans-serif; }
.input-wrap input:focus { border-color:rgba(118,223,209,.75); background:rgba(8,19,22,.92); box-shadow:0 0 0 3px rgba(118,223,209,.11),inset 0 1px 0 rgba(255,255,255,.05); }
.eye-btn { position:absolute; top:50%; right:10px; display:grid; place-items:center; padding:7px; border:0; border-radius:8px; color:var(--aura-muted); background:transparent; cursor:pointer; transform:translateY(-50%); transition:color 260ms cubic-bezier(.16,1,.3,1),background 260ms cubic-bezier(.16,1,.3,1); }
.eye-btn:hover { color:var(--aura-accent); background:rgba(118,223,209,.08); }
.hint-text { display:block; min-height:16px; margin-top:8px; color:var(--aura-muted); font-size:10px; line-height:1.45; }
.primary-btn { width:100%; min-height:52px; display:flex; align-items:center; justify-content:center; gap:13px; padding:10px 13px 10px 20px; border:1px solid rgba(202,249,241,.62); border-radius:13px; color:#062022; background:linear-gradient(115deg,#9af0e4,#68cfc4); box-shadow:inset 0 1px 0 rgba(255,255,255,.58),0 11px 30px rgba(43,153,145,.18); font-size:12px; font-weight:720; cursor:pointer; transition:transform 380ms cubic-bezier(.16,1,.3,1),box-shadow 380ms cubic-bezier(.16,1,.3,1),filter 380ms cubic-bezier(.16,1,.3,1); }
.primary-btn:hover:not(:disabled) { transform:translateY(-2px); filter:saturate(1.07); box-shadow:inset 0 1px 0 rgba(255,255,255,.7),0 15px 36px rgba(43,153,145,.28); }
.primary-btn:active:not(:disabled) { transform:translateY(1px) scale(.99); }
.primary-btn:disabled { opacity:.55; cursor:not-allowed; }
.button-orbit { width:28px; height:28px; margin-left:auto; display:grid; place-items:center; border:1px solid rgba(4,51,50,.17); border-radius:50%; color:#083a3b; background:rgba(255,255,255,.28); font-size:14px; transition:transform 380ms cubic-bezier(.16,1,.3,1),background 380ms cubic-bezier(.16,1,.3,1); }
.primary-btn:hover:not(:disabled) .button-orbit { transform:translate(2px,-2px); background:rgba(255,255,255,.48); }
.spinner { width:17px; height:17px; border:2px solid rgba(6,32,34,.25); border-top-color:#062022; border-radius:50%; animation:spin .8s cubic-bezier(.55,.06,.68,.19) infinite; }
.error-box { display:none; margin-top:14px; padding:10px 12px; border:1px solid rgba(232,135,135,.35); border-radius:10px; color:#ffc8c8; background:rgba(117,35,39,.18); font-size:11px; line-height:1.5; text-align:left; }
.error-box.show { display:block; }
.panel-footnote { display:flex; align-items:center; gap:8px; margin-top:22px; color:var(--aura-dim); font:7px ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.11em; }
.footnote-line { height:1px; flex:1; background:rgba(189,225,220,.10); }
.hidden { display:none !important; }

.voice-shell { position:relative; z-index:2; width:min(1460px,calc(100vw - 36px)); height:100dvh; min-height:0; margin:auto; display:grid; grid-template-rows:72px minmax(0,1fr) 24px; gap:13px; overflow:hidden; }
.top-bar { width:100%; min-height:60px; margin-top:0; padding:10px 15px; display:flex; align-items:center; justify-content:space-between; gap:16px; border:1px solid rgba(192,228,224,.14); border-radius:18px; background:linear-gradient(110deg,rgba(19,34,38,.88),rgba(12,24,28,.76)); box-shadow:inset 0 1px 0 rgba(255,255,255,.07),0 18px 48px rgba(0,0,0,.15); backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px); }
.brand-lockup.compact .brand-emblem { width:35px; height:35px; flex-basis:35px; border-radius:12px; }
.brand-lockup.compact .brand-emblem::before { width:16px; height:16px; }
.brand-lockup.compact .brand-emblem::after { width:6px; height:6px; }
.brand-lockup.compact .brand-emblem>span { width:27px; height:27px; }
.brand-lockup.compact .brand-wordmark strong { font-size:12px; }
.brand-lockup.compact .brand-wordmark small { font-size:7px; }
.topbar-controls { display:flex; align-items:center; justify-content:flex-end; gap:11px; }
.status-shell { min-width:91px; display:inline-flex; align-items:center; gap:8px; color:#c6d4d2; font-size:10px; }
.status-dot { width:6px; height:6px; flex:0 0 6px; border-radius:50%; background:#718384; transition:background 320ms cubic-bezier(.16,1,.3,1),box-shadow 320ms cubic-bezier(.16,1,.3,1); }
.status-dot.listening { background:var(--aura-accent); box-shadow:0 0 14px var(--aura-accent); animation:status-pulse 1.6s cubic-bezier(.2,.7,.3,1) infinite; }
.status-dot.speaking { background:var(--aura-accent-strong); box-shadow:0 0 18px var(--aura-accent); }
.status-dot.searching { background:var(--aura-accent); box-shadow:0 0 14px var(--aura-accent); animation:status-pulse 1.1s ease-in-out infinite; }
.status-dot.error { background:#ed8585; box-shadow:0 0 12px rgba(237,133,133,.45); }
.select-control { display:flex; align-items:center; gap:7px; color:var(--aura-dim); font-size:9px; }
.select-control select { min-height:34px; max-width:140px; padding:0 9px; border:1px solid rgba(189,225,220,.14); border-radius:9px; outline:none; color:#d9e7e4; background:rgba(5,13,16,.58); font-size:10px; cursor:pointer; transition:border-color 260ms cubic-bezier(.16,1,.3,1),background 260ms cubic-bezier(.16,1,.3,1); }
.select-control select:hover,.select-control select:focus-visible { border-color:rgba(118,223,209,.55); background:rgba(5,13,16,.9); }
.select-control select:disabled { opacity:.65; cursor:default; }
.select-control option { color:var(--aura-text); background:#101a1d; }
.icon-btn { width:36px; height:36px; display:grid; place-items:center; border:1px solid rgba(189,225,220,.14); border-radius:10px; color:#aebfbd; background:rgba(255,255,255,.025); cursor:pointer; transition:color 280ms cubic-bezier(.16,1,.3,1),border-color 280ms cubic-bezier(.16,1,.3,1),background 280ms cubic-bezier(.16,1,.3,1),transform 280ms cubic-bezier(.16,1,.3,1); }
.icon-btn:hover { color:var(--aura-accent); border-color:rgba(118,223,209,.36); background:var(--aura-accent-wash); transform:translateY(-1px); }
.command-layout { width:100%; height:100%; min-height:0; display:grid; grid-template-columns:minmax(340px,.92fr) minmax(410px,1.08fr); gap:16px; padding:2px 0 0; overflow:hidden; }
.transcript-panel { position:relative; min-width:0; min-height:0; display:flex; flex-direction:column; overflow:hidden; padding:18px; border:1px solid rgba(189,225,220,.12); border-radius:20px; background:linear-gradient(155deg,rgba(18,32,36,.88),rgba(10,20,24,.82)); box-shadow:inset 0 1px 0 rgba(255,255,255,.055),0 20px 50px rgba(0,0,0,.14); backdrop-filter:blur(17px); -webkit-backdrop-filter:blur(17px); }
.voice-stage { position:relative; min-width:0; min-height:0; display:flex; flex-direction:column; align-items:center; justify-content:center; overflow:hidden; padding:22px 18px 15px; border:1px solid rgba(189,225,220,.095); border-radius:24px; background:radial-gradient(ellipse at 50% 48%,rgba(38,104,103,.13),rgba(7,17,20,.05) 52%,rgba(7,17,20,.20)); }
.voice-stage::before,.voice-stage::after { content:""; position:absolute; width:22px; height:22px; border-color:rgba(118,223,209,.28); border-style:solid; pointer-events:none; }
.voice-stage::before { top:12px; left:12px; border-width:1px 0 0 1px; border-top-left-radius:8px; }
.voice-stage::after { right:12px; bottom:12px; border-width:0 1px 1px 0; border-bottom-right-radius:8px; }
.stage-meta { position:absolute; top:18px; left:21px; right:21px; display:flex; align-items:center; justify-content:space-between; gap:12px; color:var(--aura-dim); font:8px ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.12em; }
.stage-meta span:last-child { overflow:hidden; color:var(--aura-muted); text-align:right; text-overflow:ellipsis; white-space:nowrap; letter-spacing:.02em; }
.mic-container { position:relative; width:clamp(230px,27vw,340px); aspect-ratio:1; display:grid; place-items:center; margin:4px 0 0; isolation:isolate; }
#voice-canvas { z-index:0; }
.ring,.mic-btn,.core-label { z-index:1; }
.orb-backlight { position:absolute; inset:23%; z-index:-1; border-radius:50%; background:radial-gradient(circle,rgba(98,218,204,.18),rgba(51,127,126,.08) 48%,transparent 72%); filter:blur(24px); transform:scale(1.2); }
.ring { position:absolute; border:1px solid rgba(139,223,213,.16); border-radius:50%; transition:border-color 500ms cubic-bezier(.16,1,.3,1),transform 500ms cubic-bezier(.16,1,.3,1),opacity 500ms cubic-bezier(.16,1,.3,1); }
.r1 { width:66%; height:66%; border-color:rgba(139,223,213,.25); }
.r2 { width:82%; height:82%; border-color:rgba(139,223,213,.17); transform:rotateX(62deg) rotateZ(-12deg); }
.r3 { width:98%; height:98%; border-style:dashed; border-color:rgba(139,223,213,.13); transform:rotateX(68deg) rotateZ(24deg); }
.mic-container.listening .r1 { border-color:rgba(160,243,232,.62); animation:ring-pulse 2.3s cubic-bezier(.16,1,.3,1) infinite; }
.mic-container.listening .r2 { border-color:rgba(118,223,209,.38); animation:ring-orbit 13s cubic-bezier(.45,.05,.55,.95) infinite; }
.mic-container.listening .r3 { border-color:rgba(118,223,209,.30); animation:ring-orbit 19s cubic-bezier(.45,.05,.55,.95) reverse infinite; }
.mic-container.speaking .r1 { border-color:rgba(160,243,232,.78); transform:scale(1.06); }
.mic-container.speaking .r2 { border-color:rgba(118,223,209,.46); transform:rotateX(62deg) rotateZ(26deg) scale(1.04); }
.mic-container.connecting .r1,.mic-container.connecting .r2 { border-color:rgba(118,223,209,.47); animation:ring-orbit 7s cubic-bezier(.45,.05,.55,.95) infinite; }
.mic-btn { position:relative; width:clamp(116px,13vw,154px); aspect-ratio:1; display:grid; place-items:center; border:1px solid rgba(200,247,241,.66); border-radius:50%; color:#c9fff7; background:radial-gradient(circle at 35% 27%,rgba(194,255,246,.28),rgba(76,174,166,.22) 28%,rgba(12,45,48,.88) 70%); box-shadow:inset 0 2px 2px rgba(255,255,255,.22),inset 0 -16px 26px rgba(2,16,19,.42),0 0 0 7px rgba(118,223,209,.055),0 0 54px rgba(118,223,209,.23); cursor:pointer; backdrop-filter:blur(6px); transition:transform 500ms cubic-bezier(.16,1,.3,1),border-color 500ms cubic-bezier(.16,1,.3,1),box-shadow 500ms cubic-bezier(.16,1,.3,1),color 500ms cubic-bezier(.16,1,.3,1); }
.mic-btn::before { content:""; position:absolute; inset:9px; border:1px solid rgba(220,255,250,.16); border-radius:50%; pointer-events:none; }
.mic-btn:hover:not(:disabled) { transform:scale(1.035); border-color:rgba(228,255,252,.95); box-shadow:inset 0 2px 2px rgba(255,255,255,.25),0 0 0 10px rgba(118,223,209,.08),0 0 72px rgba(118,223,209,.34); }
.mic-btn:active:not(:disabled) { transform:scale(.97); }
.mic-btn:focus-visible,.icon-btn:focus-visible,.clear-btn:focus-visible,.prompt-chip:focus-visible,.primary-btn:focus-visible,#send-text-btn:focus-visible { outline:2px solid var(--aura-accent-strong); outline-offset:3px; }
.mic-btn:disabled { cursor:wait; }
.mic-btn.listening { color:#eafffb; box-shadow:inset 0 1px 2px rgba(255,255,255,.26),0 0 0 10px rgba(118,223,209,.10),0 0 82px rgba(118,223,209,.40); animation:core-breathe 2.6s cubic-bezier(.16,1,.3,1) infinite; }
.mic-btn.speaking { color:#f2fffc; border-color:rgba(234,255,251,.95); box-shadow:inset 0 1px 2px rgba(255,255,255,.32),0 0 0 12px rgba(118,223,209,.10),0 0 98px rgba(118,223,209,.50); }
.mic-btn.connecting { color:#d4fff8; }
.btn-icon { width:34px; height:34px; pointer-events:none; }
.core-label { position:absolute; bottom:11%; display:inline-flex; align-items:center; gap:7px; padding:6px 9px; border:1px solid rgba(189,225,220,.13); border-radius:99px; color:#a9bfbb; background:rgba(7,17,20,.65); font:7px ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.11em; backdrop-filter:blur(9px); }
.mic-container.listening .core-live-pip { animation:status-pulse 1.6s cubic-bezier(.2,.7,.3,1) infinite; }
.mic-hint { min-height:21px; margin:0; color:#ccdbd8; font-size:12px; text-align:center; }
.quick-prompts { width:100%; display:flex; justify-content:flex-start; flex-wrap:wrap; gap:6px; margin:10px 0 9px; }
.prompt-chip { min-height:29px; padding:0 9px; border:1px solid rgba(189,225,220,.12); border-radius:8px; color:#aebfbc; background:rgba(9,19,22,.52); font-size:8px; cursor:pointer; transition:color 260ms cubic-bezier(.16,1,.3,1),border-color 260ms cubic-bezier(.16,1,.3,1),background 260ms cubic-bezier(.16,1,.3,1),transform 260ms cubic-bezier(.16,1,.3,1); }
.prompt-chip:hover:not(:disabled) { color:var(--aura-accent-strong); border-color:rgba(118,223,209,.36); background:rgba(118,223,209,.075); transform:translateY(-1px); }
.prompt-chip:disabled { opacity:.4; cursor:not-allowed; }
.message-composer { width:100%; min-height:43px; display:flex; align-items:center; gap:7px; padding:4px 5px 4px 13px; border:1px solid rgba(189,225,220,.16); border-radius:12px; background:rgba(5,13,16,.68); box-shadow:inset 0 1px 0 rgba(255,255,255,.04); transition:border-color 260ms cubic-bezier(.16,1,.3,1),box-shadow 260ms cubic-bezier(.16,1,.3,1); }
.message-composer:focus-within { border-color:rgba(118,223,209,.54); box-shadow:0 0 0 3px rgba(118,223,209,.07); }
.message-composer input { width:100%; min-width:0; border:0; outline:0; color:var(--aura-text); background:transparent; font-size:10px; }
.message-composer input::placeholder { color:#718584; }
#send-text-btn { min-height:32px; flex:0 0 auto; display:inline-flex; align-items:center; gap:8px; padding:0 6px 0 10px; border:0; border-radius:8px; color:#092626; background:var(--aura-accent); font-size:9px; font-weight:700; cursor:pointer; transition:filter 250ms cubic-bezier(.16,1,.3,1),transform 250ms cubic-bezier(.16,1,.3,1); }
#send-text-btn:hover:not(:disabled) { filter:brightness(1.08); transform:translateY(-1px); }
#send-text-btn:disabled { opacity:.4; cursor:not-allowed; }
.send-arrow { width:21px; height:21px; display:grid; place-items:center; border:1px solid rgba(5,52,52,.18); border-radius:6px; background:rgba(255,255,255,.22); font-size:11px; }
.composer-note { margin:7px 0 0; text-align:center; color:#6f8583; font-size:8px; }
.transcript-head { display:flex; align-items:center; justify-content:space-between; gap:10px; }
.transcript-head .eyebrow { margin:0 0 5px; color:var(--aura-dim); font-size:7px; }
.transcript-head h2 { margin:0; color:var(--aura-text); font-size:19px; font-weight:550; letter-spacing:-.04em; }
.clear-btn { padding:6px 8px; border:1px solid transparent; border-radius:7px; color:var(--aura-dim); background:transparent; font-size:9px; cursor:pointer; transition:color 250ms cubic-bezier(.16,1,.3,1),border-color 250ms cubic-bezier(.16,1,.3,1),background 250ms cubic-bezier(.16,1,.3,1); }
.clear-btn:hover { color:var(--aura-accent); border-color:rgba(189,225,220,.12); background:rgba(255,255,255,.03); }
.transcript-head small { display:block; margin-top:5px; color:var(--aura-dim); font-size:9px; }
.transcript-state { display:inline-flex; align-items:center; gap:7px; margin:13px 0 10px; color:var(--aura-dim); font-size:8px; }
.state-pip { width:5px; height:5px; display:inline-block; border-radius:50%; background:#718384; }
.transcript-area { position:relative; min-height:0; flex:1; overflow-y:auto; overscroll-behavior:contain; overflow-anchor:none; padding:0 2px 5px 0; scrollbar-width:thin; scrollbar-color:rgba(118,223,209,.22) transparent; }
.transcript-inner { display:flex; flex-direction:column; align-items:stretch; gap:9px; }
.empty-state { min-height:190px; display:flex; flex-direction:column; align-items:flex-start; justify-content:center; color:var(--aura-muted); }
.empty-orbit { position:relative; width:34px; height:34px; margin-bottom:14px; border:1px solid rgba(118,223,209,.34); border-radius:50%; }
.empty-orbit::before { content:""; position:absolute; inset:7px; border:1px solid rgba(118,223,209,.43); border-radius:50%; }
.empty-orbit::after { content:""; position:absolute; top:14px; left:14px; width:5px; height:5px; border-radius:50%; background:var(--aura-accent); box-shadow:0 0 11px var(--aura-accent); }
.empty-state p { max-width:175px; margin:0 0 6px; color:#c5d4d1; font-size:12px; line-height:1.45; }
.empty-state small { max-width:180px; color:var(--aura-dim); font-size:9px; line-height:1.5; }
.msg { max-width:96%; padding:12px 14px; border:1px solid rgba(189,225,220,.10); border-radius:11px; color:#dbe8e5; background:rgba(255,255,255,.025); font-size:12px; line-height:1.7; white-space:pre-wrap; animation:message-arrive 420ms cubic-bezier(.16,1,.3,1) both; overflow-wrap:anywhere; }
.msg.user { align-self:flex-end; border-color:rgba(118,223,209,.21); background:rgba(118,223,209,.075); }
.msg.agent { align-self:flex-start; border-left:2px solid rgba(118,223,209,.48); background:rgba(118,223,209,.04); }
.msg-label { margin-bottom:5px; color:var(--aura-accent); font:8px ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.13em; text-transform:uppercase; }
.transcript-foot { display:flex; align-items:center; justify-content:space-between; gap:8px; margin-top:13px; padding-top:11px; border-top:1px solid rgba(189,225,220,.10); color:var(--aura-dim); font:7px ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.09em; }
.transcript-foot span:first-child { display:inline-flex; align-items:center; gap:6px; }
.transcript-foot .secure-pip { width:5px; height:5px; }
.session-footer { width:100%; display:flex; align-items:center; justify-content:space-between; gap:12px; padding:0 7px; color:#637575; font:7px ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.10em; }
.session-footer span { display:inline-flex; align-items:center; gap:7px; }
.session-footer .secure-pip { width:5px; height:5px; }
.session-footer b { color:var(--aura-accent); font-weight:400; }
@keyframes rise-in { from { opacity:0; transform:translate3d(0,20px,0); } to { opacity:1; transform:translate3d(0,0,0); } }
@keyframes card-arrive { from { opacity:0; transform:perspective(1400px) rotateY(-8deg) translate3d(18px,18px,0); } to { opacity:1; transform:perspective(1400px) rotateY(-3deg) translate3d(0,0,0); } }
@keyframes ring-pulse { 0%,100% { opacity:.68; transform:scale(1); } 50% { opacity:1; transform:scale(1.035); } }
@keyframes ring-orbit { from { rotate:0deg; } to { rotate:360deg; } }
@keyframes core-breathe { 0%,100% { scale:1; } 50% { scale:1.025; } }
@keyframes status-pulse { 0%,100% { opacity:1; scale:1; } 50% { opacity:.55; scale:1.3; } }
@keyframes message-arrive { from { opacity:0; transform:translate3d(0,7px,0); } to { opacity:1; transform:translate3d(0,0,0); } }
@keyframes spin { to { rotate:360deg; } }
@media (max-width:980px) {
  .key-layout { width:min(760px,calc(100vw - 48px)); grid-template-columns:minmax(0,1fr) minmax(320px,.92fr); gap:28px; }
  .welcome-title { font-size:clamp(48px,6.5vw,68px); }
  .command-layout { grid-template-columns:minmax(260px,.84fr) minmax(350px,1.16fr); }
}
@media (max-width:700px) {
  .key-layout { width:min(500px,calc(100vw - 28px)); min-height:100dvh; padding:24px 0; grid-template-columns:1fr; gap:22px; align-content:center; }
  .key-intro { padding:0 8px; }
  .key-intro>.eyebrow { margin:22px 0 12px; }
  .welcome-title { font-size:clamp(44px,13vw,66px); }
  .welcome-copy { margin:15px 0; font-size:12px; }
  .capability-list { display:none; }
  .key-footbar { margin-top:17px; }
  .key-shell { max-width:none; justify-self:stretch; transform:none; }
  .key-panel { padding:23px; }
  .voice-shell { width:calc(100vw - 20px); grid-template-rows:56px minmax(0,1fr) 18px; gap:8px; }
  .top-bar { min-height:54px; margin-top:0; padding:8px 10px; border-radius:14px; }
  .topbar-controls { gap:6px; }
  .status-shell { min-width:0; font-size:0; }
  .select-control { gap:4px; font-size:0; }
  .select-control select { max-width:98px; min-height:31px; padding:0 6px; font-size:9px; }
  .voice-control { display:none; }
  .icon-btn { width:33px; height:33px; }
  .command-layout { grid-template-columns:minmax(0,1fr); grid-template-rows:minmax(185px,36dvh) minmax(0,1fr); overflow:hidden; gap:9px; padding-top:0; }
  .voice-stage { min-height:0; padding:26px 12px 8px; border-radius:17px; }
  .stage-meta { top:14px; left:15px; right:15px; }
  .mic-container { width:min(48vw,210px,24dvh); flex:0 1 auto; }
  .mic-btn { width:120px; }
  .quick-prompts { margin:10px 0; }
  .prompt-chip { font-size:7px; }
  .transcript-panel { min-height:0; display:flex; padding:15px; }
  .transcript-head h2 { font-size:17px; }
  .transcript-state { margin:10px 0; }
  .empty-state { min-height:110px; }
  .session-footer { font-size:6px; }
}
@media (max-height:720px) and (min-width:701px) {
  .key-layout { padding-block:24px; }
  .key-intro>.eyebrow { margin-top:35px; }
  .welcome-copy { margin:16px 0 18px; }
  .capability-list { gap:8px; }
  .capability-row { padding-bottom:8px; }
  .voice-shell { grid-template-rows:62px minmax(0,1fr) 20px; gap:8px; }
  .top-bar { margin-top:0; min-height:54px; }
  .transcript-panel { padding:13px; }
  .mic-container { width:min(24vw,255px); }
  .quick-prompts { margin:7px 0; }
  .voice-stage { padding-block:15px 10px; }
}

.jump-latest { position:absolute; right:23px; bottom:148px; z-index:4; padding:8px 11px; border:1px solid rgba(118,223,209,.30); border-radius:99px; color:var(--aura-accent-strong); background:rgba(8,20,23,.94); box-shadow:0 6px 20px rgba(0,0,0,.28); font-size:10px; cursor:pointer; backdrop-filter:blur(10px); transition:opacity 180ms ease,transform 180ms ease; }
.jump-latest:hover { transform:translateY(-2px); background:rgba(25,52,53,.97); }
.message-citations { display:flex; align-items:center; flex-wrap:wrap; gap:6px; margin-top:11px; padding-top:9px; border-top:1px solid rgba(189,225,220,.10); }
.message-citations-label { width:100%; color:var(--aura-dim); font:7px ui-monospace,SFMono-Regular,Consolas,monospace; letter-spacing:.10em; text-transform:uppercase; }
.message-citation { max-width:100%; display:inline-flex; align-items:center; gap:5px; padding:5px 8px; border:1px solid rgba(118,223,209,.19); border-radius:7px; color:#a9d8d1; background:rgba(118,223,209,.045); font-size:9px; text-decoration:none; }
.message-citation:hover { color:#d9fff7; border-color:rgba(118,223,209,.44); background:rgba(118,223,209,.10); }
.message-citation span { max-width:210px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.msg.typing .typing-dots { display:inline-flex; gap:4px; margin-left:3px; vertical-align:middle; }
.typing-dots i { width:4px; height:4px; border-radius:50%; background:var(--aura-accent); animation:typing-bounce 1s ease-in-out infinite; }
.typing-dots i:nth-child(2) { animation-delay:130ms; } .typing-dots i:nth-child(3) { animation-delay:260ms; }
.mic-container.speaking .r1 { animation:speaking-bloom 1.8s ease-in-out infinite; }
.mic-container.speaking .r2 { animation:speaking-orbit 8s linear infinite; }
.mic-container.speaking .r3 { animation:speaking-orbit 13s linear infinite reverse; }
.mic-container.speaking .orb-backlight { animation:voice-glow 1.35s ease-in-out infinite; }
.mic-btn.speaking { animation:core-respond 1.35s ease-in-out infinite; }
.mic-container.researching .r2,.mic-container.researching .r3 { border-style:solid; border-color:rgba(118,223,209,.46); animation:speaking-orbit 4.8s linear infinite; }
@keyframes speaking-bloom { 0%,100% { scale:1; opacity:.68; } 50% { scale:1.075; opacity:1; } }
@keyframes speaking-orbit { from { rotate:0deg; } to { rotate:360deg; } }
@keyframes voice-glow { 0%,100% { opacity:.72; transform:scale(1.05); } 50% { opacity:1; transform:scale(1.4); } }
@keyframes core-respond { 0%,100% { scale:1; } 50% { scale:1.045; } }
@keyframes typing-bounce { 0%,60%,100% { transform:translateY(0); opacity:.55; } 30% { transform:translateY(-4px); opacity:1; } }

@media (prefers-reduced-motion:reduce) {
  *,*::before,*::after { scroll-behavior:auto !important; animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; }
}
'''

APP_JS = r'''/* ═══════════════════════════════════════════════════
   AURA VOICE AGENT — app.js
   Three.js scenes + WebRTC OpenAI Realtime Agent
═══════════════════════════════════════════════════ */

'use strict';

// ──────────────────────────────────────────────────
// 1.  THREE.JS — KEY ENTRY SCENE
// ──────────────────────────────────────────────────
let keyRenderer, keyScene, keyCamera;

function initKeyScene() {
  const canvas = document.getElementById('key-canvas');
  keyRenderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  keyRenderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  keyRenderer.setSize(innerWidth, innerHeight);

  keyScene = new THREE.Scene();
  keyCamera = new THREE.PerspectiveCamera(60, innerWidth / innerHeight, 0.1, 100);
  keyCamera.position.z = 6;

  // ── Particle field ────────────────────────────
  const geo = new THREE.BufferGeometry();
  const N = 600;
  const pos = new Float32Array(N * 3);
  for (let i = 0; i < N * 3; i++) pos[i] = (Math.random() - 0.5) * 22;
  geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const particles = new THREE.Points(
    geo,
    new THREE.PointsMaterial({ color: 0x7c3aed, size: 0.045, transparent: true, opacity: 0.75 })
  );
  keyScene.add(particles);

  // ── Floating metallic spheres ─────────────────
  const sphereData = [];
  const colors = [0x7c3aed, 0x06b6d4, 0xa78bfa, 0x0891b2, 0x6d28d9];
  for (let i = 0; i < 6; i++) {
    const r = 0.12 + Math.random() * 0.28;
    const mesh = new THREE.Mesh(
      new THREE.SphereGeometry(r, 20, 20),
      new THREE.MeshStandardMaterial({
        color: colors[i % colors.length],
        metalness: 0.92, roughness: 0.1,
        transparent: true, opacity: 0.65,
      })
    );
    mesh.position.set(
      (Math.random() - 0.5) * 10,
      (Math.random() - 0.5) * 7,
      (Math.random() - 0.5) * 4 - 1
    );
    const baseY = mesh.position.y;
    const speed = 0.4 + Math.random() * 0.6;
    const phase = Math.random() * Math.PI * 2;
    sphereData.push({ mesh, baseY, speed, phase });
    keyScene.add(mesh);
  }

  // ── Lights ────────────────────────────────────
  keyScene.add(new THREE.AmbientLight(0xffffff, 0.45));
  const pl1 = new THREE.PointLight(0x7c3aed, 2.5, 12);
  pl1.position.set(3, 4, 3);
  keyScene.add(pl1);
  const pl2 = new THREE.PointLight(0x06b6d4, 1.8, 10);
  pl2.position.set(-4, -2, 2);
  keyScene.add(pl2);

  let t = 0;
  (function animKey() {
    requestAnimationFrame(animKey);
    t += 0.008;
    particles.rotation.y += 0.0004;
    particles.rotation.x += 0.0002;
    sphereData.forEach(({ mesh, baseY, speed, phase }) => {
      mesh.position.y = baseY + Math.sin(t * speed + phase) * 0.35;
      mesh.rotation.y += 0.006;
    });
    keyRenderer.render(keyScene, keyCamera);
  })();
}


// ──────────────────────────────────────────────────
// 2.  THREE.JS — VOICE AGENT SCENE
// ──────────────────────────────────────────────────
let voiceRenderer, voiceScene, voiceCamera;
let orbMesh, wireFrame, ring1Mesh, ring2Mesh, particleMesh;
let _audioLevel = 0;

/** Called from voice logic to drive orb pulsing */
function setAudioLevel(level) { _audioLevel = level; }

// ──────────────────────────────────────────────────
// ──────────────────────────────────────────────────
// 3. SCREEN MANAGEMENT AND KEY SETUP
// ──────────────────────────────────────────────────
function showScreen(id) {
  document.querySelectorAll('.screen').forEach(function (screen) {
    screen.classList.remove('active');
    screen.setAttribute('aria-hidden', 'true');
  });
  const next = document.getElementById(id);
  next.classList.add('active');
  next.removeAttribute('aria-hidden');
}

const keyInput = document.getElementById('api-key-input');
const saveBtn = document.getElementById('save-key-btn');
const saveTxt = document.getElementById('save-btn-text');
const saveSpn = document.getElementById('save-btn-spinner');
const keyErr = document.getElementById('key-error');
const toggleVis = document.getElementById('toggle-vis');
const eyeOpen = document.getElementById('eye-open');
const eyeClosed = document.getElementById('eye-closed');
const speakPromptBtn = document.getElementById('speak-prompt-btn');
const languageSelect = document.getElementById('language-select');
let hasExistingKey = false;

function speakText(text) {
  if (!('speechSynthesis' in window)) return;
  try {
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.rate = 0.96;
    const language = (navigator.language || 'en').slice(0, 2).toLowerCase();
    const voice = window.speechSynthesis.getVoices().find(function (item) {
      return item.lang && item.lang.slice(0, 2).toLowerCase() === language;
    });
    if (voice) utterance.voice = voice;
    window.speechSynthesis.speak(utterance);
  } catch (error) {
    console.warn('[Aura] Speech prompt is unavailable.');
  }
}

if (speakPromptBtn) {
  speakPromptBtn.addEventListener('click', function () {
    speakText('Welcome to Aura. Please enter your OpenAI API key to get started.');
  });
}

toggleVis.addEventListener('click', function () {
  const reveal = keyInput.type === 'password';
  keyInput.type = reveal ? 'text' : 'password';
  eyeOpen.classList.toggle('hidden', reveal);
  eyeClosed.classList.toggle('hidden', !reveal);
  toggleVis.setAttribute('aria-label', reveal ? 'Hide API key' : 'Show API key');
  toggleVis.setAttribute('aria-pressed', String(reveal));
  keyInput.focus();
});

function showKeyError(message) {
  keyErr.textContent = message || '';
  keyErr.classList.toggle('show', Boolean(message));
  if (message) keyInput.setAttribute('aria-invalid', 'true');
  else keyInput.removeAttribute('aria-invalid');
}
function clearKeyError() { showKeyError(''); }

async function readJson(response) {
  let data = {};
  try { data = await response.json(); } catch (error) {}
  if (!response.ok) throw new Error(data.error || 'Aura could not complete that request.');
  return data;
}

async function postJson(path, payload) {
  const response = await fetch(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    cache: 'no-store',
    body: JSON.stringify(payload),
  });
  return readJson(response);
}

function enterVoiceScreen() {
  clearKeyError();
  if (!voiceRenderer && window.THREE) initVoiceScene();
  showScreen('voice-screen');
}

async function refreshKeyState() {
  try {
    const response = await fetch('/api/health', { cache: 'no-store' });
    const data = await response.json();
    hasExistingKey = Boolean(data.has_key);
    saveTxt.textContent = hasExistingKey ? 'Continue to Aura' : 'Initialize Aura';
    const hint = document.querySelector('.hint-text');
    if (hasExistingKey) {
      keyInput.placeholder = 'Enter a different key, or leave blank to continue';
      if (hint) hint.textContent = data.key_source === 'saved'
        ? 'A local key is ready. Leave this blank to use it.'
        : 'A key is already available for this run.';
    } else {
      keyInput.placeholder = 'sk-proj-...';
      if (hint) hint.textContent = 'Keys entered here stay in local server memory for this run.';
    }
  } catch (error) {
    hasExistingKey = false;
  }
}

saveBtn.addEventListener('click', submitKey);
keyInput.addEventListener('keydown', function (event) {
  if (event.key === 'Enter') submitKey();
});
keyInput.addEventListener('input', clearKeyError);

async function submitKey() {
  const key = keyInput.value.trim();
  clearKeyError();

  if (!key && hasExistingKey) {
    saveBtn.disabled = true;
    saveTxt.textContent = 'Opening Aura…';
    saveSpn.classList.remove('hidden');
    try {
      await postJson('/api/key', { use_existing: true });
      enterVoiceScreen();
    } catch (error) {
      showKeyError(error.message);
    } finally {
      saveBtn.disabled = false;
      saveTxt.textContent = 'Continue to Aura';
      saveSpn.classList.add('hidden');
    }
    return;
  }

  if (!key) {
    showKeyError('Please enter your OpenAI API key.');
    keyInput.focus();
    speakText('Please enter your OpenAI API key.');
    return;
  }
  if (!key.startsWith('sk-')) {
    showKeyError('That key does not look right. Check it and try again.');
    keyInput.focus();
    return;
  }

  saveBtn.disabled = true;
  saveTxt.textContent = 'Connecting…';
  saveSpn.classList.remove('hidden');
  try {
    await postJson('/api/key', { api_key: key });
    keyInput.value = '';
    enterVoiceScreen();
  } catch (error) {
    showKeyError(error.message);
  } finally {
    saveBtn.disabled = false;
    saveTxt.textContent = 'Continue to Aura';
    saveSpn.classList.add('hidden');
  }
}

// ──────────────────────────────────────────────────
// 4. GPT-LIVE VOICE SESSION (WebRTC)
// ──────────────────────────────────────────────────
const micBtn = document.getElementById('mic-btn');
const micContainer = document.getElementById('mic-container');
const micHint = document.getElementById('mic-hint');
const micIcon = document.getElementById('mic-icon');
const stopIcon = document.getElementById('stop-icon');
const statusDot = document.getElementById('status-dot');
const statusLabel = document.getElementById('status-label');
const txInner = document.getElementById('transcript-inner');
const settingsBtn = document.getElementById('settings-btn');
const clearChatBtn = document.getElementById('clear-chat-btn');
const remoteAudio = new Audio();
remoteAudio.autoplay = true;
remoteAudio.playsInline = true;

let peerConn = null;
let dataChannel = null;
let localStream = null;
let connected = false;
let connecting = false;
let liveMessages = { user: null, agent: null };

function setStatus(state, label) {
  statusDot.className = 'status-dot' + (state ? ' ' + state : '');
  statusLabel.textContent = label;
}

function setMicState(state) {
  micBtn.className = 'mic-btn' + (state !== 'idle' ? ' ' + state : '');
  micContainer.className = 'mic-container' + (state !== 'idle' ? ' ' + state : '');
  const hints = {
    idle: 'Click to start conversation',
    connecting: 'Connecting to Aura…',
    listening: 'Listening… click to end',
    speaking: 'Aura is speaking…',
  };
  micHint.textContent = hints[state] || '';
  micIcon.classList.toggle('hidden', state !== 'idle');
  stopIcon.classList.toggle('hidden', state === 'idle' || state === 'connecting');
  setAudioLevel(state === 'speaking' ? 0.55 : state === 'listening' ? 0.1 : 0);
}

function makeMessage(role, text) {
  const empty = document.getElementById('empty-chat');
  if (empty) empty.remove();
  const div = document.createElement('div');
  div.className = 'msg ' + role;
  const label = document.createElement('div');
  label.className = 'msg-label';
  label.textContent = role === 'user' ? 'You' : 'Aura';
  const body = document.createElement('div');
  body.textContent = text || '';
  div.append(label, body);
  txInner.appendChild(div);
  scrollChatToBottom(false);
  return body;
}

function addMessage(role, text) {
  if (text && text.trim()) makeMessage(role, text);
}

function appendTranscript(role, delta, event) {
  if (typeof delta !== 'string' || !delta) return;
  const now = Date.now();
  const identity = event.item_id || event.response_id || '';
  let current = liveMessages[role];
  if (!current || (identity && current.identity && identity !== current.identity) || now - current.lastAt > 1600) {
    current = { body: makeMessage(role, ''), identity: identity, lastAt: now, timer: null };
    liveMessages[role] = current;
  }
  current.body.textContent += delta;
  current.identity = identity || current.identity;
  current.lastAt = now;
  if (current.timer) clearTimeout(current.timer);
  current.timer = setTimeout(function () {
    if (liveMessages[role] === current) liveMessages[role] = null;
  }, 1600);
  const area = document.getElementById('transcript-area');
  if (area && scrollPinned) area.scrollTop = area.scrollHeight;
}

function handleEvent(message) {
  let event;
  try { event = JSON.parse(message.data); } catch (error) { return; }
  switch (event.type) {
    case 'session.started':
      setStatus('listening', 'Listening');
      setMicState('listening');
      break;
    case 'session.input_transcript.delta':
      appendTranscript('user', event.delta, event);
      if (connected) {
        setMicState('listening');
        setStatus('listening', 'Listening');
      }
      break;
    case 'session.output_transcript.delta':
      appendTranscript('agent', event.delta, event);
      if (connected) {
        setMicState('speaking');
        setStatus('speaking', 'Speaking');
      }
      break;
    case 'session.closed':
      if (connected || connecting) stopSession(false);
      setStatus('', 'Ready');
      setMicState('idle');
      break;
    case 'error':
      addMessage('agent', event.error && event.error.message
        ? event.error.message : 'Aura ran into a voice session issue.');
      setStatus('error', 'Session issue');
      break;
  }
}

function waitForIce(peer, maxWait) {
  if (peer.iceGatheringState === 'complete') return Promise.resolve();
  return new Promise(function (resolve) {
    let done = false;
    const finish = function () {
      if (done) return;
      done = true;
      clearTimeout(timer);
      peer.removeEventListener('icegatheringstatechange', check);
      resolve();
    };
    const check = function () {
      if (peer.iceGatheringState === 'complete') finish();
    };
    const timer = setTimeout(finish, maxWait);
    peer.addEventListener('icegatheringstatechange', check);
  });
}

function waitForChannel(channel, maxWait) {
  if (channel.readyState === 'open') return Promise.resolve();
  return new Promise(function (resolve, reject) {
    const clean = function () {
      clearTimeout(timer);
      channel.removeEventListener('open', opened);
      channel.removeEventListener('error', failed);
      channel.removeEventListener('close', closed);
    };
    const opened = function () { clean(); resolve(); };
    const failed = function () { clean(); reject(new Error('The live voice connection could not open.')); };
    const closed = function () { clean(); reject(new Error('The voice connection closed before it was ready.')); };
    const timer = setTimeout(function () {
      clean();
      reject(new Error('The voice connection took too long to start. Please try again.'));
    }, maxWait);
    channel.addEventListener('open', opened);
    channel.addEventListener('error', failed);
    channel.addEventListener('close', closed);
  });
}

function stopSession(notifyServer) {
  flushLiveMessage('user');
  flushLiveMessage('agent');
  connected = false;
  connecting = false;
  if (notifyServer !== false && dataChannel && dataChannel.readyState === 'open') {
    try { dataChannel.send(JSON.stringify({ type: 'session.close' })); } catch (error) {}
  }
  if (dataChannel) {
    dataChannel.onmessage = null;
    dataChannel.close();
    dataChannel = null;
  }
  if (peerConn) {
    peerConn.ontrack = null;
    peerConn.onconnectionstatechange = null;
    peerConn.close();
    peerConn = null;
  }
  if (localStream) {
    localStream.getTracks().forEach(function (track) { track.stop(); });
    localStream = null;
  }
  remoteAudio.pause();
  remoteAudio.srcObject = null;
  stopAnalyser();
  liveMessages = { user: null, agent: null };
  micBtn.disabled = false;
  setMicState('idle');
}

async function startSession() {
  if (connected || connecting) return;
  connecting = true;
  micBtn.disabled = true;
  setStatus('listening', 'Connecting…');
  setMicState('connecting');
  try {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      throw new Error('Microphone access is unavailable. Open Aura in a current browser on this computer.');
    }

    localStream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
      video: false,
    });
    setupAnalyser(localStream);

    peerConn = new RTCPeerConnection();
    peerConn.ontrack = function (event) {
      remoteAudio.srcObject = event.streams[0];
      remoteAudio.play().catch(function () {
        micHint.textContent = 'Tap the page once to enable Aura voice playback.';
      });
    };
    peerConn.onconnectionstatechange = function () {
      if (peerConn && peerConn.connectionState === 'failed') {
        addMessage('agent', 'The voice connection was interrupted. Check your internet connection and try again.');
        stopSession(false);
        setStatus('error', 'Connection lost');
      }
    };
    localStream.getAudioTracks().forEach(function (track) {
      peerConn.addTrack(track, localStream);
    });

    dataChannel = peerConn.createDataChannel('oai-events');
    dataChannel.addEventListener('message', handleEvent);
    const offer = await peerConn.createOffer();
    await peerConn.setLocalDescription(offer);
    await waitForIce(peerConn, 12000);

    const response = await fetch('/api/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      cache: 'no-store',
      body: JSON.stringify({
        sdp: peerConn.localDescription.sdp,
        language: languageSelect ? languageSelect.value : 'auto',
        voice: document.getElementById('voice-select')
          ? document.getElementById('voice-select').value : 'marin',
        history: chatHistory.slice(-20),
      }),
    });
    const sessionData = await readJson(response);
    if (!sessionData.sdp) throw new Error('OpenAI did not return a voice connection. Please try again.');
    await peerConn.setRemoteDescription({ type: 'answer', sdp: sessionData.sdp });
    await waitForChannel(dataChannel, 15000);

    connected = true;
    connecting = false;
    micBtn.disabled = false;
    setMicState('listening');
    setStatus('listening', 'Listening');
  } catch (error) {
    const message = error && error.message ? error.message : 'Aura could not start the voice session.';
    stopSession(false);
    setStatus('error', 'Couldn’t connect');
    addMessage('agent', message);
  }
}

micBtn.addEventListener('click', function () {
  if (connected || connecting) stopSession(true);
  else startSession();
});

settingsBtn.addEventListener('click', function () {
  stopSession(true);
  showScreen('key-screen');
  refreshKeyState();
});

if (clearChatBtn) {
  clearChatBtn.addEventListener('click', function () {
    txInner.innerHTML = '<div id="empty-chat" class="empty-state"><span class="empty-orbit"></span><p>Your conversation will appear here.</p><small>Start speaking to see the live transcript.</small></div>';
    liveMessages = { user: null, agent: null };
  });
}
// 6.  AUDIO ANALYSER (mic level → orb pulsing)
// ──────────────────────────────────────────────────
let analyserCtx, analyser, analyserData, analyserRaf;

function setupAnalyser(stream) {
  analyserCtx  = new (window.AudioContext || window.webkitAudioContext)();
  analyser     = analyserCtx.createAnalyser();
  analyser.fftSize = 256;
  analyserData = new Uint8Array(analyser.frequencyBinCount);
  analyserCtx.createMediaStreamSource(stream).connect(analyser);

  (function tick() {
    analyserRaf = requestAnimationFrame(tick);
    analyser.getByteFrequencyData(analyserData);
    const avg = analyserData.reduce((a, b) => a + b, 0) / analyserData.length;
    if (connected) setAudioLevel(avg / 128);   // normalise 0-1
  })();
}

function stopAnalyser() {
  if (analyserRaf) { cancelAnimationFrame(analyserRaf); analyserRaf = null; }
  if (analyserCtx) { analyserCtx.close(); analyserCtx = null; }
  setAudioLevel(0);
}


// ──────────────────────────────────────────────────
// 7.  RESIZE HANDLER
// ──────────────────────────────────────────────────
window.addEventListener('resize', () => {
  if (keyRenderer) {
    keyCamera.aspect = innerWidth / innerHeight;
    keyCamera.updateProjectionMatrix();
    keyRenderer.setSize(innerWidth, innerHeight);
  }
  resizeVoiceScene();
});


// ──────────────────────────────────────────────────
// ──────────────────────────────────────────────────
// ──────────────────────────────────────────────────
// Aura scene and interaction refinements.
const researchIndicator = document.getElementById('research-indicator');
const researchTitle = document.getElementById('research-title');
const researchCaption = document.getElementById('research-caption');
const sourceList = document.getElementById('source-list');
const sourceCount = document.getElementById('source-count');
const stageFocus = document.getElementById('stage-focus');
const transcriptState = document.getElementById('transcript-state');
const messageInput = document.getElementById('message-input');
const sendTextButton = document.getElementById('send-text-btn');
const promptChips = Array.from(document.querySelectorAll('.prompt-chip'));
let auraTurnCount = 0;

function initKeyScene() {
  const canvas = document.getElementById('key-canvas');
  if (!canvas || !window.THREE) return;
  keyRenderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  keyRenderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.8));
  keyRenderer.setSize(innerWidth, innerHeight);
  keyRenderer.setClearColor(0x000000, 0);
  keyScene = new THREE.Scene();
  keyCamera = new THREE.PerspectiveCamera(48, innerWidth / innerHeight, 0.1, 100);
  keyCamera.position.set(0, 0, 9);
  keyScene.add(new THREE.AmbientLight(0xb9e5df, 1.25));
  const keyLight = new THREE.PointLight(0x76dfd1, 22, 18);
  keyLight.position.set(2, 2, 4); keyScene.add(keyLight);
  const orbitGroup = new THREE.Group();
  const shell = new THREE.Mesh(new THREE.IcosahedronGeometry(1.22, 2),
    new THREE.MeshPhysicalMaterial({ color: 0x173c3d, metalness: .82, roughness: .19, clearcoat: 1, clearcoatRoughness: .12, wireframe: true, transparent: true, opacity: .28 }));
  orbitGroup.add(shell);
  const nucleus = new THREE.Mesh(new THREE.IcosahedronGeometry(.59, 2),
    new THREE.MeshPhysicalMaterial({ color: 0x76dfd1, emissive: 0x163c3a, metalness: .75, roughness: .22, clearcoat: 1 }));
  orbitGroup.add(nucleus);
  [1.8, 2.25, 2.72].forEach(function (radius, i) {
    const ring = new THREE.Mesh(new THREE.TorusGeometry(radius, i === 1 ? .009 : .014, 8, 160),
      new THREE.MeshBasicMaterial({ color: i === 1 ? 0x76dfd1 : 0x9bbdb9, transparent: true, opacity: i === 1 ? .26 : .12 }));
    ring.rotation.set(.35 + i * .42, .25 + i * .3, i * .24); orbitGroup.add(ring);
  });
  keyScene.add(orbitGroup);
  const points = new Float32Array(900);
  for (let i = 0; i < points.length; i += 3) {
    const radius = 3.2 + Math.random() * 5;
    const theta = Math.random() * Math.PI * 2;
    const phi = Math.acos(2 * Math.random() - 1);
    points[i] = radius * Math.sin(phi) * Math.cos(theta);
    points[i + 1] = radius * Math.sin(phi) * Math.sin(theta);
    points[i + 2] = radius * Math.cos(phi);
  }
  const starGeometry = new THREE.BufferGeometry();
  starGeometry.setAttribute('position', new THREE.BufferAttribute(points, 3));
  const stars = new THREE.Points(starGeometry, new THREE.PointsMaterial({ color: 0x8ccac2, size: .018, transparent: true, opacity: .52 }));
  keyScene.add(stars);
  let tick = 0;
  (function animateKey() {
    requestAnimationFrame(animateKey); tick += .003;
    orbitGroup.rotation.y = tick * .45; orbitGroup.rotation.x = Math.sin(tick * .4) * .13;
    nucleus.scale.setScalar(1 + Math.sin(tick * 2) * .025); stars.rotation.y += .00012;
    keyRenderer.render(keyScene, keyCamera);
  })();
}

function initVoiceScene() {
  const canvas = document.getElementById('voice-canvas');
  if (!canvas || !window.THREE) return;
  voiceRenderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  voiceRenderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.8));
  voiceRenderer.setClearColor(0x000000, 0);
  voiceScene = new THREE.Scene();
  voiceCamera = new THREE.PerspectiveCamera(48, 1, .1, 100);
  voiceCamera.position.set(0, 0, 5.7);
  voiceScene.add(new THREE.AmbientLight(0xb9e5df, 1.05));
  const glow = new THREE.PointLight(0x76dfd1, 27, 18); glow.position.set(0, 1.6, 3); voiceScene.add(glow);
  const rim = new THREE.PointLight(0x91d5ca, 14, 13); rim.position.set(-3, -2, 1); voiceScene.add(rim);
  const coreGroup = new THREE.Group();
  orbMesh = new THREE.Mesh(new THREE.IcosahedronGeometry(1.18, 4),
    new THREE.MeshPhysicalMaterial({ color: 0x286b66, emissive: 0x102c2a, metalness: .78, roughness: .18, clearcoat: 1, clearcoatRoughness: .12 }));
  coreGroup.add(orbMesh);
  wireFrame = new THREE.Mesh(new THREE.IcosahedronGeometry(1.35, 2),
    new THREE.MeshBasicMaterial({ color: 0xa0f3e8, wireframe: true, transparent: true, opacity: .23 }));
  coreGroup.add(wireFrame);
  ring1Mesh = new THREE.Mesh(new THREE.TorusGeometry(1.72, .012, 8, 180),
    new THREE.MeshBasicMaterial({ color: 0x91dcd1, transparent: true, opacity: .58 }));
  ring1Mesh.rotation.set(.95, .3, .18); coreGroup.add(ring1Mesh);
  ring2Mesh = new THREE.Mesh(new THREE.TorusGeometry(2.06, .007, 8, 180),
    new THREE.MeshBasicMaterial({ color: 0x76dfd1, transparent: true, opacity: .3 }));
  ring2Mesh.rotation.set(1.48, -.3, -.28); coreGroup.add(ring2Mesh);
  const p = new Float32Array(720);
  for (let i = 0; i < p.length; i += 3) {
    const radius = 2.45 + Math.random() * 1.35, a = Math.random() * Math.PI * 2, b = Math.acos(2 * Math.random() - 1);
    p[i] = radius * Math.sin(b) * Math.cos(a); p[i+1] = radius * Math.sin(b) * Math.sin(a); p[i+2] = radius * Math.cos(b);
  }
  const pg = new THREE.BufferGeometry(); pg.setAttribute('position', new THREE.BufferAttribute(p, 3));
  particleMesh = new THREE.Points(pg, new THREE.PointsMaterial({ color: 0x9be1d8, size: .021, transparent: true, opacity: .63 }));
  coreGroup.add(particleMesh); voiceScene.add(coreGroup);
  resizeVoiceScene();
  let tick = 0;
  (function animateVoice() {
    requestAnimationFrame(animateVoice); tick += .006;
    const speakingMode = micContainer && (micContainer.classList.contains('speaking') || micContainer.classList.contains('researching'));
    const floorLevel = speakingMode ? .20 + Math.sin(tick * 2.6) * .06 : 0;
    _audioLevel += ((_audioLevelTarget || floorLevel) - _audioLevel) * .10;
    const pulse = 1 + Math.min(.22, Math.max(0, _audioLevel) * .21) + Math.sin(tick * (speakingMode ? 2.8 : 1.1)) * (speakingMode ? .024 : .012);
    orbMesh.scale.setScalar(pulse); orbMesh.rotation.y += .0008 + _audioLevel * .001;
    wireFrame.rotation.y += .0011 + _audioLevel * .0015; wireFrame.rotation.x += .00035;
    ring1Mesh.rotation.z += .0012 + _audioLevel * .003; ring2Mesh.rotation.y -= .0008 + _audioLevel * .0015;
    particleMesh.rotation.y += .0005; coreGroup.rotation.y = Math.sin(tick * .25) * .08;
    voiceRenderer.render(voiceScene, voiceCamera);
  })();
}

function resizeVoiceScene() {
  if (!voiceRenderer || !voiceCamera) return;
  const canvas = document.getElementById('voice-canvas');
  if (!canvas) return;
  const width = Math.max(1, canvas.clientWidth || 1);
  const height = Math.max(1, canvas.clientHeight || 1);
  voiceCamera.aspect = width / height;
  voiceCamera.updateProjectionMatrix();
  voiceRenderer.setSize(width, height, false);
}

function updateTurnCount() {
  auraTurnCount = txInner ? txInner.querySelectorAll('.msg.user').length : auraTurnCount;
  const el = document.getElementById('turn-count');
  if (el) el.textContent = auraTurnCount + (auraTurnCount === 1 ? ' turn' : ' turns');
}

function setResearch(state, title, caption) {
  if (researchIndicator) {
    researchIndicator.dataset.state = state;
    researchIndicator.textContent = state === 'searching' ? 'SEARCHING' : state === 'complete' ? 'SOURCES READY' : state === 'error' ? 'UNAVAILABLE' : 'READY';
  }
  if (researchTitle && title) researchTitle.textContent = title;
  if (researchCaption && caption) researchCaption.textContent = caption;
}

function addCitation(source) {
  if (!sourceList || !source || typeof source.url !== 'string') return;
  let url;
  try { url = new URL(source.url); } catch (error) { return; }
  if (url.protocol !== 'https:' && url.protocol !== 'http:') return;
  const existing = Array.from(sourceList.querySelectorAll('a')).some(function (link) { return link.href === url.href; });
  if (existing) return;
  const empty = sourceList.querySelector('.source-empty'); if (empty) empty.remove();
  const link = document.createElement('a'); link.className = 'source-card'; link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer';
  const title = document.createElement('strong'); title.textContent = String(source.title || source.url).slice(0, 150);
  const domain = document.createElement('span'); domain.textContent = url.hostname.replace(/^www\./, '');
  link.append(title, domain); sourceList.appendChild(link);
  if (sourceCount) sourceCount.textContent = String(sourceList.querySelectorAll('a').length);
  setResearch('complete', 'Sources for your answer.', 'Open a citation to read the original page.');
}

function collectCitations(value, depth) {
  if (!value || depth > 8) return;
  if (Array.isArray(value)) { value.forEach(function (item) { collectCitations(item, depth + 1); }); return; }
  if (typeof value !== 'object') return;
  if (value.type === 'url_citation' || value.url_citation) {
    const cite = value.url_citation || value;
    addCitation({ url: cite.url, title: cite.title || cite.text });
  }
  if (typeof value.url === 'string' && (value.title || value.type === 'source')) addCitation(value);
  if (value.type === 'web_search_call' && value.action && Array.isArray(value.action.sources)) {
    value.action.sources.forEach(addCitation);
  }
  Object.keys(value).forEach(function (key) { if (key !== 'url') collectCitations(value[key], depth + 1); });
}

function processAuraEvent(event) {
  if (!event || typeof event !== 'object') return;
  if (event.type === 'session.delegation.created') {
    if (sourceList) sourceList.innerHTML = '<div class="source-empty">Searching trusted pages for current information…</div>';
    if (sourceCount) sourceCount.textContent = '…';
    setResearch('searching', 'Checking current sources…', 'Aura is looking up information for this answer.');
    if (stageFocus) stageFocus.textContent = 'Looking up current information';
  }
  const item = event.item || event.output_item;
  if ((item && item.type === 'web_search_call') || String(event.type || '').includes('web_search')) {
    setResearch('searching', 'Checking current sources…', 'Searching the web to ground this answer.');
  }
  if (event.type === 'response.output_item.done' || event.type === 'response.completed') collectCitations(event, 0);
  if (event.type === 'response.event' && event.event) processAuraEvent(event.event);
  switch (event.type) {
    case 'session.started':
      setStatus('listening', 'Listening'); setMicState('listening');
      break;
    case 'session.input_transcript.delta':
      appendTranscript('user', event.delta, event); updateTurnCount();
      if (connected) { setMicState('listening'); setStatus('listening', 'Listening'); }
      break;
    case 'session.output_transcript.delta':
      appendTranscript('agent', event.delta, event);
      if (connected) { setMicState('speaking'); setStatus('speaking', 'Speaking'); }
      break;
    case 'session.closed':
      if (connected || connecting) stopSession(false);
      setStatus('', 'Ready'); setMicState('idle');
      break;
    case 'error':
      addMessage('agent', event.error && event.error.message ? event.error.message : 'Aura ran into a voice session issue.');
      setStatus('error', 'Session issue');
      if (researchIndicator && researchIndicator.dataset.state === 'searching') setResearch('error', 'A live lookup could not finish.', 'Aura can still answer from general knowledge.');
      break;
    case 'response.completed':
      if (researchIndicator && researchIndicator.dataset.state === 'searching') setResearch('complete', 'Research complete.', 'Aura has finished checking current information.');
      if (stageFocus) stageFocus.textContent = 'Ready for your next question';
      break;
  }
}

function handleEvent(message) {
  let event; try { event = JSON.parse(message.data); } catch (error) { return; }
  if (event && event.type === 'response.event' && event.event) {
    let nested = event.event;
    if (typeof nested === 'string') { try { nested = JSON.parse(nested); } catch (error) { return; } }
    processAuraEvent(nested);
    return;
  }
  processAuraEvent(event);
}

function setStatus(state, label) {
  statusDot.className = 'status-dot' + (state ? ' ' + state : '');
  statusLabel.textContent = label;
  if (transcriptState) transcriptState.innerHTML = '<span class="state-pip"></span> ' + (connected ? label : 'Waiting for voice');
}

function setMicState(state) {
  micBtn.className = 'mic-btn' + (state !== 'idle' ? ' ' + state : '');
  micContainer.className = 'mic-container' + (state !== 'idle' ? ' ' + state : '');
  const hints = { idle: 'Click to start conversation', connecting: 'Connecting to Aura…', listening: 'Listening… click to end', speaking: 'Aura is speaking…' };
  micHint.textContent = hints[state] || '';
  micIcon.classList.toggle('hidden', state !== 'idle'); stopIcon.classList.toggle('hidden', state === 'idle' || state === 'connecting');
  setAudioLevel(state === 'speaking' ? .55 : state === 'listening' ? .1 : 0);
  if (messageInput) messageInput.disabled = !connected;
  if (sendTextButton) sendTextButton.disabled = !connected;
  promptChips.forEach(function (chip) { chip.disabled = !connected; });
  const labels = { idle: 'Ready when you are', connecting: 'Establishing secure voice', listening: 'Listening to you', speaking: 'Aura is responding' };
  if (stageFocus) stageFocus.textContent = labels[state] || labels.idle;
}

function sendTextMessage(text) {
  const clean = String(text || '').trim();
  if (!clean || !connected || !dataChannel || dataChannel.readyState !== 'open') return;
  try {
    dataChannel.send(JSON.stringify({ type: 'conversation.item.create', item: { type: 'message', role: 'user', content: [{ type: 'input_text', text: clean }] } }));
    dataChannel.send(JSON.stringify({ type: 'response.create' }));
    addMessage('user', clean); updateTurnCount();
    if (messageInput) messageInput.value = '';
    setStatus('listening', 'Thinking');
  } catch (error) { addMessage('agent', 'That message could not be sent. Please try again.'); }
}

if (sendTextButton) sendTextButton.addEventListener('click', function () { sendTextMessage(messageInput.value); });
if (messageInput) messageInput.addEventListener('keydown', function (event) { if (event.key === 'Enter') sendTextMessage(messageInput.value); });
promptChips.forEach(function (chip) { chip.addEventListener('click', function () { sendTextMessage(chip.dataset.prompt || chip.textContent); }); });
if (clearChatBtn) clearChatBtn.addEventListener('click', function () {
  txInner.innerHTML = '<div id="empty-chat" class="empty-state"><span class="empty-orbit" aria-hidden="true"></span><p>Your conversation will appear here.</p><small>Press the voice core to begin.</small></div>';
  liveMessages = { user: null, agent: null }; auraTurnCount = 0; updateTurnCount();
  if (sourceList) sourceList.innerHTML = '<div class="source-empty">Citations from live searches will appear here.</div>';
  if (sourceCount) sourceCount.textContent = '0';
  setResearch('idle', 'Grounded in what’s current.', 'Ask about today, the latest news, or anything that may have changed.');
});
// Keep setup voice user-initiated so it never talks over someone opening Aura.

// Unified voice/text chat, pinned scroll, inline citations, and a continuous voice core.
const scrollLatestButton = document.getElementById('scroll-latest-btn');
const chatHistory = [];
let textRequestBusy = false;
let scrollPinned = true;
let voiceResearchActive = false;
let voiceCitationTarget = null;
let pendingVoiceCitations = [];
let _audioLevelTarget = 0;

function setAudioLevel(level) {
  _audioLevelTarget = Math.max(0, Math.min(1, Number(level) || 0));
}

function chatNearBottom() {
  const area = document.getElementById('transcript-area');
  return !area || area.scrollHeight - area.scrollTop - area.clientHeight < 72;
}

function updateScrollControl() {
  const area = document.getElementById('transcript-area');
  if (!area) return;
  scrollPinned = chatNearBottom();
  if (scrollLatestButton) scrollLatestButton.classList.toggle('hidden', scrollPinned);
}

function scrollChatToBottom(force) {
  const area = document.getElementById('transcript-area');
  if (!area || (!force && !scrollPinned)) return;
  requestAnimationFrame(function () {
    area.scrollTo({ top: area.scrollHeight, behavior: force ? 'smooth' : 'auto' });
    if (force) { scrollPinned = true; if (scrollLatestButton) scrollLatestButton.classList.add('hidden'); }
  });
}

function rememberMessage(role, content) {
  const clean = String(content || '').trim();
  if (!clean) return;
  const last = chatHistory[chatHistory.length - 1];
  if (last && last.role === role && last.content === clean) return;
  chatHistory.push({ role: role, content: clean });
  if (chatHistory.length > 40) chatHistory.splice(0, chatHistory.length - 40);
}

function renderCitation(messageNode, source) {
  if (!messageNode || !source || typeof source.url !== 'string') return;
  let url; try { url = new URL(source.url); } catch (error) { return; }
  if (url.protocol !== 'https:' && url.protocol !== 'http:') return;
  let citationBox = messageNode.querySelector('.message-citations');
  if (!citationBox) {
    citationBox = document.createElement('div'); citationBox.className = 'message-citations';
    const label = document.createElement('span'); label.className = 'message-citations-label'; label.textContent = 'Sources';
    citationBox.appendChild(label); messageNode.appendChild(citationBox);
  }
  if (Array.from(citationBox.querySelectorAll('a')).some(function (item) { return item.href === url.href; })) return;
  const link = document.createElement('a'); link.className = 'message-citation'; link.href = url.href; link.target = '_blank'; link.rel = 'noopener noreferrer';
  link.title = String(source.title || url.hostname);
  const linkText = document.createElement('span'); linkText.textContent = String(source.title || url.hostname).slice(0, 100);
  const arrow = document.createElement('span'); arrow.setAttribute('aria-hidden', 'true'); arrow.textContent = '↗';
  link.append(linkText, arrow); citationBox.appendChild(link); scrollChatToBottom(false);
}

function addCitation(source) {
  if (!voiceResearchActive) return;
  const agentMessage = voiceCitationTarget || (liveMessages.agent && liveMessages.agent.body.closest('.msg'));
  if (agentMessage) renderCitation(agentMessage, source);
  else if (source && source.url && !pendingVoiceCitations.some(function (item) { return item.url === source.url; })) pendingVoiceCitations.push(source);
}

function attachPendingCitations(messageNode) {
  if (!voiceResearchActive || !messageNode) return;
  voiceCitationTarget = messageNode;
  pendingVoiceCitations.forEach(function (source) { renderCitation(messageNode, source); });
  pendingVoiceCitations = [];
}

function setResearch(state, title, caption) {
  const isSearching = state === 'searching';
  if (micContainer) micContainer.classList.toggle('researching', isSearching);
  if (stageFocus && title) stageFocus.textContent = title;
  if (isSearching) {
    setStatus('searching', 'Researching');
    if (transcriptState) transcriptState.innerHTML = '<span class="state-pip"></span> Checking current sources…';
  } else if (state === 'complete') {
    if (connected) setStatus('speaking', 'Speaking');
  } else if (state === 'error') {
    if (transcriptState) transcriptState.innerHTML = '<span class="state-pip"></span> Live lookup unavailable';
  }
}

function finishLiveMessage(role, current) {
  if (!current) return;
  if (current.timer) clearTimeout(current.timer);
  if (role === 'agent' && voiceResearchActive) attachPendingCitations(current.body.closest('.msg'));
  rememberMessage(role, current.body.textContent);
  if (liveMessages[role] === current) liveMessages[role] = null;
}

function flushLiveMessage(role) {
  const current = liveMessages[role];
  if (current) finishLiveMessage(role, current);
}

function makeMessage(role, text) {
  const empty = document.getElementById('empty-chat'); if (empty) empty.remove();
  const div = document.createElement('div'); div.className = 'msg ' + role;
  const label = document.createElement('div'); label.className = 'msg-label'; label.textContent = role === 'user' ? 'You' : 'Aura';
  const body = document.createElement('div'); body.className = 'msg-body'; body.textContent = text || '';
  div.append(label, body); txInner.appendChild(div);
  if (role === 'agent' && voiceResearchActive) attachPendingCitations(div);
  scrollChatToBottom(false); updateTurnCount();
  return body;
}

function appendTranscript(role, delta, event) {
  if (typeof delta !== 'string' || !delta) return;
  const now = Date.now(); const identity = event.item_id || event.response_id || '';
  let current = liveMessages[role];
  if (!current || (identity && current.identity && identity !== current.identity) || now - current.lastAt > 1600) {
    if (current) finishLiveMessage(role, current);
    const body = makeMessage(role, '');
    current = { body: body, identity: identity, lastAt: now, timer: null };
    liveMessages[role] = current;
    if (role === 'agent' && voiceResearchActive) attachPendingCitations(body.closest('.msg'));
  }
  current.body.textContent += delta; current.identity = identity || current.identity; current.lastAt = now;
  if (current.timer) clearTimeout(current.timer);
  current.timer = setTimeout(function () { finishLiveMessage(role, current); updateTurnCount(); }, 1300);
  updateTurnCount(); scrollChatToBottom(false);
}

function beginVoiceResearch() {
  if (!voiceResearchActive) { voiceResearchActive = true; voiceCitationTarget = null; pendingVoiceCitations = []; }
  setResearch('searching', 'Looking up current information', '');
}

function processAuraEvent(event) {
  if (!event || typeof event !== 'object') return;
  if (event.type === 'session.delegation.created') beginVoiceResearch();
  const item = event.item || event.output_item;
  if ((item && item.type === 'web_search_call') || String(event.type || '').includes('web_search')) beginVoiceResearch();
  if (event.type === 'response.output_item.done' || event.type === 'response.completed') collectCitations(event, 0);
  if (event.type === 'response.event' && event.event) processAuraEvent(event.event);
  switch (event.type) {
    case 'session.started': setStatus('listening', 'Listening'); setMicState('listening'); break;
    case 'session.input_transcript.delta':
      appendTranscript('user', event.delta, event); setMicState(connected ? 'listening' : 'idle');
      if (connected) setStatus('listening', 'Listening'); break;
    case 'session.output_transcript.delta':
      appendTranscript('agent', event.delta, event); if (connected) { setMicState('speaking'); setStatus('speaking', 'Speaking'); } break;
    case 'session.closed':
      flushLiveMessage('user'); flushLiveMessage('agent');
      if (connected || connecting) stopSession(false); setStatus('', 'Ready'); setMicState('idle'); break;
    case 'error':
      addMessage('agent', event.error && event.error.message ? event.error.message : 'Aura ran into a voice session issue.');
      setStatus('error', 'Session issue');
      if (voiceResearchActive) { voiceResearchActive = false; setResearch('error', 'A live lookup could not finish.', ''); }
      break;
    case 'response.completed':
      flushLiveMessage('user'); flushLiveMessage('agent');
      if (voiceResearchActive) { voiceResearchActive = false; voiceCitationTarget = null; pendingVoiceCitations = []; setResearch('complete', 'Ready for your next question', ''); }
      break;
  }
}

function setStatus(state, label) {
  statusDot.className = 'status-dot' + (state ? ' ' + state : '');
  statusLabel.textContent = label;
  if (transcriptState) transcriptState.innerHTML = '<span class="state-pip"></span> ' + (textRequestBusy ? label : connected ? label : state === 'error' ? label : 'Ready for a message');
}

function setMicState(state) {
  micBtn.className = 'mic-btn' + (state !== 'idle' ? ' ' + state : '');
  micContainer.className = 'mic-container' + (state !== 'idle' ? ' ' + state : '') + (voiceResearchActive ? ' researching' : '');
  const hints = { idle: 'Click the core to start a voice conversation', connecting: 'Connecting securely…', listening: 'I’m listening · click to finish', speaking: 'Aura is speaking · you can interrupt' };
  micHint.textContent = hints[state] || hints.idle;
  micIcon.classList.toggle('hidden', state !== 'idle'); stopIcon.classList.toggle('hidden', state === 'idle' || state === 'connecting');
  messageInput.disabled = connecting || textRequestBusy;
  sendTextButton.disabled = connecting || textRequestBusy;
  promptChips.forEach(function (chip) { chip.disabled = connecting || textRequestBusy; });
  const labels = { idle: 'Ready when you are', connecting: 'Establishing secure voice', listening: 'Listening to you', speaking: 'Aura is responding' };
  if (stageFocus && !voiceResearchActive) stageFocus.textContent = labels[state] || labels.idle;
  setAudioLevel(state === 'speaking' ? .28 : state === 'listening' ? .06 : 0);
}

async function sendTextMessage(text) {
  const clean = String(text || '').trim();
  if (!clean || connecting || textRequestBusy) return;
  if (connected && dataChannel && dataChannel.readyState === 'open') {
    try {
      dataChannel.send(JSON.stringify({ type: 'conversation.item.create', item: { type: 'message', role: 'user', content: [{ type: 'input_text', text: clean }] } }));
      dataChannel.send(JSON.stringify({ type: 'response.create' }));
      rememberMessage('user', clean); addMessage('user', clean); messageInput.value = '';
      scrollChatToBottom(true); setStatus('listening', 'Thinking'); return;
    } catch (error) { addMessage('agent', 'That message could not be sent. Please try again.'); return; }
  }

  rememberMessage('user', clean); addMessage('user', clean); messageInput.value = '';
  textRequestBusy = true; setMicState('idle'); setStatus('searching', 'Thinking');
  const replyBody = makeMessage('agent', '');
  const replyCard = replyBody.closest('.msg'); replyCard.classList.add('typing');
  replyBody.innerHTML = 'Thinking<span class="typing-dots" aria-label="Aura is thinking"><i></i><i></i><i></i></span>';
  scrollChatToBottom(true);
  try {
    const response = await postJson('/api/chat', { messages: chatHistory.slice(-18), language: languageSelect ? languageSelect.value : 'auto' });
    replyCard.classList.remove('typing'); replyBody.textContent = response.answer || 'I could not find a response. Please try again.';
    rememberMessage('assistant', replyBody.textContent);
    (Array.isArray(response.citations) ? response.citations : []).forEach(function (source) { renderCitation(replyCard, source); });
    setStatus('', 'Ready');
  } catch (error) {
    replyCard.classList.remove('typing'); replyBody.textContent = error && error.message ? error.message : 'Aura could not complete that request.';
    setStatus('error', 'Couldn’t reply');
  } finally {
    textRequestBusy = false; setMicState('idle');
    if (sendTextButton) sendTextButton.disabled = false;
    scrollChatToBottom(false); updateTurnCount();
  }
}

const transcriptArea = document.getElementById('transcript-area');
if (transcriptArea) transcriptArea.addEventListener('scroll', updateScrollControl, { passive: true });
if (scrollLatestButton) scrollLatestButton.addEventListener('click', function () { scrollChatToBottom(true); });
if (sendTextButton) sendTextButton.addEventListener('click', function () { sendTextMessage(messageInput.value); });
if (messageInput) messageInput.addEventListener('keydown', function (event) { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); sendTextMessage(messageInput.value); } });
promptChips.forEach(function (chip) { chip.addEventListener('click', function () { sendTextMessage(chip.dataset.prompt || chip.textContent); }); });
if (clearChatBtn) clearChatBtn.addEventListener('click', function () {
  chatHistory.length = 0; liveMessages = { user: null, agent: null }; voiceResearchActive = false; pendingVoiceCitations = []; voiceCitationTarget = null;
  txInner.innerHTML = '<div id="empty-chat" class="empty-state"><span class="empty-orbit" aria-hidden="true"></span><p>What would you like to explore?</p><small>Ask by voice or start typing below.</small></div>';
  auraTurnCount = 0; updateTurnCount(); scrollPinned = true; updateScrollControl();
  if (stageFocus) stageFocus.textContent = 'Ready when you are';
  if (micContainer) micContainer.classList.remove('researching');
  setStatus('', 'Ready');
});

// Setup and animate the 3D core continuously; smooth the audio envelope to avoid stutter.

// 8. INIT
// ──────────────────────────────────────────────────
(async function init() {
  if (window.THREE) { try { initKeyScene(); } catch (error) { console.warn('[Aura] 3D scene unavailable.'); } }
  try { await refreshKeyState(); } catch (error) {}
  // Setup speech remains available from its explicit button.
  showScreen('key-screen');
})();'''

LIVE_SESSIONS_URL = "https://api.openai.com/v1/live/sessions"
RESPONSES_URL = "https://api.openai.com/v1/responses"
AGENT_PROMPT = (
    "You are Aura, a warm, thoughtful multilingual voice assistant. Speak naturally, "
    "clearly, and concisely. Understand Urdu in Urdu script and Roman Urdu, and mirror "
    "the user's language and natural code-switching. Ask a brief follow-up only when "
    "needed. Never claim an action you did not take.\n\n"
    "Backchannel policy: Use brief acknowledgements only when they help conversation.\n"
    "Interruption policy: Stop speaking promptly when the user interrupts.\n"
    "Delegation policy: Delegate questions that depend on current facts to the backend.\n"
    "Backend tools: Live web search for current, latest, today's, or changeable facts.\n"
    "Generate <|SpawnThinking|> when: the answer needs current news, dates, weather, "
    "sports, prices, laws, public figures, software versions, or another changing fact.\n"
    "Do not generate <|SpawnThinking|> when: the user greets you or asks stable general "
    "knowledge that does not need current sources. Do not guess while research is running."
)
LANGUAGES = {
    "auto": "automatic language matching", "en": "English", "ur": "Urdu",
    "hi": "Hindi", "ar": "Arabic", "es": "Spanish", "fr": "French",
    "de": "German", "zh": "Mandarin Chinese", "pt": "Portuguese",
    "ja": "Japanese", "tr": "Turkish", "ru": "Russian",
}
VOICES = {"marin", "cedar", "coral", "alloy"}


def _saved_api_key() -> str:
    env_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if env_key:
        return env_key
    try:
        secret_key = st.secrets.get("OPENAI_API_KEY", "")
    except Exception:
        return ""
    return secret_key.strip() if isinstance(secret_key, str) else ""


ROMAN_URDU_WORDS = {
    "aaj", "aap", "ab", "abhi", "acha", "achi", "agar", "ap", "apka", "apki", "apko", "apni",
    "aur", "batao", "bataya", "bas", "bhi", "bhe", "bht", "bohat", "btao",
    "chahe", "chaye", "hai", "hain", "ha", "ho", "hua", "hu", "hun", "hoon",
    "hum", "ka", "kaam", "kab", "kahan", "kaisa", "kaise", "karo", "karna", "karta", "kerti", "ker", "keray",
    "kerna", "kero", "kesay", "kaha", "keh", "ke", "ki", "kis", "ko", "kia", "kya", "kyun", "main", "mai", "ma", "may", "mein",
    "mera", "mere", "meri", "mujhe", "mujhay", "na", "nahi", "nahin", "nay", "ne", "or", "par", "per", "pe", "py",
    "poucha", "poocha", "pucha", "raha", "rahi", "reh", "rha", "sakta", "saktay", "say", "se", "sey", "tha", "the", "thi", "to", "toh",
    "tum", "tumhe", "wo", "woh", "ya", "ye", "yeh", "yar", "yaar",
}
ROMAN_URDU_STRONG_WORDS = ROMAN_URDU_WORDS - {
    "aaj", "ab", "abhi", "agar", "ap", "bas", "chahe", "kaisa", "kaise", "main", "mai", "ma", "may", "mein",
    "na", "nay", "ne", "or", "par", "per", "pe", "py", "say", "se", "sey", "tha", "the", "thi",
    "to", "toh", "tum", "ya", "ye", "yeh",
}


def _input_script(text: str) -> str:
    if re.search(r"[\u0900-\u097f]", text):
        return "devanagari"
    if re.search(r"[\u0600-\u06ff\u0750-\u077f\u08a0-\u08ff]", text):
        return "urdu-script" if re.search(r"[ٹڈڑںھہےپچژگک]", text) else "arabic-script"
    words = set(re.findall(r"[a-z]+", text.lower()))
    if words & ROMAN_URDU_STRONG_WORDS or len(words & ROMAN_URDU_WORDS) >= 3:
        return "roman-urdu"
    return "latin"


def _reply_language_rule(language: str, latest_text: str = "") -> str:
    if language == "ur":
        return " Reply in Urdu using Urdu script (not Devanagari), unless the user explicitly asks to switch languages."
    if language == "hi":
        return " Reply in Hindi using Devanagari script, unless the user explicitly asks to switch languages."
    if language == "en":
        return " Reply in English, unless the user explicitly asks to switch languages."
    if language != "auto":
        return f" Reply in {LANGUAGES[language]}, unless the user explicitly asks to switch languages."

    script = _input_script(latest_text) if latest_text else "unknown"
    if script == "devanagari":
        return " The latest user message is in Hindi written in Devanagari. Answer in Hindi using Devanagari."
    if script == "urdu-script":
        return " The latest user message is Urdu written in Urdu script. Answer in Urdu using Urdu script, never Devanagari."
    if script == "arabic-script":
        return " The latest user message uses Arabic-derived script. Identify whether it is Urdu or Arabic, then answer in that language using the same script; never convert Urdu to Devanagari."
    if script == "roman-urdu":
        return " The latest user message is Roman Urdu written with Latin letters. Reply in natural Roman Urdu using Latin letters, keep normal English code-switching, and never translate it into Hindi or use Devanagari."
    return (
        " Detect the language and script of the latest user message and answer in that same language and script. "
        "If it is Roman Urdu, reply in natural Roman Urdu using Latin letters; do not translate it into Hindi or use Devanagari. "
        "Use Urdu script for Urdu-script Urdu, Devanagari only when the user writes Hindi, and English for English."
    )


def _instructions(language: str) -> str:
    return AGENT_PROMPT + _reply_language_rule(language) + (
        " Apply the rule to every turn based on the user's current words, not the earlier conversation. "
        "For written chat and transcripts, preserve the user's writing system: Roman Urdu stays in Latin letters."
    )


def _provider_error(error: HTTPError, api_key: str) -> str:
    try:
        message = json.loads(error.read()).get("error", {}).get("message", "")
    except (json.JSONDecodeError, AttributeError, UnicodeDecodeError):
        message = ""
    if not isinstance(message, str) or not message:
        message = "The voice session could not be started."
    message = message.replace(api_key, "[hidden]").replace("\r", " ").replace("\n", " ").strip()
    if len(message) > 420:
        message = message[:417] + "..."
    return f"OpenAI ({error.code}): {message}"


def _response_output_text(result: Any) -> str:
    if not isinstance(result, dict):
        return ""
    direct = result.get("output_text")
    if isinstance(direct, str) and direct.strip():
        return direct.strip()

    chunks = []
    output = result.get("output")
    if not isinstance(output, list):
        return ""
    for item in output:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if not isinstance(part, dict):
                continue
            part_type = part.get("type")
            if part_type in {"output_text", "text"}:
                value = part.get("text", "")
            elif part_type == "refusal":
                value = part.get("refusal") or part.get("text", "")
            else:
                continue
            if isinstance(value, str) and value.strip():
                chunks.append(value.strip())
    return "\n".join(chunks)


def _create_session(data: dict[str, Any], api_key: str) -> tuple[int, dict[str, Any]]:
    sdp, language, voice = data.get("sdp"), data.get("language", "auto"), data.get("voice", "marin")
    if not isinstance(sdp, str) or not sdp.strip() or len(sdp) > 65536:
        return 400, {"error": "The browser could not prepare a microphone connection. Please try again."}
    if not isinstance(language, str) or language not in LANGUAGES:
        language = "auto"
    if not isinstance(voice, str) or voice not in VOICES:
        voice = "marin"
    payload = {
        "session": {
            "model": "gpt-live-1",
            "instructions": _instructions(language) + _history_context(data.get("history")), 
            "audio": {"output": {"voice": voice}},
            "store": False,
            "delegation": {
                "type": "responses",
                "responses": {
                    "model": "gpt-6-luna",
                    "instructions": (
                        "Answer the delegated question with concise, accurate research. "
                        "Use web search for current or changeable claims. Prefer primary "
                        "and authoritative sources, include relevant citations, and be "
                        "clear when evidence is uncertain or sources disagree."
                        + _reply_language_rule(language)
                        + " Keep the spoken answer to one to three short sentences."
                    ),
                    "tools": [{"type": "web_search"}],
                    "tool_choice": "auto",
                    "max_output_tokens": 320,
                },
            },
        },
        "transport": {"type": "webrtc", "sdp": sdp},
    }
    request = Request(LIVE_SESSIONS_URL, data=json.dumps(payload).encode("utf-8"), headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "Accept": "application/json"
    }, method="POST")
    try:
        with urlopen(request, timeout=60) as response:
            result = json.loads(response.read())
    except HTTPError as exc:
        return 502, {"error": _provider_error(exc, api_key)}
    except (URLError, TimeoutError, OSError):
        return 502, {"error": "Aura could not reach OpenAI. Check your internet connection and try again."}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 502, {"error": "OpenAI returned a response Aura could not read. Please try again."}
    session = result.get("session") if isinstance(result, dict) else None
    transport = result.get("transport") if isinstance(result, dict) else None
    answer = transport.get("sdp") if isinstance(transport, dict) else None
    session_id = session.get("id") if isinstance(session, dict) else ""
    if not isinstance(answer, str) or not answer.strip():
        return 502, {"error": "OpenAI did not return a voice connection. Please try again."}
    return 201, {"session_id": session_id if isinstance(session_id, str) else "", "sdp": answer}


def _history_context(history: Any) -> str:
    if not isinstance(history, list):
        return ""
    lines = []
    remaining = 9000
    for message in history[-20:]:
        if not isinstance(message, dict) or message.get("role") not in {"user", "assistant"}:
            continue
        content = message.get("content", "")
        if not isinstance(content, str) or not content.strip():
            continue
        content = content.strip()[:1800]
        line = f"{message['role']}: {content}"
        if len(line) > remaining:
            break
        lines.append(line)
        remaining -= len(line) + 1
    if not lines:
        return ""
    return "\n\nContinue this existing conversation. Recent context (do not repeat it):\n" + "\n".join(lines)


def _create_text_response(data: dict[str, Any], api_key: str) -> tuple[int, dict[str, Any]]:
    messages = data.get("messages")
    language = data.get("language", "auto")
    if not isinstance(language, str) or language not in LANGUAGES:
        language = "auto"
    if not isinstance(messages, list) or not messages or len(messages) > 20:
        return 400, {"error": "Send a conversation with at least one message."}
    clean_messages = []
    for message in messages:
        if not isinstance(message, dict) or message.get("role") not in {"user", "assistant"}:
            continue
        content = message.get("content")
        if not isinstance(content, str) or not content.strip() or len(content) > 6000:
            continue
        clean_messages.append({"role": message["role"], "content": content.strip()})
    if not clean_messages or clean_messages[-1]["role"] != "user":
        return 400, {"error": "The latest chat message must be from you."}
    language_instruction = _reply_language_rule(language, clean_messages[-1]["content"])
    instructions = (
        "You are Aura, a warm and capable multilingual assistant. Give clear, useful answers. "
        "Use web search when a question asks about the latest, today, current events, or facts that may have changed. "
        "Prefer reliable primary sources; be transparent if sources disagree or evidence is uncertain. "
        "Keep casual answers concise, and provide citations through the available source annotations. "
        + language_instruction
    )
    payload = {
        "model": "gpt-6-luna",
        "instructions": instructions,
        "input": clean_messages,
        "tools": [{"type": "web_search"}],
        "tool_choice": "auto",
        "include": ["web_search_call.action.sources"],
        "max_output_tokens": 700,
        "store": False,
    }
    request = Request(RESPONSES_URL, data=json.dumps(payload).encode("utf-8"), headers={
        "Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "Accept": "application/json"
    }, method="POST")
    try:
        with urlopen(request, timeout=90) as response:
            result = json.loads(response.read())
    except HTTPError as exc:
        return 502, {"error": _provider_error(exc, api_key)}
    except (URLError, TimeoutError, OSError):
        return 502, {"error": "Aura could not reach OpenAI. Check your internet connection and try again."}
    except (json.JSONDecodeError, UnicodeDecodeError):
        return 502, {"error": "OpenAI returned a response Aura could not read. Please try again."}

    answer = _response_output_text(result)
    sources = []
    seen_urls = set()
    for item in (result.get("output", []) if isinstance(result, dict) else []):
        if not isinstance(item, dict):
            continue
        action = item.get("action")
        if item.get("type") == "web_search_call" and isinstance(action, dict):
            for source in action.get("sources", []):
                if isinstance(source, dict):
                    url = source.get("url", "")
                    if isinstance(url, str) and url.startswith(("https://", "http://")) and url not in seen_urls:
                        seen_urls.add(url)
                        sources.append({"url": url, "title": str(source.get("title") or url)[:160]})
        for content in item.get("content", []) if isinstance(item.get("content"), list) else []:
            if not isinstance(content, dict):
                continue
            for annotation in content.get("annotations", []) if isinstance(content.get("annotations"), list) else []:
                if not isinstance(annotation, dict):
                    continue
                citation = annotation.get("url_citation", annotation)
                if not isinstance(citation, dict):
                    continue
                url = citation.get("url", "")
                if isinstance(url, str) and url.startswith(("https://", "http://")) and url not in seen_urls:
                    seen_urls.add(url)
                    sources.append({"url": url, "title": str(citation.get("title") or url)[:160]})
    if not answer:
        provider_problem = result.get("error") if isinstance(result, dict) else None
        if isinstance(provider_problem, dict):
            message = provider_problem.get("message", "")
            if isinstance(message, str) and message.strip():
                message = message.replace(api_key, "[hidden]").replace("\r", " ").replace("\n", " ").strip()
                return 502, {"error": f"OpenAI could not complete the reply: {message[:360]}"}
        incomplete = result.get("incomplete_details") if isinstance(result, dict) else None
        reason = incomplete.get("reason") if isinstance(incomplete, dict) else None
        if isinstance(reason, str) and reason:
            return 502, {"error": f"OpenAI could not complete the reply ({reason.replace('_', ' ')}). Please try again."}
        return 502, {"error": "OpenAI returned no readable text for this reply. Please try again."}
    return 200, {"answer": answer, "citations": sources[:12]}


def _dispatch_api(path: str, data: Any, user_key: str) -> tuple[int, dict[str, Any], str | None]:
    if not isinstance(data, dict):
        return 400, {"error": "The request body must be an object."}, None
    saved_key = _saved_api_key()
    if path == "/api/health":
        source = "session" if user_key else ("saved" if saved_key else "")
        return 200, {"has_key": bool(user_key or saved_key), "key_source": source}, None
    if path == "/api/key":
        if data.get("use_existing") is True:
            if user_key or saved_key:
                return 200, {"success": True}, None
            return 409, {"error": "No local key is available. Enter an OpenAI API key."}, None
        value = data.get("api_key")
        if not isinstance(value, str):
            return 400, {"error": "Enter your OpenAI API key to continue."}, None
        key = value.strip()
        if len(key) < 12 or len(key) > 512 or not key.startswith("sk-"):
            return 400, {"error": "That key does not look right. Check it and try again."}, None
        return 200, {"success": True}, key
    if path not in {"/api/session", "/api/chat"}:
        return 404, {"error": "Not found."}, None
    api_key = user_key or saved_key
    if not api_key:
        return 503, {"error": "Add an OpenAI API key before starting a conversation."}, None
    if path == "/api/chat":
        status, response = _create_text_response(data, api_key)
    else:
        status, response = _create_session(data, api_key)
    return status, response, None


def _on_rpc_request_change() -> None:
    # Register the persistent component state so it is included in the result.
    return None


def _process_rpc_request(request: Any) -> bool:
    if not isinstance(request, dict):
        return False
    request_id = request.get("id")
    if not isinstance(request_id, str) or not request_id:
        return False
    if st.session_state.get("aura_last_rpc_id") == request_id:
        return False
    st.session_state["aura_last_rpc_id"] = request_id
    path, data = request.get("path"), request.get("body", {})
    if path not in {"/api/health", "/api/key", "/api/session", "/api/chat"}:
        status, result, new_key = 404, {"error": "Not found."}, None
    elif len(json.dumps(data, ensure_ascii=False).encode("utf-8")) > 100_000:
        status, result, new_key = 413, {"error": "The request is too large."}, None
    else:
        try:
            status, result, new_key = _dispatch_api(path, data, st.session_state.get("aura_user_api_key", ""))
        except Exception:
            status, result, new_key = 500, {"error": "Aura could not complete that request. Please try again."}, None
    if new_key:
        st.session_state["aura_user_api_key"] = new_key
    st.session_state["aura_rpc_response"] = {"id": request_id, "status": status, "body": result}
    return True


def _component_javascript() -> str:
    app_code = APP_JS.replace("document.getElementById(", "findById(")
    app_code = app_code.replace("document.querySelectorAll(", "root.querySelectorAll(")
    app_code = app_code.replace("document.querySelector(", "root.querySelector(")
    if app_code.count("fetch(") != 3:
        raise RuntimeError("Unexpected number of Aura API requests in the embedded UI.")
    app_code = app_code.replace("fetch(", "window.__auraRpc(")
    old_line = "  if (!voiceRenderer && window.THREE) initVoiceScene();"
    new_line = (
        "  if (!voiceRenderer && window.THREE) initVoiceScene();\n"
        "  else if (!voiceRenderer && window.__auraThreeReady) {\n"
        "    window.__auraThreeReady.then(function () { if (!voiceRenderer) initVoiceScene(); });\n"
        "  }"
    )
    if app_code.count(old_line) != 1:
        raise RuntimeError("Could not prepare Aura's 3D scene for Streamlit.")
    app_code = app_code.replace(old_line, new_line, 1)
    prefix = r'''export default function (component) {
  const { parentElement, data, setStateValue } = component;
  const root = parentElement;
  const findById = (id) => root.querySelector("#" + id);
  window.__auraStreamlitRpcState = setStateValue;
  if (data && data.rpc_response && window.__auraPendingRpc) {
    const result = data.rpc_response;
    const resolveRequest = window.__auraPendingRpc.get(result.id);
    if (resolveRequest) {
      window.__auraPendingRpc.delete(result.id);
      resolveRequest(new Response(JSON.stringify(result.body || {}), {
        status: result.status || 200,
        headers: { "Content-Type": "application/json; charset=utf-8" },
      }));
      window.__auraStreamlitRpcState("rpc_request", null);
    }
  }
  if (window.__auraAppInitialized) return;
  window.__auraAppInitialized = true;
  window.__auraPendingRpc = new Map();
  window.__auraRpc = function (path, options) {
    const url = new URL(String(path), window.location.href);
    let body = {};
    try { body = options && options.body ? JSON.parse(options.body) : {}; } catch (_) {}
    const id = window.crypto && crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2);
    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        window.__auraPendingRpc.delete(id);
        reject(new Error("Aura is taking too long to respond. Please try again."));
      }, 90000);
      window.__auraPendingRpc.set(id, (response) => { clearTimeout(timeout); resolve(response); });
      try { window.__auraStreamlitRpcState("rpc_request", { id, path: url.pathname, body }); }
      catch (error) { clearTimeout(timeout); window.__auraPendingRpc.delete(id); reject(error); }
    });
  };
  window.__auraThreeReady = new Promise((resolve) => {
    if (window.THREE) { resolve(); return; }
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.min.js";
    script.onload = resolve;
    script.onerror = resolve;
    document.head.appendChild(script);
  });
'''
    tail = "}\n"
    return prefix + app_code + tail


def _streamlit_app() -> None:
    st.set_page_config(page_title="Aura — Voice Agent", page_icon="🎙️", layout="wide", initial_sidebar_state="collapsed")
    match = re.search(r"(?is)<body[^>]*>(.*?)</body>", INDEX_HTML)
    if not match:
        st.error("Aura's embedded interface could not be loaded.")
        return
    component_html = re.sub(r"(?is)<script\b[^>]*>.*?</script\s*>", "", match.group(1))
    component_css = STYLES_CSS.replace(":root {", ":host {", 1).replace("html, body {", ":host {", 1)
    component_css = ":host { position: fixed; inset: 0; z-index: 40; display: block; width: 100vw; height: 100vh; overflow: hidden; background: #091115; }\n" + component_css
    aura = st.components.v2.component(name="aura_voice_agent", html=component_html, css=component_css,
                                      js=_component_javascript(), isolate_styles=True)
    result = aura(key="aura_component", data={"rpc_response": st.session_state.get("aura_rpc_response")},
                  default={"rpc_request": None}, width="stretch", height=850,
                  on_rpc_request_change=_on_rpc_request_change)
    if _process_rpc_request(getattr(result, "rpc_request", None)):
        st.rerun()


def main() -> None:
    if not st.runtime.exists():
        raise SystemExit("Start Aura with: streamlit run app.py")
    _streamlit_app()


if __name__ == "__main__":
    main()



