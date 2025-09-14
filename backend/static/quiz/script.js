let questions = [];
let answers = {};
let currentIndex = 0;
let timerValue = 0;
let timerInterval = null;

document.addEventListener('DOMContentLoaded', ()=> {
  const beginBtn = document.getElementById('beginBtn');
  const qArea = document.getElementById('questionArea');
  const intro = document.getElementById('intro');
  const resultArea = document.getElementById('resultArea');
  const prevBtn = document.getElementById('prevBtn');
  const nextBtn = document.getElementById('nextBtn');
  const progressBar = document.getElementById('progressBar');

  // Fix: Show quiz interface even if fetch fails (for static/demo use)
  beginBtn.onclick = async ()=>{
    beginBtn.disabled = true;
    beginBtn.innerText = 'Loading...';
    try {
      const res = await fetch('/quiz/start', {method:'POST'});
      if (!res.ok) throw new Error("Quiz fetch failed");
      const data = await res.json();
      questions = data.questions;
      timerValue = data.timer || 60;
      intro.classList.add('hidden');
      qArea.classList.remove('hidden');
      currentIndex = 0;
      startTimer();
      renderQuestion();
      updateProgress();
    } catch (e) {
      // fallback: show quiz area even if backend fails (for demo)
      intro.classList.add('hidden');
      qArea.classList.remove('hidden');
      document.getElementById('qText').innerText = "Quiz could not be loaded.";
      document.getElementById('options').innerHTML = "";
      document.getElementById('prevBtn').disabled = true;
      document.getElementById('nextBtn').disabled = true;
    }
  };

  prevBtn.onclick = ()=>{
    if(currentIndex>0) currentIndex--;
    renderQuestion();
    updateProgress();
  };
  nextBtn.onclick = ()=>{
    if(currentIndex < questions.length-1){
      currentIndex++;
      renderQuestion();
    } else {
      submitAnswers();
    }
    updateProgress();
  };
});

function renderQuestion(){
  const q = questions[currentIndex];
  document.getElementById('qNumber').innerText = `Question ${currentIndex+1} / ${questions.length}`;
  document.getElementById('qText').innerText = q.question;
  const opts = document.getElementById('options');
  opts.innerHTML = '';
  q.options.forEach((o, idx)=>{
    const div = document.createElement('div');
    div.className = 'option';
    div.innerText = o;
    div.onclick = ()=>{
      answers[String(q.id)] = idx;
      Array.from(opts.children).forEach(c=>c.classList.remove('selected'));
      div.classList.add('selected');
    };
    if(answers[String(q.id)] === idx) div.classList.add('selected');
    opts.appendChild(div);
  });
  document.getElementById('prevBtn').disabled = (currentIndex===0);
  document.getElementById('nextBtn').innerText = (currentIndex===questions.length-1? 'Finish':'Next');
}

function updateProgress(){
  const p = ((currentIndex)/ (questions.length))*100;
  document.getElementById('progressBar').style.width = p + '%';
}

function startTimer(){
  const timerEl = document.getElementById('timer');
  timerEl.innerText = timerValue;
  timerInterval = setInterval(()=>{
    timerValue--;
    timerEl.innerText = timerValue;
    if(timerValue<=0){
      clearInterval(timerInterval);
      submitAnswers();
    }
  },1000);
}

async function submitAnswers(){
  clearInterval(timerInterval);
  const payload = {answers: answers};
  const res = await fetch('/quiz/submit', {
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  showResult(data);
}

function showResult(data){
  document.getElementById('questionArea').classList.add('hidden');
  const resArea = document.getElementById('resultArea');
  resArea.classList.remove('hidden');
  document.getElementById('scoreText').innerText = `You scored ${data.score} out of ${data.total}`;
  document.getElementById('badgeText').innerText = data.badge;
  const correctList = document.getElementById('correctList');
  correctList.innerHTML = data.correct.map(q=>`<li>${q}</li>`).join('');
  const wrongList = document.getElementById('wrongList');
  wrongList.innerHTML = data.wrong.map(q=>`<li>${q}</li>`).join('');
}
