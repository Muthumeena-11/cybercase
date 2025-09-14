(() => {
  const canvas = document.getElementById("gameCanvas");
  const ctx = canvas.getContext("2d");

  const scoreEl = document.getElementById("score");
  const timeEl = document.getElementById("time");
  const missesEl = document.getElementById("misses");
  const startBtn = document.getElementById("startBtn");
  const restartBtn = document.getElementById("restartBtn");

  const overlay = document.getElementById("overlay");
  const modalTitle = document.getElementById("modalTitle");
  const modalReason = document.getElementById("modalReason");
  const closeModal = document.getElementById("closeModal");
  const playAgain = document.getElementById("playAgain");
  const reviewTableBody = document.querySelector("#reviewTable tbody");

  // Game config
  const GAME_DURATION = 60;        // seconds
  const MAX_MISSES = 5;            // miss = strong password hits the ground
  const SPAWN_INTERVAL = 900;      // ms
  const FALL_SPEED_RANGE = [1.2, 2.8];  // pixels per frame
  const ITEM_FONT = "16px monospace";   // same color for all items
  const ITEM_COLOR = "#e6edf3";         // same color constraint
  const LOCK_COLOR = "#e6edf3";         // monochrome lock, same color
  const BASKET_COLOR = "#7ee787";

  const strongPool = [...(window.gameData?.strong || [])];
  const weakPool = [...(window.gameData?.weak || [])];

  // Basket
  const basket = {
    x: canvas.width / 2 - 60,
    y: canvas.height - 28,
    w: 120,
    h: 16,
    speed: 6
  };

  let state = resetState();

  function resetState() {
    return {
      running: false,
      score: 0,
      timeLeft: GAME_DURATION,
      misses: 0,
      items: [],
      lastSpawn: 0,
      caughtLog: [],
      reason: ""
    };
  }

  function drawBasket() {
    ctx.fillStyle = BASKET_COLOR;
    ctx.fillRect(basket.x, basket.y, basket.w, basket.h);
  }

  function drawLock(x, y, scale=1) {
    // Simple monochrome padlock to avoid color hints
    ctx.save();
    ctx.translate(x, y);
    ctx.scale(scale, scale);
    ctx.strokeStyle = LOCK_COLOR;
    ctx.lineWidth = 2;

    // Shackle
    ctx.beginPath();
    ctx.arc(12, 10, 8, Math.PI, 0, false);
    ctx.stroke();

    // Body
    ctx.strokeRect(4, 10, 16, 14);

    // Keyhole
    ctx.beginPath();
    ctx.arc(12, 18, 2, 0, Math.PI * 2);
    ctx.moveTo(12, 20);
    ctx.lineTo(12, 24);
    ctx.stroke();

    ctx.restore();
  }

  function drawItem(item) {
    // item: {x, y, vy, text, strong}
    drawLock(item.x - 22, item.y - 8, 1);
    ctx.fillStyle = ITEM_COLOR;
    ctx.font = ITEM_FONT;
    ctx.fillText(item.text, item.x, item.y);
  }

  function spawnItem() {
    // Choose strong 60% of time, weak 40% (tweakable)
    const isStrong = Math.random() < 0.6;
    const pool = isStrong ? strongPool : weakPool;
    if (pool.length === 0) return;
    const text = pool[Math.floor(Math.random() * pool.length)];

    const metrics = ctx.measureText(text);
    const textWidth = Math.max(60, metrics.width + 30); // padding for lock + spacing

    const x = Math.random() * (canvas.width - textWidth - 10) + 10;
    const y = -20;
    const vy = FALL_SPEED_RANGE[0] + Math.random() * (FALL_SPEED_RANGE[1] - FALL_SPEED_RANGE[0]);

    state.items.push({ x, y, vy, text, strong: isStrong, width: textWidth, height: 20 });
  }

  function updateItems() {
    for (const item of state.items) {
      item.y += item.vy;
    }

    // collisions with basket
    const remaining = [];
    for (const item of state.items) {
      const intersects = (
        item.x < basket.x + basket.w &&
        item.x + item.width > basket.x &&
        item.y < basket.y + basket.h &&
        item.y + item.height > basket.y
      );
      if (intersects) {
        state.caughtLog.push({
          password: item.text,
          verdict: item.strong ? "✅ Strong" : "❌ Weak",
          tip: item.strong ? "Good mix of cases, numbers, symbols." : "Too common/easy to guess."
        });
        if (item.strong) {
          state.score += 1;
        } else {
          // caught a weak password -> immediate game over
          state.reason = "You caught a WEAK password.";
          endGame();
          return;
        }
      } else if (item.y > canvas.height) {
        // fell off screen
        if (item.strong) {
          state.misses += 1;
          state.caughtLog.push({
            password: item.text,
            verdict: "⚠️ Missed Strong",
            tip: "Try to catch strong passwords to score."
          });
          if (state.misses >= MAX_MISSES) {
            state.reason = "You missed too many STRONG passwords.";
            endGame();
            return;
          }
        }
        // weak item missed is fine
      } else {
        remaining.push(item);
      }
    }
    state.items = remaining;
  }

  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    // Ground line
    ctx.globalAlpha = 0.2;
    ctx.fillStyle = "#e6edf3";
    ctx.fillRect(0, canvas.height - 2, canvas.width, 2);
    ctx.globalAlpha = 1;

    drawBasket();
    for (const item of state.items) drawItem(item);

    // HUD mirrors
    scoreEl.textContent = state.score;
    missesEl.textContent = state.misses;
  }

  function loop(timestamp) {
    if (!state.running) return;
    if (!state.lastSpawn) state.lastSpawn = timestamp;

    if (timestamp - state.lastSpawn > SPAWN_INTERVAL) {
      spawnItem();
      state.lastSpawn = timestamp;
    }

    updateItems();
    draw();
    requestAnimationFrame(loop);
  }

  function tickTimer() {
    if (!state.running) return;
    state.timeLeft -= 1;
    timeEl.textContent = state.timeLeft;
    if (state.timeLeft <= 0) {
      state.reason = "Time up!";
      endGame();
      return;
    }
    setTimeout(tickTimer, 1000);
  }

  function startGame() {
    state = resetState();
    state.running = true;
    timeEl.textContent = state.timeLeft;
    startBtn.disabled = true;
    restartBtn.disabled = false;
    overlay.classList.add("hidden");
    requestAnimationFrame(loop);
    setTimeout(tickTimer, 1000);
  }

  function endGame() {
    state.running = false;
    startBtn.disabled = false;
    restartBtn.disabled = false;
    // Build review table
    reviewTableBody.innerHTML = "";
    state.caughtLog.forEach((row, idx) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${idx+1}</td><td><code>${row.password}</code></td><td>${row.verdict}</td><td>${row.tip}</td>`;
      reviewTableBody.appendChild(tr);
    });
    modalTitle.textContent = "Game Over";
    modalReason.textContent = state.reason || "Good run!";
    overlay.classList.remove("hidden");
  }

  // Input
  const keys = { left: false, right: false };
  window.addEventListener("keydown", (e) => {
    if (e.key === "ArrowLeft") keys.left = true;
    if (e.key === "ArrowRight") keys.right = true;
  });
  window.addEventListener("keyup", (e) => {
    if (e.key === "ArrowLeft") keys.left = false;
    if (e.key === "ArrowRight") keys.right = false;
  });

  // Mouse movement
  canvas.addEventListener("mousemove", (e) => {
    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    basket.x = Math.min(Math.max(mouseX - basket.w / 2, 0), canvas.width - basket.w);
  });

  function physics() {
    if (state.running) {
      if (keys.left) basket.x = Math.max(0, basket.x - basket.speed);
      if (keys.right) basket.x = Math.min(canvas.width - basket.w, basket.x + basket.speed);
    }
    requestAnimationFrame(physics);
  }
  physics();

  // Buttons
  startBtn.addEventListener("click", startGame);
  restartBtn.addEventListener("click", startGame);
  closeModal.addEventListener("click", () => overlay.classList.add("hidden"));
  playAgain.addEventListener("click", startGame);

  // Resize protection (keep canvas crisp if zoom changed)
  window.addEventListener("resize", () => {
    // no-op: fixed canvas; could add DPR scaling if desired
  });
})();
