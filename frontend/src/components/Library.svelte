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
        return '🎬';
      case 'tvshows':
      case 'show':
        return '📺';
      case 'music':
        return '🎵';
      case 'photos':
        return '📷';
      case 'audiobooks':
      case 'podcast':
        return '🎧';
      default:
        return '📁';
    }
  }
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
    <h2 class="card-title">Libraries</h2>
  </div>
  {#if libraries.length === 0}
    <div class="card text-center py-8">
      <p class="text-[--text-secondary]">No libraries found.</p>
    </div>
  {:else}
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
      {#each libraries as library}
        <button class="library-card" on:click={() => selectLibrary(library)}>
          <div class="library-icon">
            {getLibraryIcon(library.CollectionType)}
          </div>
          <div class="library-name">{library.Name}</div>
        </button>
      {/each}
    </div>
  {/if}
{/if}

<style>
  .library-card {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 24px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 16px;
    cursor: pointer;
    transition: all 0.3s;
  }

  .library-card:hover {
    transform: translateY(-4px);
    background: var(--bg-hover);
    border-color: rgba(139, 92, 246, 0.3);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  }

  .library-icon {
    font-size: 2.5rem;
    line-height: 1;
  }

  .library-name {
    font-size: 14px;
    font-weight: 500;
    color: var(--text-primary);
    text-align: center;
  }
</style>
