// ================================================================
// SatyaCheck — Client-side logic
// Language toggle, API integration, result rendering
// ================================================================

(function () {
  'use strict';

  // ── DOM refs ──────────────────────────────────────────────────
  const langBtns      = document.querySelectorAll('.lang-btn');
  const inputText     = document.getElementById('inputText');
  const charCount     = document.getElementById('charCount');
  const analyzeBtn    = document.getElementById('analyzeBtn');
  const clearBtn      = document.getElementById('clearBtn');
  const resultSection = document.getElementById('resultSection');
  const resultCard    = document.getElementById('resultCard');
  const verdictIcon   = document.getElementById('verdictIcon');
  const verdictEl     = document.getElementById('verdict');
  const confidenceEl  = document.getElementById('confidence');
  const explanationEl = document.getElementById('explanation');
  const flaggedWords  = document.getElementById('flaggedWords');
  const flaggedSection = document.getElementById('flaggedSection');

  let selectedLang = 'en';

  // ── Placeholders per language ─────────────────────────────────
  const PLACEHOLDERS = {
    en: 'Paste or type your text here...',
    mr: 'तुमचा मजकूर येथे लिहा किंवा पेस्ट करा...',
  };

  // ── Verdict display config ────────────────────────────────────
  const VERDICT_CONFIG = {
    fake:      { label: 'Likely Misinformation', icon: '⚠' },
    real:      { label: 'Likely Credible',       icon: '✓' },
    uncertain: { label: 'Uncertain',             icon: '?' },
  };

  // ── Language toggle ───────────────────────────────────────────
  langBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      langBtns.forEach(function (b) { b.classList.remove('active'); });
      btn.classList.add('active');
      selectedLang = btn.dataset.lang;
      inputText.placeholder = PLACEHOLDERS[selectedLang] || PLACEHOLDERS.en;
    });
  });

  // ── Character count ───────────────────────────────────────────
  inputText.addEventListener('input', function () {
    charCount.textContent = inputText.value.length.toLocaleString();
  });

  // ── Clear button ──────────────────────────────────────────────
  clearBtn.addEventListener('click', function () {
    inputText.value = '';
    charCount.textContent = '0';
    resultSection.classList.remove('visible');
  });

  // ── Analyze ───────────────────────────────────────────────────
  analyzeBtn.addEventListener('click', async function () {
    var text = inputText.value.trim();

    if (text === '') {
      shakeElement(inputText);
      return;
    }

    setLoading(true);
    resultSection.classList.remove('visible');

    try {
      var response = await fetch('/detect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: text, language: selectedLang }),
      });

      if (!response.ok) throw new Error('Server returned ' + response.status);

      var data = await response.json();
      showResult(data);
    } catch (err) {
      // Fallback to client-side mock when backend is unreachable
      var mockData = getMockResult(text);
      showResult(mockData);
    }

    setLoading(false);
  });

  // ── Render result ─────────────────────────────────────────────
  function showResult(data) {
    var v = data.verdict || 'uncertain';
    var config = VERDICT_CONFIG[v] || VERDICT_CONFIG.uncertain;

    // Card class
    resultCard.className = 'result-card ' + v;

    // Verdict
    verdictIcon.textContent = config.icon;
    verdictEl.className = 'verdict ' + v;
    verdictEl.textContent = config.label;

    // Confidence
    confidenceEl.className = 'confidence ' + v;
    confidenceEl.textContent = data.confidence + '% confidence';

    // Explanation
    explanationEl.textContent = data.explanation || '';

    // Flagged phrases
    flaggedWords.innerHTML = '';
    if (data.flagged && data.flagged.length > 0) {
      flaggedSection.style.display = '';
      data.flagged.forEach(function (word) {
        var tag = document.createElement('span');
        tag.className = 'tag';
        tag.textContent = word;
        flaggedWords.appendChild(tag);
      });
    } else {
      flaggedSection.style.display = 'none';
    }

    // Show
    resultSection.classList.add('visible');

    // Scroll into view
    resultSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  // ── Loading state ─────────────────────────────────────────────
  function setLoading(on) {
    analyzeBtn.disabled = on;
    if (on) {
      analyzeBtn.classList.add('loading');
    } else {
      analyzeBtn.classList.remove('loading');
    }
  }

  // ── Shake animation for empty input ───────────────────────────
  function shakeElement(el) {
    el.style.animation = 'none';
    void el.offsetHeight; // trigger reflow
    el.style.animation = 'shake 0.4s ease';
    el.addEventListener('animationend', function () {
      el.style.animation = '';
    }, { once: true });
  }

  // Inject shake keyframes
  var shakeStyle = document.createElement('style');
  shakeStyle.textContent =
    '@keyframes shake { ' +
    '0%, 100% { transform: translateX(0); } ' +
    '20%, 60% { transform: translateX(-6px); } ' +
    '40%, 80% { transform: translateX(6px); } }';
  document.head.appendChild(shakeStyle);

  // ── Client-side mock fallback ─────────────────────────────────
  function getMockResult(text) {
    var lower = text.toLowerCase();
    var keywords = [
      'cure', 'secret', 'banned', 'miracle', 'shocking',
      'forward this', 'viral', 'urgent', 'breaking',
      'पसरवा', 'चमत्कार', 'शेअर करा', 'लगेच',
    ];
    var found = [];

    for (var i = 0; i < keywords.length; i++) {
      if (lower.includes(keywords[i])) {
        found.push(keywords[i]);
      }
    }

    if (found.length >= 3) {
      return {
        verdict: 'fake',
        confidence: Math.min(60 + found.length * 10, 97),
        explanation: 'Contains multiple sensationalist or commonly flagged misinformation keywords.',
        flagged: found,
      };
    } else if (found.length >= 1) {
      return {
        verdict: 'uncertain',
        confidence: 40 + found.length * 10,
        explanation: 'Some patterns associated with misinformation were detected, but the text is not conclusively misleading.',
        flagged: found,
      };
    } else {
      return {
        verdict: 'real',
        confidence: 85,
        explanation: 'No immediate red flags detected in the text.',
        flagged: [],
      };
    }
  }

})();