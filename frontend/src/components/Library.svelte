<script>
  import { api } from '../api.js';
  import MediaGrid from './MediaGrid.svelte';

  export let serverId = null;
  export let user = null;
  export let serverType = null;

  let libraries = [];
  let selectedLibrary = null;
  let loading = true;
  let error = null;
  let librarySearch = '';

  $: if (serverId) {
    loadLibraries();
    selectedLibrary = null;
  }

  $: if (!loading && serverType === 'audiobookshelf' && libraries.length && !selectedLibrary) {
    selectedLibrary = libraries[0];
  }

  async function loadLibraries() {
    if (!serverId) return;

    loading = true;
    try {
      libraries = await api.getLibraries(serverId);
      error = null;
    } catch (e) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function selectLibrary(library) {
    selectedLibrary = library;
  }

  function goBack() {
    selectedLibrary = null;
  }

  function getLibraryIcon(type) {
    switch(type?.toLowerCase()) {
      case 'movies':
      case 'movie':
        return 'M';
      case 'tvshows':
      case 'show':
        return 'TV';
      case 'music':
        return 'MU';
      case 'photos':
        return 'PH';
      case 'audiobooks':
      case 'podcast':
        return 'AB';
      default:
        return 'LB';
    }
  }

  function colorFor(name = '') {
    const palette = [
      '#8b5cf6', '#06b6d4', '#f59e0b', '#10b981',
      '#ef4444', '#3b82f6', '#ec4899', '#14b8a6'
    ];
    let sum = 0;
    for (let i = 0; i < name.length; i++) sum += name.charCodeAt(i);
    return palette[sum % palette.length];
  }

  $: filteredLibraries = libraries.filter(lib =>
    (lib.Name || '').toLowerCase().includes(librarySearch.toLowerCase())
  );
</script>

{#if loading}
  <div class="card text-center py-12">
    <div class="inline-block animate-pulse">
      <div class="w-8 h-8 rounded-full bg-[--accent] mx-auto mb-3"></div>
      <p class="text-[--text-secondary]">Loading libraries...</p>
    </div>
  </div>
{:else if error}
  <div class="alert alert-error">{error}</div>
{:else if selectedLibrary}
  <div class="card">
    <button class="btn btn-ghost text-[--accent] !p-0 mb-4" on:click={goBack}>
      ← Back to Libraries
    </button>
    <h2 class="card-title !mb-0">{selectedLibrary.Name}</h2>
  </div>
  <MediaGrid {serverId} serverType={serverType} type="library" libraryId={selectedLibrary.ItemId} {user} />
{:else}
  <div class="card">
    <div class="card-top">
      <div>
        <h2 class="card-title !mb-1">Libraries</h2>
        <p class="muted">Pick a library to browse or search, then add items to favourites.</p>
      </div>
      <div class="search-box">
        <input
          class="input"
          type="text"
          placeholder="Search libraries..."
          bind:value={librarySearch}
        />
      </div>
    </div>

    {#if filteredLibraries.length === 0}
      <div class="text-center py-8 text-[--text-secondary]">No libraries found.</div>
    {:else}
      <div class="library-grid">
        {#each filteredLibraries as library}
          <button class="library-card" on:click={() => selectLibrary(library)}>
            <div class="library-avatar" style={`background:${colorFor(library.Name)}`}>
              {getLibraryIcon(library.CollectionType)}
            </div>
            <div class="library-info">
              <div class="library-name">{library.Name}</div>
              <div class="library-type">{library.CollectionType || 'Library'}</div>
            </div>
            <div class="chevron">›</div>
          </button>
        {/each}
      </div>
    {/if}
  </div>
{/if}

<style>
  .card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
  }

  .muted {
    color: var(--text-secondary);
    font-size: 13px;
  }

  .search-box {
    width: 240px;
  }

  .library-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
    gap: 10px;
  }

  .library-card {
    display: grid;
    grid-template-columns: auto 1fr auto;
    gap: 12px;
    padding: 14px 12px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    cursor: pointer;
    transition: all 0.3s;
    align-items: center;
  }

  .library-card:hover {
    transform: translateY(-2px);
    background: var(--bg-hover);
    border-color: rgba(139, 92, 246, 0.3);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }

  .library-avatar {
    width: 40px;
    height: 40px;
    border-radius: 10px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 700;
    font-size: 13px;
  }

  .library-info {
    text-align: left;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .library-name {
    font-size: 15px;
    font-weight: 600;
    color: var(--text-primary);
    text-overflow: ellipsis;
    overflow: hidden;
    white-space: nowrap;
  }

  .library-type {
    font-size: 12px;
    color: var(--text-secondary);
    text-transform: capitalize;
  }

  .chevron {
    color: var(--text-tertiary);
    font-size: 18px;
  }

  @media (max-width: 640px) {
    .card-top {
      flex-direction: column;
      align-items: flex-start;
    }
    .search-box {
      width: 100%;
    }
    .library-card {
      grid-template-columns: auto 1fr 14px;
    }
  }
</style>
