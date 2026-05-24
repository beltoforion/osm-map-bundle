import { Tile as TileLayer, Vector as VectorLayer } from 'ol/layer';
import { Attribution, FullScreen, defaults as defaultControls } from 'ol/control';
import { useGeographic } from 'ol/proj';
import { Stroke, Style } from 'ol/style';
import GeoJSON from 'ol/format/GeoJSON';
import GPX from 'ol/format/GPX';
import Map from 'ol/Map';
import VectorSource from 'ol/source/Vector';
import View from 'ol/View';
import XYZ from 'ol/source/XYZ';
import ZoomSlider from 'ol/control/ZoomSlider';

import { FeatureStyleDictionary } from './FeatureStyles';
import pkg from '../package.json';


export class OsmMap {
  private map: Map | undefined = undefined;
  private jsonStyles : FeatureStyleDictionary | undefined = undefined;
  // Zoomstufe, ab der POI-Textlabels sichtbar sind. Darunter werden sie ausgeblendet.
  // 0 = nie ausblenden (Standard).
  private labelMinZoom : number = 0;

  private markerStyleFunction(feature : any, resolution : any) : Style {
    if (!this.jsonStyles) {
      throw new Error('The jsonStyles property is not defined');
    }

    const geometryType = feature.getGeometry().getType();
    
    var prop = feature.getProperties();
    if (!prop || !prop.type) {
      throw new Error(`Feature properties or 'type' is missing. Properties: ${JSON.stringify(prop)}`);
    }
    
    const featureStyle = this.jsonStyles[prop.type];
    if (!featureStyle) {
      throw new Error(`No style found for feature type: ${prop.type}`);
    }

    var layersStyle = featureStyle.getStyle();
    var text = layersStyle.getText();
    if (text) {
      // Label nur anzeigen, wenn die aktuelle Zoomstufe die Schwelle erreicht.
      const view = this.map!.getView();
      const zoom = view.getZoomForResolution(resolution) ?? view.getZoom() ?? 0;
      text.setText(zoom >= this.labelMinZoom ? prop.name : '');
    }

    return layersStyle;
  }

  // Setzt die Zoomstufe, ab der POI-Textlabels eingeblendet werden. Darunter sind
  // nur die Marker/Icons sichtbar. Wert 0 = Labels immer anzeigen.
  public setLabelMinZoom(zoom : number) : OsmMap {
    this.labelMinZoom = zoom;
    this.map?.render();  // Neuzeichnen, damit die Stilfunktion sofort neu greift.
    return this;
  }

  // Zugriff auf die zugrunde liegende OpenLayers-Karte (z.B. fuer eigene Event-Handler).
  public getMap() : Map {
    if (!this.map) {
      throw new Error('The map object is not initialized');
    }
    return this.map;
  }

  // Verdrahtet ein optionales Info-Panel rein deklarativ ueber HTML-Attribute. Der Client
  // bestimmt Markup, Platzierung und Styling selbst; fehlende Elemente werden ignoriert,
  // ein nicht vorhandenes Panel erfordert keinen Aufruf. Unterstuetzte Attribute:
  //   data-osm-version  -> textContent wird auf die Versionsnummer gesetzt
  //   data-osm-coords   -> textContent zeigt den Kartenmittelpunkt (aktualisiert beim Verschieben)
  //   data-osm-copy     -> Klick kopiert die aktuellen Koordinaten in die Zwischenablage
  //                        und loest ein 'osm:copy'-CustomEvent (detail: {text, ok}) aus.
  // Format der Koordinaten ist ueber options.format anpassbar; options.root grenzt die Suche ein.
  public bindInfoControls(options : { root? : ParentNode, format? : (lat : number, lon : number) => string } = {}) : OsmMap {
    if (!this.map) {
      throw new Error('The map object is not initialized');
    }
    const map = this.map;
    const root : ParentNode = options.root ?? document;
    const format = options.format ?? ((lat : number, lon : number) => `${lat.toFixed(6)}, ${lon.toFixed(6)}`);

    // Versionsnummer
    root.querySelectorAll('[data-osm-version]').forEach((el) => {
      (el as HTMLElement).textContent = pkg.version;
    });

    const centerText = () : string => {
      const c = map.getView().getCenter();  // [lon, lat] (useGeographic)
      if (!c) {
        return '';
      }
      const [lon, lat] = c;
      return (lon === undefined || lat === undefined) ? '' : format(lat, lon);
    };

    // Koordinaten-Anzeige (live)
    const coordEls = root.querySelectorAll('[data-osm-coords]');
    if (coordEls.length > 0) {
      const update = () => {
        const t = centerText();
        coordEls.forEach((el) => { (el as HTMLElement).textContent = t; });
      };
      map.on('moveend', update);
      update();
    }

    // Copy-Button(s)
    root.querySelectorAll('[data-osm-copy]').forEach((el) => {
      el.addEventListener('click', async () => {
        const text = centerText();
        let ok = true;
        try {
          await navigator.clipboard.writeText(text);
        } catch (e) {
          // Fallback fuer unsichere Kontexte (z.B. file://)
          const ta = document.createElement('textarea');
          ta.value = text;
          ta.style.position = 'fixed';
          ta.style.opacity = '0';
          document.body.appendChild(ta);
          ta.select();
          try { ok = document.execCommand('copy'); } catch (e2) { ok = false; }
          document.body.removeChild(ta);
        }
        el.dispatchEvent(new CustomEvent('osm:copy', { detail: { text, ok }, bubbles: true }));
      });
    });

    return this;
  }

  // Wird von bindPermalink gesetzt; erlaubt der Seite, den URL-Hash nach Nicht-Karten-
  // Aenderungen (z.B. Ebenenwechsel) zu aktualisieren. No-op, solange bindPermalink nicht
  // aufgerufen wurde.
  public updatePermalink : () => void = () => {};

  // Permalink: kodiert die aktuelle Ansicht (Zoom/Breite/Laenge) im URL-Hash, sodass sich eine
  // Position als Browser-Lesezeichen merken oder per Link teilen laesst. Format:
  //   #<zoom>/<lat>/<lon>   optional gefolgt von seitenspezifischen Extra-Parametern, z.B.
  //   #16/50.99335/13.35779&layer=dgm1
  // Beim Laden wird ein vorhandener Hash angewendet (ueberschreibt setView); bei jeder
  // Kartenbewegung wird der Hash via history.replaceState aktualisiert (keine History-Eintraege,
  // kein Scroll-Sprung). options.getState/setState binden seitenspezifischen Zustand an den Hash,
  // options.precision steuert die Nachkommastellen von lat/lon (Standard 5).
  public bindPermalink(options : {
    precision? : number,
    getState? : () => Record<string, string>,
    setState? : (state : Record<string, string>) => void,
  } = {}) : OsmMap {
    if (!this.map) {
      throw new Error('The map object is not initialized');
    }
    const map = this.map;
    const view = map.getView();
    const precision = options.precision ?? 5;

    // "12.34" statt "12.340000" - ueberfluessige Nullen entfernen.
    const trim = (n : number, digits : number) : string => parseFloat(n.toFixed(digits)).toString();

    const parseHash = () => {
      const raw = window.location.hash.replace(/^#/, '');
      if (!raw) {
        return null;
      }
      const amp = raw.indexOf('&');
      const core = amp >= 0 ? raw.slice(0, amp) : raw;          // "<zoom>/<lat>/<lon>"
      const rest = amp >= 0 ? raw.slice(amp + 1) : '';          // "key=val&..."
      const parts = core.split('/');
      if (parts.length < 3) {
        return null;
      }
      const zoom = parseFloat(parts[0]!);
      const lat = parseFloat(parts[1]!);
      const lon = parseFloat(parts[2]!);
      if (Number.isNaN(zoom) || Number.isNaN(lat) || Number.isNaN(lon)) {
        return null;
      }
      const extra : Record<string, string> = {};
      new URLSearchParams(rest).forEach((v, k) => { extra[k] = v; });
      return { zoom, lat, lon, extra };
    };

    const writeHash = () => {
      const center = view.getCenter();  // [lon, lat] (useGeographic)
      const zoom = view.getZoom();
      if (!center || zoom === undefined) {
        return;
      }
      const [lon, lat] = center;
      if (lon === undefined || lat === undefined) {
        return;
      }
      let hash = `${trim(zoom, 2)}/${trim(lat, precision)}/${trim(lon, precision)}`;
      if (options.getState) {
        const params = new URLSearchParams(options.getState()).toString();
        if (params) {
          hash += '&' + params;
        }
      }
      history.replaceState(null, '', '#' + hash);
    };

    // 1) Vorhandenen Hash anwenden - erst der Extra-Zustand (z.B. Ebene -> korrektes maxZoom),
    //    dann Mittelpunkt und Zoom.
    const initial = parseHash();
    if (initial) {
      if (options.setState) {
        options.setState(initial.extra);
      }
      view.setCenter([initial.lon, initial.lat]);
      view.setZoom(initial.zoom);
    }

    // 2) Bei jeder Kartenbewegung schreiben (moveend ist bereits gedrosselt) + einmal initial,
    //    damit der Link sofort teilbar ist.
    map.on('moveend', writeHash);
    writeHash();

    // 3) Seiten koennen den Hash nach Nicht-Karten-Aenderungen (z.B. Ebenenwechsel) aktualisieren.
    this.updatePermalink = writeHash;

    return this;
  }

  // Blendet ein Fadenkreuz in der Kartenmitte ein, solange die Karte bewegt wird
  // (movestart..moveend), damit der aktuelle Mittelpunkt sichtbar ist. Das Overlay-Element wird
  // selbst erzeugt und in den Karten-Viewport gehaengt; es faengt keine Klicks ab
  // (pointer-events:none). Dunkle Linien mit hellem Halo (SVG) sorgen fuer Kontrast auf hellen
  // wie dunklen Kacheln. Groesse/Farben sind ueber options anpassbar.
  public enableCenterCrosshair(options : { size? : number, color? : string, haloColor? : string } = {}) : OsmMap {
    if (!this.map) {
      throw new Error('The map object is not initialized');
    }
    const map = this.map;
    const size = options.size ?? 40;
    const color = options.color ?? '#1c1c24';
    const halo = options.haloColor ?? '#ffffff';

    // viewBox bleibt 0..40; die Linien lassen in der Mitte eine Luecke, ein Punkt markiert das Zentrum.
    const svg =
      `<svg xmlns='http://www.w3.org/2000/svg' width='${size}' height='${size}' viewBox='0 0 40 40'>` +
      `<g fill='none' stroke-linecap='round'>` +
      `<path stroke='${halo}' stroke-width='4' opacity='0.85' d='M20 3V15M20 25V37M3 20H15M25 20H37'/>` +
      `<path stroke='${color}' stroke-width='2' d='M20 3V15M20 25V37M3 20H15M25 20H37'/>` +
      `</g><circle cx='20' cy='20' r='1.6' fill='${color}'/></svg>`;

    const el = document.createElement('div');
    el.style.cssText =
      `position:absolute;left:50%;top:50%;width:${size}px;height:${size}px;` +
      `transform:translate(-50%,-50%);pointer-events:none;z-index:1;` +
      `opacity:0;transition:opacity 140ms ease;` +
      `background:center/contain no-repeat url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
    map.getViewport().appendChild(el);

    map.on('movestart', () => { el.style.opacity = '1'; });
    map.on('moveend', () => { el.style.opacity = '0'; });

    return this;
  }

  public setView(coord : [number, number], zoom_min: number, zoom_max : number, zoom_initial : number) : OsmMap {
    if (!this.map) {
      throw new Error('The map object is not initialized');
    }

    const view : View = new View({
      center: [coord[1], coord[0]],
      zoom: zoom_initial,
      minZoom: zoom_min,
      maxZoom: zoom_max,
    });

    this.map.setView(view);

    return this;
  }

  public addGpxLayer(url:string, color : string, width : number) : OsmMap {
    if (!this.map) {
      throw new Error('The map object is not initialized');
    }

    var gpxLayer = new VectorLayer({
        visible: true,
        source: new VectorSource({
          url: url,
          format: new GPX(),
        }),
        style: new Style({
          stroke: new Stroke({
            color: color || '#f00', // Default to red if no color specified
            width: width || 4, // Default width of 4
          }),
        }),
    });

    this.map.addLayer(gpxLayer);

    return this;
  }

  public addTileLayer(url:string, maxZoom? : number) : OsmMap {
    if (!this.map) {
      throw new Error('The map object is not initialized');
    }

    // maxZoom = hoechste Zoomstufe, fuer die Kacheln existieren. Ist die Ansicht
    // weiter hineingezoomt, skaliert OpenLayers diese Kacheln hoch (Over-Zoom),
    // statt nicht vorhandene Kacheln anzufordern (sonst leere Flaechen).
    var source = new XYZ({
      url: url,
      tileSize: 256,
      maxZoom: maxZoom,
    });

    this.map.addLayer(new TileLayer({ source: source }));

    return this;
  }

  public addJsonLayer(json : any, jsonStyles : FeatureStyleDictionary) : OsmMap {
    if (!this.map) {
      throw new Error('The map object is not initialized');
    }

    if (!jsonStyles) {
      throw new Error('The jsonStyles parameter is required');
    }

    this.jsonStyles = jsonStyles;

    var jsonLayer = new VectorLayer({
      source: new VectorSource({
        features: new GeoJSON().readFeatures(json),
      }),
      style: this.markerStyleFunction.bind(this)
    });

    this.map.addLayer(jsonLayer);

    return this
  }

  public constructor(id: string) {
    useGeographic();

    const divMap = document.getElementById(id) as HTMLDivElement;
    if (!divMap) {
      throw new Error('The HTML document does not contain a div element named "' + id + '"');
    }

    this.map = new Map({   
      target: id,
      controls: defaultControls({attribution : true}).extend([new ZoomSlider(), new FullScreen()]),
    });

    // change mouse cursor when over marker
    this.map.on('pointermove', (e) => {
      if (this.map==undefined) {
        return;
      }

      let cursorChanged = false;
      
      this.map.forEachFeatureAtPixel(e.pixel, (feature, layer) => {
        if (this.map==undefined) {
          return;
        }
  
        const properties = feature.getProperties();
        const url = properties.url;

        if (url !== undefined) {
          this.map.getTargetElement().style.cursor = 'pointer';
          cursorChanged = true;
        }        
      });

      if (!cursorChanged) {
        this.map.getTargetElement().style.cursor = '';
      }
    });

    this.map.on('click', (e) => {
      if (this.map==undefined) {
        return;
      }

      this.map.forEachFeatureAtPixel(e.pixel, (feature, layer) => {
        const properties = feature.getProperties();
        const url = properties.url;

        if (url) {
//          window.open(url, '_blank');
          window.location.href = url;
        }
      });    
    });
  }
}
