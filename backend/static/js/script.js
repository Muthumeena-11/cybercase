document.addEventListener('DOMContentLoaded', function(){
  const phoneIcon = document.getElementById('phoneIcon');
  const messagesIcon = document.getElementById('messagesIcon');
  const contentArea = document.getElementById('contentArea');
  const submitBtn = document.getElementById('submitBtn');
  const answerInput = document.getElementById('answerInput');
  const ansFeedback = document.getElementById('ansFeedback');
  const notesArea = document.getElementById('notesArea');
  const clearNotes = document.getElementById('clearNotes');
  const statusInfo = document.getElementById('statusInfo');

  // load notes from sessionStorage
  notesArea.value = sessionStorage.getItem('mission_notes') || '';
  notesArea.addEventListener('input', function(){ sessionStorage.setItem('mission_notes', notesArea.value); });
  clearNotes.addEventListener('click', function(){ notesArea.value=''; sessionStorage.removeItem('mission_notes'); });

  function loadApp(path){
    fetch(path).then(r=>r.text()).then(html=>{
      contentArea.innerHTML = html;
    }).catch(err=>{
      contentArea.innerHTML = '<div class="app-screen"><p>Error loading app.</p></div>';
    });
  }

  phoneIcon.addEventListener('click', ()=> loadApp('/phone'));
  messagesIcon.addEventListener('click', ()=> loadApp('/messages'));

  // validation
  submitBtn.addEventListener('click', function(){
    const ans = answerInput.value.trim();
    if(!ans){ ansFeedback.style.color='yellow'; ansFeedback.innerText='Please enter a name.'; return; }
    fetch('/validate', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({answer: ans})
    }).then(r=>r.json()).then(data=>{
      if(data.result === 'correct'){
        ansFeedback.style.color='lightgreen'; ansFeedback.innerText = data.message || 'Correct!';
        // redirect to completed
        setTimeout(()=> window.location.href = data.redirect || '/completed', 600);
      } else {
        ansFeedback.style.color='yellow'; ansFeedback.innerText = data.message || 'Incorrect. Try again.';
      }
    }).catch(err=>{
      ansFeedback.style.color='yellow'; ansFeedback.innerText = 'Validation error.';
    });
  });

  // fetch status
  fetch('/status').then(r=>r.json()).then(d=>{
    if(d.status && d.status !== 'not cleared') statusInfo.innerText = 'Score: '+d.score+' — '+d.status;
    else statusInfo.innerText = 'Score: 0 — not cleared';
  }).catch(()=> statusInfo.innerText = 'Status unavailable');
});

document.getElementById('answerForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const answer = document.getElementById('answer').value.trim();
    fetch('/validate_answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer })
    })
    .then(res => res.json())
    .then(data => {
        const feedback = document.getElementById('feedback');
        if (data.status === "correct") {
            feedback.innerHTML = '<span style="color: green;">Correct! Redirecting...</span>';
            setTimeout(() => window.location.href = "/completed", 1500);
        } else {
            feedback.innerHTML = '<span style="color: yellow;">Incorrect. Try again.</span>';
        }
    })
    .catch(err => console.error(err));
});
