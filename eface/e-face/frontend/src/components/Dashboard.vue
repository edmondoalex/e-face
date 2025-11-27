<template>
  <div class="control4-shell">
    <header class="dashboard-header card compact-header">
      <div class="header-inline">
        <div class="brand-logo tiny" aria-label="Logo">EF</div>
        <div class="status-inline">
          <div class="weather-chip compact">
            <span class="icon" aria-hidden="true" v-html="iconMarkup(weatherSnapshot.icon)"></span>
            <div class="weather-meta">
              <strong>{{ weatherSnapshot.temperature }}</strong>
              <small>{{ weatherSnapshot.condition }}</small>
            </div>
          </div>
          <div class="alarm-chip" :class="alarmStatusChip.tone">
            <span class="icon" aria-hidden="true" v-html="iconMarkup(alarmStatusChip.icon)"></span>
            <div>
              <strong>{{ alarmStatusChip.label }}</strong>
              <small>{{ alarmStatusChip.details }}</small>
            </div>
          </div>
        </div>
      </div>
      <div class="header-actions compact">
        <div
          v-if="!isAdmin"
          class="connection-dot"
          :class="`tone-${connectionStatusChip.tone}`"
          role="status"
          aria-live="polite"
          :aria-label="`Connessione ${connectionStatusChip.label}`"
          :title="`Connessione ${connectionStatusChip.label}`"
        >
          <span class="dot"></span>
          <span class="sr-only">{{ connectionStatusChip.details }}</span>
        </div>
        <button class="ghost-btn icon-only" type="button" @click="openLightsModal" aria-label="Luci attive">
          <span class="icon" aria-hidden="true" v-html="iconMarkup('bulb')"></span>
        </button>
        <button class="ghost-btn icon-only" type="button" @click="$emit('open-settings')" aria-label="Impostazioni">
          <span class="icon" aria-hidden="true" v-html="iconMarkup('settings')"></span>
        </button>
      </div>
    </header>

    <section class="console" :class="{ 'console--compact': !isAdmin }">
      <aside class="nav rail card">
        <h3 class="sr-only">Sezioni</h3>
        <button
          v-for="cat in categories"
          :key="cat.id"
          class="nav-btn"
          :class="{ active: activeCategory === cat.id }"
          type="button"
          :title="cat.label"
          @click="setCategory(cat.id)"
        >
          <span class="nav-icon" aria-hidden="true" v-html="iconMarkup(cat.icon)"></span>
          <span class="sr-only">{{ cat.label }}</span>
        </button>
      </aside>

      <div class="content">
        <section v-if="structuredRooms.length > 1" class="room-selector card">
          <div class="room-select-mobile">
            <label class="sr-only" for="roomSelectMobile">Seleziona stanza</label>
            <select
              id="roomSelectMobile"
              aria-label="Seleziona stanza"
              :value="currentRoomId ?? (structuredRooms[0] && structuredRooms[0].id)"
              @change="focusRoom($event.target.value)"
            >
              <option v-for="room in structuredRooms" :key="room.id" :value="room.id">{{ room.name }}</option>
            </select>
          </div>
          <div class="room-chip-row">
            <button
              v-for="room in structuredRooms"
              :key="room.id"
              class="room-chip"
              :class="{ active: room.id === currentRoomId }"
              type="button"
              @click="focusRoom(room.id)"
            >
              <span class="chip-icon" aria-hidden="true" v-html="iconMarkup(roomIcon(room))"></span>
              <div>
                <strong>{{ room.name }}</strong>
              </div>
            </button>
          </div>
        </section>

        <template v-if="activeCategory === 'lights'">
          <section v-if="hasLights" class="rooms-grid">
            <article
              v-for="room in visibleRooms"
              :key="room.id"
              class="room-card card"
              :class="{ focused: room.id === currentRoomId, 'has-bg': !!room.background }"
              :style="roomBackgroundStyle(room)"
            >
              <header class="room-head">
                <div>
                  <h3>{{ room.name }}</h3>
                </div>
                <div class="room-actions">
                  <div class="primary-actions">
                    <button class="pill" type="button" :class="{ on: roomActiveLights(room) > 0 }" @click="toggleRoom(room)">
                      {{ roomActiveLights(room) ? 'Spegni tutto' : 'Accendi tutto' }}
                    </button>
                    <button
                      class="pill ghost"
                      v-if="room.id !== currentRoomId"
                      type="button"
                      @click="focusRoom(room.id)"
                    >
                      Apri stanza
                    </button>
                  </div>
                  <div class="scene-actions" v-if="room.scenes && room.scenes.length">
                    <button
                      v-for="scene in room.scenes"
                      :key="scene.id"
                      class="pill scene"
                      type="button"
                      :disabled="sceneTriggering === scene.id"
                      @click="triggerScene(scene)"
                    >
                      {{ scene.name }}
                    </button>
                  </div>
                </div>
              </header>

              <div class="lights-grid">
                <article
                  v-for="device in room.devices"
                  :key="device.id"
                  class="light-card"
                  :class="{ active: isOn(device) }"
                  :style="lightCardStyle(device)"
                  role="button"
                  tabindex="0"
                  @click="tryOpenDevicePanel(device, room)"
                  @keydown.enter.prevent="tryOpenDevicePanel(device, room)"
                  @keydown.space.prevent="tryOpenDevicePanel(device, room)"
                >
                  <div class="light-head">
                    <div class="device-chip">
                      <button
                        class="device-icon-btn"
                        type="button"
                        :aria-pressed="isOn(device)"
                        :style="deviceIconStyle(device)"
                        @click.stop="toggle(device)"
                      >
                        <span class="device-icon" aria-hidden="true" v-html="iconMarkup(deviceIcon(device))"></span>
                      </button>
                      <div class="light-text-block">
                        <p class="light-label">{{ device.name }}</p>
                        <p class="muted tiny">{{ deviceStateLabel(device) }}</p>
                        <div class="device-tags" v-if="device.labels && device.labels.length">
                          <span
                            v-for="tag in device.labels"
                            :key="device.id + '-' + tag"
                            class="device-tag"
                          >{{ formatTag(tag) }}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                </article>
              </div>
            </article>
          </section>

          <div v-else class="empty-state card">
            <div class="empty-icon" aria-hidden="true" v-html="iconMarkup('plug')"></div>
            <h3>Nessuna luce sincronizzata</h3>
            <p class="muted">Assicurati che l'integrazione Home Assistant sia attiva e che le stanze siano assegnate.</p>
            <button class="ghost-btn" type="button" @click="$emit('open-settings')">
              Apri impostazioni
            </button>
          </div>
        </template>

        <template v-else>
          <section class="placeholder card">
            <h3>{{ activeCategoryLabel }}</h3>
            <p class="muted">
              Questa vista replica la suddivisione Control4 per media, sicurezza e comfort in attesa del collegamento dispositivi.
            </p>
            <div class="placeholder-grid">
              <article v-for="tile in placeholderTiles" :key="tile.title" class="placeholder-card">
                <h4>{{ tile.title }}</h4>
                <p class="muted tiny">{{ tile.desc }}</p>
              </article>
            </div>
          </section>
        </template>
      </div>

      <aside class="right rail card" v-if="isAdmin">
        <h3>Stato impianto</h3>
        <div class="connection-status-card" :class="connectionStatusChip.tone" aria-live="polite">
          <span class="icon" aria-hidden="true" v-html="iconMarkup(connectionStatusChip.icon)"></span>
          <div class="meta">
            <p class="tiny muted">Percorso rete</p>
            <strong>{{ connectionStatusChip.label }}</strong>
            <small>{{ connectionStatusChip.details }}</small>
          </div>
        </div>
        <div class="system-pills">
          <div v-for="pill in systemPills" :key="pill.id" class="system-pill" :class="pill.accent">
            <p>{{ pill.label }}</p>
            <small>{{ pill.value }}</small>
          </div>
        </div>
        <div class="telemetry">
          <div class="telemetry-item">
            <div>
              <p class="tiny muted">Connessione HA</p>
              <strong>{{ hasLights ? 'Operativa' : 'In attesa' }}</strong>
            </div>
            <span class="status-dot" :class="{ on: hasLights }"></span>
          </div>
          <div class="telemetry-item">
            <div>
              <p class="tiny muted">Ultimo comando</p>
              <strong>{{ lastCommandLabel }}</strong>
            </div>
            <button class="tag compact" type="button" @click="refreshNow">Aggiorna</button>
          </div>
          <div class="telemetry-item">
            <div>
              <p class="tiny muted">Ultimo aggiornamento</p>
              <strong>{{ lastRefreshLabel }}</strong>
            </div>
          </div>
        </div>
        <div class="support-card">
          <p class="eyebrow">Suggerimenti</p>
          <p class="muted">Usa questa vista per monitorare rapidamente lo stato generale dell'impianto.</p>
          <button class="ghost-btn" type="button" @click="$emit('open-settings')">
            Centro impostazioni
          </button>
        </div>
      </aside>
    </section>

    <transition name="fade">
      <div v-if="lightsModalOpen" class="lights-overlay" role="dialog" aria-modal="true">
        <div class="lights-panel card">
          <header class="panel-head">
            <div>
              <p class="eyebrow">Illuminazione</p>
              <h3>Luci attive</h3>
            </div>
            <button class="ghost-btn icon-only" type="button" @click="closeLightsModal" aria-label="Chiudi">
              <span class="icon" aria-hidden="true" v-html="iconMarkup('close')"></span>
            </button>
          </header>
          <div v-if="activeLightDevices.length" class="active-lights-list">
            <div v-for="device in activeLightDevices" :key="device.id" class="active-light-row">
              <span class="icon" aria-hidden="true" v-html="iconMarkup('bulb')"></span>
              <div>
                <strong>{{ device.name }}</strong>
                <small>{{ device.roomName }}</small>
              </div>
              <button class="pill ghost" type="button" @click="toggle(device.ref)">Spegni</button>
            </div>
          </div>
          <p v-else class="muted">Nessuna luce risulta accesa.</p>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div
        v-if="devicePanel.open"
        class="device-overlay"
        role="dialog"
        aria-modal="true"
        @click.self="closeDevicePanel"
      >
        <div class="device-panel card">
          <header class="panel-head">
            <div>
              <p class="eyebrow">{{ devicePanel.roomName || 'Illuminazione' }}</p>
              <h3>{{ devicePanel.device?.name }}</h3>
              <span class="state-chip" :class="{ on: isOn(devicePanel.device) }">
                {{ isOn(devicePanel.device) ? 'Accesa' : 'Spenta' }}
              </span>
            </div>
            <button class="ghost-btn icon-only" type="button" @click="closeDevicePanel" aria-label="Chiudi pannello luce">
              <span class="icon" aria-hidden="true" v-html="iconMarkup('close')"></span>
            </button>
          </header>

          <section v-if="panelSupportsBrightness" class="panel-section">
            <div class="section-head">
              <p>Luminosità</p>
              <span>{{ panelBrightnessPercent }}%</span>
            </div>
            <div class="slider-row">
              <input
                type="range"
                min="1"
                max="255"
                :value="devicePanel.brightness"
                @input="previewPanelBrightness($event.target.value)"
                @change="commitPanelBrightness"
              />
            </div>
          </section>

          <section v-if="panelSupportsColorTemp" class="panel-section">
            <div class="section-head">
              <p>Tonalità</p>
              <span>{{ panelColorTempLabel }}</span>
            </div>
            <div class="slider-row">
              <input
                type="range"
                :min="panelColorTempRange.min"
                :max="panelColorTempRange.max"
                :value="devicePanel.colorTemp || panelColorTempRange.min"
                @input="previewPanelColorTemp($event.target.value)"
                @change="commitPanelColorTemp"
              />
            </div>
          </section>

          <section v-if="panelSupportsColor" class="panel-section">
            <div class="section-head">
              <p>Colore</p>
              <span>{{ devicePanel.color }}</span>
            </div>
            <div class="color-palette">
              <button
                v-for="preset in colorPresets"
                :key="preset"
                type="button"
                class="swatch"
                :class="{ active: preset === devicePanel.color }"
                :style="{ '--swatch-color': preset }"
                @click="applyPanelColor(preset)"
                :aria-label="`Imposta colore ${preset}`"
              ></button>
            </div>
            <div class="hue-slider">
              <input
                type="range"
                min="0"
                max="360"
                :value="devicePanel.hue"
                @input="previewPanelHue($event.target.value)"
                @change="commitPanelHue"
              />
              <div class="hue-track" :style="{ background: hueGradient }"></div>
            </div>
          </section>

          <p v-if="devicePanel.open && !panelHasControls" class="muted no-controls">Nessun controllo aggiuntivo disponibile per questa luce.</p>
        </div>
      </div>
    </transition>
  </div>
</template>

<script>
import axios from 'axios'
import {
  callLightService,
  extractBrightness,
  extractRgb,
  rgbToHex,
  hexToRgb,
  normalizeBrightness,
  isValidHexColor
} from '../utils/lightControl'

const ICONS = {
  default: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 10.5 12 4l9 6.5V20a1 1 0 0 1-1 1h-5v-5H9v5H4a1 1 0 0 1-1-1Z"/></svg>',
  sun: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4.5"/><path d="M12 2v2M12 20v2M4 12H2M22 12h-2M5.64 5.64 4.22 4.22M19.78 19.78l-1.42-1.42M19.78 4.22l-1.42 1.42M4.22 19.78l1.42-1.42"/></svg>',
  cloud: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M7 18a4 4 0 0 1 0-8h.5A5.5 5.5 0 0 1 17 7.5a4.5 4.5 0 0 1 .5 9H7Z"/></svg>',
  rain: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 15a4 4 0 0 1 .5-8A5.5 5.5 0 0 1 17 7.5a4.5 4.5 0 0 1 .5 9H6Z"/><path d="m8 19-1 3M12 19l-1 3M16 19l-1 3"/></svg>',
  storm: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 15a4 4 0 0 1 .5-8A5.5 5.5 0 0 1 17 7.5a4.5 4.5 0 0 1 .5 9H6Z"/><path d="M10 13h3l-2 4h3l-3 5"/></svg>',
  snow: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/XMLSchema" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2"/><path d="M12 4v4M12 16v4M4 12h4M16 12h4M7 7l2.5 2.5M14.5 14.5 17 17M17 7l-2.5 2.5M9.5 14.5 7 17"/></svg>',
  wind: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M4 12h9a2 2 0 1 0-2-2"/><path d="M2 16h13a3 3 0 1 1-3 3"/></svg>',
  settings: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" strokeLinejoin="round"><path d="M10.343 3.94c.09-.54.56-.94 1.11-.94h1.093c.55 0 1.02.4 1.11.94l.15.894c.07.424.383.764.78.93.398.164.855.142 1.204-.108l.738-.527a1.125 1.125 0 0 1 1.45.12l.773.774c.39.39.44 1.002.12 1.45l-.527.737c-.25.35-.272.806-.107 1.204.165.397.505.71.93.78l.894.15c.54.09.94.56.94 1.109v1.094c0 .55-.4 1.02-.94 1.109l-.894.15c-.425.07-.765.383-.93.78-.165.398-.143.854.107 1.204l.527.738c.32.448.27 1.06-.12 1.45l-.774.774a1.125 1.125 0 0 1-1.449.12l-.738-.527c-.35-.25-.806-.272-1.204-.107-.397.165-.71.505-.78.93l-.15.894c-.09.54-.56.94-1.11.94h-1.093c-.55 0-1.02-.4-1.11-.94l-.15-.894c-.07-.425-.383-.765-.78-.93-.398-.165-.854-.143-1.204.107l-.737.527a1.125 1.125 0 0 1-1.45-.12l-.773-.774a1.125 1.125 0 0 1-.12-1.45l.527-.737c.25-.35.272-.806.107-1.204-.165-.397-.505-.71-.93-.78l-.894-.15c-.54-.09-.94-.56-.94-1.109v-1.094c0-.55.4-1.019.94-1.108l.894-.15c.424-.07.765-.383.93-.78.165-.398.143-.854-.107-1.204l-.527-.738a1.125 1.125 0 0 1 .12-1.449l.773-.774a1.125 1.125 0 0 1 1.45-.12l.737.527c.35.25.807.272 1.204.107.397-.165.71-.505.78-.93l.15-.894Z"/><path d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/></svg>',
  bulb: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" strokeLinejoin="round"><path d="M12 3a5 5 0 0 1 5 5c0 1.9-.9 3.2-2 4.2-.5.4-.8.9-.8 1.5V16H9.8v-2.3c0-.6-.3-1.1-.8-1.5-1.1-1-2-2.3-2-4.2a5 5 0 0 1 5-5Z"/><path d="M9 20h6"/><path d="M10 22h4"/></svg>',
  shield: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" strokeLinejoin="round"><path d="M12 3 20 6v6c0 4.6-3.2 8.8-8 10-4.8-1.2-8-5.4-8-10V6l8-3Z"/></svg>',
  play: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M9 7v10l8-5-8-5Z"/></svg>',
  thermo: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3a2 2 0 0 0-2 2v9.76a4 4 0 1 0 4 0V5a2 2 0 0 0-2-2Z"/></svg>',
  home: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 10.5 12 4l9 6.5V20a1 1 0 0 1-1 1h-5v-5H9v5H4a1 1 0 0 1-1-1Z"/></svg>',
  bed: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/XMLSchema" fill="none" stroke="currentColor" stroke-width="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M3 11h18v9H3z"/><path d="M3 16h18"/></svg>',
  bath: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M5 7a2 2 0 0 1 2-2h1"/><path d="M3 13h18v2a4 4 0 0 1-4 4H7a4 4 0 0 1-4-4v-2Z"/><path d="M6 19v2M18 19v2"/></svg>',
  desk: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 10h16v7H4z"/><path d="M8 17v4M16 17v4"/></svg>',
  sofa: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M4 12a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v4H4Z"/><path d="M6 16v3M18 16v3"/></svg>',
  plug: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="M9 2v6m6-6v6"/><path d="M7 12h10v4a4 4 0 0 1-4 4h-2a4 4 0 0 1-4-4v-4Z"/></svg>',
  close: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" strokeLinecap="round" strokeLinejoin="round"><path d="m6 6 12 12M18 6 6 18"/></svg>',
  cloud: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M17.5 19H7a4 4 0 0 1-.5-8A5.5 5.5 0 0 1 17 7.5a4.5 4.5 0 0 1 .5 9Z"/></svg>',
  cloudOff: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="m3 3 18 18"/><path d="M18 18H7a4 4 0 0 1-.5-8 5.5 5.5 0 0 1 9.22-4"/></svg>',
  lan: '<svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="3" width="12" height="6" rx="1.5"/><path d="M12 9v4"/><rect x="4" y="15" width="6" height="6" rx="1"/><rect x="14" y="15" width="6" height="6" rx="1"/></svg>'
}

export default {
  name: 'Dashboard',
  props: {
    rooms: {
      type: Array,
      default: () => []
    },
    devices: {
      type: Array,
      default: () => []
    },
    roomName: {
      type: String,
      default: ''
    },
    currentRoom: {
      type: [String, Number, null],
      default: null
    },
    isAdmin: {
      type: Boolean,
      default: false
    },
    connMode: {
      type: String,
      default: 'unknown'
    },
    haConnected: {
      type: Boolean,
      default: false
    },
    backendConnected: {
      type: Boolean,
      default: false
    }
  },
  emits: ['open-settings', 'refresh-room', 'room-selected'],
  data() {
    return {
      categories: [
        { id: 'lights', label: 'Illuminazione', icon: 'bulb' },
        { id: 'media', label: 'Media', icon: 'play' },
        { id: 'security', label: 'Sicurezza', icon: 'shield' },
        { id: 'comfort', label: 'Comfort', icon: 'thermo' }
      ],
      activeCategory: 'lights',
      currentRoomId: this.currentRoom ?? null,
      lastCommand: null,
      lastRefresh: Date.now(),
      lightsModalOpen: false,
      haWeather: null,
      sceneTriggering: null,
      devicePanel: {
        open: false,
        device: null,
        roomName: '',
        brightness: 0,
        color: '#ffffff',
        hue: 0,
        colorTemp: null,
        supportsBrightness: false,
        supportsColor: false,
        supportsColorTemp: false
      },
      colorPresets: ['#ffffff', '#ffe1c4', '#ffd369', '#ffb3c6', '#f7aef8', '#cdb4ff', '#9bf6ff', '#a7ff83'],
      pendingRoomRefresh: null,
      optimisticStates: {},
      optimisticTimers: {}
    }
  },
  computed: {
    roomNameLabel() {
      if (this.roomName) return this.roomName
      return this.currentRoomObj?.name || 'Ambiente'
    },
    structuredRooms() {
      if (Array.isArray(this.rooms) && this.rooms.length) {
        return this.rooms.map((room) => ({
          ...room,
          devices: Array.isArray(room.devices)
            ? room.devices
            : room.id === this.currentRoom
              ? this.devices
              : []
        }))
      }
      if (this.devices.length) {
        const label = this.roomName || 'Ambiente'
        return [{ id: this.currentRoom || 'default-room', name: label, devices: this.devices }]
      }
      return []
    },
    connectionStatusChip() {
      const normalizedMode = (this.connMode || '').toLowerCase()
      if (!this.haConnected) {
        if (normalizedMode === 'cloud') {
          return { label: 'Cloud', details: 'Connessione…', icon: 'cloud', tone: 'cloud' }
        }
        if (normalizedMode === 'local') {
          return { label: 'Locale', details: 'Connessione…', icon: 'lan', tone: 'local' }
        }
        return { label: 'Offline', details: 'In attesa', icon: 'cloudOff', tone: 'offline' }
      }
      if (normalizedMode === 'cloud') {
        return { label: 'Cloud', details: 'Tunnel remoto', icon: 'cloud', tone: 'cloud' }
      }
      return { label: 'Locale', details: 'Rete interna', icon: 'lan', tone: 'local' }
    },
    currentRoomObj() {
      if (!this.currentRoomId) return null
      return this.structuredRooms.find((room) => room.id === this.currentRoomId) || null
    },
    visibleRooms() {
      if (!this.structuredRooms.length) return []
      if (!this.currentRoomId) return this.structuredRooms
      const focused = this.structuredRooms.filter((room) => room.id === this.currentRoomId)
      const rest = this.structuredRooms.filter((room) => room.id !== this.currentRoomId)
      return [...focused, ...rest]
    },
    hasLights() {
      return this.totalLights > 0
    },
    totalLights() {
      return this.structuredRooms.reduce((acc, room) => acc + (room.devices?.length || 0), 0)
    },
    activeLights() {
      return this.structuredRooms.reduce((acc, room) => acc + this.roomActiveLights(room), 0)
    },
    activeCategoryLabel() {
      return this.categories.find((cat) => cat.id === this.activeCategory)?.label || ''
    },
    placeholderTiles() {
      const base = {
        media: [
          { title: 'Cinema', desc: 'Scene Dolby Atmos' },
          { title: 'Playlist', desc: 'Audio multi-room' },
          { title: 'Streaming', desc: 'Ingressi HDMI e ARC' }
        ],
        security: [
          { title: 'Ingressi', desc: 'Sensori porte/finestre' },
          { title: 'Telecamere', desc: 'Dirette IP H.265' },
          { title: 'Automazioni', desc: 'Inserimento intelligente' }
        ],
        comfort: [
          { title: 'Clima', desc: 'Termostati e fan-coil' },
          { title: 'Tende', desc: 'Scene sunrise/sunset' },
          { title: 'Qualità aria', desc: 'PM2.5 e umidità' }
        ]
      }
      return base[this.activeCategory] || []
    },
    summaryLine() {
      if (!this.hasLights) return 'Nessuna luce rilevata - verifica integrazione.'
      const roomsLabel = this.structuredRooms.length === 1 ? 'stanza' : 'stanze'
      return `${this.activeLights} luci accese in ${this.structuredRooms.length} ${roomsLabel}`
    },
    panelSupportsBrightness() {
      if (!this.devicePanel.device) return false
      if (typeof this.devicePanel.supportsBrightness === 'boolean') return this.devicePanel.supportsBrightness
      return this.supportsBrightness(this.devicePanel.device)
    },
    panelSupportsColor() {
      if (!this.devicePanel.device) return false
      if (typeof this.devicePanel.supportsColor === 'boolean') return this.devicePanel.supportsColor
      return this.supportsColor(this.devicePanel.device)
    },
    panelSupportsColorTemp() {
      if (!this.devicePanel.device) return false
      if (typeof this.devicePanel.supportsColorTemp === 'boolean') return this.devicePanel.supportsColorTemp
      return this.supportsColorTemperature(this.devicePanel.device)
    },
    panelHasControls() {
      return this.panelSupportsBrightness || this.panelSupportsColor || this.panelSupportsColorTemp
    },
    panelColorTempRange() {
      if (!this.devicePanel.device || !this.panelSupportsColorTemp) return { min: 153, max: 500 }
      return this.colorTempBounds(this.devicePanel.device)
    },
    panelColorTempLabel() {
      if (!this.panelSupportsColorTemp || !this.devicePanel.colorTemp) return '-- K'
      const kelvin = Math.round(1000000 / this.devicePanel.colorTemp)
      return `${kelvin} K`
    },
    lastRefreshLabel() {
      return new Intl.DateTimeFormat('it-IT', { hour: '2-digit', minute: '2-digit' }).format(this.lastRefresh)
    },
    lastCommandLabel() {
      if (!this.lastCommand) return '—'
      return new Intl.DateTimeFormat('it-IT', { hour: '2-digit', minute: '2-digit', second: '2-digit' }).format(this.lastCommand)
    },
    systemPills() {
      return [
        { id: 'ha', label: 'Home Assistant', value: this.hasLights ? 'Operativo' : 'In attesa', accent: this.hasLights ? 'positive' : 'warning' },
        { id: 'devices', label: 'Dispositivi', value: `${this.totalLights} luci`, accent: 'neutral' },
        { id: 'command', label: 'Ultimo comando', value: this.lastCommandLabel, accent: 'neutral' }
      ]
    },
    activeLightDevices() {
      return this.flattenedDevices()
        .filter(({ device }) => this.isOn(device))
        .map(({ device, room }) => ({ id: device.id, name: device.name, roomName: room.name, ref: device }))
    },
    weatherSnapshot() {
      const fallback = { icon: 'sun', temperature: '--°', condition: 'In attesa dati HA' }
      const source = this.haWeather || this.findWeatherDevice()
      if (!source) return fallback
      const resolved = this.normalizeHaWeather(source)
      return resolved || fallback
    },
    alarmSnapshot() {
      const device = [...this.devices, ...(this.currentRoomObj?.devices || [])].find((dev) => {
        const domain = (dev?.domain || dev?.type || '').toLowerCase()
        const entity = (dev?.id || dev?.entity_id || '').toLowerCase()
        const name = (dev?.name || '').toLowerCase()
        return domain === 'alarm_control_panel' || entity.includes('alarm') || name.includes('allarme')
      })
      if (!device) return null
      const state = String(device.state || '').toLowerCase()
      const mapping = {
        disarmed: 'Disinserito',
        armed_home: 'Inserito casa',
        armed_away: 'Inserito totale',
        armed_night: 'Inserito notte',
        pending: 'In attesa',
        triggered: 'Allarme attivo'
      }
      const label = mapping[state] || this.formatCondition(device.state || 'Allarme')
      const timestamp = device.last_changed || device.last_updated
      const details = timestamp
        ? `Agg. ${new Date(timestamp).toLocaleTimeString('it-IT', { hour: '2-digit', minute: '2-digit' })}`
        : 'Monitoraggio attivo'
      return { icon: 'shield', label, details }
    },
    alarmStatusChip() {
      const snapshot = this.alarmSnapshot
      if (snapshot) {
        const lowerLabel = snapshot.label.toLowerCase()
        let tone = 'idle'
        if (lowerLabel.includes('allarme') || lowerLabel.includes('trigger')) tone = 'alert'
        else if (lowerLabel.includes('inserito')) tone = 'armed'
        return { ...snapshot, tone }
      }
      return {
        icon: 'shield',
        label: 'Allarme',
        details: 'Non configurato',
        tone: 'idle'
      }
    },
    panelBrightnessPercent() {
      const value = Number(this.devicePanel.brightness) || 0
      return Math.round((value / 255) * 100)
    },
    hueGradient() {
      return 'linear-gradient(90deg, #ff0000 0%, #ff9900 16%, #ffff00 32%, #00ff00 48%, #00ffff 64%, #0055ff 80%, #ff00ff 100%)'
    }
  },
  watch: {
    currentRoom(value) {
      if (typeof value === 'undefined') return
      this.currentRoomId = value === null ? null : this.normalizeRoomId(value)
    },
    rooms: {
      handler(newRooms) {
        if (!this.currentRoomId && Array.isArray(newRooms) && newRooms.length) {
          this.currentRoomId = this.normalizeRoomId(newRooms[0].id)
        }
        this.syncDevicePanel()
        this.updateWeatherFromDevices()
        this.reconcileOptimisticStates()
      },
      deep: true,
      immediate: true
    },
    devices: {
      handler() {
        this.lastRefresh = Date.now()
        if (!this.currentRoomId && this.currentRoom !== null) {
          this.currentRoomId = this.normalizeRoomId(this.currentRoom)
        }
        this.syncDevicePanel()
        this.updateWeatherFromDevices()
        this.reconcileOptimisticStates()
      },
      deep: true,
      immediate: true
    }
  },
  mounted() {
    if (!this.currentRoomId && this.structuredRooms.length) {
      this.currentRoomId = this.normalizeRoomId(this.structuredRooms[0].id)
    }
    if (typeof window !== 'undefined') {
      window.addEventListener('ha_event', this.handleHaEvent)
    }
    this.fetchHaWeather()
  },
  beforeUnmount() {
    if (typeof window !== 'undefined') {
      window.removeEventListener('ha_event', this.handleHaEvent)
    }
    this.clearQueuedRoomRefresh()
    this.clearAllOptimisticTimers()
  },
  methods: {
    getDirectHaCaller() {
      if (typeof window === 'undefined') return null
      const fn = window.__efaceHaCallService
      return typeof fn === 'function' ? fn : null
    },
    entityDomain(entityId) {
      if (typeof entityId !== 'string') return ''
      return entityId.includes('.') ? entityId.split('.', 1)[0] : ''
    },
    setCategory(id) {
      this.activeCategory = id
    },
    refreshNow() {
      this.lastRefresh = Date.now()
      this.clearQueuedRoomRefresh()
      this.$emit('refresh-room')
      this.fetchHaWeather()
    },
    focusRoom(roomId) {
      if (roomId === undefined || roomId === null) return
      const normalized = this.normalizeRoomId(roomId)
      this.currentRoomId = normalized
      this.$emit('room-selected', normalized)
    },
    normalizeRoomId(value) {
      if (value === null || value === undefined) return null
      if (typeof this.currentRoomId === 'number' || typeof value === 'number') {
        const num = Number(value)
        return Number.isNaN(num) ? value : num
      }
      return value
    },
    roomIcon(room) {
      const name = (room?.name || '').toLowerCase()
      if (name.includes('living') || name.includes('salotto') || name.includes('soggiorno')) return 'sofa'
      if (name.includes('studio') || name.includes('office')) return 'desk'
      if (name.includes('camera') || name.includes('bed')) return 'bed'
      if (name.includes('bagno') || name.includes('bath')) return 'bath'
      return 'home'
    },
    sanitizeCssUrl(value) {
      if (!value) return ''
      return String(value)
        .replace(/"/g, '\\"')
        .replace(/\n|\r/g, '')
        .trim()
    },
    roomBackgroundStyle(room) {
      const sanitized = this.sanitizeCssUrl(room?.background)
      if (!sanitized) return {}
      return {
        backgroundImage: `linear-gradient(135deg, rgba(8,10,16,0.82), rgba(8,10,16,0.72)), url("${sanitized}")`,
        backgroundSize: 'cover',
        backgroundPosition: 'center'
      }
    },
    flattenedDevices() {
      const list = []
      this.structuredRooms.forEach((room) => {
        (room.devices || []).forEach((device) => list.push({ room, device }))
      })
      return list
    },
    deviceState(device) {
      if (!device) return null
      const entityId = device.id
      if (entityId && this.optimisticStates[entityId]) {
        return this.optimisticStates[entityId]
      }
      return (
        this.normalizeStateValue(device.state) ||
        this.normalizeStateValue(device?.attributes?.state) ||
        null
      )
    },
    normalizeStateValue(value) {
      if (typeof value === 'string') {
        const normalized = value.trim().toLowerCase()
        if (normalized === 'on' || normalized === 'off') return normalized
        return null
      }
      if (typeof value === 'boolean') {
        return value ? 'on' : 'off'
      }
      return null
    },
    isOn(device) {
      return this.deviceState(device) === 'on'
    },
    roomActiveLights(room) {
      return (room.devices || []).filter((device) => this.isOn(device)).length
    },
    deviceStateLabel(device) {
      if (!device) return 'Stato sconosciuto'
      if (device.brightness)
      {
        const brightness = extractBrightness(device)
        const percent = Math.round((brightness / 255) * 100)
        return this.isOn(device) ? `Accesa al ${percent}%` : 'Spenta'
      }
      return this.isOn(device) ? 'Accesa' : 'Spenta'
    },
    deviceIcon() {
      return 'bulb'
    },
    colorModes(device) {
      const attrs = device?.attributes || {}
      const modes = new Set()
      const candidates = [
        attrs.supported_color_modes,
        attrs.capabilities?.supported_color_modes,
        device?.supported_color_modes,
        device?.capabilities?.supported_color_modes
      ]
      const pushCandidate = (value) => {
        if (!value) return
        if (Array.isArray(value)) {
          value.forEach((mode) => {
            const normalized = (mode ?? '').toString().trim()
            if (normalized) modes.add(normalized)
          })
          return
        }
        if (typeof value === 'string') {
          value.split(',').forEach((mode) => {
            const normalized = mode.trim()
            if (normalized) modes.add(normalized)
          })
        }
      }
      candidates.forEach(pushCandidate)
      const singleMode = attrs.color_mode || device?.color_mode
      if (singleMode) modes.add(singleMode)
      return Array.from(modes)
    },
    supportedFeatures(device) {
      const attrs = device?.attributes || {}
      const raw = attrs.supported_features ?? device?.supported_features
      if (typeof raw === 'number') return raw
      if (typeof raw === 'string' && raw.trim().length) {
        const parsed = Number(raw)
        return Number.isNaN(parsed) ? null : parsed
      }
      return null
    },
    supportsBrightness(device) {
      const attrs = device?.attributes || {}
      if (typeof device?.brightness === 'number' || typeof attrs.brightness === 'number') return true
      const modes = this.colorModes(device)
      if (modes.some((mode) => ['brightness', 'hs', 'xy', 'rgb', 'rgbw', 'rgbww', 'color_temp'].includes((mode || '').toString().trim().toLowerCase()))) {
        return true
      }
      const features = this.supportedFeatures(device)
      return typeof features === 'number' && (features & 1) === 1
    },
    supportsColor(device) {
      const attrs = device?.attributes || {}
      if (Array.isArray(device?.rgb_color) || Array.isArray(attrs.rgb_color)) return true
      if (Array.isArray(attrs.xy_color) || Array.isArray(attrs.hs_color)) return true
      const modes = this.colorModes(device)
      const colorTokens = ['hs', 'rgb', 'rgbw', 'rgbww', 'xy', 'xy_color', 'rgb_color']
      if (modes.some((mode) => colorTokens.includes((mode || '').toString().trim().toLowerCase()))) {
        return true
      }
      const features = this.supportedFeatures(device)
      if (typeof features === 'number') {
        const COLOR_FLAG = 16
        const WHITE_VALUE_FLAG = 128
        if ((features & COLOR_FLAG) === COLOR_FLAG || (features & WHITE_VALUE_FLAG) === WHITE_VALUE_FLAG) {
          return true
        }
      }
      return false
    },
    supportsColorTemperature(device) {
      const attrs = device?.attributes || {}
      if (typeof attrs.color_temp === 'number' || typeof device?.color_temp === 'number') return true
      const modes = this.colorModes(device)
      if (modes.some((mode) => ['color_temp', 'ct'].includes((mode || '').toString().trim().toLowerCase()))) {
        return true
      }
      const features = this.supportedFeatures(device)
      const COLOR_TEMP_FLAG = 2
      return typeof features === 'number' && (features & COLOR_TEMP_FLAG) === COLOR_TEMP_FLAG
    },
    supportsAdvancedControls(device) {
      return this.supportsBrightness(device) || this.supportsColor(device) || this.supportsColorTemperature(device)
    },
    brightnessValue(device) {
      if (!device) return 0
      return extractBrightness(device)
    },
    colorValue(device) {
      if (!device) return '#ffffff'
      const rgb = extractRgb(device)
      return rgb ? rgbToHex(rgb) : '#ffffff'
    },
    colorFromMireds(mireds) {
      const kelvin = 1000000 / Math.max(1, Number(mireds) || 1)
      const clamped = Math.min(6500, Math.max(2000, kelvin))
      const ratio = (clamped - 2000) / (6500 - 2000)
      return this.mixHex('#ffb347', '#8ab4ff', ratio)
    },
    mixHex(start, end, t = 0.5) {
      const a = hexToRgb(this.ensureHexFormat(start)) || [255, 255, 255]
      const b = hexToRgb(this.ensureHexFormat(end)) || [255, 255, 255]
      const mix = a.map((val, idx) => Math.round(val + (b[idx] - val) * Math.min(1, Math.max(0, t))))
      return rgbToHex(mix)
    },
    hexWithAlpha(hex, alpha = 1) {
      const rgb = hexToRgb(this.ensureHexFormat(hex)) || [255, 255, 255]
      return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${Math.min(1, Math.max(0, alpha))})`
    },
    deviceActiveColor(device) {
      if (!this.isOn(device)) return null
      if (this.supportsColor(device)) return this.colorValue(device)
      if (this.supportsColorTemperature(device)) {
        const temp = this.colorTempValue(device)
        if (temp) return this.colorFromMireds(temp)
      }
      return '#ffd54f'
    },
    async triggerScene(scene) {
      if (!scene || !scene.id) return
      if (this.sceneTriggering === scene.id) return
      const domain = scene.domain || this.entityDomain(scene.id) || 'button'
      const service = scene.service || (domain === 'button' ? 'press' : 'turn_on')
      const payload = { entity_id: scene.id }
      const direct = this.getDirectHaCaller()
      this.sceneTriggering = scene.id
      try {
        if (direct) {
          try {
            await direct(domain, service, payload)
            this.lastCommand = Date.now()
            return
          } catch (err) {
            console.warn('Direct HA scene trigger failed, falling back to backend', err)
          }
        }
        await axios.post(`/api/devices/${scene.id}/trigger`, { domain, service })
        this.lastCommand = Date.now()
      } catch (err) {
        console.error('Scene trigger failed', err)
      } finally {
        this.sceneTriggering = null
      }
    },
    lightCardStyle(device) {
      const color = this.deviceActiveColor(device)
      if (!color) return {}
      return {
        '--light-accent': color,
        borderColor: this.hexWithAlpha(color, 0.55),
        background: `linear-gradient(140deg, ${this.hexWithAlpha(color, 0.28)}, rgba(5, 7, 20, 0.82))`,
        boxShadow: `0 18px 32px ${this.hexWithAlpha(color, 0.28)}`
      }
    },
    deviceIconStyle(device) {
      const color = this.deviceActiveColor(device)
      if (!color) return {}
      return {
        background: this.hexWithAlpha(color, 0.32),
        borderColor: this.hexWithAlpha(color, 0.65)
      }
    },
    colorTempBounds(device) {
      const attrs = device?.attributes || {}
      const min = Number(attrs.min_mireds ?? 153)
      const max = Number(attrs.max_mireds ?? 500)
      return {
        min: Math.max(100, Math.min(600, min)),
        max: Math.max(200, Math.min(600, Math.max(min + 1, max)))
      }
    },
    colorTempValue(device) {
      if (!device) return null
      const attrs = device?.attributes || {}
      if (typeof attrs.color_temp === 'number') return attrs.color_temp
      if (typeof device?.color_temp === 'number') return device.color_temp
      const bounds = this.colorTempBounds(device)
      return Math.round((bounds.min + bounds.max) / 2)
    },
    async toggleDevice(device, forceState) {
      if (!device) return
      const shouldTurnOn = typeof forceState === 'boolean' ? forceState : !this.isOn(device)
      const previousState = this.isOn(device)
      this.applyOptimisticState(device, shouldTurnOn)
      try {
        if (device.type === 'light') {
          await callLightService(device, shouldTurnOn ? 'turn_on' : 'turn_off')
        } else {
          await axios.post('/api/device/toggle', { id: device.id, state: shouldTurnOn })
        }
        this.lastCommand = Date.now()
        this.queueRoomRefresh()
      } catch (error) {
        console.error(error)
        alert('Impossibile eseguire il comando')
        this.applyOptimisticState(device, previousState)
        this.reconcileOptimisticStates()
        this.queueRoomRefresh(200, { force: true })
      }
    },
    toggle(device) {
      this.toggleDevice(device)
    },
    toggleRoom(room) {
      if (!room?.devices?.length) return
      const shouldTurnOn = this.roomActiveLights(room) === 0
      room.devices.forEach((device) => this.toggleDevice(device, shouldTurnOn))
    },
    openLightsModal() {
      this.lightsModalOpen = true
    },
    closeLightsModal() {
      this.lightsModalOpen = false
    },
    tryOpenDevicePanel(device, room) {
      if (!device) return
      const supportsBrightness = this.supportsBrightness(device)
      const supportsColor = this.supportsColor(device)
      const supportsColorTemp = this.supportsColorTemperature(device)
      if (!supportsBrightness && !supportsColor && !supportsColorTemp) {
        this.toggle(device)
        return
      }
      const color = this.colorValue(device)
      this.devicePanel = {
        open: true,
        device,
        roomName: room?.name || this.roomNameLabel,
        brightness: this.brightnessValue(device) || 0,
        color,
        hue: this.hexToHue(color),
        colorTemp: supportsColorTemp ? this.colorTempValue(device) : null,
        supportsBrightness,
        supportsColor,
        supportsColorTemp
      }
    },
    closeDevicePanel() {
      this.devicePanel = {
        ...this.devicePanel,
        open: false
      }
    },
    syncDevicePanel() {
      if (!this.devicePanel.open || !this.devicePanel.device) return
      const entry = this.flattenedDevices().find(({ device }) => device.id === this.devicePanel.device.id)
      if (!entry) return
      const prevDevice = this.devicePanel.device || {}
      const nextDevice = entry.device || {}
      const mergedAttributes = {
        ...(prevDevice.attributes || {}),
        ...(nextDevice.attributes || {})
      }
      const mergedDevice = {
        ...prevDevice,
        ...nextDevice,
        attributes: mergedAttributes
      }
      const color = this.colorValue(mergedDevice)
      const supportsTemp = this.supportsColorTemperature(mergedDevice)
      this.devicePanel = {
        ...this.devicePanel,
        device: mergedDevice,
        roomName: entry.room?.name || this.devicePanel.roomName,
        brightness: this.brightnessValue(mergedDevice) || 0,
        color,
        hue: this.hexToHue(color),
        colorTemp: supportsTemp ? this.colorTempValue(mergedDevice) : null,
        supportsBrightness: this.devicePanel.supportsBrightness || this.supportsBrightness(mergedDevice),
        supportsColor: this.devicePanel.supportsColor || this.supportsColor(mergedDevice),
        supportsColorTemp: this.devicePanel.supportsColorTemp || supportsTemp
      }
    },
    normalizeColorTemp(value, device = null) {
      const bounds = this.colorTempBounds(device || this.devicePanel.device || {})
      const num = Math.round(Number(value))
      if (Number.isNaN(num)) return bounds.min
      return Math.max(bounds.min, Math.min(bounds.max, num))
    },
    previewPanelBrightness(value) {
      const next = Number(value)
      this.devicePanel = { ...this.devicePanel, brightness: Number.isNaN(next) ? 0 : next }
    },
    async commitPanelBrightness() {
      if (!this.devicePanel.device || !this.panelSupportsBrightness) return
      const prevState = this.isOn(this.devicePanel.device)
      this.applyOptimisticState(this.devicePanel.device, true)
      try {
        await callLightService(this.devicePanel.device, 'turn_on', {
          brightness: normalizeBrightness(this.devicePanel.brightness)
        })
        this.lastCommand = Date.now()
        this.queueRoomRefresh()
      } catch (e) {
        console.error(e)
        alert('Impossibile aggiornare la luminosità')
        this.applyOptimisticState(this.devicePanel.device, prevState)
        this.reconcileOptimisticStates()
        this.queueRoomRefresh(200, { force: true })
      }
    },
    previewPanelColorTemp(value) {
      const normalized = this.normalizeColorTemp(value)
      this.devicePanel = { ...this.devicePanel, colorTemp: normalized }
    },
    async commitPanelColorTemp() {
      if (!this.devicePanel.device || !this.panelSupportsColorTemp || !this.devicePanel.colorTemp) return
      const prevState = this.isOn(this.devicePanel.device)
      this.applyOptimisticState(this.devicePanel.device, true)
      try {
        await callLightService(this.devicePanel.device, 'turn_on', { color_temp: this.devicePanel.colorTemp })
        this.lastCommand = Date.now()
        this.queueRoomRefresh()
      } catch (e) {
        console.error(e)
        alert('Impossibile aggiornare la tonalità')
        this.applyOptimisticState(this.devicePanel.device, prevState)
        this.reconcileOptimisticStates()
        this.queueRoomRefresh(200, { force: true })
      }
    },
    previewPanelHue(value) {
      const hue = Number(value)
      const normalizedHue = Number.isNaN(hue) ? 0 : Math.max(0, Math.min(360, hue))
      this.devicePanel = { ...this.devicePanel, hue: normalizedHue, color: this.hueToHex(normalizedHue) }
    },
    async commitPanelHue() {
      if (!this.devicePanel.device || !this.panelSupportsColor) return
      const prevState = this.isOn(this.devicePanel.device)
      this.applyOptimisticState(this.devicePanel.device, true)
      try {
        const rgb = hexToRgb(this.ensureHexFormat(this.devicePanel.color))
        await callLightService(this.devicePanel.device, 'turn_on', { rgb_color: rgb })
        this.lastCommand = Date.now()
        this.queueRoomRefresh()
      } catch (e) {
        console.error(e)
        alert('Impossibile aggiornare la tonalità colore')
        this.applyOptimisticState(this.devicePanel.device, prevState)
        this.reconcileOptimisticStates()
        this.queueRoomRefresh(200, { force: true })
      }
    },
    async applyPanelColor(color) {
      if (!this.devicePanel.device || !this.supportsColor(this.devicePanel.device)) return
      const normalized = this.ensureHexFormat(color)
      if (!isValidHexColor(normalized)) return
      const rgb = hexToRgb(normalized)
      if (!rgb) return
      const payload = { rgb_color: rgb }
      if (this.supportsBrightness(this.devicePanel.device)) {
        payload.brightness = normalizeBrightness(this.devicePanel.brightness)
      }
      const prevState = this.isOn(this.devicePanel.device)
      this.applyOptimisticState(this.devicePanel.device, true)
      try {
        await callLightService(this.devicePanel.device, 'color', payload)
        this.devicePanel = { ...this.devicePanel, color: normalized, hue: this.hexToHue(normalized) }
        this.lastCommand = Date.now()
        this.queueRoomRefresh()
      } catch (e) {
        console.error(e)
        alert('Impossibile aggiornare il colore')
        this.applyOptimisticState(this.devicePanel.device, prevState)
        this.reconcileOptimisticStates()
        this.queueRoomRefresh(200, { force: true })
      }
    },
    applyOptimisticState(device, stateValue) {
      if (!device?.id) return
      if (typeof stateValue !== 'boolean') {
        this.clearOptimisticState(device.id)
        return
      }
      const next = stateValue ? 'on' : 'off'
      const updated = { ...this.optimisticStates, [device.id]: next }
      this.optimisticStates = updated
      this.scheduleOptimisticExpiry(device.id)
    },
    clearOptimisticState(entityId) {
      if (!entityId) return
      if (this.optimisticStates[entityId]) {
        const clone = { ...this.optimisticStates }
        delete clone[entityId]
        this.optimisticStates = clone
      }
      this.clearOptimisticTimer(entityId)
    },
    scheduleOptimisticExpiry(entityId, ttl = 7000) {
      if (!entityId) return
      this.clearOptimisticTimer(entityId)
      this.optimisticTimers[entityId] = setTimeout(() => {
        this.clearOptimisticState(entityId)
      }, ttl)
    },
    clearOptimisticTimer(entityId) {
      if (!entityId) return
      const timer = this.optimisticTimers[entityId]
      if (timer) {
        clearTimeout(timer)
        delete this.optimisticTimers[entityId]
      }
    },
    clearAllOptimisticTimers() {
      Object.keys(this.optimisticTimers).forEach((key) => this.clearOptimisticTimer(key))
    },
    reconcileOptimisticStates() {
      const entries = Object.keys(this.optimisticStates || {})
      if (!entries.length) return
      const snapshot = new Map()
      this.flattenedDevices().forEach(({ device }) => {
        if (device?.id) {
          snapshot.set(device.id, this.normalizeStateValue(device.state) || this.normalizeStateValue(device?.attributes?.state))
        }
      })
      let mutated = false
      const clone = { ...this.optimisticStates }
      entries.forEach((entityId) => {
        const optimistic = clone[entityId]
        const actual = snapshot.get(entityId)
        if (!optimistic || optimistic === actual) {
          delete clone[entityId]
          this.clearOptimisticTimer(entityId)
          mutated = true
        }
      })
      if (mutated) {
        this.optimisticStates = clone
      }
    },
    queueRoomRefresh(delay = 500, options = {}) {
      const { force = false } = options
      const optimisticCount = Object.keys(this.optimisticStates || {}).length
      const hasOptimisticState = optimisticCount > 0
      const relyOnRealtime = this.haConnected === true || this.backendConnected === true
      if (!force && hasOptimisticState && relyOnRealtime) {
        return
      }
      let effectiveDelay = delay
      if (!force && hasOptimisticState && !relyOnRealtime) {
        // fallback to backend refresh so optimistic state settles for remote panels
        effectiveDelay = Math.max(delay, 900)
      }
      if (this.pendingRoomRefresh) {
        clearTimeout(this.pendingRoomRefresh)
      }
      this.pendingRoomRefresh = setTimeout(() => {
        this.$emit('refresh-room')
        this.pendingRoomRefresh = null
      }, effectiveDelay)
    },
    clearQueuedRoomRefresh() {
      if (this.pendingRoomRefresh) {
        clearTimeout(this.pendingRoomRefresh)
        this.pendingRoomRefresh = null
      }
    },
    handleHaEvent(evt) {
      const payload = evt?.detail
      const weatherPayload = this.extractWeatherPayload(payload)
      if (weatherPayload) {
        this.haWeather = weatherPayload
      }
    },
    extractWeatherPayload(detail) {
      if (!detail) return null
      const mapPayload = detail.event?.a || detail.a
      if (mapPayload) {
        const found = this.findWeatherInMap(mapPayload)
        if (found) return found
      }
      const data = detail.event?.data || detail.data || detail
      const entityId = data?.entity_id || detail.entity_id
      if (this.isWeatherEntity(entityId)) {
        const newState = data?.new_state || detail.new_state || detail.state || {}
        const attrs = newState?.attributes || data?.attributes || detail.attributes || {}
        const stateVal = newState?.state ?? data?.state ?? detail.state ?? null
        return { state: stateVal, attributes: attrs }
      }
      return null
    },
    findWeatherInMap(collection) {
      if (!collection || typeof collection !== 'object') return null
      for (const [entityId, payload] of Object.entries(collection)) {
        if (this.isWeatherEntity(entityId)) {
          const attrs = payload?.a || payload?.attributes || {}
          const stateVal = payload?.s ?? payload?.state ?? null
          return { state: stateVal, attributes: attrs }
        }
      }
      return null
    },
    isWeatherEntity(entityId) {
      return typeof entityId === 'string' && entityId.toLowerCase().startsWith('weather.')
    },
    findWeatherDevice() {
      const dataset = Array.isArray(this.devices) ? this.devices : []
      return dataset.find((dev) => {
        const entity = (dev?.id || dev?.entity_id || '').toLowerCase()
        return entity.startsWith('weather.')
      }) || null
    },
    updateWeatherFromDevices() {
      this.haWeather = this.findWeatherDevice()
    },
    async fetchHaWeather() {
      this.updateWeatherFromDevices()
    },
    normalizeHaWeather(payload) {
      if (!payload) return null
      const attrs = payload.attributes || payload.a || {}
      const tempSource = attrs.temperature ?? attrs.current_temperature ?? payload.temperature
      const temperature = typeof tempSource === 'number'
        ? `${Math.round(tempSource)}°`
        : (typeof tempSource === 'string' && tempSource.trim() ? tempSource : '--°')
      const stateValue = payload.state ?? payload.s ?? ''
      const conditionRaw = stateValue || attrs.condition || payload.condition || ''
      return {
        icon: this.matchWeatherIcon(conditionRaw),
        temperature,
        condition: this.formatCondition(conditionRaw) || 'In attesa'
      }
    },
    hueToHex(hue) {
      return this.hslToHex(Number(hue) || 0, 0.85, 0.55)
    },
    hslToHex(hue, saturation = 0.85, lightness = 0.55) {
      const h = (((hue % 360) + 360) % 360) / 360
      const s = Math.min(1, Math.max(0, saturation))
      const l = Math.min(1, Math.max(0, lightness))
      const c = (1 - Math.abs(2 * l - 1)) * s
      const x = c * (1 - Math.abs(((h * 6) % 2) - 1))
      const m = l - c / 2
      const segment = Math.floor(h * 6)
      let r = 0
      let g = 0
      let b = 0
      switch (segment) {
        case 0:
          r = c; g = x; b = 0
          break
        case 1:
          r = x; g = c; b = 0
          break
        case 2:
          r = 0; g = c; b = x
          break
        case 3:
          r = 0; g = x; b = c
          break
        case 4:
          r = x; g = 0; b = c
          break
        default:
          r = c; g = 0; b = x
      }
      const rgb = [r + m, g + m, b + m].map((val) => Math.round(val * 255))
      return rgbToHex(rgb)
    },
    hexToHue(hex) {
      const rgb = hexToRgb(this.ensureHexFormat(hex))
      if (!rgb) return 0
      const [r, g, b] = rgb.map((val) => val / 255)
      const max = Math.max(r, g, b)
      const min = Math.min(r, g, b)
      if (max === min) return 0
      let h
      if (max === r) {
        h = (60 * ((g - b) / (max - min)) + 360) % 360
      } else if (max === g) {
        h = (60 * ((b - r) / (max - min)) + 120) % 360
      } else {
        h = (60 * ((r - g) / (max - min)) + 240) % 360
      }
      return Math.round(h)
    },
    ensureHexFormat(color) {
      if (!color) return '#ffffff'
      return color.startsWith('#') ? color : `#${color}`
    },
    iconMarkup(key) {
      return ICONS[key] || ICONS.default
    },
    matchWeatherIcon(condition) {
      const value = (condition || '').toLowerCase()
      if (value.includes('storm') || value.includes('temporale')) return 'storm'
      if (value.includes('rain') || value.includes('pioggia')) return 'rain'
      if (value.includes('snow') || value.includes('neve')) return 'snow'
      if (value.includes('cloud') || value.includes('nuvol')) return 'cloud'
      if (value.includes('wind') || value.includes('vento')) return 'wind'
      return 'sun'
    },
    formatTag(tag) {
      if (tag === null || typeof tag === 'undefined') return ''
      const normalized = String(tag).replace(/[_-]+/g, ' ').trim()
      if (!normalized) return ''
      return normalized.charAt(0).toUpperCase() + normalized.slice(1)
    },
    formatCondition(value) {
      if (!value) return ''
      return String(value)
        .replace(/_/g, ' ')
        .replace(/\b\w/g, (match) => match.toUpperCase())
        .trim()
    }
  }
}
</script>

<style scoped>
:global(body) {
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.control4-shell {
  display: flex;
  flex-direction: column;
  gap: clamp(16px, 2vw, 28px);
  min-height: calc(100vh - 40px);
  width: 100%;
  box-sizing: border-box;
  color: #f4f7ff;
  --text: #f4f7ff;
  --muted: rgba(255, 255, 255, 0.74);
  --primary: #6c8cff;
  --accent: #22c1c3;
  --card: rgba(9, 12, 24, 0.85);
  padding-bottom: clamp(200px, 24vh, 260px);
  scroll-padding-bottom: 140px;
}

.card {
  border-radius: 22px;
  background: rgba(9, 12, 24, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.05);
  padding: clamp(18px, 1.8vw, 28px);
  backdrop-filter: blur(18px);
  width: 100%;
  box-sizing: border-box;
}


.dashboard-header {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
}

.compact-header {
  padding: clamp(10px, 1.1vw, 18px) clamp(12px, 1.6vw, 22px);
}

.header-inline {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.connection-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  padding: 6px 12px;
  min-height: 34px;
  background: rgba(255, 255, 255, 0.05);
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.28);
}

.connection-chip.compact {
  padding: 4px 10px;
  min-height: 28px;
  border-radius: 12px;
  box-shadow: none;
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
}

.connection-chip > div {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.connection-chip strong {
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.connection-chip.compact strong {
  font-size: 10px;
}

.connection-chip small {
  font-size: 9px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.75);
}

.connection-chip.compact small {
  font-size: 8px;
  letter-spacing: 0.04em;
}

.connection-chip .icon {
  width: 26px;
  height: 26px;
  border-radius: 12px;
  background: rgba(5, 7, 20, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.18);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.connection-chip.compact .icon {
  width: 20px;
  height: 20px;
  border-radius: 10px;
}

.connection-chip.local {
  border-color: rgba(111, 223, 190, 0.8);
  background: rgba(92, 217, 178, 0.18);
}

.connection-chip.cloud {
  border-color: rgba(142, 189, 255, 0.8);
  background: linear-gradient(135deg, rgba(142, 189, 255, 0.18), rgba(97, 125, 255, 0.24));
}

.connection-chip.offline {
  border-color: rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
  opacity: 0.85;
}

.connection-dot {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: rgba(0, 0, 0, 0.3);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 3px;
  margin-right: 6px;
}

.connection-dot .dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
}

.connection-dot.tone-local .dot {
  background: #34c759;
  box-shadow: 0 0 6px rgba(52, 199, 89, 0.8);
}

.connection-dot.tone-cloud .dot {
  background: #ffd60a;
  box-shadow: 0 0 6px rgba(255, 214, 10, 0.8);
}

.connection-dot.tone-offline .dot {
  background: #ff453a;
  box-shadow: 0 0 6px rgba(255, 69, 58, 0.7);
}

.connection-status-card {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 6px 0 18px;
  padding: 16px 18px;
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.connection-status-card .icon {
  width: 42px;
  height: 42px;
  border-radius: 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(5, 7, 20, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.15);
}

.connection-status-card .meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.connection-status-card .meta strong {
  font-size: 18px;
  letter-spacing: 0.04em;
}

.connection-status-card .meta small {
  font-size: 12px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.78);
}

.connection-status-card.local {
  border-color: rgba(111, 223, 190, 0.4);
  background: linear-gradient(135deg, rgba(92, 217, 178, 0.18), rgba(11, 16, 30, 0.85));
}

.connection-status-card.cloud {
  border-color: rgba(142, 189, 255, 0.45);
  background: linear-gradient(135deg, rgba(142, 189, 255, 0.16), rgba(12, 18, 36, 0.88));
}

.connection-status-card.offline {
  border-color: rgba(255, 255, 255, 0.08);
  opacity: 0.9;
}

.brand-logo {
  width: 56px;
  height: 56px;
  border-radius: 18px;
  background: linear-gradient(135deg, #6c8cff, #22c1c3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.brand-logo.tiny {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  font-size: 14px;
}

.muted {
  color: rgba(255, 255, 255, 0.94);
}

.tiny {
  font-size: 12px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.92);
}

.eyebrow {
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  font-size: 12px;
  color: var(--muted);
}

.dashboard-header h1 {
  margin: 4px 0;
}

h3 {
  color: rgba(255, 255, 255, 0.97);
  letter-spacing: 0.01em;
}

.weather-chip,
.alarm-chip {
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.07);
}

.weather-chip {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 190px;
  padding: 12px 18px;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(49, 85, 255, 0.18));
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.35);
}

.weather-chip .icon {
  width: 34px;
  height: 34px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: rgba(5, 7, 20, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.weather-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}

.weather-meta strong {
  font-size: clamp(20px, 2.2vw, 30px);
  color: #ffffff;
}

.diag-row>strong{
  color: #ffffff;
}

.weather-meta small {
  margin-top: 2px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.78);
}
.weather-chip.compact {
  padding: 6px 10px;
  min-width: auto;
  gap: 8px;
  min-height: 34px;
}

.alarm-chip {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 32px;
  padding: 6px 10px;
  max-width: 170px;
  background: rgba(255, 255, 255, 0.07);
}

.alarm-chip strong {
  font-size: 10px;
  letter-spacing: 0.04em;
}

.alarm-chip small {
  font-size: 8px;
  letter-spacing: 0.04em;
}

.alarm-chip.armed {
  border-color: rgba(137, 227, 255, 0.5);
}

.alarm-chip.alert {
  border-color: rgba(255, 107, 107, 0.7);
  background: rgba(255, 87, 87, 0.15);
}

.header-actions {
  display: flex;
  gap: 10px;
  justify-self: flex-end;
}

.header-actions .connection-chip {
  margin-right: 4px;
}

.header-actions.compact .ghost-btn {
  width: 44px;
  height: 44px;
}

.ghost-btn {
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  color: var(--text);
  padding: 8px 14px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  transition: background 0.2s, border 0.2s;
}

.ghost-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

.icon-only {
  width: 48px;
  height: 48px;
  justify-content: center;
  padding: 0;
  border-radius: 16px;
}

.ghost-btn .icon {
  width: 20px;
  height: 20px;
  color: inherit;
}

.icon :deep(svg),
.nav-icon :deep(svg),
.device-icon :deep(svg) {
  width: 100%;
  height: 100%;
  display: block;
}

.console {
  display: grid;
  grid-template-columns: clamp(96px, 10vw, 120px) minmax(0, 1fr) clamp(190px, 22vw, 280px);
  grid-template-areas: 'nav content right';
  gap: clamp(16px, 2vw, 28px);
  align-items: flex-start;
  padding-bottom: 40px;
}

.console--compact {
  grid-template-columns: clamp(96px, 10vw, 120px) minmax(0, 1fr);
  grid-template-areas: 'nav content';
}

.nav.rail {
  grid-area: nav;
  display: flex;
  flex-direction: column;
  gap: 12px;
  position: sticky;
  top: 32px;
  align-items: center;
  justify-content: flex-start;
  padding: 12px 10px;
  background: rgba(5, 7, 20, 0.8);
  border: 1px solid rgba(255, 255, 255, 0.04);
  border-radius: 22px;
  box-shadow: 0 25px 45px rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(18px);
  width: clamp(70px, 7vw, 92px);
  z-index: 6;
}

.nav-btn {
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 20px;
  padding: 5px;
  background: transparent;
  color: var(--text);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  flex: 0 0 50px;
  cursor: pointer;
  transition: border 0.2s, background 0.2s, transform 0.2s;
}

.nav-btn.active {
  background: linear-gradient(120deg, var(--primary), var(--accent));
  color: #050714;
  border-color: transparent;
}

.nav-icon {
  width: 30px;
  height: 30px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.content {
  grid-area: content;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding-bottom: clamp(140px, 20vh, 200px);
}

.right.rail {
  grid-area: right;
  position: sticky;
  top: 12px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.room-selector {
  display: flex;
  min-height: 180px;
  width: auto;
  min-width: 0;
  box-sizing: border-box;
  flex-direction: column;
  gap: 16px;
  position: sticky;
  top: calc(env(safe-area-inset-top, 0px) + 8px);
  z-index: 8;
}

.room-selector.card {
  background: rgba(9, 12, 24, 0.95);
  min-height: 50px;
}

.room-select-mobile {
  display: none;
  flex-direction: column;
  gap: 4px;
}

.room-select-mobile select {
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(7, 10, 20, 0.85);
  color: var(--text);
  padding: 10px 14px;
}

.room-chip-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.room-chip {
  border-radius: 18px;
  padding: 14px 16px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(10, 13, 26, 0.65);
  display: flex;
  align-items: center;
  gap: 12px;
  cursor: pointer;
  transition: border 0.2s, transform 0.2s;
}

.room-chip strong {
  color: #ffffff;
  font-weight: 600;
}

.room-chip.active {
  border-color: transparent;
  background: linear-gradient(135deg, rgba(108, 140, 255, 0.18), rgba(34, 193, 195, 0.3));
  transform: translateY(-2px);
}

.chip-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
}

.rooms-grid {
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding-bottom: 40px;
}

.room-card {
  position: relative;
  overflow: hidden;
  min-height: 320px;
  width: 100%;
}

.room-card.has-bg::after {
  content: '';
  position: absolute;
  inset: 1px;
  border-radius: inherit;
  background: rgba(5, 7, 15, 0.45);
  pointer-events: none;
}

.room-card.focused {
  border-color: rgba(108, 140, 255, 0.6);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.45);
}

.room-card > * {
  position: relative;
  z-index: 2;
}

.room-head {
  display: flex;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.room-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
  align-items: center;
  width: 100%;
}

.primary-actions {
  display: inline-flex;
  gap: 8px;
  align-items: center;
}

.scene-actions {
  display: inline-flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  justify-content: flex-start;
}

.pill {
  border-radius: 999px;
  padding: 8px 14px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.05);
  color: var(--text);
  cursor: pointer;
  font-size: 13px;
}

.pill.on {
  background: linear-gradient(135deg, rgba(108, 140, 255, 0.4), rgba(34, 193, 195, 0.4));
  border-color: transparent;
}

.pill.ghost {
  background: transparent;
}

.pill.scene {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.12);
  font-size: 12px;
  padding-inline: 12px;
}

.pill.scene:disabled {
  opacity: 0.5;
  cursor: wait;
}

.lights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.light-card {
  border-radius: 18px;
  padding: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.35);
  display: flex;
  flex-direction: column;
  gap: 12px;
  cursor: pointer;
  transition: border 0.2s, transform 0.2s, box-shadow 0.2s;
  color: rgba(255, 255, 255, 0.95);
  width: auto;
  min-width: 0;
}

.light-card.active {
  border-color: rgba(138, 180, 255, 0.6);
  box-shadow: 0 12px 25px rgba(0, 0, 0, 0.35);
}

.light-head {
  display: flex;
  justify-content: space-between;
  gap: 14px;
}

.device-chip {
  display: flex;
  gap: 10px;
  align-items: center;
}

.device-icon-btn {
  border-radius: 16px;
  width: 50px;
  height: 50px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  cursor: pointer;
  transition: transform 0.15s ease, border 0.2s ease, background 0.2s ease;
}

.device-icon-btn:focus-visible {
  outline: 2px solid var(--primary);
  outline-offset: 2px;
}

.device-icon-btn:active {
  transform: scale(0.95);
}

.device-icon {
  width: 40px;
  height: 40px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
}

.light-text-block {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 54px;
  flex: 1;
}

.device-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
}

.device-tag {
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 10px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.8);
}

.light-label {
  margin: 0;
  font-weight: 600;
  min-height: 22px;
}

.switch {
  position: relative;
  width: 46px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 999px;
  transition: background 0.2s;
}

.slider::before {
  content: '';
  position: absolute;
  height: 18px;
  width: 18px;
  left: 3px;
  top: 3px;
  border-radius: 50%;
  background: #050714;
  transition: transform 0.2s, background 0.2s;
}

.switch input:checked + .slider {
  background: linear-gradient(120deg, var(--primary), var(--accent));
}

.switch input:checked + .slider::before {
  transform: translateX(22px);
  background: #fff;
}

.light-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 36px;
  gap: 8px;
  flex-wrap: wrap;
}

.state-chip {
  border-radius: 999px;
  padding: 4px 12px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  min-width: 96px;
  text-align: center;
}

.state-chip.on {
  border-color: transparent;
  background: rgba(255, 255, 255, 0.18);
  color: #050714;
}

.empty-state {
  text-align: center;
  padding: 48px 24px;
}

.empty-icon {
  width: 72px;
  height: 72px;
  border-radius: 22px;
  margin: 0 auto 16px;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.placeholder-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
}

.placeholder-card {
  border-radius: 18px;
  padding: 18px;
  border: 1px dashed rgba(255, 255, 255, 0.2);
}

.system-pills {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.system-pill {
  border-radius: 16px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.system-pill.positive {
  border-color: rgba(74, 222, 128, 0.4);
}

.system-pill.warning {
  border-color: rgba(248, 181, 0, 0.4);
}

.telemetry {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.telemetry-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.status-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.25);
}

.status-dot.on {
  background: #66ffa6;
  box-shadow: 0 0 15px rgba(102, 255, 166, 0.5);
}

.tag {
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  padding: 6px 14px;
  background: transparent;
  color: var(--text);
}

.tag.compact {
  padding: 4px 10px;
  font-size: 12px;
}

.support-card {
  border-radius: 18px;
  padding: 18px;
  background: rgba(5, 7, 18, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.lights-overlay,
.device-overlay {
  position: fixed;
  inset: 0;
  background: rgba(3, 5, 15, 0.72);
  display: flex;
  align-items: flex-end;
  justify-content: flex-end;
  padding: clamp(16px, 3vw, 32px);
  padding-bottom: calc(clamp(16px, 3vw, 32px) + 110px + env(safe-area-inset-bottom, 0px));
  z-index: 20;
}

.lights-panel,
.device-panel {
  width: min(480px, 100%);
  max-height: min(80vh, 760px);
  overflow-y: auto;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.active-lights-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 16px;
}

.active-light-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
}

.device-overlay {
  align-items: center;
  justify-content: center;
}

.device-panel {
  width: min(520px, 100%);
}

.panel-section {
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.section-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.slider-row input[type='range'] {
  width: 100%;
}

.color-palette {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(32px, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.swatch {
  border-radius: 12px;
  border: 2px solid transparent;
  padding: 0;
  height: 36px;
  background: var(--swatch-color);
  cursor: pointer;
}

.swatch.active {
  border-color: #ffffff;
}

.hue-slider {
  position: relative;
  margin-top: 16px;
  padding-top: 12px;
  overflow: hidden;
}

.hue-slider input[type='range'] {
  width: 100%;
  appearance: none;
  background: transparent;
  position: relative;
  z-index: 2;
  height: 14px;
  border: none;
  outline: none;
}

.hue-track {
  position: absolute;
  inset: 0;
  border-radius: 999px;
  opacity: 0.35;
  pointer-events: none;
  z-index: 1;
}

.hue-slider input[type='range']::-webkit-slider-thumb {
  appearance: none;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6c8cff, #22c1c3);
  border: 2px solid rgba(5, 7, 20, 0.6);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.hue-slider input[type='range']::-webkit-slider-runnable-track {
  height: 14px;
  background: transparent;
  border: none;
}

.hue-slider input[type='range']::-moz-range-thumb {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: linear-gradient(135deg, #6c8cff, #22c1c3);
  border: 2px solid rgba(5, 7, 20, 0.6);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}

.hue-slider input[type='range']::-moz-range-track {
  height: 14px;
  background: transparent;
  border: none;
}

.hue-slider input[type='range']::-moz-range-progress {
  background: transparent;
}

.hue-slider input[type='range']::-ms-track {
  height: 14px;
  background: transparent;
  border-color: transparent;
  color: transparent;
}

.hue-slider input[type='range']::-ms-fill-lower,
.hue-slider input[type='range']::-ms-fill-upper {
  background: transparent;
}

.no-controls {
  margin-top: 24px;
  text-align: center;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 1100px) {
  .console,
  .console--compact {
    display: flex;
    flex-direction: column;
    gap: 18px;
  }

  .nav.rail {
    flex-direction: row;
    width: 100%;
    max-width: none;
    justify-content: space-between;
    align-items: center;
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    transform: none;
    top: auto;
    border-radius: 0;
    padding: clamp(10px, 2vh, 14px) clamp(18px, 5vw, 32px);
    padding-bottom: calc(clamp(10px, 2vh, 14px) + env(safe-area-inset-bottom, 0px));
    min-height: 0;
    max-height: 84px;
    box-sizing: border-box;
    z-index: 30;
    gap: 6px;
    border-left: none;
    border-right: none;
    border-bottom: none;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }

  .nav-btn {
    flex: 1 1 0;
    width: auto;
    height: 44px;
    border-radius: 16px;
    max-width: 64px;
    min-width: 44px;
  }

  .control4-shell {
    padding-bottom: 120px;
  }

  .right.rail {
    position: static;
  }
}

@media (max-width: 768px) {
  .dashboard-header {
    grid-template-columns: 1fr;
  }

  .room-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 6px;
  }

  .primary-actions {
    justify-content: space-between;
  }

  .scene-actions {
    justify-content: flex-start;
  }

  .room-card {
    min-height: auto;
  }

  .nav.rail {
    border-radius: 0;
    padding: clamp(10px, 2vh, 14px) clamp(16px, 6vw, 22px);
    padding-bottom: calc(clamp(10px, 2vh, 14px) + env(safe-area-inset-bottom, 0px));
    gap: 10px;
    width: 100%;
    left: 0;
    right: 0;
    top: auto;
    bottom: 0;
  }

  .room-actions {
    justify-content: flex-start;
  }

  .room-select-mobile {
    display: flex;
  }

  .room-chip-row {
    display: none;
  }

  .rooms-grid {
    grid-template-columns: 1fr;
  }

  .lights-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .lights-overlay,
  .device-overlay {
    align-items: flex-end;
    justify-content: center;
  }
}

@media (max-width: 520px) {
  .nav.rail {
    padding: clamp(10px, 2vh, 14px) clamp(12px, 8vw, 18px);
    padding-bottom: calc(clamp(10px, 2vh, 14px) + env(safe-area-inset-bottom, 0px));
    border-radius: 0;
    left: 0;
    right: 0;
    bottom: 0;
  }

  .light-head {
    flex-direction: row;
    align-items: center;
    gap: 12px;
  }

  .light-card {
    padding: 12px;
  }

  .lights-grid {
    display: flex;
    flex-direction: column;
    gap: 10px;
  }

  .light-card {
    flex-direction: row;
    align-items: center;
    width: 100%;
    max-width: 520px;
    margin: 0 auto;
    min-height: 96px;
  }
}
</style>
