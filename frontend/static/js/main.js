const langBtns = document.querySelectorAll('.lang-btn');
let selectedLang = 'en';

langBtns.forEach(function(btn) {
  btn.addEventListener('click', function() {
    langBtns.forEach(function(b) { b.classList.remove('active'); });
    btn.classList.add('active');
    selectedLang = btn.dataset.lang;

    var textarea = document.getElementById('inputText');
    if (selectedLang === 'mr') {
      
    } else {
      
    }
  });
});

var inputText = document.getElementById('inputText');
var charCount = document.getElementById('charCount');

inputText.addEventListener('input', function() {
  charCount.textContent = inputText.value.length;
});

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
    var mockData = getMockResult(text);
    showResult(mockData);
  }

  analyzeBtn.textContent = 'Analyze Text';
  analyzeBtn.disabled = false;
});

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

function getMockResult(text) {
  var lower = text.toLowerCase();
  var keywords = ['cure', 'secret', 'banned', 'miracle', 'shocking', 'forward this', 'viral', 'पसरवा', 'चमत्कार'];
  var found = [];

  for (var i = 0; i < keywords.length; i++) {
    if (lower.includes(keywords[i])) {
      found.push(keywords[i]);
    }
  }

}