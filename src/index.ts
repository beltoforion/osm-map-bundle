import { GpxOsmMap } from './GpxOsmMap'

//export var map : OsmMap | null = null

export function createGpxMap(config: any) : GpxOsmMap {
  var map : GpxOsmMap= new GpxOsmMap(config);
  return map
}