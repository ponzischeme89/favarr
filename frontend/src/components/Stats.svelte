<script>
  import { onMount, onDestroy } from 'svelte';
  import { api } from '../api';

  // Display state – populated from quick endpoint or live refresh
  let stats = null;
  let statsLoading = false;
  let statsError = '';
  let lastUpdated = null;

  // Collection state
  let collecting = false;
  let collectionProgress = 0;
  let collectionMessage = '';
  let collectionPollTimer = null;

  // Snapshots
  let snapshots = [];
  let snapshotsLoading = false;

  onMount(async () => {
    await loadQuickStats();
    loadSnapshots();
  });

  onDestroy(() => {
    if (collectionPollTimer) clearTimeout(collectionPollTimer);
  });

  async function loadQuickStats() {
    statsLoading = true;
    statsError = '';
    try {
      const data = await api.getQuickStats();
      // Build a stats shape from the quick response
      const snap = data.snapshot;
      stats = {
        servers: data.servers,
        users: {
          total: snap ? snap.users_total : 0,
          by_server: snap ? (snap.users_by_server || []) : []
        },
        favorites: {
          total: snap ? snap.favorites_total : 0,
          by_server: snap ? (snap.favorites_by_server || []) : [],
          by_type: snap ? (snap.favorites_by_type || {}) : {}
        }
      };
      if (snap) {
        lastUpdated = new Date(snap.created_at);
      }
    } catch (err) {
      statsError = err.message || 'Failed to load statistics';
    } finally {
      statsLoading = false;
    }
  }

  async function refreshLiveStats() {
    statsLoading = true;
    statsError = '';
    try {
      stats = await api.getStats();
      lastUpdated = new Date();
    } catch (err) {
      statsError = err.message || 'Failed to load live statistics';
    } finally {
      statsLoading = false;
    }
  }

  async function loadSnapshots() {
    snapshotsLoading = true;
    try {
      snapshots = await api.getSnapshots(10);
    } catch (err) {
      console.error('Failed to load snapshots:', err);
    } finally {
      snapshotsLoading = false;
    }
  }

  async function startCollection() {
    collecting = true;
    collectionProgress = 0;
    collectionMessage = 'Starting collection...';
    try {
      await api.collectStats();
      pollCollectionStatus();
    } catch (err) {
      statsError = err.message || 'Failed to start collection';
      collecting = false;
    }
  }

  async function pollCollectionStatus() {
    if (collectionPollTimer) clearTimeout(collectionPollTimer);
    try {
      const status = await api.getCollectionStatus();
      collectionProgress = status.progress || 0;
      collectionMessage = status.message || '';
      if (status.status === 'running') {
        collectionPollTimer = setTimeout(pollCollectionStatus, 1000);
      } else {
        collecting = false;
        if (status.status === 'completed') {
          loadQuickStats();
          loadSnapshots();
        }
      }
    } catch (err) {
      console.error('Failed to poll status:', err);
      collectionPollTimer = setTimeout(pollCollectionStatus, 2000);
    }
  }

  function formatDate(dateStr) {
    const date = dateStr instanceof Date ? dateStr : new Date(dateStr);
    return date.toLocaleString();
  }

  function timeAgo(date) {
    if (!date) return '';
    const seconds = Math.floor((new Date() - date) / 1000);
    if (seconds < 60) return 'just now';
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  }
</script>

<div class="stats-page">
  <div class="stats-header">
    <div>
      <h2 class="stats-title">Statistics</h2>
      <p class="stats-subtitle">
        Overview of your media servers and favorites
        {#if lastUpdated}
          <span class="last-updated" title={formatDate(lastUpdated)}>
            &middot; Updated {timeAgo(lastUpdated)}
          </span>
        {/if}
      </p>
    </div>
    <div class="stats-actions">
      <button class="btn btn-primary btn-sm" on:click={startCollection} disabled={collecting || statsLoading}>
        {#if collecting}
          <span class="spinner small"></span>
          Collecting...
        {:else}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 12a9 9 0 11-6.219-8.56"/>
          </svg>
          Collect Now
        {/if}
      </button>
      <button class="btn btn-secondary btn-sm" on:click={refreshLiveStats} disabled={statsLoading || collecting}>
        {#if statsLoading}
          <span class="spinner small"></span>
        {:else}
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="23 4 23 10 17 10"/>
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/>
          </svg>
        {/if}
        Refresh
      </button>
    </div>
  </div>

  {#if collecting}
    <div class="collection-progress">
      <div class="progress-header">
        <span class="progress-label">Collecting statistics...</span>
        <span class="progress-percent">{collectionProgress}%</span>
      </div>
      <div class="progress-bar-container">
        <div class="progress-bar" style="width: {collectionProgress}%"></div>
      </div>
      <p class="progress-message">{collectionMessage}</p>
    </div>
  {/if}

  {#if statsError}
    <div class="alert alert-error">{statsError}</div>
  {/if}

  {#if statsLoading && !stats}
    <div class="stats-skeleton">
      {#each Array(3) as _}
        <div class="skeleton-stat">
          <div class="skeleton circle"></div>
          <div class="skeleton lines">
            <div class="skeleton line w-40"></div>
            <div class="skeleton line w-60"></div>
          </div>
        </div>
      {/each}
    </div>
  {:else if stats}
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon servers">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
            <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
            <line x1="6" y1="6" x2="6.01" y2="6"/>
            <line x1="6" y1="18" x2="6.01" y2="18"/>
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-value">{stats.servers?.total || 0}</span>
          <span class="stat-label">Connected Servers</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon users">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
            <circle cx="9" cy="7" r="4"/>
            <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
            <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-value">{stats.users?.total || 0}</span>
          <span class="stat-label">Total Users</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon favorites">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
        </div>
        <div class="stat-info">
          <span class="stat-value">{stats.favorites?.total || 0}</span>
          <span class="stat-label">Total Favorites</span>
        </div>
      </div>
    </div>

    {#if stats.servers?.by_type && Object.keys(stats.servers.by_type).length > 0}
      <div class="stats-section">
        <h4>Servers by Type</h4>
        <div class="breakdown-list">
          {#each Object.entries(stats.servers.by_type) as [type, count]}
            <div class="breakdown-item">
              <span class="breakdown-label">{type}</span>
              <span class="breakdown-value">{count}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    {#if stats.favorites?.by_server && stats.favorites.by_server.length > 0}
      <div class="stats-section">
        <h4>Favorites by Server</h4>
        <div class="breakdown-list">
          {#each stats.favorites.by_server as server}
            <div class="breakdown-item">
              <span class="breakdown-label">{server.name}</span>
              <div class="breakdown-bar-container">
                <div
                  class="breakdown-bar"
                  style="width: {stats.favorites.total > 0 ? (server.count / stats.favorites.total * 100) : 0}%"
                ></div>
              </div>
              <span class="breakdown-value">{server.count}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}

    {#if stats.favorites?.by_type && Object.keys(stats.favorites.by_type).length > 0}
      <div class="stats-section">
        <h4>Favorites by Type</h4>
        <div class="type-chips">
          {#each Object.entries(stats.favorites.by_type) as [type, count]}
            <div class="type-chip">
              <span class="type-name">{type}</span>
              <span class="type-count">{count}</span>
            </div>
          {/each}
        </div>
      </div>
    {/if}
  {/if}

  <!-- Snapshots History -->
  <div class="stats-section">
    <h4>Collection History</h4>
    {#if snapshotsLoading}
      <div class="snapshots-loading">
        <span class="spinner small"></span>
        Loading history...
      </div>
    {:else if snapshots.length === 0}
      <p class="snapshots-empty">No collection history yet. Click "Collect Now" to create your first snapshot.</p>
    {:else}
      <div class="snapshots-list">
        {#each snapshots as snapshot}
          <div class="snapshot-item">
            <div class="snapshot-date">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
              {formatDate(snapshot.created_at)}
            </div>
            <div class="snapshot-stats">
              <span class="snapshot-stat">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
                  <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
                </svg>
                {snapshot.servers_total} servers
              </span>
              <span class="snapshot-stat">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                  <circle cx="9" cy="7" r="4"/>
                </svg>
                {snapshot.users_total} users
              </span>
              <span class="snapshot-stat">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                </svg>
                {snapshot.favorites_total} favorites
              </span>
            </div>
            {#if snapshot.collection_status === 'failed'}
              <span class="snapshot-status failed">Failed</span>
            {/if}
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .stats-page {
  }

  .stats-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 24px;
    flex-wrap: wrap;
    gap: 16px;
  }

  .stats-title {
    font-size: 22px;
    font-weight: 700;
    color: var(--text-primary);
    margin: 0 0 4px;
  }

  .stats-subtitle {
    font-size: 13px;
    color: var(--text-tertiary);
    margin: 0;
  }

  .last-updated {
    color: var(--text-tertiary);
  }

  .stats-actions {
    display: flex;
    gap: 8px;
  }

  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }

  .stat-card {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    transition: all 0.2s;
  }

  .stat-card:hover {
    border-color: rgba(139, 92, 246, 0.25);
  }

  .stat-icon {
    width: 48px;
    height: 48px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 12px;
    flex-shrink: 0;
  }

  .stat-icon.servers {
    background: rgba(59, 130, 246, 0.15);
    color: #3b82f6;
  }

  .stat-icon.users {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
  }

  .stat-icon.favorites {
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
  }

  .stat-info {
    display: flex;
    flex-direction: column;
  }

  .stat-value {
    font-size: 28px;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1;
  }

  .stat-label {
    font-size: 13px;
    color: var(--text-tertiary);
    margin-top: 4px;
  }

  .stats-section {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
  }

  .stats-section h4 {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 16px;
  }

  .breakdown-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .breakdown-item {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .breakdown-label {
    font-size: 13px;
    color: var(--text-secondary);
    min-width: 100px;
    text-transform: capitalize;
  }

  .breakdown-bar-container {
    flex: 1;
    height: 8px;
    background: var(--bg-secondary);
    border-radius: 4px;
    overflow: hidden;
  }

  .breakdown-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), #c084fc);
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  .breakdown-value {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-primary);
    min-width: 40px;
    text-align: right;
  }

  .type-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .type-chip {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 12px;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 20px;
  }

  .type-name {
    font-size: 13px;
    color: var(--text-secondary);
  }

  .type-count {
    font-size: 12px;
    font-weight: 600;
    color: var(--accent);
    background: rgba(139, 92, 246, 0.15);
    padding: 2px 8px;
    border-radius: 10px;
  }

  .stats-skeleton {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
  }

  .skeleton-stat {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 20px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
  }

  .skeleton.circle {
    width: 48px;
    height: 48px;
    border-radius: 12px;
  }

  .collection-progress {
    background: var(--bg-card);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 20px;
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }

  .progress-label {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
  }

  .progress-percent {
    font-size: 13px;
    font-weight: 600;
    color: var(--accent);
  }

  .progress-bar-container {
    height: 8px;
    background: var(--bg-secondary);
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 8px;
  }

  .progress-bar {
    height: 100%;
    background: linear-gradient(90deg, var(--accent), #c084fc);
    border-radius: 4px;
    transition: width 0.3s ease;
  }

  .progress-message {
    font-size: 12px;
    color: var(--text-tertiary);
    margin: 0;
  }

  .snapshots-loading {
    display: flex;
    align-items: center;
    gap: 10px;
    color: var(--text-tertiary);
    font-size: 13px;
    padding: 12px 0;
  }

  .snapshots-empty {
    font-size: 13px;
    color: var(--text-tertiary);
    margin: 0;
  }

  .snapshots-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .snapshot-item {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 12px 16px;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 10px;
    flex-wrap: wrap;
  }

  .snapshot-date {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: var(--text-secondary);
    min-width: 180px;
  }

  .snapshot-date svg {
    color: var(--text-tertiary);
  }

  .snapshot-stats {
    display: flex;
    gap: 16px;
    flex: 1;
  }

  .snapshot-stat {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--text-tertiary);
  }

  .snapshot-stat svg {
    color: var(--text-tertiary);
  }

  .snapshot-status {
    padding: 4px 10px;
    border-radius: 20px;
    font-size: 11px;
    font-weight: 500;
  }

  .snapshot-status.failed {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
  }

  .alert {
    padding: 12px 16px;
    border-radius: 10px;
    font-size: 13px;
    margin-bottom: 16px;
  }

  .alert-error {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    color: #ef4444;
  }
</style>
