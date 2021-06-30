import Map from 'ol/Map';

import { Tile as TileLayer, Vector as VectorLayer } from 'ol/layer';
import OSM from 'ol/source/OSM';
import View from 'ol/View';
import ZoomSlider from 'ol/control/ZoomSlider';
import { defaults as defaultControls } from 'ol/control';
import { useGeographic } from 'ol/proj';
import VectorSource from 'ol/source/Vector';
import GPX from 'ol/format/GPX';
import { Circle as CircleStyle, Fill, Stroke, Style, Text } from 'ol/style';
import GeoJSON from 'ol/format/GeoJSON';

export class GpxOsmMap { 
    private map : Map | undefined = undefined
    private gpxLayer : VectorLayer | undefined = undefined;
    private rasterLayer : TileLayer | undefined = undefined;
    private annotationLayer : VectorLayer | null = null;
    private lineStyle : Style | undefined = undefined;

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

    public constructor(config : any) {
        useGeographic();

        var divMap = document.getElementById(config.id) as HTMLDivElement;
        if (divMap == null)
        {
            throw Error('The html document does not contain a div element named "' + config.id + '"')
        }

        var view : View = new View({
             center: [config.lon, config.lat],
             zoom : 10,
             minZoom: config.minZoom ?? 9,
             maxZoom: config.maxZoom ?? 20,
           })
        
        this.lineStyle = new Style({
          stroke: new Stroke({
            color: '#f00',
            width: 4,
          })
        })

        var gpxLayer = this.gpxLayer = new VectorLayer({
            visible: true,
            source: new VectorSource({
              url: config.gpx,
              format: new GPX(),
           }),
           style: this.lineStyle
         });

        if (config.annotation_geojson != null) {
          this.annotationLayer = new VectorLayer({
            visible: true,
            source: new VectorSource({
              features: new GeoJSON().readFeatures(config.annotation_geojson),
            }),
            style: this.markerStyleFunction 
          });
        }

        // Fit gpx to map after first render
        this.gpxLayer.once("postrender", e => {
          view.fit(gpxLayer.getSource().getExtent(), { padding: [60, 60, 60, 60] });
        });

        this.rasterLayer = new TileLayer({
          source: new OSM(),
        })
        
        this.map = new Map({
            layers: [this.rasterLayer, this.gpxLayer ],
            target: divMap.id,
            view: view,
            controls: defaultControls().extend([new ZoomSlider()])
          });

          if (this.annotationLayer != null)
            this.map.addLayer( this.annotationLayer)
    }
}