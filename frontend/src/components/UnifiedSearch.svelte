<script>
  import { onMount } from 'svelte';
  import { api } from '../api.js';
  import MediaCard from './MediaCard.svelte';
  import { getServerType } from '../serverIcons.js';

  export let servers = [];
  export let primaryUser = null;
  export let query = '';

  let loading = false;
  let error = null;
  let results = [];
  let usersCache = {};
  let searchStartTime = 0;
  let searchDuration = 0;

  const normalize = (s) => (s || '').toString().toLowerCase().trim();

  function levenshtein(a, b) {
    a = normalize(a);
    b = normalize(b);
    if (a === b) return 0;
    const matrix = Array.from({ length: a.length + 1 }, () => new Array(b.length + 1).fill(0));
    for (let i = 0; i <= a.length; i++) matrix[i][0] = i;
    for (let j = 0; j <= b.length; j++) matrix[0][j] = j;
    for (let i = 1; i <= a.length; i++) {
      for (let j = 1; j <= b.length; j++) {
        const cost = a[i - 1] === b[j - 1] ? 0 : 1;
        matrix[i][j] = Math.min(
          matrix[i - 1][j] + 1,
          matrix[i][j - 1] + 1,
          matrix[i - 1][j - 1] + cost
        );
      }
    }
    return matrix[a.length][b.length];
  }

  function bestUserMatch(targetName, users) {
    if (!targetName || !users?.length) return null;
    const normalizedTarget = normalize(targetName);
    let best = null;
    let bestScore = Infinity;
    for (const user of users) {
      const candidate = normalize(user.Name);
      let score = levenshtein(normalizedTarget, candidate);
      if (candidate.startsWith(normalizedTarget) || normalizedTarget.startsWith(candidate)) {
        score = 0;
      } else if (candidate.includes(normalizedTarget) || normalizedTarget.includes(candidate)) {
        score = Math.min(score, 1);
      }
      if (score < bestScore) {
        bestScore = score;
        best = user;
      }
    }
    const threshold = Math.max(3, Math.round(normalizedTarget.length * 0.25));
    return bestScore <= threshold ? best : null;
  }

  async function loadUsers(server) {
    if (usersCache[server.id]) return usersCache[server.id];
    try {
      const users = await api.getUsers(server.id);
      usersCache[server.id] = users;
      return users;
    } catch {
      usersCache[server.id] = [];
      return [];
    }
  }

  // Group results by server type
  function groupResultsByServer(results) {
    const grouped = {};
    for (const result of results) {
      const key = result.serverLabel;
      if (!grouped[key]) {
        grouped[key] = {
          serverType: result.serverLabel,
          serverInfo: getServerType(result.serverLabel),
          items: []
        };
      }
      grouped[key].items.push(result);
    }
    return Object.values(grouped);
  }

  async function searchAll() {
    const term = (query || '').trim();
    if (!term) {
      results = [];
      return;
    }
    loading = true;
    error = null;
    results = [];
    searchStartTime = Date.now();

    const tasks = servers.map(async (server) => {
      try {
        const users = await loadUsers(server);
        const matchedUser = primaryUser ? bestUserMatch(primaryUser.Name, users) : null;
        const res = await api.getItems(server.id, { search: term, limit: 20 });
        const items = res.Items || [];
        return items.map((item) => ({
          serverId: server.id,
          serverLabel: server.server_type,
          user: matchedUser,
          item
        }));
      } catch (e) {
        return [];
      }
    });

    try {
      const grouped = await Promise.all(tasks);
      results = grouped.flat();
      searchDuration = Date.now() - searchStartTime;
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  $: searchAll();

  $: groupedResults = groupResultsByServer(results);
</script>

<div class="search-container">
  <!-- Search Header -->
  <div class="search-header">
    <div class="search-info">
      {#if loading}
        <div class="search-status searching">
          <span class="spinner"></span>
          <span>Searching across {servers.length} integration{servers.length !== 1 ? 's' : ''}...</span>
        </div>
      {:else if query?.trim() && results.length > 0}
        <div class="search-status">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <span class="result-count">{results.length} result{results.length !== 1 ? 's' : ''}</span>
          <span class="search-term">for "<strong>{query}</strong>"</span>
          <span class="search-time">({(searchDuration / 1000).toFixed(2)}s)</span>
        </div>
      {:else if query?.trim()}
        <div class="search-status empty">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="11" cy="11" r="8"/>
            <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          </svg>
          <span>No results for "<strong>{query}</strong>"</span>
        </div>
      {/if}
    </div>
  </div>

  <!-- Content Area -->
  {#if loading}
    <div class="unified-grid">
      {#each Array(12) as _, idx}
        <div class="skeleton-card" aria-hidden="true">
          <div class="skeleton thumb"></div>
          <div class="skeleton-info">
            <div class="skeleton line w-80"></div>
            <div class="skeleton line w-60"></div>
          </div>
        </div>
      {/each}
    </div>
  {:else if error}
    <div class="error-state">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <line x1="12" y1="8" x2="12" y2="12"/>
        <line x1="12" y1="16" x2="12.01" y2="16"/>
      </svg>
      <h3>Search failed</h3>
      <p>{error}</p>
      <button class="btn btn-secondary" on:click={searchAll}>Try again</button>
    </div>
  {:else if !query?.trim()}
    <div class="empty-state">
      <div class="empty-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
        </svg>
      </div>
      <h3>Unified Search</h3>
      <p>Search across all your connected integrations at once. Enter a search term above to get started.</p>
      <div class="server-badges">
        {#each servers as server}
          <span class="server-badge">
            <img src={getServerType(server.server_type).icon} alt={server.server_type} />
            {server.server_type}
          </span>
        {/each}
      </div>
    </div>
  {:else if results.length === 0}
    <div class="empty-state">
      <div class="empty-icon muted">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
          <circle cx="11" cy="11" r="8"/>
          <line x1="21" y1="21" x2="16.65" y2="16.65"/>
          <line x1="8" y1="8" x2="14" y2="14"/>
          <line x1="14" y1="8" x2="8" y2="14"/>
        </svg>
      </div>
      <h3>No results found</h3>
      <p>Try a different search term or check your server connections.</p>
    </div>
  {:else}
    <!-- Results grouped by server -->
    {#each groupedResults as group}
      <div class="result-group">
        <div class="group-header">
          <div class="group-title">
            <img src={group.serverInfo.icon} alt={group.serverType} class="group-icon" />
            <span>{group.serverInfo.name}</span>
          </div>
          <span class="group-count">{group.items.length} item{group.items.length !== 1 ? 's' : ''}</span>
        </div>
        <div class="unified-grid">
          {#each group.items as result (result.serverId + ':' + result.item.Id)}
            <MediaCard
              serverId={result.serverId}
              item={result.item}
              user={result.user}
              serverLabel={result.serverLabel}
            />
          {/each}
        </div>
      </div>
    {/each}
  {/if}
</div>

<style>
  .search-container {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .search-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 16px;
  }

  .search-info {
    flex: 1;
  }

  .search-status {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    color: var(--text-secondary);
  }

  .search-status.searching {
    color: var(--accent);
  }

  .search-status.empty {
    color: var(--text-tertiary);
  }

  .search-status svg {
    flex-shrink: 0;
  }

  .result-count {
    font-weight: 600;
    color: var(--text-primary);
  }

  .search-term strong {
    color: var(--accent);
  }

  .search-time {
    color: var(--text-tertiary);
    font-size: 12px;
  }

  .spinner {
    width: 18px;
    height: 18px;
    border: 2px solid rgba(139, 92, 246, 0.2);
    border-top-color: var(--accent);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }

  @keyframes spin {
    to { transform: rotate(360deg); }
  }

  /* Result Groups */
  .result-group {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 20px;
  }

  .group-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }

  .group-title {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .group-icon {
    width: 24px;
    height: 24px;
    object-fit: contain;
  }

  .group-count {
    font-size: 13px;
    color: var(--text-tertiary);
    background: var(--bg-primary);
    padding: 4px 10px;
    border-radius: 20px;
  }

  /* Grid Layout */
  .unified-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
    gap: 16px;
  }

  /* Skeleton Loading */
  .skeleton-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
  }

  .skeleton {
    background: linear-gradient(90deg, rgba(255,255,255,0.04) 25%, rgba(255,255,255,0.1) 37%, rgba(255,255,255,0.04) 63%);
    background-size: 400% 100%;
    animation: shimmer 1.4s ease infinite;
  }

  .skeleton.thumb {
    width: 100%;
    aspect-ratio: 2/3;
  }

  .skeleton-info {
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .skeleton.line {
    height: 12px;
    border-radius: 6px;
  }

  .skeleton.line.w-80 { width: 80%; }
  .skeleton.line.w-60 { width: 60%; }

  @keyframes shimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
  }

  /* Empty & Error States */
  .empty-state,
  .error-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    text-align: center;
    padding: 60px 20px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
  }

  .empty-icon {
    width: 80px;
    height: 80px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(139, 92, 246, 0.1);
    border: 1px solid rgba(139, 92, 246, 0.2);
    border-radius: 20px;
    color: var(--accent);
    margin-bottom: 20px;
  }

  .empty-icon.muted {
    background: var(--bg-primary);
    border-color: var(--border);
    color: var(--text-tertiary);
  }

  .error-state svg {
    color: #ef4444;
    margin-bottom: 16px;
  }

  .empty-state h3,
  .error-state h3 {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 8px;
  }

  .empty-state p,
  .error-state p {
    font-size: 14px;
    color: var(--text-tertiary);
    max-width: 400px;
    margin-bottom: 20px;
  }

  .server-badges {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    justify-content: center;
  }

  .server-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 12px;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 20px;
    font-size: 12px;
    color: var(--text-secondary);
    text-transform: capitalize;
  }

  .server-badge img {
    width: 14px;
    height: 14px;
    object-fit: contain;
  }
</style>
