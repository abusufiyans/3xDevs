// Language toggle
const langBtns = document.querySelectorAll('.lang-btn');
let selectedLang = 'en';

langBtns.forEach(function(btn) {
  btn.addEventListener('click', function() {
    langBtns.forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');
    selectedLang = btn.dataset.lang;

    var textarea = document.getElementById('inputText');
    if (selectedLang === 'mr') {
      textarea.placeholder = 'येथे मजकूर पेस्ट करा किंवा टाइप करा...';
    } else {
      textarea.placeholder = 'Paste or type your text here...';
    }
  });
});

// Character count
var inputText = document.getElementById('inputText');
var charCount = document.getElementById('charCount');

inputText.addEventListener('input', function() {
  charCount.textContent = inputText.value.length;
});

// Analyze button click
var analyzeBtn = document.getElementById('analyzeBtn');
var resultSection = document.getElementById('resultSection');

analyzeBtn.addEventListener('click', async function() {
  var text = inputText.value.trim();

  if (text === '') {
    alert('Please enter some text.');
    return;
  }

  analyzeBtn.textContent = 'Analyzing...';
  analyzeBtn.disabled = true;
  resultSection.classList.remove('visible');

  try {
    var response = await fetch('/detect', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: text, language: selectedLang })
    });

    if (!response.ok) throw new Error('Server error');

    var data = await response.json();
    showResult(data);

  } catch (err) {
    // backend not connected yet, use mock
    var mockData = getMockResult(text);
    showResult(mockData);
  }

  analyzeBtn.textContent = 'Analyze Text';
  analyzeBtn.disabled = false;
});

// Show result on page
function showResult(data) {
  var resultCard = document.getElementById('resultCard');
  var verdictEl = document.getElementById('verdict');
  var confidenceEl = document.getElementById('confidence');
  var explanationEl = document.getElementById('explanation');
  var flaggedWordsEl = document.getElementById('flaggedWords');

  var labels = {
    fake: 'Likely Misinformation',
    real: 'Likely Credible',
    uncertain: 'Uncertain'
  };

  resultCard.className = 'result-card ' + data.verdict;
  verdictEl.className = 'verdict ' + data.verdict;
  verdictEl.textContent = labels[data.verdict] || data.verdict;
  confidenceEl.textContent = 'Confidence: ' + data.confidence + '%';
  explanationEl.textContent = data.explanation;

  flaggedWordsEl.innerHTML = '';
  if (data.flagged && data.flagged.length > 0) {
    data.flagged.forEach(function(word) {
      var tag = document.createElement('span');
      tag.className = 'tag';
      tag.textContent = word;
      flaggedWordsEl.appendChild(tag);
    });
  } else {
    flaggedWordsEl.innerHTML = '<span style="color:#aaa; font-size:0.8rem;">None detected</span>';
  }

  resultSection.classList.add('visible');
}

// Mock result for demo when backend is offline
function getMockResult(text) {
  var lower = text.toLowerCase();
  var keywords = ['cure', 'secret', 'banned', 'miracle', 'shocking', 'forward this', 'viral', 'पसरवा', 'चमत्कार'];
  var found = [];

  for (var i = 0; i < keywords.length; i++) {
    if (lower.includes(keywords[i])) {
      found.push(keywords[i]);
    }
  }

  if (found.length >= 2) {
    return {
      verdict: 'fake',
      confidence: 85,
      explanation: 'This text contains multiple patterns commonly found in misinformation — sensational language and unverified claims that are meant to trigger emotional sharing.',
      flagged: found
    };
  } else if (found.length === 1) {
    return {
      verdict: 'uncertain',
      confidence: 52,
      explanation: 'Some patterns were detected that could indicate misleading content. Verify this through a trusted source before sharing.',
      flagged: found
    };
  } else {
    return {
      verdict: 'real',
      confidence: 90,
      explanation: 'No major misinformation patterns were detected. The text does not contain sensational or emotionally manipulative language.',
      flagged: []
    };
  }
}