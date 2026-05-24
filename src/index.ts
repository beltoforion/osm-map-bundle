import pkg from '../package.json';

export { OsmMap } from './OsmMap';
export { FeatureStyleDictionary, LineStyle, IconStyle, AnnotatedPointStyle } from './FeatureStyles';

// Versionsnummer aus package.json - im UMD-Namespace als OsmMap.VERSION verfuegbar.
export const VERSION: string = pkg.version;
