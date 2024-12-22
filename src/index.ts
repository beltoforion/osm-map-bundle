import { GpxOsmMap, GpxOsmMapConfig } from './GpxOsmMap'

export { GpxOsmMap, GpxOsmMapConfig };

export function createGpxMap(config: GpxOsmMapConfig) : GpxOsmMap {
  var map : GpxOsmMap= new GpxOsmMap(config);
  return map
}