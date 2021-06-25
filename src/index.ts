import { OsmMap } from './osm-gps-map'

//export var map : OsmMap | null = null

export function createGpxMap(config: any) : OsmMap {


  var map : OsmMap= new OsmMap(config);
  return map
}