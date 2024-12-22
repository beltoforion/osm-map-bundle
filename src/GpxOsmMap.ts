import { Tile as TileLayer, Vector as VectorLayer } from 'ol/layer';
import { defaults as defaultControls } from 'ol/control';
import { useGeographic } from 'ol/proj';
import { Circle as CircleStyle, Fill, Stroke, Style, Text } from 'ol/style';
import { Extent } from 'ol/extent';
import GeoJSON from 'ol/format/GeoJSON';
import GPX from 'ol/format/GPX';
import Map from 'ol/Map';
import OSM from 'ol/source/OSM';
import VectorSource from 'ol/source/Vector';
import View from 'ol/View';
import XYZ from 'ol/source/XYZ';
import ZoomSlider from 'ol/control/ZoomSlider';


export class GpxOsmMapConfig {
  public id: string;
  public lon: number;
  public lat: number;
  
  public minZoom: number = 9;
  public maxZoom: number = 20;
  public initialZoom: number = 10;

  public local_tile_folder?: string;
  public gpxLayers?: { url: string; color?: string; width?: number }[];
  public annotation_geojson?: any;

  public setZoom(minZoom: number, maxZoom: number, initialZoom: number) {
    this.minZoom = minZoom;
    this.maxZoom = maxZoom;
    this.initialZoom = initialZoom;
  }

  public setGpxLayers(gpxLayers: { url: string; color?: string; width?: number }[]) {
    this.gpxLayers = gpxLayers;
  }

  public setAnnotationLayer(annotation_geojson: string) {
    this.annotation_geojson = annotation_geojson;
  }

  constructor(
    id: string,
    lon: number,
    lat: number,
    local_tile_folder?: string) 
  {
    this.id = id;
    this.lon = lon;
    this.lat = lat;
    this.local_tile_folder = local_tile_folder;
  }
}

export class GpxOsmMap {
  private map: Map | undefined = undefined;
  private gpxLayers: VectorLayer<VectorSource>[] = [];
  private annotationLayer : VectorLayer<VectorSource> | undefined = undefined;
  private rasterLayer: TileLayer<OSM> | undefined = undefined;

  private markerStyleFunction(feature : any, resolution : any) : Style {
    return new Style({
      image: new CircleStyle({
        fill: new Fill({ color: 'rgba(255,255,0,0.7)' }),
        radius: 8,
        stroke: new Stroke({ color: '#ff0', width: 1 })
      }),
      text : new Text({
        text: feature.get('name'),
        scale: 1.3,
        offsetX: 0,
        offsetY: 20,
        fill: new Fill({ color: '#000000' }),
        stroke: new Stroke({ color: '#FFFF99', width: 3.5 })
      })
    })
  }

  public constructor(config: GpxOsmMapConfig) {
    useGeographic();

    const divMap = document.getElementById(config.id) as HTMLDivElement;
    if (!divMap) {
      throw new Error('The HTML document does not contain a div element named "' + config.id + '"');
    }

    const view : View = new View({
      center: [config.lon, config.lat],
      zoom: config.initialZoom,
      minZoom: config.minZoom,
      maxZoom: config.maxZoom,
    });

    // If a local tile folder is specified, use it. Otherwise, use OSM tiles
    var source_xyz : XYZ = (config.local_tile_folder !== "") 
      ? new XYZ({
        url: `./${config.local_tile_folder}/{z}/{x}/{y}.png`, 
        tileSize: 256
      })
      : new OSM();

    this.rasterLayer = new TileLayer({ source: source_xyz });

    // Process multiple GPX layers
    if (config.gpxLayers != null)
    {
      config.gpxLayers.forEach((gpxConfig) => {
        const gpxLayer = new VectorLayer({
          visible: true,
          source: new VectorSource({
            url: gpxConfig.url,
            format: new GPX(),
          }),
          style: new Style({
            stroke: new Stroke({
              color: gpxConfig.color || '#f00', // Default to red if no color specified
              width: gpxConfig.width || 4, // Default width of 4
            }),
          }),
        });

        // Fit the map view to the extent of the first GPX layer
        if (this.gpxLayers.length === 0) {
          gpxLayer.once('postrender', () => {
            const extent: Extent = gpxLayer.getSource()?.getExtent() ?? [0, 0, 0, 0];
            view.fit(extent, { padding: [60, 60, 60, 60] });
          });
        }

        this.gpxLayers.push(gpxLayer);
      });
    }


    // Initialize the map
    this.map = new Map({
      layers: [this.rasterLayer, ...this.gpxLayers],
      target: divMap.id,
      view: view,
      controls: defaultControls().extend([new ZoomSlider()]),
    });

    if (config.annotation_geojson != null) {
      this.annotationLayer = new VectorLayer({
        visible: true,
        source: new VectorSource({
          features: new GeoJSON().readFeatures(config.annotation_geojson),
        }),
        style: this.markerStyleFunction 
      });

      this.map.addLayer( this.annotationLayer)
    }
  }
}
