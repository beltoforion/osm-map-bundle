import Map from 'ol/Map';

import { Tile as TileLayer, Vector as VectorLayer } from 'ol/layer';
import OSM from 'ol/source/OSM';
import View from 'ol/View';
import ViewOptions from 'ol/View';
import Coordinate from 'ol/coordinate';
import TileState from 'ol/TileState';
import ZoomSlider from 'ol/control/ZoomSlider';
import { defaults as defaultControls } from 'ol/control';
import { useGeographic } from 'ol/proj';
import VectorSource from 'ol/source/Vector';
import GPX from 'ol/format/GPX';
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style';
import { coordinate } from 'openlayers';
import { Extent } from 'ol/extent';

export class OsmMap { 
    private lon : number = 0
    private lat : number = 0
    private map : Map | null = null
    private view : View | null = null;
    private gpxLayer : VectorLayer | null = null;
    private rasterLayer : TileLayer | null = null;
    private lineStyle : Style | null = null;
    private markerStyle : Style | null = null;

    
    public constructor(config : any) {
        useGeographic();

        var divMap = document.getElementById(config.id) as HTMLDivElement;
        if (divMap == null)
        {
            throw Error('The html document does not contain a div element named "' + config.id + '"')
        }

        this.view = new View({
             center: [config.lon, config.lat],
             zoom: 14,
             minZoom: 9,
             maxZoom: 20,
           })
        
        this.lineStyle = new Style({
          stroke: new Stroke({
            color: '#f00',
            width: 4,
          })
        })

        this.markerStyle = new Style({
            image: new CircleStyle({
              fill: new Fill({
                color: 'rgba(255,255,0,0.4)',
              }),
              radius: 5,
              stroke: new Stroke({
                color: '#ff0',
                width: 1
              })
            })
          })

        this.gpxLayer = new VectorLayer({
           source: new VectorSource({
             url: config.gpx,
             format: new GPX(),
           }),
           style: this.lineStyle
         });

        this.rasterLayer = new TileLayer({
          source: new OSM(),
        })
        
        this.map = new Map({
            layers: [this.rasterLayer, this.gpxLayer ],
            target: divMap.id,
            view: this.view,
            controls: defaultControls().extend([new ZoomSlider()])
          });

          var extent = this.gpxLayer.getExtent();
          // if (extent === undefined)
          // {
          //   throw new Error('Gpx layer Extent is undefined!');
          // }

          // this.view.fit(extent)
    }
}