const path = require('path');
const CopyWebpackPlugin = require("copy-webpack-plugin");

module.exports = {
  entry: './src/index.ts', // Entry file
  module: {
    rules: [
      {
        test: /\.tsx?$/, // TypeScript files
        use: 'ts-loader',
        exclude: /node_modules/,
      },
    ],
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
  },
  output: {
    path: path.resolve(__dirname, 'dist'), // Output directory
    filename: 'osm-map-bundle.js', // Output file
    library: 'OsmMap', // Global variable
    libraryTarget: 'umd', // Universal Module Definition
    globalObject: 'this', // Ensure compatibility
  },
  devtool: 'source-map', // Source maps for debugging
  plugins: [
    new CopyWebpackPlugin({
      patterns: [
        { from: path.resolve(__dirname, 'assets'), to: 'assets' }
      ]
    })
  ]
};
