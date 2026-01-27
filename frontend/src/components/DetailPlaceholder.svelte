<script>
  import { onMount, onDestroy } from 'svelte';

  const messages = [
    'Select an item to view details.',
    'I can wait. I am very patient. Forever even.',
    'Pick something—your watch history isn\'t going to judge itself.',
    'Still empty. Is this some sort of minimalist art piece?',
    'Any time now. I brought popcorn.',
    'Click a poster. Any poster. I promise it won\'t bite.',
    'Hovering isn\'t choosing. Commit already.',
    'Analysis paralysis? Let\'s start with the shiny one.',
    'Your mouse looks bored. Give it a purpose.',
    'One of these is bound to have explosions. Go find it.',
    'I\'ve seen statues move faster. Tap something.',
    'Pretend this is Netflix and keep scrolling forever. Or just click.',
    'Somewhere in here is your next favorite. It won\'t pick itself.',
    'This is the part where you click. Seriously.'
  ];

  let currentMessage = '';
  let messageIndex = 0;
  let charIndex = 0;
  let typingInterval = null;
  let holdTimeout = null;

  function resetTimers() {
    if (typingInterval) clearInterval(typingInterval);
    if (holdTimeout) clearTimeout(holdTimeout);
  }

  function startTyping() {
    resetTimers();
    currentMessage = '';
    charIndex = 0;

    typingInterval = setInterval(() => {
      const full = messages[messageIndex];
      if (charIndex < full.length) {
        currentMessage += full.charAt(charIndex);
        charIndex += 1;
      } else {
        clearInterval(typingInterval);
        holdTimeout = setTimeout(() => {
          messageIndex = (messageIndex + 1) % messages.length;
          startTyping();
        }, 1400);
      }
    }, 32);
  }

  onMount(startTyping);
  onDestroy(resetTimers);
</script>

<div class="detail-empty">
  <div class="empty-icon">
    <svg class="idle-star" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
    </svg>
    <span class="star-glow" aria-hidden="true"></span>
    <div class="mini-stars" aria-hidden="true">
      <svg class="mini-star s1" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      </svg>
      <svg class="mini-star s2" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      </svg>
      <svg class="mini-star s3" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
        <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
      </svg>
    </div>
  </div>
  <p class="typewriter">{currentMessage}</p>
  <span class="hint">Or use bulk select to remove multiple items</span>
</div>

<style>
  .detail-empty {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: flex-start;
    padding: 16px 32px 32px;
    text-align: center;
    color: var(--text-tertiary);
    gap: 6px;
  }

  .detail-empty .empty-icon {
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 16px;
    margin-bottom: 8px;
    position: relative;
    overflow: hidden;
  }

  .idle-star {
    animation: starFloat 2.2s ease-in-out infinite;
  }

  .star-glow {
    position: absolute;
    width: 120%;
    height: 120%;
    background: radial-gradient(circle at 50% 40%, rgba(139, 92, 246, 0.25), transparent 55%);
    filter: blur(6px);
    animation: starPulse 3s ease-in-out infinite;
    pointer-events: none;
  }

  .mini-stars {
    position: absolute;
    inset: 0;
    pointer-events: none;
  }

  .mini-star {
    position: absolute;
    color: var(--accent);
    opacity: 0.2;
    animation: starTwinkle 2s ease-in-out infinite;
  }

  .mini-star.s1 { top: 6px; left: 8px; animation-delay: 0.2s; }
  .mini-star.s2 { bottom: 8px; right: 6px; animation-delay: 0.8s; }
  .mini-star.s3 { top: 4px; right: 12px; animation-delay: 1.4s; }

  .typewriter {
    font-size: 14px;
    color: var(--text-secondary);
    min-height: 22px;
    letter-spacing: 0.01em;
    font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
  }

  .hint {
    font-size: 12px;
  }

  @keyframes starFloat {
    0% { transform: translateY(0); }
    50% { transform: translateY(-4px); }
    100% { transform: translateY(0); }
  }

  @keyframes starPulse {
    0% { opacity: 0.25; transform: scale(0.96); }
    50% { opacity: 0.45; transform: scale(1.05); }
    100% { opacity: 0.25; transform: scale(0.96); }
  }

  @keyframes starTwinkle {
    0% { opacity: 0.15; transform: scale(0.9); }
    50% { opacity: 0.55; transform: scale(1.05); }
    100% { opacity: 0.15; transform: scale(0.9); }
  }
</style>
