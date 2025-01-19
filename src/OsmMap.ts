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


export class OsmMap {
  private map: Map | undefined = undefined;
  private jsonStyles : FeatureStyleDictionary | undefined = undefined;

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
      text.setText(prop.name);
    }

    return layersStyle;
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

  public addTileLayer(url:string) : OsmMap {
    if (!this.map) {
      throw new Error('The map object is not initialized');
    }

    var tileLayer = new TileLayer({
      source: new XYZ({
        url: url,
        tileSize: 256
      })
    });

    this.map.addLayer(tileLayer);

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
