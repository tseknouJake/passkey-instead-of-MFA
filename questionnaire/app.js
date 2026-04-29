// DATA
const levels = [
  {
    id: 0,
    name: "Level 01",
    label: "Passwords",
    scenarios: [
      {
        eyebrow: "SCENARIO 1 · PASSWORD LOGIN",
        title: "You get an email saying your account is about to be locked",
        context: "You use a normal username and password to log in to your university portal. You just got this email.",
        url: '<span class="url-sus">http://univ-portal-secure-login.com/verify</span>',
        sim: `
          <div class="email-box">
            <div class="email-header">
              <div class="email-from">From: <span>security-noreply@univ-portal-secure-login.com</span></div>
              <div class="email-subj">⚠ Your account will be locked in 24 hours</div>
            </div>
            <div class="email-body">
              Hi,<br><br>
              We noticed unusual activity on your account. Click the link below to verify your login details and avoid being locked out.<br><br>
              <a class="email-link sus" onclick="return false">👉 http://univ-portal-secure-login.com/verify</a><br><br>
              — University IT Team
            </div>
          </div>`,
        prompt: "You click the link and it opens a page that looks exactly like your university login. What do you do?",
        choices: [
          { text: "Log in — it looks exactly like the real page so it must be fine", correct: false, failMsg: "Scammers copy the look of real websites perfectly — that is the whole trick. The page can look identical but still be fake. The only thing that matters is the web address at the top of your browser, not how the page looks." },
          { text: "Look at the web address at the top of the browser — it is different from your university's real website", correct: true },
          { text: "Type a wrong password first to see if it rejects it", correct: false, failMsg: "Fake login pages are set up to always say wrong password the first time — they want you to try again with your real one. Even entering a wrong password tells the attacker your username. Do not type anything on a page you are not sure about." },
        ],
        pass: "Good instinct. The web address at the top of the browser is the one thing scammers cannot fake — it will always be different from the real site. If the address does not match the official website you know, close the tab immediately.",
      },
      {
        eyebrow: "SCENARIO 2 · PASSWORD LOGIN",
        title: "Someone is trying to guess your password automatically",
        context: "Your email was included in a data breach — it got leaked online. Now someone is using a program that automatically tries thousands of common passwords on your account.",
        url: '<span class="url-ok">https://portal.university.nl/login</span>',
        sim: `
          <div class="bf-terminal" id="bf-anim">
            <span class="bf-line info">> Trying passwords for: alice@university.nl</span>
            <span class="bf-line info">> Starting...</span>
          </div>`,
        prompt: "Which of these passwords would stop the attack?",
        choices: [
          { text: "student2024 — easy to remember", correct: false, failMsg: "Passwords like student2024 are some of the first ones these programs try. They go through millions of common words, names, and number combinations automatically. Easy to remember usually means easy to guess." },
          { text: "P@ssw0rd! — replaced letters with symbols", correct: false, failMsg: "Swapping letters for symbols like @ for a or 0 for o is a very well-known trick — these programs already have those variations in their list. It looks stronger than it is." },
          { text: "A random mix of letters, numbers and symbols that does not spell anything", correct: true },
        ],
        pass: "Exactly. A random password that does not spell any word or follow any pattern is the only kind that is truly safe from this kind of attack. A password manager can generate and remember these for you so you do not have to.",
        hasBfAnim: true,
      },
    ]
  },
  {
    id: 1,
    name: "Level 02",
    label: "Two-Factor Authentication",
    scenarios: [
      {
        eyebrow: "SCENARIO 1 · TWO-FACTOR AUTH",
        title: "You have a code sent to your phone — but so does the attacker",
        context: "You use two-factor authentication where your bank texts you a 6-digit code every time you log in. Unknown to you, someone called your phone company pretending to be you and got your number moved to their SIM card.",
        url: '<span class="url-ok">https://bank.com/login</span>',
        sim: `
          <div style="display:grid;gap:14px;">
            <div style="border:1px solid var(--border);padding:14px;background:var(--bg);">
              <div style="font-size:0.65rem;color:var(--red);letter-spacing:2px;margin-bottom:8px;">WHAT HAPPENED EARLIER TODAY</div>
              <div style="font-size:0.75rem;line-height:1.8;color:var(--text-dim);">
                Someone called your phone company and said: "Hi, I lost my phone, can you move my number to this new SIM?"<br><br>
                <span style="color:var(--yellow);">Phone company: "Sure, just give us your date of birth and last 4 digits — done!"</span>
              </div>
            </div>
            <div style="border:1px solid var(--red);padding:14px;background:var(--bg);text-align:center;">
              <div style="font-size:0.65rem;color:var(--red);letter-spacing:2px;margin-bottom:8px;">YOUR PHONE NOW</div>
              <div style="font-size:2rem;">📵</div>
              <div style="font-size:0.72rem;color:var(--text-dim);margin-top:8px;">No signal. All your texts including login codes are going to someone else's phone.</div>
            </div>
          </div>`,
        prompt: "Your phone suddenly has no signal and you are not getting texts anymore. What is the safest thing to do?",
        choices: [
          { text: "Wait — it is probably just a network outage", correct: false, failMsg: "Suddenly losing all signal, especially if you were getting texts before, can be a sign your number was moved. While you wait, someone could be using those login codes to get into your accounts. It is worth calling your phone company straight away to check." },
          { text: "Call your phone company immediately to check if your number has been moved without your permission", correct: true },
          { text: "Try logging into your accounts to see if your password still works", correct: false, failMsg: "If someone has your texts, they also have any login codes sent to you. Logging in right now might trigger a code being sent — which goes straight to the attacker. Call your phone company first before doing anything else." },
        ],
        pass: "Right move. Sudden loss of signal out of nowhere is a warning sign worth taking seriously. A quick call to your phone company can confirm whether your number is still on your SIM or if someone moved it.",
      },
      {
        eyebrow: "SCENARIO 2 · TWO-FACTOR AUTH",
        title: "You get a phone call asking for your login code",
        context: "You use an app that gives you a 6-digit code to log in alongside your password. You just got a phone call out of nowhere.",
        url: '<span class="url-ok">https://portal.university.nl/login</span>',
        sim: `
          <div style="border:1px solid var(--border);padding:20px;background:var(--bg);text-align:center;">
            <div style="font-size:2.5rem;margin-bottom:12px;">📞</div>
            <div style="font-size:0.85rem;margin-bottom:16px;">Incoming call: <span style="color:var(--yellow);">University IT Support</span></div>
            <div style="font-size:0.78rem;color:var(--text-dim);line-height:1.9;text-align:left;padding:0 8px;">
              "Hi, this is IT support. We detected a login attempt on your account and need to verify it is you. 
              Could you open your authenticator app and read me the 6-digit code? We just need it to confirm your identity."
            </div>
          </div>`,
        prompt: "What do you do?",
        choices: [
          { text: "Read them the code — they called from an official number and sound professional", correct: false, failMsg: "Phone numbers can be faked to show any name or number including official ones. More importantly, real IT support will never ask for your login code. Nobody legitimate needs that code except you, at the moment you are logging in." },
          { text: "Ask them to verify themselves first by telling you your student ID", correct: false, failMsg: "This is better thinking, but a scammer can still bluff or make something up. The safest rule is simpler: no legitimate service will ever call and ask for your login code. Just hang up." },
          { text: "Hang up — nobody should ever ask you for your login code, not even IT support", correct: true },
        ],
        pass: "Correct. This is called social engineering — tricking people into handing over security codes by pretending to be someone trusted. The rule is simple: your login code is only for you to type in when you are logging in. Nobody else should ever ask for it.",
      },
    ]
  },
  {
    id: 3,
    name: "Level 04",
    label: "Passkeys & Biometrics",
    scenarios: [
      {
        eyebrow: "SCENARIO 1 · PASSKEY LOGIN",
        title: "You use your fingerprint to log in — no password needed",
        context: "You have set up a passkey on your phone. Instead of typing a password, you just use your fingerprint or face to log in. You get the same fake email as Level 1 — someone trying to get you to log in on their fake website.",
        url: '<span class="url-sus">http://univ-portal-secure-login.com/verify</span>',
        sim: `
          <div style="display:grid;gap:14px;">
            <div style="border:1px solid var(--border);padding:14px;background:var(--bg);">
              <div style="font-size:0.65rem;color:var(--text-dim);letter-spacing:2px;margin-bottom:8px;">WHAT YOUR PHONE CHECKS</div>
              <div style="font-size:0.75rem;line-height:1.9;">
                Website asking to log in: <span style="color:var(--red);">univ-portal-secure-login.com</span><br>
                Website your passkey is registered for: <span style="color:var(--green);">portal.university.nl</span><br><br>
                <span style="color:var(--red);">These do not match — your phone refuses to log in.</span>
              </div>
            </div>
            <div style="border:1px solid var(--green);padding:14px;background:rgba(0,255,136,0.04);">
              <div style="font-size:0.65rem;color:var(--green);letter-spacing:2px;margin-bottom:8px;">RESULT</div>
              <div style="font-size:0.75rem;line-height:1.8;color:var(--text-dim);">
                The fake site never gets your details. Your phone blocked it automatically — you did not even have to spot the scam yourself.
              </div>
            </div>
          </div>`,
        prompt: "The scam failed automatically even though you clicked the link. Why?",
        choices: [
          { text: "Your fingerprint is impossible to copy so the attacker could not fake it", correct: false, failMsg: "Your fingerprint is used locally on your device to unlock it — it is never sent anywhere. The reason the scam failed is different: your passkey is locked to the real website address, so it simply will not work on a fake one." },
          { text: "Your passkey only works on the real website — your phone checks the address automatically and refuses fake sites", correct: true },
          { text: "The fake site did not have a padlock icon so the browser blocked it", correct: false, failMsg: "Fake sites can and often do have a padlock — it just means the connection is encrypted, not that the site is trustworthy. The real protection is that your passkey is registered to a specific website address. If the address does not match exactly, your phone will not log you in." },
        ],
        pass: "Exactly. Your passkey is linked to the exact website address you registered it on. Your phone checks this automatically every time. Even if you click a scam link by mistake, your phone will simply refuse — there is nothing for the scammer to steal.",
      },
      {
        eyebrow: "SCENARIO 2 · PASSKEY LOGIN",
        title: "Someone finds out your password — but you use a passkey",
        context: "You use a passkey to log in to your email — no password, just your fingerprint. Somehow a scammer found out the password you used before you switched. They try to log in with it.",
        url: '<span class="url-ok">https://mail.service.com/login</span>',
        sim: `
          <div class="bf-terminal">
            <span class="bf-line info">> Trying to log in as: alex@mail.service.com</span>
            <span class="bf-line warn">> Entering old password: "MyOldPassword2022!"</span>
            <span class="bf-line ok">> Server: This account uses passkey login.</span>
            <span class="bf-line ok">> Password login is disabled for this account.</span>
            <span class="bf-line ok">> Login requires the physical device with the registered passkey.</span>
            <span class="bf-line ok">> Login attempt failed.</span>
          </div>`,
        prompt: "The attacker has your old password but still cannot get in. Why not?",
        choices: [
          { text: "Your new password is stronger so they guessed wrong", correct: false, failMsg: "There is no password anymore — that is the key point. With a passkey, the password is completely gone. There is nothing to guess, steal, or leak." },
          { text: "With a passkey there is no password at all — logging in requires your physical device, so knowing a password does nothing", correct: true },
          { text: "The account got locked after too many wrong attempts", correct: false, failMsg: "Account lockouts help with passwords, but the reason here is more fundamental — passkeys remove the password entirely. The attacker can try as many times as they want and it still will not work because there is no password to be right about." },
        ],
        pass: "Right. Switching to a passkey means the password is gone entirely — not just changed to something stronger, but completely removed. There is nothing left to steal, guess, or leak from a data breach. Your physical device is the only way in.",
      },
    ]
  }
];

// STATE
let currentLevel = 0;
let currentScenario = 0;
let sessionResults = [];
let levelResults = {};
let otpInterval = null;

// NAVIGATION
function show(screenId) {
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  document.getElementById('screen-' + screenId).classList.add('active');
  window.scrollTo(0,0);
}

function goToLevels() { show('levels'); }

function startLevel(lvIdx) {
  currentLevel = lvIdx;
  currentScenario = 0;
  sessionResults = [];
  if (otpInterval) clearInterval(otpInterval);
  loadScenario();
  show('scenario');
}

function nextScenario() {
  currentScenario++;
  const level = levels[currentLevel];
  if (currentScenario >= level.scenarios.length) {
    showLevelResults();
  } else {
    loadScenario();
    document.getElementById('result-panel').style.display = 'none';
    window.scrollTo(0,0);
  }
}

// LOAD SCENARIO
function loadScenario() {
  if (otpInterval) clearInterval(otpInterval);
  const level = levels[currentLevel];
  const sc = level.scenarios[currentScenario];

  document.getElementById('bar-level').textContent = level.name;
  document.getElementById('bar-step').textContent = (currentScenario + 1) + ' / ' + level.scenarios.length;

  // dots
  const dotsEl = document.getElementById('bar-dots');
  dotsEl.innerHTML = '';
  level.scenarios.forEach((_, i) => {
    const d = document.createElement('div');
    d.className = 'dot';
    if (i < currentScenario) {
      const r = sessionResults[i];
      d.classList.add(r ? 'dot-pass' : 'dot-fail');
    } else if (i === currentScenario) {
      d.style.background = 'var(--cyan)';
      d.style.boxShadow = '0 0 6px var(--cyan)';
    } else {
      d.classList.add('dot-skip');
    }
    dotsEl.appendChild(d);
  });

  document.getElementById('sc-eyebrow').textContent = sc.eyebrow;
  document.getElementById('sc-title').textContent = sc.title;
  document.getElementById('sc-context').textContent = sc.context;
  document.getElementById('win-url').innerHTML = sc.url;
  document.getElementById('sim-content').innerHTML = sc.sim;
  document.getElementById('choice-prompt').textContent = sc.prompt;
  document.getElementById('result-panel').style.display = 'none';
  document.getElementById('next-btn').style.display = '';

  // Build choices
  const choicesEl = document.getElementById('choices');
  choicesEl.innerHTML = '';
  sc.choices.forEach((c, i) => {
    const btn = document.createElement('button');
    btn.className = 'choice-btn';
    btn.textContent = c.text;
    btn.onclick = () => handleChoice(i, c.correct, sc);
    choicesEl.appendChild(btn);
  });

  // Brute force animation
  if (sc.hasBfAnim) {
    setTimeout(runBfAnim, 600);
  }

  // OTP timer
  if (sc.hasOtpTimer) {
    let t = 28;
    const el = document.getElementById('otp-countdown');
    if (el) {
      otpInterval = setInterval(() => {
        t--;
        if (t <= 0) { t = 30; }
        if (el) el.textContent = t;
      }, 1000);
    }
  }
}

function handleChoice(idx, correct, sc) {
  const btns = document.querySelectorAll('.choice-btn');
  btns.forEach((b, i) => {
    b.disabled = true;
    if (i === idx) {
      b.classList.add(correct ? 'correct' : 'wrong');
    }
    if (!correct && sc.choices[i].correct) {
      b.classList.add('correct');
    }
  });

  sessionResults.push(correct);

  const panel = document.getElementById('result-panel');
  panel.className = 'result-panel ' + (correct ? 'pass' : 'fail');
  panel.style.display = 'block';

  document.getElementById('result-verdict').textContent = correct ? '✓ CORRECT — YOU\'RE SECURE' : '✗ CAUGHT — ACCOUNT COMPROMISED';
  const failText = sc.choices[idx].failMsg || sc.fail;
  document.getElementById('result-explain').textContent = correct ? sc.pass : failText;

  const isLast = currentScenario === levels[currentLevel].scenarios.length - 1;
  const nextBtn = document.getElementById('next-btn');
  nextBtn.textContent = isLast ? 'SEE RESULTS →' : 'NEXT SCENARIO →';

  panel.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// BRUTE FORCE ANIMATION
async function runBfAnim() {
  const el = document.getElementById('bf-anim');
  if (!el) return;
  const lines = [
    { t:'try', s:'> Attempt 001: password → FAIL' },
    { t:'try', s:'> Attempt 002: 123456 → FAIL' },
    { t:'try', s:'> Attempt 047: iloveyou → FAIL' },
    { t:'try', s:'> Attempt 083: student2024 → ...' },
    { t:'hit', s:'> ✗ MATCH at attempt 083: student2024' },
    { t:'hit', s:'> Account accessed. Session token captured.' },
  ];
  for (const line of lines) {
    await sleep(380 + Math.random() * 250);
    const span = document.createElement('span');
    span.className = 'bf-line ' + line.t;
    span.textContent = line.s;
    el.appendChild(span);
    el.scrollTop = el.scrollHeight;
  }
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function showLevelResults() {
  const level = levels[currentLevel];
  const passed = sessionResults.filter(Boolean).length;
  const total = sessionResults.length;

  // Save to level scores
  levelResults[currentLevel] = { passed, total };

  // Update level card indicator
  const scoreEl = document.getElementById('score-lv' + currentLevel);
  if (scoreEl) {
    const allPass = passed === total;
    scoreEl.innerHTML = `<span class="dot ${allPass ? 'dot-pass' : 'dot-fail'}"></span> ${passed}/${total} passed`;
  }

  // Build results screen
  document.getElementById('final-title').textContent = level.name + ' COMPLETE';
  document.getElementById('final-sub').textContent = level.label + ' — ' + (passed === total ? 'Excellent work.' : 'Review the explanations below.');
  document.getElementById('final-score').innerHTML = `<span style="color:${passed===total?'var(--green)':'var(--yellow)'}">${passed}/${total}</span>`;

  const grid = document.getElementById('results-grid');
  grid.innerHTML = '';
  level.scenarios.forEach((sc, i) => {
    const pass = sessionResults[i];
    const div = document.createElement('div');
    div.className = 'result-row ' + (pass ? 'pass' : 'fail');
    div.innerHTML = `
      <div class="result-icon">${pass ? '✓' : '✗'}</div>
      <div class="result-info">
        <div class="result-name">${sc.title}</div>
        <div class="result-sub">${pass ? 'DEFENDED' : 'COMPROMISED'}${rating ? ' &nbsp;·&nbsp; EASE: ' + rating.rating + '/5' : ''}</div>
      </div>`;
    grid.appendChild(div);
  });

  show('results');
}

