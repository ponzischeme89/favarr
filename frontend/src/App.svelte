<script>
  import { api } from './api.js';
  import ServerManager from './components/ServerManager.svelte';
  import Library from './components/Library.svelte';
  import MediaGrid from './components/MediaGrid.svelte';
  import FavoritesManager from './components/FavoritesManager.svelte';
  import Settings from './components/Settings.svelte';
  import UnifiedSearch from './components/UnifiedSearch.svelte';
  import { getServerType, getServerGradient, usesNativeColor } from './serverIcons';

  const appVersion = 'v1.0.3';

  let servers = [];
  let selectedServer = null;
  let currentView = 'library';
  let loading = true;
  let error = null;
  let previousView = 'library';
  let globalSearchInput = '';
  let globalSearchTerm = '';
  let searchSuggestions = [];
  let suggestionCache = {};
  let suggestionsLoading = false;
  let warmCache = [];
  let suggestionDebounce;
  let showSuggestions = false;

  // Server management
  let showAddServer = false;
  let editingServer = null;

  // User selection for current server
  let users = [];
  let selectedUser = null;
  let userSearch = '';
  let showUserDropdown = false;

  $: filteredUsers = users.filter(u =>
    u.Name?.toLowerCase().includes(userSearch.toLowerCase())
  );

  async function loadServers() {
    loading = true;
    try {
      servers = await api.getServers();
      if (servers.length > 0 && !selectedServer) {
        selectServer(servers[0]);
      }
      error = null;
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  loadServers();

  async function selectServer(server) {
    selectedServer = server;
    selectedUser = null;
    users = [];
    userSearch = '';
    globalSearchInput = '';
    globalSearchTerm = '';
    if (currentView === 'search') {
      currentView = 'library';
    }

    try {
      users = await api.getUsers(server.id);
      if (users.length > 0) {
        selectedUser = users[0];
      }
    } catch (e) {
      console.error('Failed to load users:', e);
    }
  }

  function handleServerSaved() {
    showAddServer = false;
    editingServer = null;
    loadServers();
  }

  function handleServerCancel() {
    showAddServer = false;
    editingServer = null;
  }

  async function deleteServer(server) {
    if (!confirm(`Delete "${server.name}"? This cannot be undone.`)) return;

    try {
      await api.deleteServer(server.id);
      if (selectedServer?.id === server.id) {
        selectedServer = null;
        users = [];
        selectedUser = null;
        currentView = 'library';
        previousView = 'library';
        globalSearchInput = '';
        globalSearchTerm = '';
      }
      loadServers();
    } catch (e) {
      error = e.message;
    }
  }

  function selectUser(user) {
    selectedUser = user;
    userSearch = '';
    showUserDropdown = false;
  }

  function submitGlobalSearch() {
    if (!selectedServer && servers.length === 0) return;
    const term = globalSearchInput.trim();
    if (!term) {
      clearGlobalSearch();
      return;
    }
    if (currentView !== 'search') {
      previousView = currentView;
    }
    globalSearchTerm = term;
    currentView = 'search';
  }

  function clearGlobalSearch() {
    globalSearchInput = '';
    globalSearchTerm = '';
    if (currentView === 'search') {
      currentView = previousView || 'library';
    }
    searchSuggestions = [];
    showSuggestions = false;
  }

  function goToView(view) {
    currentView = view;
    previousView = view;
    if (globalSearchTerm) {
      globalSearchTerm = '';
    }
    searchSuggestions = [];
  }

  function getServerColor(type) {
    return getServerGradient(type);
  }

  function getServerIconUrl(type) {
    return getServerType(type).icon;
  }

  function normalize(text) {
    return (text || '').toString().toLowerCase();
  }

  function cacheSuggestions(term, suggestions) {
    suggestionCache[term] = suggestions;
    searchSuggestions = suggestions;
  }

  async function warmSearchCache() {
    if (!servers.length) return;
    suggestionsLoading = true;
    try {
      const all = [];
      for (const server of servers) {
        try {
          const res = await api.getItems(server.id, { limit: 200 });
          const items = res.Items || [];
          items.forEach(item => {
            all.push({
              item,
              serverId: server.id,
              serverLabel: server.server_type
            });
          });
        } catch (e) {
          continue;
        }
      }
      warmCache = all;
      suggestionCache = {};
    } finally {
      suggestionsLoading = false;
    }
  }

  async function fetchSuggestions(term) {
    const trimmed = term.trim();
    if (trimmed.length < 2) {
      searchSuggestions = [];
      return;
    }
    if (suggestionCache[trimmed]) {
      searchSuggestions = suggestionCache[trimmed];
      return;
    }
    suggestionsLoading = true;
    // If we have a warmed cache, use it locally
    if (warmCache.length > 0) {
      const filtered = warmCache.filter(entry =>
        normalize(entry.item?.Name).includes(normalize(trimmed))
      ).slice(0, 12);
      cacheSuggestions(trimmed, filtered);
      suggestionsLoading = false;
      return;
    }
    try {
      const tasks = servers.map(async server => {
        try {
          const res = await api.getItems(server.id, { search: trimmed, limit: 5 });
          const items = res.Items || [];
          return items.map(item => ({
            item,
            serverId: server.id,
            serverLabel: server.server_type
          }));
        } catch (e) {
          return [];
        }
      });
      const collected = (await Promise.all(tasks)).flat().slice(0, 12);
      cacheSuggestions(trimmed, collected);
    } finally {
      suggestionsLoading = false;
    }
  }

  function handleSearchInput(event) {
    globalSearchInput = event.target.value;
    if (suggestionDebounce) {
      clearTimeout(suggestionDebounce);
    }
    suggestionDebounce = setTimeout(() => fetchSuggestions(globalSearchInput), 250);
  }

  function pickSuggestion(suggestion) {
    globalSearchInput = suggestion.item?.Name || '';
    globalSearchTerm = globalSearchInput;
    currentView = 'search';
    searchSuggestions = [];
    showSuggestions = false;
  }

  function handleWarmSearchCache() {
    warmSearchCache();
  }
</script>

<div class="app-layout">
  <!-- Sidebar -->
  <aside class="sidebar">
    <div class="sidebar-scroll">
      <div class="sidebar-header">
        <h1 class="text-gradient font-bold text-lg">Favarr</h1> <br>
     
        <div class="section-header">
          <span class="text-xs font-medium text-[--text-secondary] uppercase tracking-wide">Servers</span>
          <button class="add-btn" on:click={() => showAddServer = true} title="Add Server">+</button>
        </div>

        {#if loading}
          <div class="p-4 text-center">
            <div class="animate-pulse text-[--text-tertiary] text-sm">Loading...</div>
          </div>
        {:else if servers.length === 0}
          <div class="p-4 text-center">
            <p class="text-sm text-[--text-tertiary] mb-3">No servers configured</p>
            <button class="btn btn-primary btn-sm" on:click={() => showAddServer = true}>
              Add Server
            </button>
          </div>
        {:else}
          <div class="server-list">
            {#each servers as server}
              <button
                class="server-item"
                class:active={selectedServer?.id === server.id}
                on:click={() => selectServer(server)}
              >
                <span class="server-icon" class:native-color={usesNativeColor(server.server_type)} style="background: {getServerColor(server.server_type)}">
                  <img src={getServerIconUrl(server.server_type)} alt={server.server_type} class="icon-img" />
                </span>
                <div class="server-details">
                  <span class="server-name">{server.server_type}</span>
                </div>
                <div class="server-actions">
                  <button class="action-btn" on:click|stopPropagation={() => editingServer = server} title="Edit">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                    </svg>
                  </button>
                  <button class="action-btn delete" on:click|stopPropagation={() => deleteServer(server)} title="Delete">
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                      <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                    </svg>
                  </button>
                </div>
              </button>
            {/each}
          </div>
        {/if}

        <nav class="nav-menu">
          <button
            class="nav-item"
            class:active={currentView === 'library'}
            on:click={() => goToView('library')}
            disabled={!selectedServer}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
              <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
            </svg>
            Library
          </button>
          <button
            class="nav-item"
            class:active={currentView === 'recent'}
            on:click={() => goToView('recent')}
            disabled={!selectedServer}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            Recent
          </button>
          <button
            class="nav-item"
            class:active={currentView === 'favorites'}
            on:click={() => goToView('favorites')}
            disabled={!selectedServer}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
            </svg>
            Favorites
          </button>
          <button
            class="nav-item"
            class:active={currentView === 'settings'}
            on:click={() => goToView('settings')}
            disabled={!selectedServer}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="3" />
              <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.6a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9c.29.31.46.72.51 1.14V10a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
            </svg>
            Settings
          </button>
        </nav>
      </div>
    </div>

    <div class="sidebar-footer">
     
      <div class="version">{appVersion}</div>
      <div class="copyright">&copy 2026 ponzischeme89</div> <a class="repo-link" href="https://github.com/ponzischeme89/favsapp" target="_blank" rel="noreferrer">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
          <path d="M12 0C5.37 0 0 5.37 0 12c0 5.3 3.44 9.8 8.21 11.39.6.11.82-.26.82-.58 0-.29-.01-1.05-.02-2.06-3.34.73-4.04-1.61-4.04-1.61-.55-1.39-1.34-1.76-1.34-1.76-1.09-.75.08-.74.08-.74 1.2.08 1.83 1.23 1.83 1.23 1.07 1.83 2.8 1.3 3.49.99.11-.78.42-1.3.76-1.6-2.67-.3-5.47-1.34-5.47-5.96 0-1.32.47-2.39 1.23-3.23-.12-.3-.53-1.52.12-3.17 0 0 1.01-.32 3.31 1.23a11.5 11.5 0 0 1 6.02 0c2.3-1.55 3.31-1.23 3.31-1.23.65 1.65.24 2.87.12 3.17.77.84 1.23 1.91 1.23 3.23 0 4.63-2.8 5.66-5.48 5.96.43.38.81 1.12.81 2.26 0 1.63-.02 2.94-.02 3.34 0 .32.22.7.83.58A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z"/>
        </svg>
        
      </a>
    </div>
  </aside>

  <!-- Main Content -->
  <main class="main-content">
    {#if showAddServer || editingServer}
      <div class="modal-overlay" on:click={handleServerCancel}>
        <div class="modal" on:click|stopPropagation>
          <ServerManager
            editServer={editingServer}
            on:saved={handleServerSaved}
            on:cancel={handleServerCancel}
          />
        </div>
      </div>
    {/if}

    {#if error}
      <div class="alert alert-error m-4">{error}</div>
    {/if}

    <header class="content-header">
      <div class="header-bar">
        <div class="header-brand">
          {#if selectedServer}
            <span class="server-icon" class:native-color={usesNativeColor(selectedServer.server_type)} style="background: {getServerColor(selectedServer.server_type)}">
              <img src={getServerIconUrl(selectedServer.server_type)} alt={selectedServer.server_type} class="icon-img" />
            </span>
          {:else}
            <span class="server-placeholder">Select a server</span>
          {/if}
        </div>

        <form class="global-search" on:submit|preventDefault={submitGlobalSearch}>
          <div class="search-input">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="11" cy="11" r="8"/>
              <line x1="21" y1="21" x2="16.65" y2="16.65"/>
            </svg>
            <input
              type="text"
              class="input"
              placeholder="Unified search across all integrations"
              bind:value={globalSearchInput}
              on:input={handleSearchInput}
              on:focus={() => showSuggestions = true}
              on:blur={() => setTimeout(() => showSuggestions = false, 120)}
              disabled={servers.length === 0}
            />
            {#if showSuggestions && (searchSuggestions.length > 0 || suggestionsLoading || globalSearchInput.trim().length >= 2)}
              <div class="suggestions">
                {#if suggestionsLoading}
                  {#each Array(4) as _}
                    <div class="suggestion-row loading">
                      <span class="pulse block w-32 h-3"></span>
                      <span class="pulse block w-16 h-3"></span>
                    </div>
                  {/each}
                {:else if searchSuggestions.length === 0}
                  <div class="suggestion-row empty">No suggestions</div>
                {:else}
                  {#each searchSuggestions as suggestion (suggestion.item?.Id + suggestion.serverId)}
                    <button class="suggestion-row" type="button" on:click={() => pickSuggestion(suggestion)}>
                      <div class="suggestion-main">
                        <div class="title">{suggestion.item?.Name || 'Untitled'}</div>
                        {#if suggestion.item?.Type}
                          <span class="badge badge-ghost">{suggestion.item.Type}</span>
                        {/if}
                      </div>
                      <span class="badge badge-soft">{suggestion.serverLabel}</span>
                    </button>
                  {/each}
                {/if}
              </div>
            {/if}
          </div>
          {#if globalSearchTerm}
            <button type="button" class="btn btn-ghost btn-sm" on:click={clearGlobalSearch}>
              Clear
            </button>
          {/if}
          <button type="submit" class="btn btn-primary btn-sm" disabled={!selectedServer}>
            Search
          </button>
        </form>

        {#if selectedServer && users.length > 0}
          <div class="user-selector header-user">
            <button class="user-btn" on:click={() => showUserDropdown = !showUserDropdown}>
              <span class="user-avatar">{selectedUser?.Name?.charAt(0) || '?'}</span>
              <span class="user-name">{selectedUser?.Name || 'Select user'}</span>
              <svg class="chevron" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="6 9 12 15 18 9"/>
              </svg>
            </button>
            {#if showUserDropdown}
              <div class="user-dropdown">
                <input
                  type="text"
                  class="user-search"
                  placeholder="Search users..."
                  bind:value={userSearch}
                />
                <div class="user-list">
                  {#each filteredUsers as user}
                    <button
                      class="user-option"
                      class:active={selectedUser?.Id === user.Id}
                      on:click={() => selectUser(user)}
                    >
                      <span class="user-avatar small">{user.Name?.charAt(0) || '?'}</span>
                      {user.Name}
                    </button>
                  {/each}
                </div>
              </div>
            {/if}
          </div>
        {/if}
      </div>
    </header>

    {#if !selectedServer}
      <div class="empty-state">
        <div class="empty-icon">
          <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <rect x="2" y="2" width="20" height="8" rx="2" ry="2"/>
            <rect x="2" y="14" width="20" height="8" rx="2" ry="2"/>
            <line x1="6" y1="6" x2="6.01" y2="6"/>
            <line x1="6" y1="18" x2="6.01" y2="18"/>
          </svg>
        </div>
        <h2 class="text-xl font-bold mb-2">No Server Selected</h2>
        <p class="text-[--text-secondary] mb-4">
          {servers.length === 0
            ? 'Add a media server to get started'
            : 'Select a server from the sidebar'}
        </p>
        {#if servers.length === 0}
          <button class="btn btn-primary" on:click={() => showAddServer = true}>
            Add Your First Server
          </button>
        {/if}
      </div>
    {:else}
      <div class="content-area">
        {#if currentView === 'search'}
          <UnifiedSearch
            servers={servers}
            primaryUser={selectedUser}
            query={globalSearchTerm}
          />
        {:else if currentView === 'library'}
          <Library serverId={selectedServer.id} serverType={selectedServer.server_type} user={selectedUser} />
        {:else if currentView === 'recent'}
          <MediaGrid serverId={selectedServer.id} serverType={selectedServer.server_type} type="recent" user={selectedUser} />
        {:else if currentView === 'favorites'}
          <FavoritesManager
            serverId={selectedServer.id}
            serverType={selectedServer.server_type}
            user={selectedUser}
          />
        {:else if currentView === 'settings'}
          <Settings serverId={selectedServer.id} user={selectedUser} on:warmsearch={handleWarmSearchCache} />
        {/if}
      </div>
    {/if}
  </main>
</div>

<style>
  .app-layout {
    display: flex;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
    background: var(--bg-primary);
  }

  .sidebar {
    width: 280px;
    min-width: 280px;
    height: 100vh;
    background: var(--bg-secondary);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .sidebar-scroll {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
  }

  .sidebar-header {
    padding: 20px;
    border-bottom: 1px solid var(--border);
  }

  .sidebar-section {
    padding: 16px;
    border-bottom: 1px solid var(--border);
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .add-btn {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 6px;
    font-size: 16px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .add-btn:hover {
    transform: scale(1.1);
  }

  .server-list {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .server-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
    width: 100%;
  }

  .server-item:hover {
    background: var(--bg-hover);
  }

  .server-item.active {
    background: rgba(139, 92, 246, 0.15);
    border-color: rgba(139, 92, 246, 0.3);
  }

  .server-icon {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    color: white;
    font-weight: 700;
    font-size: 14px;
    flex-shrink: 0;
  }

  .server-icon .icon-img {
    width: 16px;
    height: 16px;
    object-fit: contain;
    filter: brightness(0) invert(1);
  }

  .server-icon.native-color .icon-img {
    filter: none;
  }

  .server-details {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
  }

  .server-name {
    font-size: 13px;
    font-weight: 500;
    color: var(--text-primary);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .server-type {
    font-size: 11px;
    color: var(--text-tertiary);
    text-transform: capitalize;
  }

  .server-actions {
    display: flex;
    gap: 4px;
    opacity: 0;
    transition: opacity 0.2s;
  }

  .server-item:hover .server-actions {
    opacity: 1;
  }

  .action-btn {
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.2s;
  }

  .action-btn:hover {
    color: var(--accent);
    border-color: var(--accent);
  }

  .action-btn.delete:hover {
    color: #f87171;
    border-color: #f87171;
  }

  .user-selector {
    position: relative;
  }

  .user-btn {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    background: var(--bg-primary);
    border: 1px solid var(--border);
    border-radius: 10px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .user-btn:hover {
    border-color: rgba(139, 92, 246, 0.3);
  }

  .user-avatar {
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent);
    color: white;
    border-radius: 50%;
    font-size: 12px;
    font-weight: 600;
  }

  .user-avatar.small {
    width: 24px;
    height: 24px;
    font-size: 11px;
  }

  .user-name {
    flex: 1;
    text-align: left;
    font-size: 13px;
    color: var(--text-primary);
  }

  .chevron {
    color: var(--text-tertiary);
  }

  .user-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    margin-top: 4px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    z-index: 100;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
  }

  .user-search {
    width: 100%;
    padding: 10px 12px;
    background: var(--bg-primary);
    border: none;
    border-bottom: 1px solid var(--border);
    color: var(--text-primary);
    font-size: 13px;
  }

  .user-search::placeholder {
    color: var(--text-tertiary);
  }

  .user-list {
    max-height: 200px;
    overflow-y: auto;
  }

  .user-option {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 12px;
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 13px;
    color: var(--text-primary);
    transition: background 0.15s;
    text-align: left;
  }

  .user-option:hover {
    background: var(--bg-hover);
  }

  .user-option.active {
    background: rgba(139, 92, 246, 0.15);
  }

  .nav-menu {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .nav-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 12px;
    background: transparent;
    border: none;
    border-radius: 10px;
    color: var(--text-secondary);
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
    text-align: left;
  }

  .nav-item:hover:not(:disabled) {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .nav-item.active {
    background: rgba(139, 92, 246, 0.15);
    color: var(--accent);
  }

  .nav-item:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  @media (max-width: 768px) {
    .sidebar {
      width: 240px;
      min-width: 240px;
    }
  }

  .sidebar-footer {
    padding: 14px 16px 18px;
    border-top: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    gap: 6px;
    background: var(--bg-secondary);
  }

  .repo-link {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: var(--text-primary);
    text-decoration: none;
    font-size: 13px;
  }

  .repo-link:hover {
    color: var(--accent);
  }

  .version {
    font-size: 11px;
    color: var(--text-tertiary);
  }

  .copyright {
    font-size: 11px;
    color: var(--text-tertiary);
  }

  .main-content {
    flex: 1;
    height: 100vh;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
  }

  .content-header {
    padding: 20px 24px;
    border-bottom: 1px solid var(--border);
    background: var(--bg-secondary);
  }

  .header-bar {
    display: grid;
    grid-template-columns: auto 1fr auto;
    align-items: center;
    gap: 12px;
    width: 100%;
  }

  .header-brand .server-icon {
    width: 38px;
    height: 38px;
  }

  .header-brand .server-icon .icon-img {
    width: 20px;
    height: 20px;
  }

  .server-placeholder {
    font-size: 12px;
    color: var(--text-tertiary);
  }

  .global-search {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
  }

  .search-input {
    position: relative;
    flex: 1;
  }

  .search-input svg {
    position: absolute;
    left: 12px;
    top: 50%;
    transform: translateY(-50%);
    color: var(--text-tertiary);
  }

  .search-input .input {
    padding-left: 36px;
  }

  .suggestions {
    position: absolute;
    top: calc(100% + 6px);
    left: 0;
    right: 0;
    background: var(--bg-secondary);
    border: 1px solid var(--border);
    border-radius: 12px;
    box-shadow: 0 14px 40px rgba(0, 0, 0, 0.35);
    z-index: 20;
    max-height: 300px;
    overflow-y: auto;
  }

  .suggestion-row {
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    padding: 10px 12px;
    background: transparent;
    border: none;
    color: var(--text-primary);
    cursor: pointer;
    text-align: left;
    transition: background 0.15s;
  }

  .suggestion-row:hover {
    background: var(--bg-hover);
  }

  .suggestion-row.empty {
    cursor: default;
    color: var(--text-tertiary);
  }

  .suggestion-row.loading {
    display: flex;
    gap: 12px;
    align-items: center;
  }

  .pulse {
    background: var(--bg-hover);
    border-radius: 6px;
    animation: pulse 1.2s ease-in-out infinite;
  }

  .suggestion-main {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .badge-soft {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid var(--border);
    color: var(--text-secondary);
    padding: 4px 8px;
    border-radius: 999px;
    font-size: 11px;
    text-transform: capitalize;
  }

  @keyframes pulse {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
  }

  .content-area {
    flex: 1;
    padding: 24px;
    overflow-y: auto;
  }

  .empty-state {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    padding: 40px;
  }

  .empty-icon {
    width: 100px;
    height: 100px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    margin-bottom: 20px;
    color: var(--text-tertiary);
  }

  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    backdrop-filter: blur(4px);
  }

  .modal {
    width: 100%;
    max-width: 500px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    overflow: hidden;
  }

  @media (max-width: 768px) {
    .global-search {
      max-width: none;
    }
  }
</style>
