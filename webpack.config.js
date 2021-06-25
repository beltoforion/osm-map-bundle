module.exports = {
    entry: './src/index.ts',
    module: {
        rules: [
          {
            test: /\.tsx?$/,
            use: 'ts-loader',
            exclude: /node_modules/
          }
        ]
    },
    resolve: {
        extensions: [ '.tsx', '.ts', '.js' ]
    },
    output: {
        path: __dirname + '/dist', 
        filename: 'osm-gps-map-bundle.js',
        library: 'OsmMap'
//        pathinfo: true
    },
    devtool: 'source-map'
}