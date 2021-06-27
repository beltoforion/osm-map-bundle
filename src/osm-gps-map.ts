import Map from 'ol/Map';

import { Tile as TileLayer, Vector as VectorLayer } from 'ol/layer';
import OSM from 'ol/source/OSM';
import View from 'ol/View';
import ZoomSlider from 'ol/control/ZoomSlider';
import { defaults as defaultControls } from 'ol/control';
import { useGeographic } from 'ol/proj';
import VectorSource from 'ol/source/Vector';
import GPX from 'ol/format/GPX';
import { Circle as CircleStyle, Fill, Stroke, Style } from 'ol/style';

export class OsmMap { 
    private map : Map | undefined = undefined
    private gpxLayer : VectorLayer | undefined = undefined;
    private rasterLayer : TileLayer | undefined = undefined;
    private lineStyle : Style | undefined = undefined;
    private markerStyle : Style | undefined = undefined;

    
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

        var gpxLayer = this.gpxLayer = new VectorLayer({
            visible: true,
            source: new VectorSource({
              url: config.gpx,
              format: new GPX(),
           }),
           style: this.lineStyle
         });

        // Fit gpx to map after first render
        this.gpxLayer.once("postrender", e => {
          view.fit(gpxLayer.getSource().getExtent(), { padding: [40, 40, 40, 40] });
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
    }
}