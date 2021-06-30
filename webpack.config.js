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
        filename: 'gpx-osm-map-bundle.js',
        library: 'GpxOsmMap'
//        pathinfo: true
    },
    devtool: 'source-map'
}